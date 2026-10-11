"""Bounded GOLD91 diagnostics using recovered, hash-recorded fitting functions.

The historical notebook is read as source; only selected function definitions
are compiled. No notebook top-level loops or original outputs are executed.
This adapter is called by Passive_Spiral_MASTER.ipynb. Its targeted Galight
experiments retain the legacy truth to diagnose existing flips; the corrected
normalization is tested separately, not silently applied to historical rows.
"""
from pathlib import Path
import ast, copy, hashlib, inspect, json, os, random, sys, time, traceback
import numpy as np
import pandas as pd
import h5py, galsim
from galsim.des import DES_PSFEx
from astropy.io import fits
from astropy.cosmology import Planck18
from astropy.wcs import WCS
from photutils.aperture import EllipticalAperture
from lenstronomy.Util import param_util, simulation_util
from lenstronomy.Data.imaging_data import ImageData
from lenstronomy.Data.psf import PSF
from lenstronomy.LightModel.light_model import LightModel
from lenstronomy.ImSim.image_model import ImageModel
from galight.data_process import DataProcess
from galight.fitting_specify import FittingSpecify
from galight.fitting_process import FittingProcess
from integrated_bt_normalization import integrated_component_amplitudes

IDS = [10109,119834,215914,232853,287626,629834,732291,752147]
PRIMARY_PROBES = [10109,215914,629834]

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(8*1024**2),b''): h.update(chunk)
    return h.hexdigest()

def atomic_json(path, value):
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value,indent=2,allow_nan=False))
    tmp.replace(path)

def load_functions(path, cells, namespace, names=None):
    notebook=json.loads(path.read_text())
    for i in cells:
        tree=ast.parse(''.join(notebook['cells'][i]['source']))
        definitions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and (names is None or n.name in names)]
        exec(compile(ast.Module(body=definitions,type_ignores=[]),str(path)+f':cell{i}','exec'),namespace)

def adapters(project, output):
    namespace=dict(globals())
    sys.path.insert(0,str(project/'Codes'))
    from passive_disk_forward_model import empirical_blank_aperture_sigma
    namespace.update(PIX=.03, PIXEL_SCALE_ARCSEC=.03,E_COMPONENT_LIMIT=.58,
                     N_NEIGHBOURS_TO_MODEL=3,BLANK_APERTURE_RADIUS_ARCSEC=.15,
                     RNG=np.random.default_rng(20260916),TARGET_FILTER='F444W',
                     PSO_REPEATS=2,FIT_DIR=output,empirical_blank_aperture_sigma=empirical_blank_aperture_sigma)
    if not hasattr(np,'int0'): np.int0=np.intp
    if not hasattr(np,'int'): np.int=int
    nb=project/'Codes/05_GOLD403_z3_MODEL_based_injection_FAST_PILOT.ipynb'
    names={'make_minimal_wcs_header','find_central_label','segmentation_geometry',
           'choose_nearest_neighbours','ellipticity_from_q_theta','center_arcsec',
           'build_galight_data_process','one_component_params','pack_source_params',
           'bd_condition','run_galight_model','_context_neighbours_model',
           '_crop_model_injection','empirical_injected_snr_model'}
    load_functions(nb,[24,26,41],namespace,names)
    load_functions(project/'astro-forward-modeling/scripts/gold403_validation_notebook_cells.py',[],namespace) if False else None
    tree=ast.parse((project/'astro-forward-modeling/scripts/gold403_validation_notebook_cells.py').read_text())
    needed={'_inside_bounds','perturb_bd_source_params'}
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in needed],type_ignores=[]),'validated_helpers','exec'),namespace)
    recovered=Path('/home/bahareh/Downloads/GOLD91_FINAL_v3_exclude_487778_clean_real_E0.ipynb')
    load_functions(recovered,[4],namespace,{'_safe_savename','_bound_hits','_neighbor_component_params','_prepare_real_context','fit_real_bd_branch'})
    return namespace

