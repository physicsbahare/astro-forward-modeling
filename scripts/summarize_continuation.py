"""Source-by-source gate inventory and durable continuation checkpoint.

Summarizes receipts only. Unknown classifications never become non-disks.
Historic point solutions and current analytic-total diagnostics are explicitly
named; no demographic correction or population interpretation is inferred.
"""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
from astropy.table import Table
from gold91_recovery_audit import sha,atomic_json

def fits_flags(frame):
    result=frame.copy()
    for name in result:
        if name.endswith(('fit_valid','optimizer_converged')) or name=='analytic_real_measurement_quality':
            def encode(v):
                if pd.isna(v):return np.nan
                if not isinstance(v,(bool,np.bool_)):raise TypeError('Unknown or ambiguous flag type')
                return float(v)
            result[name]=result[name].map(encode)
    return result

def summarize(project,bundle):
    project=Path(project);bundle=Path(bundle);root=project/'Results/Project_Completion_20261011'
    input_manifest=json.loads((bundle/'input_manifest.json').read_text())
    for name,digest in input_manifest['inputs'].items():
        if sha(Path(name))!=digest:raise RuntimeError(f'Changed input/method: {name}')
    models=json.loads((bundle/'models.json').read_text());controls={};refined={}
    sampling=json.loads((bundle/'sampling/sampling_manifest.json').read_text())
    if sampling['models_sha256']!=sha(bundle/'models.json'):raise RuntimeError('Sampling models changed')
    if sampling['code_sha256']!=sha(Path(__file__).with_name('check_truth_sampling.py')):raise RuntimeError('Sampling method changed')
    refinement=json.loads((bundle/'sampling_refinement/manifest.json').read_text()) if (bundle/'sampling_refinement/manifest.json').exists() else None
    if refinement:
        expected_refinement=hashlib.sha256(json.dumps(dict(source=sampling['fingerprint'],code=sha(Path(__file__).with_name('refine_truth_sampling.py')),candidate=[64,24],reference=[128,24],radius_reference=[64,36]),sort_keys=True).encode()).hexdigest()
        if refinement['original_fingerprint']!=sampling['fingerprint'] or refinement['fingerprint']!=expected_refinement:raise RuntimeError('Refinement lineage/method changed')
    for p in (bundle/'sampling').glob('sampling_ID*.json'):
        receipt=json.loads(p.read_text())
        if receipt['fingerprint']!=sampling['fingerprint']:raise RuntimeError('Stale numerical control')
        if 'inherited_checkpoint' in receipt:
            original=receipt['inherited_checkpoint']
            if sha(Path(original['path']))!=original['sha256']:raise RuntimeError('Inherited receipt changed')
        for r in receipt['rows']:controls[(r['source_id'],r['stage'],r['branch'])]=r
    for p in (bundle/'sampling_refinement').glob('ID*.json'):
        r=json.loads(p.read_text())
        if not refinement or r['fingerprint']!=refinement['fingerprint']:raise RuntimeError('Stale refinement')
        refined[(r['source_id'],r['stage'],r['branch'])]=r
    real={};scalar={}
    analytic=root/'corrected_GOLD403_analytic_v1'
    for directory,dest in [('targeted_real',real),('targeted_scalar',scalar)]:
        for p in (analytic/directory).glob('ID*.json'):
            r=json.loads(p.read_text())
            if 'branch' in r:dest[(r['source_id'],r['branch'])]=r
    numerical_fits={}
    recovered_path=bundle/'targeted_fitted_numerics/fitted_numerical_receipt.json'
    if recovered_path.exists():
        recovered=json.loads(recovered_path.read_text())
        if recovered['code_sha256']!=sha(Path(__file__).with_name('audit_recovered_numerics.py')):raise RuntimeError('Recovered diagnostic code changed')
        for row in recovered['rows']:
            if sha(Path(row['fit']))!=row['fit_sha256']:raise RuntimeError('Fitted diagnostic input changed')
            numerical_fits.setdefault(row['fit_sha256'],[]).append(row)
    rows=[]
    for m in models:
        oid=m['source_id'];model=m.get('model',{});r=dict(source_id=oid,z_source=m['z_source'],logM=m['logM'],
            input_status=m['status'],source_flux_mode=m.get('source_flux_mode','UNAVAILABLE'),
            **{key:model.get(key) for key in ['single_re_arcsec','single_q','disk_re_arcsec','disk_q','bulge_re_arcsec','bulge_q']},
            n_mapped=model.get('single_n'),bt_mapped=model.get('bt'),target_fnu_jy=m.get('target_fnu_jy'),
            truth_class='DISK' if model and model['single_n']<2.5 and model['bt']<.5 else 'NON_DISK' if model else 'UNKNOWN',
            spectral_validity='CONDITIONAL_QUADRATIC_SED_MODEL' if m['status']=='OK' else 'UNAVAILABLE',
            bt_identifiability='UNASSESSED',validated_morphology_class='UNKNOWN',production_state='NOT_RUN_GATED',
            mapped_single_pair=':'.join(m.get('single_pair',[])),mapped_bd_pair=':'.join(m.get('bd_pair',[])))
        passed=[]
        for stage in ['native','clean']:
            for branch in ['single','bd']:
                key=(oid,stage,branch);c=controls.get(key);f=refined.get(key)
                if c is None:state='PENDING' if m['status']=='OK' else 'UNSUPPORTED_INPUT'
                elif c['relative_l2_32core6_vs_64core12']<.001 and c['relative_l2_64_vs_128']<.001:state='PASS_32_CORE6'
                elif f and f['pass_numerical_gate']:state='PASS_64_CORE24'
                else:state='NEEDS_REFINEMENT'
                r[f'{stage}_{branch}_numerics']=state;passed.append(state.startswith('PASS'))
        r['all_truth_numerics_pass']=all(passed)
        for branch in ['single','bd']:
            fit=real.get((oid,branch));other=scalar.get((oid,branch))
            if fit:
                r.update({f'analytic_real_{branch}_{k}':fit.get(k) for k in ['status','fit_valid','optimizer_converged','source_aperture_snr','chisq']})
                qa=numerical_fits.get(sha(Path(fit['saved_fit'])),[]) if fit.get('saved_fit') else []
                r[f'analytic_real_{branch}_recovered_numerics']='REFERENCE_AGREEMENT_ONLY' if qa and all(q['actual_grid_valid'] for q in qa) else 'FAIL' if qa else 'UNASSESSED'
                r[f'analytic_real_{branch}_point']=fit.get('n' if branch=='single' else 'bt')
                r[f'analytic_real_{branch}_checkpoint']=str(analytic/'targeted_real'/f'ID{oid}_real_{branch}.json')
            if other:r[f'analytic_scalar_real_{branch}_point']=other.get('n' if branch=='single' else 'bt')
        if (oid,'single') in real and (oid,'bd') in real:
            s,b=real[(oid,'single')],real[(oid,'bd')]
            measured=bool(r.get('analytic_real_single_recovered_numerics')=='PASS' and r.get('analytic_real_bd_recovered_numerics')=='PASS' and s.get('fit_valid') and b.get('fit_valid') and min(s.get('source_aperture_snr',0),b.get('source_aperture_snr',0))>=20)
            r['analytic_real_measurement_quality']=measured
            if measured:r['recovered_class_point_only']='DISK' if s['n']<2.5 and b['bt']<.5 else 'NON_DISK'
            r['production_state']='TARGETED_DIAGNOSTIC_ONLY'
        if oid==732291:r['bt_identifiability']='RECOVERED_BULGE_NUMERICAL_FAILURE'
        rows.append(r)
    history=bundle/'catalog_history';history.mkdir(exist_ok=True)
    import shutil
    for name in ['source_catalog.csv','source_catalog.fits','project_checkpoint.json']:
        previous=bundle/name
        if previous.exists():
            dest=history/(sha(previous)[:16]+'_'+name)
            if not dest.exists():shutil.copy2(previous,dest)
    d=pd.DataFrame(rows);d.to_csv(bundle/'source_catalog.csv',index=False)
    fits_table=Table.from_pandas(fits_flags(d));fits_table.meta['FLAGDEF']='Quality flags 1=true,0=false,NaN=unassessed; classes UNKNOWN preserved'
    temporary=bundle/'source_catalog.tmp.fits';fits_table.write(temporary,overwrite=True)
    temporary.replace(bundle/'source_catalog.fits')
    sampling_receipt=bundle/'sampling/truth_sampling_receipt.json'
    expected={(r['source_id'],stage,branch) for r in models if r['status']=='OK' for stage in ['native','clean'] for branch in ['single','bd']}
    sampling_done=False
    if sampling_receipt.exists():
        finished=json.loads(sampling_receipt.read_text())
        if finished['fingerprint']!=sampling['fingerprint']:raise RuntimeError('Stale global receipt')
        sampling_done=set(controls)==expected and finished['N']==len(expected)
    chain=root/'continuation_gates_v2/posterior/ID10109_seed1/chain_checkpoint.json'
    mc=json.loads(chain.read_text()) if chain.exists() else {}
    checkpoint=dict(status='ACTIVE_SCIENCE_GATES',N_sources=403,N_supported_input_models=sum(m['status']=='OK' for m in models),
        N_mapped_input_disks=sum(r['truth_class']=='DISK' for r in rows),N_sources_numerically_passed=int(d.all_truth_numerics_pass.sum()),
        N_numerical_controls=len(controls),global_sampling_complete=sampling_done,N_refined_controls=len(refined),
        N_analytic_targeted_real_stages=len(real),N_analytic_targeted_scalar_stages=len(scalar),
        input_manifest_sha256=sha(bundle/'input_manifest.json'),models_sha256=sha(bundle/'models.json'),code_sha256=sha(Path(__file__)),
        old_science_preserved=True,full_GOLD403_production_started=False,corrected_BT_population_calibration=False,intrinsic_population_fractions=False,
        conditional_chain_checkpoint=mc,
        completed=['literal unclipped rendering and integrated B/T contract','analytic total-flux normalization test',
            'complete manifest dependencies; deterministic contexts for missing IDs','native optimizer/physical prior/nonpenalty/positive-neighbor checks',
            'exact prior reload validated on six saved fits','master original30 cells preserved; nine continuation cells executed',
            'native M/L and morphology eligibility diagnostics aligned to observed denominator bins'],
        unresolved=['global numerical gate and factor64 refinements','B/T structural/optimizer degeneracy and conditional chain convergence',
            'quadratic spectral model discrepancy/flux-dependent classification uncertainty','native detection/footprint/class-confusion/quiescence/migration calibration'],
        scope='Supported parametric observational recovery only. No failed or unknown fit is counted as a physical morphology transformation. All403 retained.')
    atomic_json(bundle/'project_checkpoint.json',checkpoint);print(json.dumps({k:v for k,v in checkpoint.items() if not isinstance(v,(dict,list))},indent=2));return checkpoint
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--bundle',type=Path,required=True);a=p.parse_args();summarize(a.project,a.bundle)
