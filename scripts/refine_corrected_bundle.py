"""Re-score cached cleaned photometry; explicit homogeneous published fallback.

Does not re-clean images or refit morphology. Raw dependencies must retain their
hashes. Method evolution is declared and archived, not silently accepted as a
stale checkpoint. All 403 objects, including unsupported models, stay present.
"""
from pathlib import Path
import copy,json,hashlib
import numpy as np,pandas as pd
from astropy.io import fits
from astropy.cosmology import Planck18
from prepare_corrected_models import supported_flux
from verification.nircam_throughput_sensitivity import load_mean_throughput
from gold91_recovery_audit import atomic_json,sha

def refine(project,cached,out):
    project=Path(project);cached=Path(cached);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    if (out/'models.json').exists():raise RuntimeError('Choose a new immutable bundle output')
    old=json.loads((cached/'input_manifest.json').read_text());inputs={};method_changes=[]
    declared={project/'astro-forward-modeling/scripts'/name for name in ['corrected_four_stage.py','refine_corrected_bundle.py','optimizer_quality.py','run_corrected_four_stage.py','check_truth_sampling.py']}
    for name,digest in old['inputs'].items():
        p=Path(name);actual=sha(p)
        if actual!=digest:
            if p not in declared:raise RuntimeError(f'Undeclared dependency changed: {p}')
            method_changes.append(dict(path=str(p),previous_sha256=digest,current_sha256=actual,
                reason='Declared optimizer-quality/physical-domain instrumentation and complete provenance; scientific truth and source flux invariants checked separately'))
        inputs[name]=actual
    repo=project/'astro-forward-modeling'
    for name in ['refine_corrected_bundle.py','optimizer_quality.py','run_corrected_four_stage.py','check_truth_sampling.py']:
        p=repo/'scripts'/name;inputs[str(p)]=sha(p)
    extra=[Path('/home/bahareh/Downloads/GOLD91_FINAL_v3_exclude_487778_clean_real_E0.ipynb'),
        repo/'scripts/gold403_validation_notebook_cells.py',
        project/'Results/GOLD91_wavelength_interpolated_v2_branch_specific/tables/GOLD91_wavelength_interpolated_full_results.csv',
        project/'Data/forward_z3_GOLD403_v1/model_based_v1/production_frozen_20260919T2115/real_background_pilot.csv']
    for p in extra:inputs[str(p)]=sha(p)
    policy=copy.deepcopy(old['policy']);policy.update(supersampling='adaptive32_core6',
        physical_domain='all fitted component ellipticities inside unit disk; center separation uses existing branch condition',
        normalization='analytic-total luminosity; finite stamp losses retained, no aperture boost',
        optimizer_quality='record native SciPy SIMPLEX termination; nonconvergence is independent invalidity flag',
        source_flux_fallback='only missing supported positive cleaned flux: homogeneous published GALIGHT B+D totals in all bands; systemic flag mandatory')
    fp=hashlib.sha256(json.dumps(dict(inputs=inputs,policy=policy),sort_keys=True).encode()).hexdigest()
    rows=copy.deepcopy(json.loads((cached/'models.json').read_text()))
    root=Path('/home/bahareh/nircam_throughputs_Jan2025_v7/nircam_throughputs/mean_throughputs')
    bands=('F115W','F150W','F277W','F444W');curves={b:load_mean_throughput(b,root) for b in bands}
    gold=pd.read_csv(project/'Data/passive_disk_GOLD403_with_visual_flags.csv');index=dict(zip(gold.id,gold.row_index))
    raw=Path('/home/bahareh/Desktop/Projects/Data_General/Cosmos_Web/COSMOSWeb_mastercatalog_v1.1.fits')
    fallback=[]
    with fits.open(raw,memmap=True) as f:
        for r in rows:
            r['fingerprint']=fp
            if r['status']=='UNSUPPORTED_MORPHOLOGY':continue
            cleaned=r.get('cleaned_scene_fluxes_before_fallback',r['source_fluxes_jy'])
            try:
                spectral=supported_flux(cleaned,curves,r['z_source']);fluxes=cleaned
                r['source_flux_mode']='cleaned_scene_integrated'
            except ValueError as cleaning_failure:
                g=f[7].data[int(index[r['source_id']])];fluxes={}
                for b in bands:
                    md,mb=(float(g[f'mag_{c}_{b.lower()}_bd']) for c in ['disk','bulge'])
                    if not(0<md<90 and 0<mb<90):raise ValueError(f'Invalid fallback magnitudes for {r["source_id"]}')
                    fluxes[b]=3631*(10**(-.4*md)+10**(-.4*mb))
                spectral=supported_flux(fluxes,curves,r['z_source'])
                r.update(cleaned_scene_fluxes_before_fallback=cleaned,source_flux_systematic='MODEL_TOTAL_VS_CLEANED_SCENE_APERTURE',
                    source_flux_mode='published_GALIGHT_BD_total_consistent_all_bands',fallback_reason=str(cleaning_failure))
                fallback.append(r['source_id'])
            ratio=float(4/(1+r['z_source'])*(Planck18.luminosity_distance(r['z_source']).value/Planck18.luminosity_distance(3.).value)**2)
            r.update(status='OK',source_fluxes_jy=fluxes,spectral=spectral,source_to_target_ratio=ratio,
                target_fnu_jy=spectral['source_equivalent_target_fnu_jy']*ratio)
            r.pop('spectral_error',None)
    # Freeze context assignment; recover absent historical contexts deterministically.
    from run_corrected_four_stage import context_admission
    from gold91_recovery_audit import read_context
    contexts=pd.read_csv(project/'Data/forward_z3_GOLD403_v1/context_bank/context_manifest.csv')
    hist=pd.read_csv(project/'Data/forward_z3_GOLD403_v1/model_based_v1/production_frozen_20260919T2115/real_background_pilot.csv')
    saved=pd.read_csv(project/'Results/GOLD91_wavelength_interpolated_v2_branch_specific/tables/GOLD91_wavelength_interpolated_full_results.csv')
    assignments={int(r.source_id):(str(r.context_tile),int(r.context_id)) for _,r in hist.loc[hist.evolution=='E0'].iterrows() if np.isfinite(r.context_id)}
    assignments.update({int(r.source_id):(str(r.context_tile),int(r.context_id)) for _,r in saved.iterrows()})
    for r in rows:
        if r['status']!='OK':continue
        if r['source_id'] in assignments:
            tile,cid=assignments[r['source_id']];origin='existing_frozen_context'
        else:
            choices=contexts.loc[contexts.tile==r['tile']].sort_values('context_id');chosen=None
            for _,candidate in choices.iterrows():
                sci,err,seg=read_context(project,candidate)
                if context_admission(sci,err,seg)['usable']:chosen=candidate;break
            if chosen is None:raise RuntimeError(f'No valid same-tile context: {r["source_id"]}')
            tile,cid=str(chosen.tile),int(chosen.context_id);origin='deterministic_first_valid_same_tile'
        r['frozen_context']=dict(tile=tile,context_id=cid,origin=origin)
    atomic_json(out/'input_manifest.json',dict(inputs=inputs,policy=policy,fingerprint=fp,environment=old['environment'],
        declared_method_changes=method_changes,cached_bundle=str(cached),cached_models_sha256=sha(cached/'models.json'),previous_input_manifest_sha256=sha(cached/'input_manifest.json')))
    atomic_json(out/'models.json',rows)
    atomic_json(out/'source_input_resolution_receipt.json',dict(N=len(rows),fallback_ids=fallback,
        status_counts=pd.Series([r['status'] for r in rows]).value_counts().to_dict(),raw_data_reused_without_refitting=True))
    return rows
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--cached',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();refine(a.project,a.cached,a.output)
