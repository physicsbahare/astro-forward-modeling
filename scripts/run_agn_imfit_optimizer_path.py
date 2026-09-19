#!/usr/bin/env python3
"""C5p: preserve C5o and compare two bounded Imfit optimizer paths."""
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
C5O_RUN=33819349854
C5O_COMMIT='7041907231a26292f8c663c2df898f3192175a7e'
C5O_ARTIFACT=9917827458
C5O_RECEIPT=ROOT/'benchmarks/zhuang_shen_2024/c5o_33819349854.json'
PROTOCOL=ROOT/'benchmarks/zhuang_shen_2024/C5P_PROTOCOL.md'
MODULES=('A','B')
SOLVERS=(('lm',()),('nm',('--nm',)))
TIMEOUT=180


def configuration(module):
    if module not in MODULES: raise ValueError('module must be A or B')
    start=dict(c5o.STARTS[1])
    return dict(stage='C5p bounded Imfit optimizer-path diagnostic',
        github_run_id=os.getenv('GITHUB_RUN_ID'),github_sha=os.getenv('GITHUB_SHA'),
        c5o_run=C5O_RUN,c5o_commit=C5O_COMMIT,c5o_artifact_id=C5O_ARTIFACT,
        c5o_receipt_sha256=c5o.sha(C5O_RECEIPT),protocol_sha256=c5o.sha(PROTOCOL),
        parent_run=c5o.PARENT_RUN,parent_commit=c5o.PARENT_COMMIT,
        parent_artifact_id=c5o.ARTIFACTS[4],module=module,host_n=4,ratio=10.,
        start=start,solvers=[name for name,_ in SOLVERS],timeout_seconds=TIMEOUT,
        shape_bounds=c5o.SHAPE_BOUNDS,amplitude_bounds=c5o.AMPLITUDE_BOUNDS,
        centers='fixed at Imfit 1-based (101,101); host and nucleus coincident',
        objective='constant unit noise map; full-crop unweighted pixel-space chi-square',
        psf='archived native fine-Quintic point template; matched module; signed; --no-normalize',
        imfit_version='1.9.0',imfit_binary_sha256=c5o.IMFIT_SHA,imfit_threads=1,
        pins=PINS,runtime_versions={k:importlib.metadata.version(k) for k in PINS},
        expected_attempts=2,
        completion_rule='both bounded processes and logs recorded; timeout/nonconvergence retained',
        acceptance='diagnostic only; no convergence or recovery band')


def run_solver(binary,data,psf,noise,initial,solver,flags,directory):
    directory.mkdir(parents=True,exist_ok=False)
    local_initial=directory/'initial.dat'; local_initial.write_text(initial.read_text())
    best=directory/'bestfit.dat'; model=directory/'model.fits'; residual=directory/'residual.fits'
    cmd=['/usr/bin/timeout','--kill-after=5s',str(TIMEOUT),str(binary),str(data),
         '-c',str(local_initial),'--noise',str(noise),'--psf',str(psf),'--no-normalize',
         '--max-threads','1',*flags,'--save-params',str(best),'--save-model',str(model),
         '--save-residual',str(residual)]
    dump(directory/'command.json',cmd); started=time.monotonic()
    with (directory/'stdout.txt').open('w') as stdout,(directory/'stderr.txt').open('w') as stderr:
        result=subprocess.run(cmd,stdout=stdout,stderr=stderr,check=False)
    row=dict(solver=solver,returncode=result.returncode,wall_seconds=time.monotonic()-started,
             products_complete=all(p.exists() for p in (best,model,residual)))
    if result.returncode==0 and row['products_complete']:
        pars=c5o.parse_bestfit(best)
        with fits.open(data,memmap=False) as h: observed=np.asarray(h[0].data,float)
        with fits.open(model,memmap=False) as h: predicted=np.asarray(h[0].data,float)
        with fits.open(residual,memmap=False) as h: saved=np.asarray(h[0].data,float)
        calc=observed-predicted
        if not all(np.isfinite(x).all() for x in (observed,predicted,saved)):
            raise RuntimeError('nonfinite fit image')
        row.update(finite=True,**pars,bound_hits=c5o.bound_hits(pars),sse=float(np.sum(calc**2)),
                   residual_l1_over_data_l1=float(np.abs(calc).sum()/np.abs(observed).sum()),
                   saved_residual_max_abs_error=float(np.max(np.abs(calc-saved))),
                   bestfit_sha256=c5o.sha(best),model_sha256=c5o.sha(model),residual_sha256=c5o.sha(residual))
        np.savez_compressed(directory/'images.npz',data=observed,model=predicted,
                            residual=calc,saved_residual=saved)
    else:
        row.update(finite=False,error='nonzero exit or missing products')
    dump(directory/'result.json',row); return row


