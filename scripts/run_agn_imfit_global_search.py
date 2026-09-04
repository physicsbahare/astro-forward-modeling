#!/usr/bin/env python3
"""C5q: seeded Imfit DE-LHS on the frozen C5p difficult scenes."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import time

import run_agn_imfit_optimizer_path as c5p
from run_agn_empirical_psf_transfer import dump

ROOT=Path(__file__).resolve().parents[1]
C5P_RUN=33823405733
C5P_COMMIT='b5644c92fa1efc7204cd267acdc098636cf437b2'
C5P_ARTIFACTS={'A':9919733109,'B':9920016772}
C5P_RECEIPT=ROOT/'benchmarks/zhuang_shen_2024/c5p_33823405733.json'
PROTOCOL=ROOT/'benchmarks/zhuang_shen_2024/C5Q_PROTOCOL.md'
SEEDS=(20260904,20260905)


def configuration(module):
    if module not in c5p.MODULES: raise ValueError('module must be A or B')
    return dict(stage='C5q seeded Imfit global-search diagnostic',
        github_run_id=os.getenv('GITHUB_RUN_ID'),github_sha=os.getenv('GITHUB_SHA'),
        c5p_run=C5P_RUN,c5p_commit=C5P_COMMIT,c5p_artifact_id=C5P_ARTIFACTS[module],
        c5p_receipt_sha256=c5p.c5o.sha(C5P_RECEIPT),protocol_sha256=c5p.c5o.sha(PROTOCOL),
        module=module,host_n=4,ratio=10.,start=dict(c5p.c5o.STARTS[1]),
        solver='Imfit 1.9.0 Differential Evolution with Latin-hypercube initialization',
        cli_solver_flag='--de-lhs',seeds=list(SEEDS),timeout_seconds=c5p.TIMEOUT,
        shape_bounds=c5p.c5o.SHAPE_BOUNDS,amplitude_bounds=c5p.c5o.AMPLITUDE_BOUNDS,
        centers='fixed at Imfit 1-based (101,101); host and nucleus coincident',
        objective='constant unit noise map; full-crop unweighted pixel-space chi-square',
        psf='exact archived C5p matched signed native PSF; --no-normalize',
        imfit_version='1.9.0',imfit_binary_sha256=c5p.c5o.IMFIT_SHA,imfit_threads=1,
        pins=c5p.PINS,runtime_versions={k:importlib.metadata.version(k) for k in c5p.PINS},
        expected_attempts=2,
        completion_rule='both seeded bounded processes and logs recorded; timeout/nonconvergence retained',
        acceptance='diagnostic only; no convergence or recovery band')


def run(module,source,binary,out):
    out.mkdir(parents=True,exist_ok=False);cfg=configuration(module);dump(out/'config.json',cfg)
    if cfg['runtime_versions']!=cfg['pins']: raise RuntimeError('dependency pin mismatch')
    if c5p.c5o.sha(binary)!=c5p.c5o.IMFIT_SHA: raise RuntimeError('wrong Imfit executable')
    receipt=json.loads(C5P_RECEIPT.read_text())
    if receipt['run_id']!=C5P_RUN or receipt['github_conclusion']!='success': raise RuntimeError('wrong C5p receipt')
    parent_cfg=json.loads((source/'config.json').read_text())
    parent_summary=json.loads((source/'summary.json').read_text())
    if parent_cfg!=parent_summary['config'] or parent_cfg['github_sha']!=C5P_COMMIT or parent_cfg['module']!=module:
        raise RuntimeError('wrong C5p artifact')
    data=source/'inputs'/f'data_{module}_ratio10.fits';psf=source/'inputs'/f'psf_{module}.fits'
    noise=source/'inputs/noise.fits';initial=source/'compact_initial.dat'
    attempts=[]
    for seed in SEEDS:
        label=f'de_lhs_seed{seed}'
        row=c5p.run_solver(binary,data,psf,noise,initial,label,('--de-lhs','--seed',str(seed)),out/'fits'/label)
        row['seed']=seed;attempts.append(row);dump(out/'fits'/label/'result.json',row)
    if len(attempts)!=cfg['expected_attempts']: raise RuntimeError('incomplete attempted processes')
    dump(out/'summary.json',dict(config=cfg,attempts=attempts,
        interpretation='seeded global-search diagnostic; finite output or agreement is not physical recovery'))


def main():
    p=argparse.ArgumentParser();p.add_argument('--module',choices=c5p.MODULES,required=True)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--imfit',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args();started=time.monotonic()
    try: run(a.module,a.source,a.imfit,a.out)
    except Exception as error:
        a.out.mkdir(parents=True,exist_ok=True);dump(a.out/'failure.json',dict(type=type(error).__name__,message=str(error)));raise
    finally:
        a.out.mkdir(parents=True,exist_ok=True);dump(a.out/'runtime.json',dict(wall_seconds=time.monotonic()-started,
            max_resident_set_kib_linux=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


if __name__=='__main__':main()
