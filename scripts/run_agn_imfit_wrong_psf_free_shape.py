#!/usr/bin/env python3
"""C5r wrong-PSF free-shape Imfit diagnostic at the high-contrast anchor."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import subprocess
import time

import numpy as np
from astropy.io import fits

import run_agn_imfit_free_shape as c5o
from run_agn_empirical_psf_transfer import PINS, dump

ROOT=Path(__file__).resolve().parents[1]
C5Q_RUN=33830661656
C5Q_COMMIT='ff39701f7ec5b9f698873064bd85da53ca417544'
C5Q_RECEIPT=ROOT/'benchmarks/zhuang_shen_2024/c5q_33830661656.json'
PROTOCOL=ROOT/'benchmarks/zhuang_shen_2024/C5R_PROTOCOL.md'
RATIO=10.
FIT_PSF={'A':'B','B':'A'}


def configuration(host_n):
    if host_n not in c5o.ARTIFACTS: raise ValueError('host n must be 1 or 4')
    starts=[]
    for start in c5o.STARTS:
        row=dict(start);row['n']=float(host_n) if row['n'] is None else row['n'];starts.append(row)
    return dict(stage='C5r wrong-PSF free-shape Imfit diagnostic',
        github_run_id=os.getenv('GITHUB_RUN_ID'),github_sha=os.getenv('GITHUB_SHA'),
        c5q_run=C5Q_RUN,c5q_commit=C5Q_COMMIT,c5q_receipt_sha256=c5o.sha(C5Q_RECEIPT),
        parent_run=c5o.PARENT_RUN,parent_commit=c5o.PARENT_COMMIT,
        parent_artifact_id=c5o.ARTIFACTS[host_n],parent_audit_sha256=c5o.sha(c5o.AUDIT),
        protocol_sha256=c5o.sha(PROTOCOL),host_n=host_n,ratio=RATIO,
        truth_modules=list(c5o.MODULES),fit_psf_for_truth=FIT_PSF,starts=starts,stamp=201,
        truth=dict(re=16.,q=.6,pa_deg=45.,host_flux=1.,point_flux=RATIO),
        shape_bounds=c5o.SHAPE_BOUNDS,amplitude_bounds=c5o.AMPLITUDE_BOUNDS,
        centers='fixed at Imfit 1-based (101,101); host and nucleus coincident',
        objective='constant unit noise map; full-crop unweighted pixel-space chi-square',
        psf='opposite-module archived signed native point template; --no-normalize',
        solver='Imfit 1.9.0 bounded default Levenberg-Marquardt',
        imfit_version='1.9.0',imfit_binary_sha256=c5o.IMFIT_SHA,imfit_threads=1,
        timeout_seconds=180,pins=PINS,
        runtime_versions={k:importlib.metadata.version(k) for k in PINS},
        expected_cases=2,expected_attempts=6,
        winner='minimum finite recomputed SSE per mismatch direction',
        completion_rule='all attempts/logs recorded; timeout and boundary outcomes retained',
        acceptance='diagnostic only; no convergence or recovery band',
        limitations='signed empirical PSFs; no noise, matched rerun, survey or production claim')


def run(host_n,source,binary,out):
    out.mkdir(parents=True,exist_ok=False);cfg=configuration(host_n);dump(out/'config.json',cfg)
    if cfg['runtime_versions']!=cfg['pins']: raise RuntimeError('dependency pin mismatch')
    if c5o.sha(binary)!=c5o.IMFIT_SHA: raise RuntimeError('wrong Imfit executable')
    receipt=json.loads(C5Q_RECEIPT.read_text())
    if receipt['run_id']!=C5Q_RUN or receipt['commit']!=C5Q_COMMIT or receipt['github_conclusion']!='success':
        raise RuntimeError('unreviewed C5q receipt')
    c5o.verified_parent(source,out,host_n)
    version=subprocess.run([str(binary),'--version'],capture_output=True,text=True,check=False)
    dump(out/'binary.json',dict(sha256=c5o.sha(binary),stdout=version.stdout,stderr=version.stderr,
        returncode=version.returncode))
    if 'version 1.9.0' not in version.stdout: raise RuntimeError('wrong Imfit version')
    with np.load(source/'templates.npz') as z: templates={k:z[k].copy() for k in z.files}
    inputs=out/'inputs';inputs.mkdir();fits.writeto(inputs/'noise.fits',np.ones((201,201)),overwrite=False)
    for module in c5o.MODULES:
        fits.writeto(inputs/f'psf_{module}.fits',templates[f'{module}_fine_quintic_point'],overwrite=False)
    attempts=[];winners=[]
    for truth_module in c5o.MODULES:
        fit_module=FIT_PSF[truth_module]
        with np.load(source/f'truth{truth_module}_ratio10.npz') as z: data=z['data'].copy()
        data_path=inputs/f'data_{truth_module}_ratio10.fits';fits.writeto(data_path,data,overwrite=False)
        case=f'n{host_n}_truth{truth_module}_fit{fit_module}_ratio10';rows=[]
        for start in cfg['starts']:
            directory=out/'fits'/case/start['label']
            row=c5o.run_start(binary,data_path,inputs/f'psf_{fit_module}.fits',inputs/'noise.fits',
                              host_n,RATIO,start,directory)
            row.update(case=case,truth_module=truth_module,fit_psf_module=fit_module,ratio=RATIO,
                       true_n=host_n,true_re=16.,true_q=.6,true_pa_imfit=-45.,true_point_flux=RATIO)
            dump(directory/'result.json',row);rows.append(row);attempts.append(row)
            c5o.write_csv(out/'fit_starts.csv',attempts)
        finite=[row for row in rows if row.get('success') and np.isfinite(row.get('sse',np.nan))]
        if finite:
            winner=dict(min(finite,key=lambda row:row['sse']));winner['winner']=True;winners.append(winner)
            c5o.write_csv(out/'metrics.csv',winners)
    if len(attempts)!=cfg['expected_attempts']: raise RuntimeError('incomplete attempted processes')
    if not (out/'metrics.csv').exists(): (out/'metrics.csv').write_text('case,truth_module,fit_psf_module,sse\n')
    dump(out/'summary.json',dict(config=cfg,results=winners,attempts=attempts,
        interpretation='wrong-PSF free-shape diagnostic; finite minimum is not physical truth'))


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--imfit',type=Path,required=True);p.add_argument('--host-n',type=int,choices=(1,4),required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args();started=time.monotonic()
    try: run(a.host_n,a.source,a.imfit,a.out)
    except Exception as error:
        a.out.mkdir(parents=True,exist_ok=True);dump(a.out/'failure.json',dict(type=type(error).__name__,message=str(error)));raise
    finally:
        a.out.mkdir(parents=True,exist_ok=True);dump(a.out/'runtime.json',dict(wall_seconds=time.monotonic()-started,
            max_resident_set_kib_linux=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


if __name__=='__main__':main()
