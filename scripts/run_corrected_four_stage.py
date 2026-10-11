"""Checkpointed corrected four-stage Galight execution.

All previous runs are immutable. Each new stage has a strict input/method
identity. ERROR and quality rows are checkpointed and skipped on resume.
"""
from pathlib import Path
import argparse,json,hashlib,traceback
import numpy as np,pandas as pd,galsim
from galsim.des import DES_PSFEx
from astropy.io import fits
from astropy.cosmology import Planck18
from corrected_four_stage import render_truth,fit_image,adaptive_numerics
from gold91_recovery_audit import adapters,atomic_json,context_psf,read_context,sha

PILOT_IDS=[164952,283184,666469,10109,215914,732291,487469]

def context_admission(sci,err,seg,minimum_fraction=.95):
    if sci.shape!=err.shape or sci.shape!=seg.shape or sci.ndim!=2:
        return dict(usable=False,reason='SHAPE_MISMATCH')
    valid=np.isfinite(sci)&np.isfinite(err)&(err>0);c=sci.shape[0]//2
    fraction=float(np.mean(valid));center=bool(valid[c,c]);blank=bool(seg[c,c]==0)
    return dict(usable=fraction>=minimum_fraction and center and blank,valid_fraction=fraction,
                center_valid=center,blank_center=blank,bad_pixels=int(valid.size-valid.sum()),minimum_fraction=minimum_fraction)

def native_psf(project,record,band):
    tile=record['tile'];path=project/f'Data/forward_z3_GOLD403_v1/cache/cosmos_web_psfs_v5.0/cosmos_web_psf_jwst_{band.lower()}_{tile}_v5.0.psf'
    with fits.open(path) as f:side=int(np.ceil(f[1].header['PSFAXIS1']*f[1].header['PSF_SAMP']))
    side+=side%2==0
    kernel=DES_PSFEx(str(path)).getPSF(galsim.PositionD(record['x_image']+1,record['y_image']+1)).drawImage(nx=side,ny=side,scale=1.,method='no_pixel').array.astype(float)
    if not np.all(np.isfinite(kernel)) or kernel.sum()<=0:raise ValueError('Invalid native signed PSF')
    return kernel/kernel.sum()

def strict(value):
    if isinstance(value,dict):return {k:strict(v) for k,v in value.items()}
    if isinstance(value,list):return [strict(v) for v in value]
    if isinstance(value,(np.bool_,)):return bool(value)
    if isinstance(value,(np.integer,)):return int(value)
    if isinstance(value,(float,np.floating)) and not np.isfinite(value):return None
    return value