def run(module,source,c5o_artifact,binary,out):
    out.mkdir(parents=True,exist_ok=False); cfg=configuration(module); dump(out/'config.json',cfg)
    if cfg['runtime_versions']!=cfg['pins']: raise RuntimeError('dependency pin mismatch')
    if c5o.sha(binary)!=c5o.IMFIT_SHA: raise RuntimeError('wrong Imfit executable')
    receipt=json.loads(C5O_RECEIPT.read_text())
    if receipt['run_id']!=C5O_RUN or receipt['github_conclusion']!='failure': raise RuntimeError('wrong C5o receipt')
    prior=json.loads((c5o_artifact/'failure.json').read_text())
    if prior!={'type':'RuntimeError','message':'incomplete fit starts'}: raise RuntimeError('unexpected C5o failure')
    prior_cfg=json.loads((c5o_artifact/'config.json').read_text())
    if prior_cfg['github_sha']!=C5O_COMMIT or prior_cfg['host_n']!=4: raise RuntimeError('wrong C5o artifact')
    c5o.verified_parent(source,out,4)
    with np.load(source/'templates.npz') as z: templates={k:z[k].copy() for k in z.files}
    with np.load(source/f'truth{module}_ratio10.npz') as z: data=z['data'].copy()
    inputs=out/'inputs'; inputs.mkdir()
    data_path=inputs/f'data_{module}_ratio10.fits'; fits.writeto(data_path,data,overwrite=False)
    psf=inputs/f'psf_{module}.fits'; fits.writeto(psf,templates[f'{module}_fine_quintic_point'],overwrite=False)
    noise=inputs/'noise.fits'; fits.writeto(noise,np.ones((201,201)),overwrite=False)
    if module=='A':
        if c5o.sha(data_path)!=c5o.sha(c5o_artifact/'inputs/data_A_ratio10.fits'): raise RuntimeError('C5o data mismatch')
        if c5o.sha(psf)!=c5o.sha(c5o_artifact/'inputs/psf_A.fits'): raise RuntimeError('C5o PSF mismatch')
    initial=out/'compact_initial.dat'; initial.write_text(c5o.model_text(4,cfg['start'],10.))
    attempts=[]
    for solver,flags in SOLVERS:
        attempts.append(run_solver(binary,data_path,psf,noise,initial,solver,flags,out/'fits'/solver))
    if len(attempts)!=cfg['expected_attempts']: raise RuntimeError('incomplete attempted processes')
    dump(out/'summary.json',dict(config=cfg,attempts=attempts,
        interpretation='optimizer-path diagnostic; finite fit or exit status is not physical recovery'))


def main():
    p=argparse.ArgumentParser();p.add_argument('--module',choices=MODULES,required=True)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--c5o',type=Path,required=True)
    p.add_argument('--imfit',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();started=time.monotonic()
    try: run(a.module,a.source,a.c5o,a.imfit,a.out)
    except Exception as error:
        a.out.mkdir(parents=True,exist_ok=True);dump(a.out/'failure.json',dict(type=type(error).__name__,message=str(error)));raise
    finally:
        a.out.mkdir(parents=True,exist_ok=True);dump(a.out/'runtime.json',dict(wall_seconds=time.monotonic()-started,
            max_resident_set_kib_linux=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


if __name__=='__main__': main()