def context_psf(project,c):
    path=project/f'Data/forward_z3_GOLD403_v1/cache/cosmos_web_psfs_v5.0/cosmos_web_psf_jwst_f444w_{c.tile}_v5.0.psf'
    with fits.open(path) as f: side=int(np.ceil(f[1].header['PSFAXIS1']*f[1].header['PSF_SAMP']))
    side+=side%2==0
    im=DES_PSFEx(str(path)).getPSF(galsim.PositionD(float(c.x_f444w)+1,float(c.y_f444w)+1)).drawImage(nx=side,ny=side,scale=1,method='no_pixel').array.astype(float)
    if not np.all(np.isfinite(im)) or im.sum()<=0: raise ValueError('Invalid signed PSF')
    return im/im.sum(),path

def source_theta(project,oid,ns):
    manifest=pd.read_csv(project/'Data/real_cutouts_GOLD403_for_z3/real_cutout_manifest.csv')
    r=manifest.loc[manifest.id==oid].iloc[0]
    with h5py.File(r.output_h5) as f:
        if int(f['id'][int(r.h5_index)])!=oid: raise ValueError('H5 ID mismatch')
        seg=f['SEGMENTATION'][int(r.h5_index)]
    meta=ns['segmentation_geometry'](seg,ns['find_central_label'](seg))
    return float(meta['theta']) if meta is not None else 0.

def render(r,psf,theta):
    light=LightModel(['SERSIC_ELLIPSE']*2,sersic_major_axis=True)
    model=ImageModel(ImageData(**simulation_util.data_configure_simple(267,.03)),PSF(psf_type='PIXEL',kernel_point_source=psf),lens_light_model_class=light,kwargs_numerics={'supersampling_factor':2})
    kw=[]
    for n,re,q in [(1,r.z3_disk_re_pix*.03,r.input_disk_q),(4,r.z3_bulge_re_pix*.03,r.input_bulge_q)]:
        e1,e2=param_util.phi_q2_ellipticity(theta,q)
        kw.append(dict(amp=1,R_sersic=re,n_sersic=n,e1=e1,e2=e2,center_x=0,center_y=0))
    imgs=[model.lens_surface_brightness(kw,k=i) for i in range(2)]
    totals=np.array(light.total_flux(kw))
    finite=np.array([im.sum() for im in imgs])
    legacy_amplitude=np.array([1-r.input_bt,r.input_bt])/finite
    integrated=legacy_amplitude*totals
    legacy=sum(a*im for a,im in zip(legacy_amplitude,imgs))
    corrected_amplitude=integrated_component_amplitudes(totals,r.input_bt)
    corrected=sum(a*im for a,im in zip(corrected_amplitude,imgs))
    corrected/=corrected.sum()
    linear=np.linalg.lstsq(np.column_stack([im.ravel() for im in imgs]),corrected.ravel(),rcond=None)[0]*totals
    if abs(linear[1]/linear.sum()-r.input_bt)>1e-10: raise AssertionError('Integrated truth closure failed')
    return legacy,imgs,totals,dict(legacy_integrated_bt=float(integrated[1]/integrated.sum()),
         corrected_linear_bt=float(linear[1]/linear.sum()),disk_stamp_fraction=float(finite[0]/totals[0]),
         bulge_stamp_fraction=float(finite[1]/totals[1]),theta=theta,
         psf_signed_sum=float(psf.sum()),psf_negative_fraction=float(-psf[psf<0].sum()))

def read_context(project,c):
    with h5py.File(project/'Data/forward_z3_GOLD403_v1/context_bank/contexts.h5') as f:
        return tuple(f[f'{c.tile}/{key}'][int(c.context_id)].astype(float if key!='SEG' else int)
                     for key in ['F444W/SCI','F444W/ERR','SEG'])

