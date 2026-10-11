"""Refine only failed fingerprinted truth sampling controls, never fit sources.

Candidate: adaptive32 core24, compared with adaptive64 core36 and factor64
core24. The original 1e-3 tolerance is unchanged. Residual numerical failures
remain unsupported states; no morphology-dependent thresholds are tuned.
"""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
from astropy.cosmology import Planck18
from corrected_four_stage import render_truth,adaptive_numerics
from run_corrected_four_stage import native_psf
from gold91_recovery_audit import atomic_json,context_psf,sha

def refine(project,bundle,controls,out):
    project=Path(project);bundle=Path(bundle);controls=Path(controls);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((bundle/'input_manifest.json').read_text())
    for p,digest in manifest['inputs'].items():
        if sha(Path(p))!=digest:raise RuntimeError(f'Changed dependency: {p}')
    original=json.loads((controls/'sampling_manifest.json').read_text())
    if original['models_sha256']!=sha(bundle/'models.json'):raise RuntimeError('Sampling bundle mismatch')
    fp=hashlib.sha256(json.dumps(dict(source=original['fingerprint'],code=sha(Path(__file__)),candidate=[64,24],reference=[128,24],radius_reference=[64,36]),sort_keys=True).encode()).hexdigest()
    atomic_json(out/'manifest.json',dict(fingerprint=fp,original_fingerprint=original['fingerprint'],candidate='adaptive64_core24',reference='adaptive128_core24_and64_core36',tolerance=.001))
    records={r['source_id']:r for r in json.loads((bundle/'models.json').read_text())}
    contexts=pd.read_csv(project/'Data/forward_z3_GOLD403_v1/context_bank/context_manifest.csv');rows=[]
    for path in sorted(controls.glob('sampling_ID*.json')):
        old=json.loads(path.read_text())
        if old['fingerprint']!=original['fingerprint']:raise RuntimeError('Stale control')
        for row in old['rows']:
            if row['relative_l2_32core6_vs_64core12']<.001 and row['relative_l2_64_vs_128']<.001:continue
            oid=row['source_id'];stage=row['stage'];branch=row['branch'];dest=out/f'ID{oid}_{stage}_{branch}.json'
            if dest.exists():
                saved=json.loads(dest.read_text())
                if saved['fingerprint']!=fp:raise RuntimeError('Stale refined control')
                rows.append(saved);continue
            r=records[oid];ctx=r['frozen_context'];context=contexts.loc[(contexts.tile==ctx['tile'])&(contexts.context_id==ctx['context_id'])].iloc[0]
            psf=native_psf(project,r,r[branch+'_native_ref_band']) if stage=='native' else context_psf(project,context)[0]
            scale=1. if stage=='native' else float(Planck18.angular_diameter_distance(r['z_source']).value/Planck18.angular_diameter_distance(3).value)
            images={}
            for factor,radius in [(64,24),(128,24),(64,36)]:
                images[(factor,radius)]=render_truth(r['model'],psf,r['theta'],branch=branch,scale=scale,numerics=adaptive_numerics(267,factor=factor,radius=radius))[0]
            ref=images[(128,24)];err=float(np.linalg.norm(images[(64,24)]-ref)/np.linalg.norm(ref));radius_error=float(np.linalg.norm(images[(64,24)]-images[(64,36)])/np.linalg.norm(ref))
            result=dict(source_id=oid,stage=stage,branch=branch,fingerprint=fp,candidate_factor=64,candidate_radius=24,
                relative_l2=err,radius_convergence_l2=radius_error,pass_numerical_gate=err+radius_error<.001)
            atomic_json(dest,result);rows.append(result);print('REFINED_CONTROL',oid,stage,branch,err,result['pass_numerical_gate'],flush=True)
    if rows:pd.DataFrame(rows).to_csv(out/'refined_sampling.csv',index=False)
    return rows
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--controls',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();refine(a.project,a.bundle,a.controls,a.output)
