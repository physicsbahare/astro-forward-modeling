"""Freeze corrected structures, source photometry and supported bandpass fluxes.

Reuses the recovered branch interpolation and source cleaning definitions.
No fits run here. All 403 IDs and unsupported inputs remain in the bundle.
"""
from pathlib import Path
import itertools,json,hashlib,importlib.metadata
import numpy as np,pandas as pd,h5py
from astropy.io import fits
from astropy.cosmology import Planck18
from scipy.ndimage import binary_dilation
from skimage.restoration import denoise_wavelet
from gold91_recovery_audit import load_functions,source_theta,adapters,sha,atomic_json
from lenstronomy.Util import param_util

def supported_flux(fluxes,curves,z,*,minimum_coverage=.99):
    from verification.nircam_throughput_sensitivity import fnu_response_moments,curved_fnu_bandpass_weights,interpolation_weights,mapped_target_moments
    means={b:fnu_response_moments(c.wavelength_um,c.throughput,1)[1] for b,c in curves.items()}
    support={}
    for b,c in curves.items():
        significant=c.throughput>c.throughput.max()*.001
        support[b]=(float(c.wavelength_um[significant].min()),float(c.wavelength_um[significant].max()))
    target=curves['F444W'];lam=target.wavelength_um*(1+z)/4;weight=target.throughput/lam
    candidates=[]
    for bands in itertools.combinations([b for b in curves if b in fluxes and np.isfinite(fluxes[b]) and fluxes[b]>0],3):
        lo=min(support[b][0] for b in bands);hi=max(support[b][1] for b in bands)
        coverage=np.trapezoid(weight*((lam>=lo)&(lam<=hi)),lam)/np.trapezoid(weight,lam)
        if coverage>=minimum_coverage:candidates.append((np.log(hi/lo),bands,float(coverage)))
    if not candidates:raise ValueError('SPECTRAL_SUPPORT_FAILURE: no positive three-band response envelope covers >=99% mapped throughput')
    _,bands,coverage=min(candidates,key=lambda t:(t[0],t[1]))
    matrix=np.vstack([fnu_response_moments(curves[b].wavelength_um,curves[b].throughput,2) for b in bands])
    target_m=mapped_target_moments(fnu_response_moments(target.wavelength_um,target.throughput,2),z,3.)
    weights=interpolation_weights(matrix,target_m)
    value=float(weights@np.array([fluxes[b] for b in bands]))
    if not np.isfinite(value) or value<=0:raise ValueError('NONPOSITIVE_FULL_THROUGHPUT_FLUX')
    return dict(source_bands=list(bands),source_weights=weights.tolist(),mapped_response_coverage=coverage,
        support_definition='envelope of source passband wavelengths with T>0.001 peak; >=99% target photon-response coverage',
        source_equivalent_target_fnu_jy=value,negative_weight_l1=float(-weights[weights<0].sum()),
        source_moment_condition=float(np.linalg.cond(matrix)))

