#!/usr/bin/env python3
"""C5k: bounded grid/cutoff experiment; historical C5j remains incomplete."""
import argparse
import itertools
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

import galsim
import numpy as np
import run_agn_fourier_controls as engine

parent = engine.parent
ROOT = engine.ROOT
PROTOCOL = ROOT/'benchmarks/zhuang_shen_2024/C5K_PROTOCOL.md'
LOCAL_RECORD = ROOT/'benchmarks/zhuang_shen_2024/c5j_local_20260903.json'
GRIDS = (1024,1536)
MULTIPLIERS = (1,2,4)
ARMS = ('replay',)+tuple(f'grid{g}_k{k}' for g,k in itertools.product(GRIDS,MULTIPLIERS))


def arm_config(arm):
    if arm not in ARMS:
        raise ValueError('outside frozen bounded grid/cutoff list')
    cfg = dict(settings=dict(parent.SETTINGS['fine']),calculate_stepk=True,
        calculate_maxk=True,force_maxk_multiplier=None)
    if arm != 'replay':
        grid,multiplier = arm.removeprefix('grid').split('_k')
        cfg['settings']['minimum_fft_size'] = int(grid)
        cfg.update(calculate_stepk=False,force_maxk_multiplier=int(multiplier))
    return cfg


def configuration(host_n):
    cfg = engine.configuration(host_n)
    cfg.update(stage='C5k bounded Fourier-spacing/cutoff diagnosis',
        protocol_sha256=parent.sha(PROTOCOL),arms={a:arm_config(a) for a in ARMS},
        c5j_local_record_sha256=parent.sha(LOCAL_RECORD),
        worker_adapter='C5j bounded worker with an explicit scoped C5k model-construction adapter',
        worker_engine_sha256=parent.sha(ROOT/'scripts/run_agn_fourier_controls.py'),
        c5j_status='LOCAL incomplete; four MemoryErrors retained; never dispatched',
        expected_workers=28,expected_sersic_images=28,
        expected_gaussian_images=28 if host_n==1 else 0,expected_direct_starts=28,
        expected_pairwise_comparisons=84,
        limitations='finite bounded cutoff sequence, not the full interpolant range or independent convergence')
    return cfg


def models(case, normalized, arm, gaussian=False):
    cfg = arm_config(arm)
    if arm == 'replay':
        return historical_models(case,normalized,'fine',gaussian)
    source,radius = parent.galaxy(case,cfg['settings'],'nominal_hlr',gaussian)
    inherited_psf = parent.effective_psf(normalized,parent.SETTINGS['fine'])
    reference_maxk = float(inherited_psf.maxk)
    forced_maxk = reference_maxk*cfg['force_maxk_multiplier']
    psf = galsim.InterpolatedImage(galsim.Image(np.array(normalized,dtype=float),scale=engine.PSF_SCALE),
        normalization='flux',x_interpolant='quintic',k_interpolant='quintic',pad_factor=4.,
        depixelize=False,use_true_center=True,noise_pad_size=0,
        calculate_stepk=False,calculate_maxk=True,_force_maxk=forced_maxk,
        gsparams=galsim.GSParams(**cfg['settings']))
    convolution = galsim.Convolve(source,psf,propagate_gsparams=True)
    assert source.gsparams == psf.gsparams == convolution.gsparams
    assert psf.maxk == forced_maxk == convolution.obj_list[1].maxk
    radius.update(inherited_psf_maxk_inverse_arcsec=reference_maxk,
        forced_psf_maxk_inverse_arcsec=forced_maxk,minimum_fft_size=cfg['settings']['minimum_fft_size'])
    return source,psf,convolution,radius


# Explicit dependency injection in each isolated worker; C5j source/settings are unchanged.
historical_models = engine.models


def worker(path):
    original = engine.models
    try:
        engine.models = models
        status = engine.worker(path)
        if status == 0:
            # Completeness only: do not accept a successful image with a missing
            # FFT receipt. This leaves the frozen rendering settings unchanged.
            directory = path.parent
            result = engine.read(directory/'result.json')
            try:
                cfg = engine.read(path)
                expected = 2 if cfg['case']['n'] == .5 else 1
                if len(engine.read(directory/'fft_trace.json')) != expected:
                    raise RuntimeError('incomplete FFT trace: every draw requires a receipt')
            except Exception as error:
                result.update(success=False,exception_type=type(error).__name__,message=str(error))
                engine.dump(directory/'result.json',result)
                return 1
        return status
    finally:
        engine.models = original


