"""Targeted numerical sampling and native-reference PSF sensitivity controls.

No fitting, no data modification. Requested parameters stay fixed. The
observational transfer uses a finite assigned stamp flux; compare shapes as
well as analytic/stamp ratios rather than interpreting flux renormalization as
convergence. Signed empirical PSFs remain unchanged.
"""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
from astropy.cosmology import Planck18
from corrected_four_stage import render_truth,adaptive_numerics
from run_corrected_four_stage import native_psf,PILOT_IDS
from gold91_recovery_audit import atomic_json,context_psf,sha

def check(project,bundle,out,*,all_models=False):
    project=Path(project);bundle=Path(bundle);out=Path(out);out.mkdir(exist_ok=True)
    manifest=json.loads((bundle/'input_manifest.json').read_text())
    for path,digest in manifest['inputs'].items():
        if sha(Path(path))!=digest:raise RuntimeError(f'Sampling dependency changed: {path}')
    fingerprint=hashlib.sha256(json.dumps(dict(models_sha=sha(bundle/'models.json'),code_sha=sha(Path(__file__)),inputs=manifest['fingerprint']),sort_keys=True).encode()).hexdigest()
    atomic_json(out/'sampling_manifest.json',dict(fingerprint=fingerprint,models_sha256=sha(bundle/'models.json'),code_sha256=sha(Path(__file__))))
    records={r['source_id']:r for r in json.loads((bundle/'models.json').read_text())}
    existing=pd.read_csv(project/'Results/GOLD91_wavelength_interpolated_v2_branch_specific/tables/GOLD91_wavelength_interpolated_full_results.csv')
    contexts=pd.read_csv(project/'Data/forward_z3_GOLD403_v1/context_bank/context_manifest.csv')
    historical=pd.read_csv(project/'Data/forward_z3_GOLD403_v1/model_based_v1/production_frozen_20260919T2115/real_background_pilot.csv')
    old_records={int(r.source_id):r for _,r in historical.loc[historical.evolution=='E0'].iterrows()}
    old_records.update({int(r.source_id):r for _,r in existing.iterrows()})
    rows=[]
    ids=[oid for oid,r in records.items() if r['status']=='OK'] if all_models else PILOT_IDS
    for oid in ids:
        checkpoint=out/f'sampling_ID{oid}.json'
        if checkpoint.exists():
            receipt=json.loads(checkpoint.read_text())
            if not isinstance(receipt,dict) or receipt.get('fingerprint')!=fingerprint:raise RuntimeError('Stale sampling checkpoint')
            rows.extend(receipt['rows']);continue
        r=records[oid];before=len(rows)
        if 'frozen_context' in r:
            tile,cid=r['frozen_context']['tile'],r['frozen_context']['context_id']
        else:
            old=old_records[oid];tile,cid=old.context_tile,old.context_id
        context=contexts.loc[(contexts.tile==tile)&(contexts.context_id==cid)].iloc[0]
        target_psf,_=context_psf(project,context)
        for stage in ['native','clean']:
            scale=1. if stage=='native' else float(Planck18.angular_diameter_distance(r['z_source']).value/Planck18.angular_diameter_distance(3).value)
            for branch in ['single','bd']:
                psf=native_psf(project,r,r[branch+'_native_ref_band']) if stage=='native' else target_psf
                images={};metas={}
                for factor,radius in [(32,6),(64,6),(128,6),(64,12)]:
                    image,_,meta=render_truth(r['model'],psf,r['theta'],branch=branch,scale=scale,
                                           numerics=adaptive_numerics(267,factor=factor,radius=radius))
                    images[(factor,radius)]=image;metas[(factor,radius)]=meta
                ref=images[(64,12)];c=len(ref)//2;yy,xx=np.indices(ref.shape);ap=(yy-c)**2+(xx-c)**2<=25
                rows.append(dict(source_id=oid,stage=stage,branch=branch,
                    relative_l2_32core6_vs_64core12=float(np.linalg.norm(images[(32,6)]-ref)/np.linalg.norm(ref)),
                    relative_l2_64_vs_128=float(np.linalg.norm(images[(64,6)]-images[(128,6)])/np.linalg.norm(ref)),
                    aperture_fractional_difference=float(images[(32,6)][ap].sum()/ref[ap].sum()-1),
                    stamp_analytic_ratio_32=metas[(32,6)]['stamp_to_analytic_flux_ratio'],stamp_analytic_ratio_reference=metas[(64,12)]['stamp_to_analytic_flux_ratio']))
        atomic_json(checkpoint,dict(fingerprint=fingerprint,rows=rows[before:]));print('SAMPLING_CHECKPOINT',oid,flush=True)
    d=pd.DataFrame(rows);d.to_csv(out/'truth_sampling_sensitivity.csv',index=False)
    atomic_json(out/'truth_sampling_receipt.json',dict(fingerprint=fingerprint,N=len(d),max_relative_l2_32core6_vs_64core12=float(d.relative_l2_32core6_vs_64core12.max()),
        max_relative_l2_64_vs_128=float(d.relative_l2_64_vs_128.max()),
        numerical_tolerance=.001,pass_numerical_gate=bool((d.relative_l2_32core6_vs_64core12<.001).all() and (d.relative_l2_64_vs_128<.001).all()),
        interpretation='Matched adaptive Lenstronomy shape convergence, not an astrophysical morphology change; 1e-3 numerical tolerance frozen before evaluating this test.'))
    print(d.to_string(index=False))
    return d

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--all',action='store_true');a=p.parse_args();check(a.project,a.bundle,a.output,all_models=a.all)