def diagnostics(project,output,run_fits=False):
    project=Path(project); output=Path(output); output.mkdir(parents=True,exist_ok=True)
    ns=adapters(project,output/'fit_products')
    ns['FIT_DIR'].mkdir(exist_ok=True)
    d=pd.read_csv(project/'Results/GOLD91_wavelength_interpolated_v2_branch_specific/tables/GOLD91_wavelength_interpolated_full_results.csv')
    ctx=pd.read_csv(project/'Data/forward_z3_GOLD403_v1/context_bank/context_manifest.csv')
    code_inputs=[Path(__file__),project/'Codes/05_GOLD403_z3_MODEL_based_injection_FAST_PILOT.ipynb',
       Path('/home/bahareh/Downloads/GOLD91_FINAL_v3_exclude_487778_clean_real_E0.ipynb'),
       project/'astro-forward-modeling/scripts/gold403_validation_notebook_cells.py',
       project/'astro-forward-modeling/scripts/integrated_bt_normalization.py',
       project/'Results/GOLD91_wavelength_interpolated_v2_branch_specific/tables/GOLD91_wavelength_interpolated_full_results.csv',
       project/'Data/forward_z3_GOLD403_v1/context_bank/context_manifest.csv']
    identity={str(p):sha(p) for p in code_inputs}
    fingerprint=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
    manifest=output/'diagnostic_manifest.json'
    if manifest.exists() and json.loads(manifest.read_text())['fingerprint']!=fingerprint:
        raise RuntimeError('Diagnostic inputs/code changed; select a new output directory')
    atomic_json(manifest,dict(fingerprint=fingerprint,inputs=identity,primary_probes=PRIMARY_PROBES,
          seeds=[2026101101,2026101102],truth='legacy finite-stamp normalization, original flux; diagnosis only',
          alternate_context='next valid same-tile context in context_id order; no additional noise'))
    summaries=[]
    for _,r in d.iterrows():
        c=ctx.loc[(ctx.tile==r.context_tile)&(ctx.context_id==r.context_id)].iloc[0]
        theta=source_theta(project,int(r.source_id),ns)
        psf,psf_path=context_psf(project,c)
        legacy,imgs,totals,meta=render(r,psf,theta)
        record=dict(source_id=int(r.source_id),input_bt=float(r.input_bt),clean_bt=float(r.clean_bt),
                    real_bt=float(r.e0_real_bt),**meta,psf_path=str(psf_path),psf_sha256=sha(psf_path))
        if int(r.source_id) in IDS:
            sci,err,seg=read_context(project,c)
            scale=float(r.e0_target_fnu_jy)/(1e6*(.03*np.pi/(180*3600))**2)
            source=legacy*scale
            truth=dict(target_single_re_arcsec=r.z3_single_re_pix*.03,truth_disk_re=r.z3_disk_re_pix*.03,
                       truth_bulge_re=r.z3_bulge_re_pix*.03,truth_disk_q=r.input_disk_q,
                       truth_bulge_q=r.input_bulge_q,theta=theta)
            prep=ns['_prepare_real_context'](sci+source,err,seg,psf,
                    re_reference_arcsec=max(truth['target_single_re_arcsec'],truth['truth_disk_re'],truth['truth_bulge_re']),q=r.input_disk_q,theta=theta)
            rad=prep['fit_radius'];cy=sci.shape[0]//2; sl=np.s_[cy-rad:cy+rad+1,cy-rad:cy+rad+1]
            mask=prep['likelihood_mask']>0
            shape=np.column_stack([im[sl][mask]/prep['err'][mask] for im in imgs])
            value=prep['image'][mask]/prep['err'][mask]
            for bg in [False,True]:
                design=np.column_stack([shape,1/prep['err'][mask]]) if bg else shape
                fit=np.linalg.lstsq(design,value,rcond=None)[0]
                flux=fit[:2]*totals
                record['fixed_shape_bt_'+('constant_bg' if bg else 'zero_bg')]=float(flux[1]/flux.sum())
                if bg:record['fixed_shape_background']=float(fit[-1])
            _,sigma,nblank=ns['empirical_injected_snr_model'](sci+source,seg)
            yy,xx=np.indices(sci.shape);ap=(xx-cy)**2+(yy-cy)**2<=25
            record.update(source_only_ap_snr=float(source[ap].sum()/sigma),
                  original_scene_ap_snr=float(r.e0_real_bd_snr),n_blank_ap=nblank,
                  n_neighbours=len(prep['neighbours']),masked_fraction=1-float(mask.mean()),
                  weighted_template_condition=float(np.linalg.cond(shape)),
                  component_template_correlation=float(np.corrcoef(shape.T)[0,1]))
            np.savez_compressed(output/f'ID{int(r.source_id)}_diagnostic_images.npz',
                    context=sci,source=source,injected=sci+source,err=err,seg=seg,psf=psf)
        summaries.append(record)
    result=pd.DataFrame(summaries);result.to_csv(output/'normalization_and_context_diagnostics.csv',index=False)
    if not run_fits: return result
    # Three predeclared cases: B/T boundary, strong high-SNR flip, low-SNR flip.
    for oid in PRIMARY_PROBES:
        r=d.loc[d.source_id==oid].iloc[0];theta=source_theta(project,oid,ns)
        original=ctx.loc[(ctx.tile==r.context_tile)&(ctx.context_id==r.context_id)].iloc[0]
        alternative=None
        for _,candidate in ctx.loc[(ctx.tile==r.context_tile)&(ctx.context_id!=r.context_id)].sort_values('context_id').iterrows():
            sci,err,seg=read_context(project,candidate);center=len(sci)//2
            if np.all(np.isfinite(sci)) and np.all(np.isfinite(err)&(err>0)) and seg[center,center]==0:
                alternative=candidate;break
        experiments=[('same_context_seed1',original,2026101101),('same_context_seed2',original,2026101102)]
        if alternative is not None:experiments.append(('independent_context',alternative,2026101101))
        for label,c,seed in experiments:
            dest=output/f'ID{oid}_{label}.json'
            if dest.exists():
                saved=json.loads(dest.read_text())
                if saved['fingerprint']!=fingerprint:raise RuntimeError('Stale fit checkpoint')
                continue
            row=dict(source_id=oid,experiment=label,seed=seed,tile=str(c.tile),context_id=int(c.context_id),fingerprint=fingerprint)
            try:
                psf,_=context_psf(project,c);legacy,_,_,meta=render(r,psf,theta)
                sci,err,seg=read_context(project,c)
                source=legacy*float(r.e0_target_fnu_jy)/(1e6*(.03*np.pi/(180*3600))**2)
                truth=dict(target_single_re_arcsec=r.z3_single_re_pix*.03,truth_disk_re=r.z3_disk_re_pix*.03,
                      truth_bulge_re=r.z3_bulge_re_pix*.03,truth_disk_q=r.input_disk_q,truth_bulge_q=r.input_bulge_q,theta=theta)
                ns['FIT_DIR']=output/'fit_products'/f'ID{oid}_{label}';ns['FIT_DIR'].mkdir(parents=True,exist_ok=True)
                original_runner=ns['run_galight_model']
                def run_and_preserve(*args,**kwargs):
                    fit=original_runner(*args,**kwargs)
                    fit.dump_result()
                    return fit
                ns['run_galight_model']=run_and_preserve
                try:
                    row.update(ns['fit_real_bd_branch']({'id':oid},sci+source,err,seg,psf,truth,c,evolution='E0',seed=seed))
                finally:ns['run_galight_model']=original_runner
                row.update(status='OK',legacy_integrated_bt=meta['legacy_integrated_bt'])
            except Exception as exc:
                row.update(status='ERROR',error=f'{type(exc).__name__}: {exc}',traceback=traceback.format_exc())
            # Undefined quantities preserved explicitly; strict JSON never invents a class.
            row={k:(None if isinstance(v,float) and not np.isfinite(v) else v) for k,v in row.items()}
            atomic_json(dest,row)
            print('CHECKPOINT',oid,label,row['status'],row.get('bt'),flush=True)
    return result

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--fits',action='store_true')
    args=p.parse_args();diagnostics(args.project,args.output,args.fits)