def prepare(project,out):
    import sys
    project=Path(project);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(project/'astro-forward-modeling'));sys.path.insert(0,str(project/'Codes'))
    from passive_disk_forward_model import central_segment_mask
    from verification.nircam_throughput_sensitivity import load_mean_throughput
    curve_root=Path('/home/bahareh/nircam_throughputs_Jan2025_v7/nircam_throughputs/mean_throughputs')
    bands=('F115W','F150W','F277W','F444W');curves={b:load_mean_throughput(b,curve_root) for b in bands}
    paths=[Path(__file__),project/'astro-forward-modeling/scripts/corrected_four_stage.py',
        project/'astro-forward-modeling/scripts/gold91_recovery_audit.py',project/'astro-forward-modeling/scripts/integrated_bt_normalization.py',
        project/'astro-forward-modeling/verification/nircam_throughput_sensitivity.py',project/'Codes/passive_disk_forward_model.py',
        project/'Codes/05_GOLD403_z3_MODEL_based_injection_FAST_PILOT.ipynb',project/'Data/passive_disk_GOLD403_with_visual_flags.csv',
        project/'Results/Project_Completion_20261011/source_snapshots/gold91_generating_notebook.json',
        project/'Data/forward_z3_GOLD403_v1/context_bank/contexts.h5',project/'Data/forward_z3_GOLD403_v1/context_bank/context_manifest.csv',
        project/'Data/real_cutouts_GOLD403_for_z3/real_cutout_manifest.csv',
        Path('/home/bahareh/Desktop/Projects/Data_General/Cosmos_Web/COSMOSWeb_mastercatalog_v1.1.fits')]
    manifest=pd.read_csv(project/'Data/real_cutouts_GOLD403_for_z3/real_cutout_manifest.csv')
    paths += [Path(p) for p in manifest.output_h5.unique()]
    paths += [curve_root/f'{b}_May2024_mean_system_throughput.txt' for b in bands]
    psf_root=project/'Data/forward_z3_GOLD403_v1/cache/cosmos_web_psfs_v5.0'
    paths += list(psf_root.glob('cosmos_web_psf_jwst_f*w_*_v5.0.psf'))
    inputs={str(p):sha(p) for p in sorted(set(paths))}
    policy=dict(method='parametric families fixed at mapped morphology; exact integrated full-throughput amplitude',z_target=3.,
        spectral_coverage=.99,source_triplet='narrowest positive supported three-band response envelope',native_psf='nearest valid morphology band per branch at actual source position',
        normalization='common finite-stamp assigned flux; integrated B/T invariant, aperture/numerical ratios explicit',supersampling=2,
        fit_bounds='no truth clipping; radius lower<=min(1e-4,0.1*truth), upper>=max(stamp radius,4*truth)',
        real_SNR='deterministic injected-source aperture flux / original-context blank-aperture sigma; no second noise')
    fingerprint=hashlib.sha256(json.dumps(dict(inputs=inputs,policy=policy),sort_keys=True).encode()).hexdigest()
    header=out/'input_manifest.json'
    if header.exists():
        old=json.loads(header.read_text())
        if old['fingerprint']!=fingerprint:raise RuntimeError('Input/method identity changed; choose a new output area')
        if (out/'models.json').exists():return json.loads((out/'models.json').read_text())
    atomic_json(header,dict(inputs=inputs,policy=policy,fingerprint=fingerprint,
        environment={k:importlib.metadata.version(k) for k in ['numpy','scipy','pandas','astropy','galight','lenstronomy','galsim','emcee']}))
    rawcurves={b:(c.wavelength_um,c.throughput) for b,c in curves.items()}
    source=project/'Results/Project_Completion_20261011/source_snapshots/gold91_generating_notebook.json'
    ns=dict(np=np,CURVES=rawcurves,TARGET_FILTER='F444W',Z_TARGET=3.,AVAILABLE_MORPH_BANDS=bands,INTERP_WEIGHT_TOL=1e-6,
            _SINGLE_MORPH_CACHE={},_BD_MORPH_CACHE={})
    names={'photon_weighted_mean_lambda_um','mapped_target_effective_lambda_um','_band_effective_lambda_um',
        '_single_branch_valid','_bd_branch_valid','_available_branch_measurements','_closest_valid_bracketing_pair',
        '_log_interp_positive','_linear_interp','wavelength_interpolated_single_morphology','wavelength_interpolated_bd_morphology'}
    load_functions(source,[5],ns,names)
    clean_ns=dict(np=np,binary_dilation=binary_dilation,denoise_wavelet=denoise_wavelet,central_segment_mask=central_segment_mask,
        SOURCE_MASK_DILATION_PIX=8,SOURCE_WAVELET_LEVELS=3)
    load_functions(project/'Codes/05_GOLD403_z3_MODEL_based_injection_FAST_PILOT.ipynb',[15],clean_ns,{'fit_background_plane','clean_source_band'})
    gold=pd.read_csv(project/'Data/passive_disk_GOLD403_with_visual_flags.csv',low_memory=False)
    if len(gold)!=403 or gold.id.nunique()!=403:raise ValueError('Frozen GOLD403 identity invalid')
    morph={};positions={}
    with fits.open(paths[12],memmap=True) as f:
        if not np.array_equal(np.array(f[1].data['id'][gold.row_index.to_numpy(int)],int),gold.id):raise ValueError('Catalog identity mismatch')
        for _,r in gold.iterrows():
            i=int(r.row_index);g=f[7].data[i];bd=f['B+D'].data[i];phot=f[1].data[i]
            tile=phot['tile'].decode() if isinstance(phot['tile'],bytes) else str(phot['tile'])
            positions[int(r.id)]=dict(tile=tile,x_image=float(phot['x_image']),y_image=float(phot['y_image']))
            for b in bands:
                low=b.lower();md=float(g[f'mag_disk_{low}_bd']);mb=float(g[f'mag_bulge_{low}_bd'])
                bt=1/(1+10**(-.4*(md-mb))) if 0<md<90 and 0<mb<90 else np.nan
                def q_component(label):
                    for col in [f'qratio_{label}_{low}_bd',f'q_{label}_{low}_bd',f'qratio_{low}_{label}_bd',f'axisratio_{label}_{low}_bd']:
                        if col in f[7].columns.names and 0<float(g[col])<=1:return float(g[col])
                    return float(np.clip(bd[f'{label}_axratio'],.08,1))
                morph[(int(r.id),b)]=dict(single_n=float(g[f'nsersic_{low}_sersic']),single_re_arcsec=float(g[f'rearc_{low}_sersic']),
                    single_q=float(g[f'qratio_{low}_sersic']),disk_re_arcsec=float(g[f'rearc_disk_{low}_bd']),
                    bulge_re_arcsec=float(g[f'rearc_bulge_{low}_bd']),disk_q=q_component('disk'),bulge_q=q_component('bulge'),bt=bt,morph_filter=b)
    ns['_published_morphology_for_band']=lambda r,b:morph[(int(r['id']),b)]
    helper=adapters(project,out/'fit_products');rows=[]
    for _,r in gold.iterrows():
        oid=int(r.id);record=dict(source_id=oid,z_source=float(r.z),logM=float(r.logM),fingerprint=fingerprint,status='OK',**positions[oid])
        try:
            single=ns['wavelength_interpolated_single_morphology'](r);bd=ns['wavelength_interpolated_bd_morphology'](r)
            record['model']={k:single[k] for k in ['single_n','single_re_arcsec','single_q']}
            record['model'].update({k:bd[k] for k in ['bt','disk_re_arcsec','bulge_re_arcsec','disk_q','bulge_q']})
            record['single_pair']=[single['low_band'],single['high_band']];record['bd_pair']=[bd['low_band'],bd['high_band']]
            mapped=single['target_lambda_eff_um'];record['mapped_lambda_um']=mapped
            for branch in ['single','bd']:
                valid=[b for b in bands if ns['_single_branch_valid' if branch=='single' else '_bd_branch_valid'](morph[(oid,b)])]
                record[branch+'_native_ref_band']=min(valid,key=lambda b:abs(ns['_band_effective_lambda_um'](b)-mapped))
            record['theta']=source_theta(project,oid,helper)
        except Exception as e:record.update(status='UNSUPPORTED_MORPHOLOGY',error=str(e))
        fluxes={};band_errors={};m=manifest.loc[manifest.id==oid].iloc[0]
        with h5py.File(m.output_h5) as f:
            j=int(m.h5_index)
            if int(f['id'][j])!=oid:raise ValueError('H5 identity mismatch')
            seg=f['SEGMENTATION'][j]
            for b in bands:
                try:
                    image,support,_,_=clean_ns['clean_source_band'](f[b]['SCI'][j],f[b]['ERR'][j],seg)
                    value=float(image[support&np.isfinite(image)].sum()*1e6*(.03/206265.)**2)
                    if value<=0 or not np.isfinite(value):raise ValueError('Nonpositive source flux')
                    fluxes[b]=value
                except Exception as e:band_errors[b]=str(e)
        record['source_fluxes_jy']=fluxes;record['source_band_errors']=band_errors
        try:
            spectral=supported_flux(fluxes,curves,float(r.z))
            ratio=float((4/(1+r.z))*(Planck18.luminosity_distance(r.z).value/Planck18.luminosity_distance(3).value)**2)
            record.update(spectral=spectral,source_to_target_ratio=ratio,target_fnu_jy=spectral['source_equivalent_target_fnu_jy']*ratio)
        except Exception as e:
            record['spectral_error']=str(e)
            if record['status']=='OK':record['status']='SPECTRAL_SUPPORT_FAILURE'
        rows.append(record)
        atomic_json(out/'models_partial.json',rows)
    # A saved result is reused only after input hashes and method identity match.
    previous=pd.read_csv(project/'Results/GOLD91_wavelength_interpolated_v2_branch_specific/tables/GOLD91_wavelength_interpolated_full_results.csv')
    lookup={r['source_id']:r for r in rows}
    for _,old in previous.iterrows():
        model=lookup[int(old.source_id)]['model']
        if abs(model['single_n']-old.input_single_n)>1e-9 or abs(model['bt']-old.input_bt)>1e-9:
            raise ValueError('Saved GOLD91 structural input reproduction failed')
    atomic_json(out/'models.json',rows)
    pd.DataFrame([{k:v for k,v in r.items() if k not in ['model','spectral','source_fluxes_jy','source_band_errors']} for r in rows]).to_csv(out/'model_manifest.csv',index=False)
    print('FROZEN',pd.Series([r['status'] for r in rows]).value_counts().to_dict(),flush=True)
    return rows

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.project,a.output)