def run_worker(case,module,arm,psf_path,directory):
    directory.mkdir(parents=True,exist_ok=False)
    cfg=dict(case=case,module=module,arm=arm,arm_config=arm_config(arm),psf_path=str(psf_path),
        timeout_seconds=engine.TIMEOUT,address_space_bytes=engine.ADDRESS_SPACE_BYTES)
    path=directory/'worker_config.json';engine.dump(path,cfg)
    command=['/usr/bin/timeout','--kill-after=5s',str(engine.TIMEOUT),sys.executable,
             str(Path(__file__).resolve()),'--worker',str(path)]
    engine.dump(directory/'command.json',command); start=time.monotonic()
    try:
        with (directory/'stdout.txt').open('w') as stdout,(directory/'stderr.txt').open('w') as stderr:
            completed=subprocess.run(command,stdout=stdout,stderr=stderr,check=False)
        result=directory/'result.json'
        row=engine.read(result) if result.exists() else dict(success=False,message='no worker result')
        row['returncode']=completed.returncode
        if completed.returncode:
            row.update(success=False,process_error='timeout' if completed.returncode in (124,137) else 'worker failed')
    except Exception as error:
        row=dict(success=False,exception_type=type(error).__name__,message=str(error))
    row.update(name=directory.name,case=case,module=module,arm=arm,wall_seconds=time.monotonic()-start)
    engine.dump(directory/'process_result.json',row)
    return row


def run(host_n,source,out):
    cfg=configuration(host_n);engine.dump(out/'config.json',cfg)
    if cfg['pins']!=cfg['runtime_versions']:
        raise RuntimeError('dependency pin mismatch')
    record=engine.read(LOCAL_RECORD)
    assert record['scope'].startswith('LOCAL ONLY')
    assert sum(a['counts']['failed_workers'] for a in record['artifacts'])==4
    for path,digest in record['source_sha256'].items():
        assert parent.sha(ROOT/path)==digest, 'historical C5j source changed'
    copied=engine.verified_inputs(source,out,host_n)
    workers=[];rows=[];starts=[];images={};pairs=[]
    comparison_dir=out/'comparisons';comparison_dir.mkdir()
    for case,module,arm in itertools.product(parent.cases(host_n),('A','B'),ARMS):
        name=f"{case['name']}_{module}_{arm}";directory=out/'renders'/name
        w=run_worker(case,module,arm,copied/'psfs.npz',directory)
        workers.append(w);engine.dump(out/'worker_progress.json',workers)
        print(dict(worker=name,success=w['success'],wall_seconds=w['wall_seconds']),flush=True)
        if not w['success']:continue
        with np.load(directory/'images.npz',allow_pickle=False) as f:image=f['image'].copy()
        images[case['name'],module,arm]=image
        with np.load(copied/f"renders/{case['name']}_{module}_fine/nominal_hlr.npz") as f:reference=f['sersic'].copy()
        with np.load(copied/f"parent/renders/{case['name']}_{module}_s8/native.npz") as f:imfit=f['image'].copy()
        if arm=='replay':np.testing.assert_allclose(image,reference,rtol=0,atol=1e-12)
        row,prediction=parent.amplitude_comparison(reference,image)
        row.update(case=name,shape=case['name'],n=case['n'],re=case['re'],q=case['q'],module=module,arm=arm,
            comparison_to_imfit8=parent.comparison(image,imfit),
            replay_max_abs_error=float(np.abs(image-reference).max()) if arm=='replay' else None)
        rows.append(row);starts.append(dict(**row,start=0,start_type='one direct NNLS, not nonlinear multistart'))
        parent.save_arrays(comparison_dir/(name+'.npz'),reference=reference,template=image,
            prediction=prediction,residual=prediction-reference)
    pair_dir=out/'pairwise';pair_dir.mkdir()
    for case,module in itertools.product(parent.cases(host_n),('A','B')):
        for left,right in itertools.combinations(ARMS,2):
            a,b=images.get((case['name'],module,left)),images.get((case['name'],module,right))
            if a is None or b is None:continue
            name=f"{case['name']}_{module}_{left}_vs_{right}"
            pairs.append(dict(case=name,shape=case['name'],n=case['n'],q=case['q'],module=module,
                left=left,right=right,left_sha256=engine.digest(a),right_sha256=engine.digest(b),
                **parent.comparison(a,b)))
            parent.save_arrays(pair_dir/(name+'.npz'),residual=a-b)
    engine.write_csv(out/'metrics.csv',rows);engine.write_csv(out/'fit_starts.csv',starts)
    engine.write_csv(out/'pairwise.csv',pairs);engine.manifest(out)
    complete=len(workers)==28 and all(w['success'] for w in workers) and len(rows)==28 and len(pairs)==84
    engine.dump(out/'summary.json',dict(config=cfg,complete=complete,workers=workers,results=rows,
        starts=starts,pairwise=pairs,interpretation='Bounded sensitivity, not full-range convergence or morphology recovery'))
    if not complete:raise RuntimeError('incomplete C5k diagnostic; every attempt/failure retained')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--worker',type=Path)
    parser.add_argument('--source',type=Path)
    parser.add_argument('--host-n',type=int,choices=(1,4))
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    if args.worker:return worker(args.worker.resolve())
    if args.source is None or args.host_n is None or args.out is None:
        parser.error('--source, --host-n and --out are required')
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False);start=time.monotonic()
    try:run(args.host_n,args.source.resolve(),out)
    except Exception as error:
        engine.dump(out/'failure.json',dict(exception_type=type(error).__name__,message=str(error)));raise
    finally:
        engine.dump(out/'runtime.json',dict(wall_seconds=time.monotonic()-start,
            peak_parent_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    return 0


if __name__=='__main__':sys.exit(main())