def run(project,bundle,out,ids,*,clean_algorithm='PSO',real=True,flux_mode='curved',context_variant=False,adaptive=False,only_real=False):
    project=Path(project);bundle=Path(bundle);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((bundle/'input_manifest.json').read_text())
    # Guard every raw dependency once before reusing any checkpoint.
    for p,expected in manifest['inputs'].items():
        if sha(Path(p))!=expected:raise RuntimeError(f'Input/method changed: {p}')
    config=dict(input_fingerprint=manifest['fingerprint'],models_sha256=sha(bundle/'models.json'),driver_sha256=sha(Path(__file__)),
                clean_algorithm=clean_algorithm,real=real,flux_mode=flux_mode,context_variant=context_variant,
                pso_passes=2,simplex_polish=1500,npix=267,snr_aperture_radius_pix=5.,snr_threshold=20.,adaptive=adaptive,only_real=only_real,context_minimum_valid_fraction=.95)
    fingerprint=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
    config_path=out/'run_manifest.json'
    if config_path.exists() and json.loads(config_path.read_text())['fingerprint']!=fingerprint:
        raise RuntimeError('Run configuration changed; choose a new output directory')
    atomic_json(config_path,dict(fingerprint=fingerprint,config=config,selected_ids=ids))
    models={r['source_id']:r for r in json.loads((bundle/'models.json').read_text())}
    old=pd.read_csv(project/'Results/GOLD91_wavelength_interpolated_v2_branch_specific/tables/GOLD91_wavelength_interpolated_full_results.csv')
    contexts=pd.read_csv(project/'Data/forward_z3_GOLD403_v1/context_bank/context_manifest.csv')
    legacy_context={int(r.source_id):(str(r.context_tile),int(r.context_id)) for _,r in old.iterrows()}
    historical=pd.read_csv(project/'Data/forward_z3_GOLD403_v1/model_based_v1/production_frozen_20260919T2115/real_background_pilot.csv')
    legacy_context.update({int(r.source_id):(str(r.context_tile),int(r.context_id)) for _,r in historical.loc[historical.evolution=='E0'].iterrows() if np.isfinite(r.source_id) and int(r.source_id) not in legacy_context and np.isfinite(r.context_id)})
    ns=adapters(project,out/'fit_products');ns['FIT_DIR'].mkdir(exist_ok=True)
    for oid in ids:
        record=models[oid]
        if record['status']!='OK':
            dest=out/f'ID{oid}_INPUT.json'
            if not dest.exists():atomic_json(dest,dict(source_id=oid,status=record['status'],fingerprint=fingerprint,error=record.get('error') or record.get('spectral_error')))
            continue
        failed_context=out/f'ID{oid}_CONTEXT.json'
        if failed_context.exists():
            saved_failure=json.loads(failed_context.read_text())
            if saved_failure['fingerprint']!=fingerprint:raise RuntimeError('Stale context failure checkpoint')
            continue
        try:
            tile,cid=(str(record['frozen_context']['tile']),int(record['frozen_context']['context_id'])) if 'frozen_context' in record else legacy_context[oid]
            context=contexts.loc[(contexts.tile==tile)&(contexts.context_id==cid)].iloc[0]
            if context_variant:
                found=False
                for _,candidate in contexts.loc[(contexts.tile==tile)&(contexts.context_id!=cid)].sort_values('context_id').iterrows():
                    sc,er,se=read_context(project,candidate);c=len(sc)//2
                    if np.all(np.isfinite(sc)) and np.all(np.isfinite(er)&(er>0)) and se[c,c]==0:
                        context=candidate;found=True;break
                if not found:raise ValueError('No valid independent context')
            target_psf,_=context_psf(project,context)
            scale=float(Planck18.angular_diameter_distance(record['z_source']).value/Planck18.angular_diameter_distance(3.).value)
            sci,err,seg=read_context(project,context)
            admission=context_admission(sci,err,seg)
            if not admission['usable']:
                dest=out/f'ID{oid}_CONTEXT.json'
                if not dest.exists():atomic_json(dest,dict(source_id=oid,status='ERROR',quality_code='INVALID_CONTEXT',context_admission=admission,fingerprint=fingerprint))
                continue
        except Exception as e:
            dest=out/f'ID{oid}_CONTEXT.json'
            if not dest.exists():atomic_json(dest,dict(source_id=oid,status='ERROR',quality_code='CONTEXT_OR_PSF_FAILURE',error=f'{type(e).__name__}: {e}',traceback=traceback.format_exc(),fingerprint=fingerprint))
            continue
        stages=['real'] if only_real else ['native','clean','real'] if real else ['native','clean']
        for stage in stages:
            for branch in ['single','bd']:
                dest=out/f'ID{oid}_{stage}_{branch}.json'
                if dest.exists():
                    previous=json.loads(dest.read_text())
                    if previous['fingerprint']!=fingerprint:raise RuntimeError('Stale stage checkpoint')
                    continue
                row=dict(source_id=oid,z_source=record['z_source'],logM=record['logM'],stage=stage,branch=branch,
                    status='ERROR',fingerprint=fingerprint,context_tile=str(context.tile),context_id=int(context.context_id),input_model=record['model'],context_admission=admission)
                try:
                    psf=native_psf(project,record,record[branch+'_native_ref_band']) if stage=='native' else target_psf
                    angular_scale=1. if stage=='native' else scale
                    numerics_map=record.get('numerics_by_stage_branch',{})
                    settings=numerics_map.get(stage+':'+branch,numerics_map.get('clean:'+branch,{}) if stage=='real' else {})
                    if stage=='real' and settings!=numerics_map.get('clean:'+branch,settings):raise RuntimeError('Clean/real numerics mismatch')
                    truth,kwargs,meta=render_truth(record['model'],psf,record['theta'],branch=branch,scale=angular_scale,
                                                 numerics=adaptive_numerics(267,**settings) if adaptive else None)
                    row.update(truth_metadata=meta,angular_scale=angular_scale,native_ref_band=record[branch+'_native_ref_band'],
                              requested_radii=[k['R_sersic'] for k in kwargs])
                    if stage=='real':
                        fnu=record['target_fnu_jy']
                        if flux_mode=='scalar':
                            match=old.loc[old.source_id==oid]
                            if len(match)!=1:raise ValueError('No saved scalar-flux counterfactual for this ID')
                            fnu=float(match.e0_target_fnu_jy.iloc[0])
                        source=truth/meta['analytic_integrated_flux']*fnu/(1e6*(.03/206265.)**2)
                        image=sci+source;noise=err;segmentation=seg
                        ns['RNG']=np.random.default_rng(20261011+oid)
                        _,blank_sigma,nblank=ns['empirical_injected_snr_model'](sci,seg)
                        c=len(sci)//2;yy,xx=np.indices(sci.shape);ap=(yy-c)**2+(xx-c)**2<=25
                        row.update(target_fnu_jy=fnu,photometric_normalization='analytic_total',spectral_classification_validity='CONDITIONAL_QUADRATIC_SED_MODEL',
                                  finite_stamp_fnu_jy=fnu*meta['stamp_to_analytic_flux_ratio'],source_flux_mode=record.get('source_flux_mode'),source_aperture_snr=float(source[ap].sum()/blank_sigma),
                                  n_blank_ap=nblank,blank_aperture_sigma=float(blank_sigma),source_noise='no extra source/background noise')
                    else:image=truth;noise=np.ones_like(truth);segmentation=np.zeros_like(truth,dtype=int)
                    fit_record,_=fit_image(image,noise,segmentation,psf,record['model'],kwargs,record['theta'],branch,
                        out/'fit_products'/f'ID{oid}_{stage}_{branch}',ns,real=stage=='real',
                        seed=(2026101100+oid*10+['native','clean','real'].index(stage)*2+(branch=='bd'))%(2**32-1),algorithm='PSO' if stage=='real' else clean_algorithm,adaptive=adaptive,adaptive_settings=settings)
                    row.update(fit_record)
                    if stage!='real':
                        expected=record['model']['single_n' if branch=='single' else 'bt']
                        error=abs(row['n' if branch=='single' else 'bt']-expected) if row['n' if branch=='single' else 'bt'] is not None else None
                        row.update(recovery_absolute_error=error,accuracy_gate=error is not None and error<=(.5 if branch=='single' else .1))
                    row['identifiability']='UNASSESSED_POSTERIOR' if stage=='real' else 'CONTROLLED_TRUTH_RECOVERY' if row.get('accuracy_gate') and row['fit_valid'] else 'CLEAN_RECOVERY_NONIDENTIFIABLE_OR_BOUND'
                except Exception as e:row.update(error=f'{type(e).__name__}: {e}',traceback=traceback.format_exc())
                atomic_json(dest,strict(row))
                print('CHECKPOINT',oid,stage,branch,row['status'],row.get('n'),row.get('bt'),row.get('accuracy_gate'),flush=True)
        case_rows=[json.loads(p.read_text()) for p in sorted(out.glob(f'ID{oid}_*.json'))]
        atomic_json(out/f'case_{oid}.json',dict(source_id=oid,fingerprint=fingerprint,stages=case_rows))
    all_rows=[json.loads(p.read_text()) for p in sorted(out.glob('ID*.json'))]
    pd.DataFrame([{k:v for k,v in r.items() if k not in ['input_model','truth_metadata','traceback']} for r in all_rows]).to_csv(out/'stage_summary.csv',index=False)
    return all_rows

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--ids',default=','.join(map(str,PILOT_IDS)));p.add_argument('--all',action='store_true');p.add_argument('--clean-algorithm',choices=['PSO','SIMPLEX'],default='PSO');p.add_argument('--no-real',action='store_true');p.add_argument('--scalar',action='store_true');p.add_argument('--context-variant',action='store_true');p.add_argument('--adaptive',action='store_true');p.add_argument('--only-real',action='store_true')
    a=p.parse_args();ids=[r['source_id'] for r in json.loads((a.bundle/'models.json').read_text())] if a.all else [int(s) for s in a.ids.split(',')]
    run(a.project,a.bundle,a.output,ids,clean_algorithm=a.clean_algorithm,real=not a.no_real,flux_mode='scalar' if a.scalar else 'curved',context_variant=a.context_variant,adaptive=a.adaptive,only_real=a.only_real)
