#!/usr/bin/env python3
"""C5g: nuclear-centroid release, with immutable host shapes and signed PSFs.

Thin Photutils/SciPy adapter, not a new optimizer or physical PSF construction.
Frozen choices: benchmarks/zhuang_shen_2024/C5G_PROTOCOL.md.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import shutil
import time
import warnings

import numpy as np
from scipy.optimize import least_squares
from run_agn_empirical_psf_centroid import STARTS, OPTIONS
from run_agn_empirical_psf_phase import ROOT, PINS, models, digest
from run_agn_empirical_psf_transfer import solve_fluxes, dump, RATIOS
from run_agn_nuclear_fraction_noiseless import write_csv

PARENT_RUN = 33717899427
PARENT_COMMIT = '88f3fb646a0b89e6cb9b8b8ee1aacae377edca56'
ARTIFACTS = {1:9880481087, 4:9880386950}
PARENT_AUDIT = ROOT/'benchmarks/zhuang_shen_2024/empirical_transfer_33717899427.json'
CENTROID_AUDIT = ROOT/'benchmarks/zhuang_shen_2024/centroid_33734876563.json'
BOUNDS = ((-1.,-1.),(1.,1.))
STAMP = 201


def configuration(host_n):
    if host_n not in ARTIFACTS:
        raise ValueError('host n must be 1 or 4')
    return dict(stage='C5g nuclear-centroid release with fixed host shape',
        github_run_id=os.getenv('GITHUB_RUN_ID'), github_sha=os.getenv('GITHUB_SHA'),
        parent_run=PARENT_RUN, parent_commit=PARENT_COMMIT,
        parent_artifact_id=ARTIFACTS[host_n], host_n=host_n,
        parent_audit_sha256=hashlib.sha256(PARENT_AUDIT.read_bytes()).hexdigest(),
        prerequisite_run=33734876563,
        prerequisite_audit_sha256=hashlib.sha256(CENTROID_AUDIT.read_bytes()).hexdigest(),
        pins=PINS, runtime_versions={k:importlib.metadata.version(k) for k in PINS},
        stamp=STAMP, ratios=RATIOS, truth_modules=['A','B'], fit_modules=['A','B'],
        true_host_flux=1., true_re_native_pix=16., true_q=.6, true_pa_deg=45.,
        fixed='archived fine-Quintic host shape/center/PA; zero background; no noise',
        point='C5e/f cubic ImagePSF, original signed normalization, no second pixel',
        bounds=BOUNDS, starts=STARTS, optimizer=OPTIONS,
        objective='inherited two-amplitude NNLS; full-crop RMS-normalized least squares',
        winner='minimum finite cost regardless of optimizer success',
        expected_comparisons=12, expected_nonlinear_starts=36,
        acceptance='complete finite output, provenance/algebra; no new offset or flux band',
        limitations='conditional signed-model diagnostic, not free-shape or physical astrometry')


def load_parent(source, out, host_n):
    audit=json.loads(PARENT_AUDIT.read_text())
    prerequisite=json.loads(CENTROID_AUDIT.read_text())
    if audit['run_id']!=PARENT_RUN or audit['commit']!=PARENT_COMMIT:
        raise RuntimeError('wrong C5d audit')
    if prerequisite['run_id']!=33734876563 or prerequisite['github_conclusion']!='success':
        raise RuntimeError('unreviewed C5f prerequisite')
    record=next(a for a in audit['artifacts'] if a['artifact_id']==ARTIFACTS[host_n])
    for rel, expected in record['file_sha256'].items():
        if hashlib.sha256((source/rel).read_bytes()).hexdigest()!=expected:
            raise RuntimeError('parent checksum mismatch: '+rel)
    config=json.loads((source/'config.json').read_text())
    if config['github_run_id']!=str(PARENT_RUN) or config['host_n']!=host_n:
        raise RuntimeError('wrong parent run or host')
    if (source/'commit.txt').read_text().strip()!=PARENT_COMMIT:
        raise RuntimeError('wrong parent commit')
    shutil.copytree(source, out/'parent')
    dump(out/'source_manifest.json',dict(run=PARENT_RUN,commit=PARENT_COMMIT,
        artifact_id=ARTIFACTS[host_n],file_sha256=record['file_sha256']))
    with np.load(source/'templates.npz') as bundle:
        templates={k:bundle[k].copy() for k in bundle.files}
    return templates, json.loads((source/'summary.json').read_text())['results']


def fit_scene(data, host, point_model, checkpoint=None):
    if data.shape!=(STAMP,STAMP) or host.shape!=data.shape:
        raise ValueError('unexpected detector crop')
    if not np.isfinite(data).all() or not np.isfinite(host).all():
        raise ValueError('nonfinite scene')
    scale=float(np.sqrt(np.mean(data**2)))
    if scale<=0:
        raise ValueError('zero data norm')
    yy,xx=np.indices(data.shape,dtype=float)
    def point(p):
        return np.asarray(point_model.evaluate(xx,yy,1.,100+p[0],100+p[1]))
    def evaluate(p):
        template=point(p)
        row,prediction=solve_fluxes(data,host,template)
        return row,prediction,prediction-data,template
    fixed,fp,fr,ft=evaluate((0.,0.))
    arrays=dict(data=data,host_template=host,fixed_point_template=ft,
                fixed_prediction=fp,fixed_residual=fr)
    rows=[]
    for i,start in enumerate(STARTS):
        common=dict(start=i,initial_x=start[0],initial_y=start[1])
        try:
            result=least_squares(lambda p:evaluate(p)[2].ravel()/scale,
                start,bounds=BOUNDS,**OPTIONS)
            row,prediction,residual,template=evaluate(result.x)
            row.update(common,success=bool(result.success),status=int(result.status),
                message=str(result.message),nfev=int(result.nfev),
                optimality=float(result.optimality),x=float(result.x[0]),y=float(result.x[1]),
                radial_offset_pix=float(np.hypot(*result.x)),
                active_x=int(result.active_mask[0]),active_y=int(result.active_mask[1]),
                hit_centroid_bound=bool(np.any(result.active_mask)),exception_type='')
            if not np.isfinite(row['cost']) or not np.isfinite(prediction).all():
                raise RuntimeError('nonfinite optimizer product')
            arrays.update({f'start{i}_point_template':template,
                f'start{i}_prediction':prediction,f'start{i}_residual':residual})
        except Exception as error:
            # Preserve and attempt the remaining frozen starts; the workflow fails
            # after archiving partial evidence, never treating an exception as success.
            row=dict(common,success=False,status=-999,message=str(error),
                     exception_type=type(error).__name__,cost=None)
        rows.append(row)
        if checkpoint is not None:
            checkpoint(fixed,rows,arrays)
    candidates=[r for r in rows if r['cost'] is not None and np.isfinite(r['cost'])]
    if any(r['exception_type'] for r in rows):
        raise RuntimeError('one or more centroid starts raised; see start progress')
    winner=dict(min(candidates,key=lambda r:r['cost']))
    winner.update(fixed_cost=fixed['cost'], fixed_host_flux=fixed['host_flux'],
        fixed_nuclear_flux=fixed['nuclear_flux'],
        cost_change=winner['cost']-fixed['cost'],
        host_flux_change=winner['host_flux']-fixed['host_flux'],
        nuclear_flux_change=winner['nuclear_flux']-fixed['nuclear_flux'],
        x_start_range=float(np.ptp([r['x'] for r in rows])),
        y_start_range=float(np.ptp([r['y'] for r in rows])),
        cost_start_range=float(np.ptp([r['cost'] for r in rows])))
    return fixed,winner,rows,arrays


def run(host_n, source, out):
    cfg=configuration(host_n); dump(out/'config.json',cfg)
    if cfg['runtime_versions']!=PINS:
        raise RuntimeError('dependency pin mismatch')
    templates,parent_rows=load_parent(source,out,host_n)
    point_models={m:models(templates[m+'_normalized_input'])['photutils_cubic'] for m in ('A','B')}
    yy,xx=np.indices((STAMP,STAMP),dtype=float)
    controls=[]
    for m,model in point_models.items():
        actual=model.evaluate(xx,yy,1.,100.,100.)
        archived=templates[m+'_fine_quintic_point']
        difference=float(np.max(np.abs(actual-archived)))
        controls.append(dict(module=m,zero_phase_max_abs_parent_difference=difference))
        if difference>1e-12:
            raise RuntimeError('zero-phase point convention identity failed')
    dump(out/'point_controls.json',controls)
    winners,baselines,all_starts=[],[],[]
    for truth in ('A','B'):
        for ratio in RATIOS:
            with np.load(source/f'truth{truth}_ratio{ratio:g}.npz') as image:
                data=image['data'].copy()
                truth_arrays={k:image[k].copy() for k in ('host_truth','nuclear_truth')}
            for adopted in ('A','B'):
                case=f'n{host_n}_truth{truth}_fit{adopted}_ratio{ratio:g}'
                parent=next(r for r in parent_rows if r['truth_module']==truth and
                    r['fit_module']==adopted and r['fit_variant']=='fine_quintic' and r['agn_to_host']==ratio)
                if digest(data)!=parent['data_sha256']:
                    raise RuntimeError('parent data hash mismatch')
                host=templates[adopted+'_fine_quintic_host']
                metadata=dict(case=case,true_n=host_n,true_re_native_pix=16.,true_q=.6,
                    true_host_flux=1.,true_nuclear_flux=ratio,agn_to_host=ratio,
                    truth_module=truth,fit_module=adopted,data_sha256=digest(data),
                    parent_cost=parent['cost'],parent_host_flux=parent['host_flux'],
                    parent_nuclear_flux=parent['nuclear_flux'])
                def save_progress(fixed, rows, arrays):
                    dump(out/(case+'_starts.json'),dict(metadata=metadata,fixed=fixed,starts=rows))
                    np.savez_compressed(out/(case+'.npz'),**arrays,**truth_arrays)
                fixed,winner,rows,arrays=fit_scene(data,host,point_models[adopted],save_progress)
                baseline=dict(**metadata,**fixed,
                    cost_change_from_parent=fixed['cost']-parent['cost'],
                    host_flux_change_from_parent=fixed['host_flux']-parent['host_flux'],
                    nuclear_flux_change_from_parent=fixed['nuclear_flux']-parent['nuclear_flux'])
                winner.update(metadata,host_flux_bias=winner['host_flux']-1.,
                    nuclear_flux_fractional_bias=winner['nuclear_flux']/ratio-1.)
                baselines.append(baseline); winners.append(winner)
                all_starts.extend(dict(**metadata,**r) for r in rows)
                write_csv(out/'fixed_metrics.csv',baselines)
                write_csv(out/'metrics.csv',winners)
                write_csv(out/'fit_starts.csv',all_starts)
                print(json.dumps(winner,allow_nan=False),flush=True)
    if len(winners)!=12 or len(baselines)!=12 or len(all_starts)!=36:
        raise RuntimeError('incomplete case coverage')
    dump(out/'summary.json',dict(config=cfg,results=winners,fixed_results=baselines,
        starts=all_starts,controls=controls,
        interpretation='Signed-model conditional flux/offset diagnostic; no free-shape recovery claim'))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--host-n',type=int,choices=(1,4),required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    start=time.monotonic(); captured=[]
    try:
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter('always')
            run(args.host_n,args.source,args.out)
    except Exception as error:
        dump(args.out/'failure.json',dict(error_type=type(error).__name__,message=str(error)))
        raise
    finally:
        dump(args.out/'runtime.json',dict(wall_seconds=time.monotonic()-start,
            max_resident_set_kib_linux=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        dump(args.out/'warnings.json',[dict(category=w.category.__name__,message=str(w.message)) for w in captured])


if __name__=='__main__':
    main()
