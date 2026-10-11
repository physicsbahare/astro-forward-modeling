"""Freeze per-stage numerical settings after all input controls pass.

Real settings inherit clean settings exactly. This closes only input rendering;
fitted-model convergence and B/T identifiability still gate production.
"""
from pathlib import Path
import copy,json,hashlib
from summarize_continuation import summarize
from gold91_recovery_audit import atomic_json,sha

def freeze(project,bundle,out):
    project=Path(project);bundle=Path(bundle);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    if (out/'models.json').exists():raise RuntimeError('Immutable policy already exists')
    summary=summarize(project,bundle)
    if not summary['global_sampling_complete'] or summary['N_sources_numerically_passed']!=395:raise RuntimeError('Numerical input gate incomplete')
    models=copy.deepcopy(json.loads((bundle/'models.json').read_text()));controls={};refined={}
    for p in (bundle/'sampling').glob('sampling_ID*.json'):
        for r in json.loads(p.read_text())['rows']:controls[(r['source_id'],r['stage'],r['branch'])]=r
    for p in (bundle/'sampling_refinement').glob('ID*.json'):
        r=json.loads(p.read_text());refined[(r['source_id'],r['stage'],r['branch'])]=r
    counts={};receipts={}
    for r in models:
        if r['status']!='OK':continue
        settings={}
        for stage in ['native','clean']:
            for branch in ['single','bd']:
                key=(r['source_id'],stage,branch);c=controls[key]
                basic=c['relative_l2_32core6_vs_64core12']<.001 and c['relative_l2_64_vs_128']<.001
                numerical={'factor':32,'radius':6} if basic else {'factor':64,'radius':24}
                if not basic and not refined[key]['pass_numerical_gate']:raise RuntimeError('Failed refined control')
                settings[stage+':'+branch]=numerical;name=f"{numerical['factor']}/core{numerical['radius']}";counts[name]=counts.get(name,0)+1
        for branch in ['single','bd']:settings['real:'+branch]=copy.deepcopy(settings['clean:'+branch])
        r['numerics_by_stage_branch']=settings
    manifest=json.loads((bundle/'input_manifest.json').read_text());manifest['policy']['numerics']='per-stage validated32/core6 or64/core24; real exactly matches clean'
    manifest['inputs'][str(Path(__file__).resolve())]=sha(Path(__file__))
    fp=hashlib.sha256(json.dumps(dict(inputs=manifest['inputs'],policy=manifest['policy']),sort_keys=True).encode()).hexdigest()
    manifest['fingerprint']=fp
    for r in models:r['fingerprint']=fp
    atomic_json(out/'input_manifest.json',manifest);atomic_json(out/'models.json',models)
    atomic_json(out/'numerical_policy_receipt.json',dict(input_bundle=str(bundle),input_models_sha256=sha(bundle/'models.json'),N_supported=395,N_unsupported=8,N_controls=1580,settings_counts=counts,
        truth_numerical_gate=True,fit_numerical_gate=False,BT_identifiability_gate=False,production_authorized_by_science=False,
        scope='Numerical input policy only; no automatic fit or classification promotion'))
    print('INPUT_POLICY_FROZEN',counts)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();freeze(a.project,a.bundle,a.output)
