#!/usr/bin/env python3
"""C5l: explicit finite-cell controls using existing GalSim objects only."""
import argparse
import itertools
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time
import numpy as np
import galsim
import run_agn_fourier_grid as grid

e=grid.engine
p=grid.parent
ROOT=grid.ROOT
PROTOCOL=ROOT/'benchmarks/zhuang_shen_2024/C5L_PROTOCOL.md'
AUDIT=ROOT/'benchmarks/zhuang_shen_2024/fourier_grid_33788705952.json'
ARMS=('no_cell','cell2','cell4','cell8')
SAMPLES=(2,4,8)


def arm_config(arm):
    if arm not in ARMS:raise ValueError('outside frozen cell controls')
    return dict(**grid.arm_config('grid1536_k4'),
        numerical_cell_sampling=None if arm=='no_cell' else int(arm[4:]),
        cell_role='diagnostic numerical response, NOT an added physical detector pixel')


def configuration(n):
    cfg=grid.configuration(n)
    cfg.update(stage='C5l finite numerical-cell convention diagnostic',
        protocol_sha256=p.sha(PROTOCOL),parent_run=33788705952,
        parent_commit='7ad6e1ca1b6a78dcde83d6cdea9e3c1bc26bd33b',
        parent_audit_sha256=p.sha(AUDIT),secondary_parent_run=33766246396,
        secondary_parent_audit_sha256=p.sha(e.AUDIT),
        arms={a:arm_config(a) for a in ARMS},imfit_reference_samples=SAMPLES,
        worker_adapter='C5j worker with explicit composite-PSF numerical cell; strict C5k receipt rule',
        expected_workers=16,expected_sersic_images=16,expected_gaussian_images=16 if n==1 else 0,
        expected_direct_starts=48,expected_pairwise_comparisons=24,
        limitations='uniform cell is not exact Imfit adaptive integration; finite cutoff and signed PSF remain')
    return cfg


def models(case,normalized,arm,gaussian=False):
    cfg=arm_config(arm)
    source,psf,convolution,radius=grid.models(case,normalized,'grid1536_k4',gaussian)
    sampling=cfg['numerical_cell_sampling']
    radius.update(numerical_cell_sampling=sampling,numerical_cell_scale_arcsec=None,
                  cell_is_physical_detector_response=False)
    if sampling is not None:
        scale=e.NATIVE_SCALE/sampling
        cell=galsim.Pixel(scale=scale,flux=1.,gsparams=psf.gsparams)
        psf=galsim.Convolve(psf,cell,propagate_gsparams=True)
        convolution=galsim.Convolve(source,psf,propagate_gsparams=True)
        radius.update(numerical_cell_scale_arcsec=scale,numerical_cell_flux=cell.flux)
    assert source.gsparams==psf.gsparams==convolution.gsparams
    return source,psf,convolution,radius


def worker(path):
    original=e.models
    try:
        e.models=models
        status=e.worker(path)
        if status==0:
            expected=2 if e.read(path)['case']['n']==.5 else 1
            if len(e.read(path.parent/'fft_trace.json'))!=expected:
                row=e.read(path.parent/'result.json')
                row.update(success=False,message='incomplete FFT draw receipts')
                e.dump(path.parent/'result.json',row);return 1
        return status
    finally:e.models=original


def run_worker(case,module,arm,psf_path,directory):
    directory.mkdir(parents=True,exist_ok=False)
    config=directory/'worker_config.json'
    e.dump(config,dict(case=case,module=module,arm=arm,arm_config=arm_config(arm),
        psf_path=str(psf_path),timeout_seconds=e.TIMEOUT,address_space_bytes=e.ADDRESS_SPACE_BYTES))
    command=['/usr/bin/timeout','--kill-after=5s',str(e.TIMEOUT),sys.executable,
             str(Path(__file__).resolve()),'--worker',str(config)]
    e.dump(directory/'command.json',command);start=time.monotonic()
    with (directory/'stdout.txt').open('w') as stdout,(directory/'stderr.txt').open('w') as stderr:
        result=subprocess.run(command,stdout=stdout,stderr=stderr,check=False)
    path=directory/'result.json'
    row=e.read(path) if path.exists() else dict(success=False,message='no worker result')
    row.update(returncode=result.returncode,name=directory.name,case=case,module=module,
               arm=arm,wall_seconds=time.monotonic()-start)
    if result.returncode:row.update(success=False,process_error='worker failed or timed out')
    e.dump(directory/'process_result.json',row);return row


def verified_inputs(source,imfit_source,out,n):
    records={}
    for key,root,record in [('grid',source,e.read(AUDIT)),('imfit',imfit_source,e.read(e.AUDIT))]:
        receipt=record['github_confirmation']
        assert receipt['status']=='completed' and receipt['conclusion']=='success'
        assert len(receipt['jobs'])==2 and all(j['conclusion']=='success' for j in receipt['jobs'])
        a=next(x for x in record['artifacts'] if x['host_n']==n)
        p.verify_manifest(root,a['file_sha256'])
        selected=['config.json','source_manifest.json']
        if key=='grid':
            assert record['run_id']==33788705952
            selected += ['parent/psfs.npz','commit.txt']
            selected += [f"renders/{c['name']}_{m}_grid1536_k4/images.npz" for c,m in itertools.product(p.cases(n),('A','B'))]
        else:
            assert record['run_id']==33766246396
            selected += [f"parent/renders/{c['name']}_{m}_s{s}/native.npz" for c,m,s in itertools.product(p.cases(n),('A','B'),SAMPLES)]
        for rel in selected:
            target=out/'parent'/key/rel;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(root/rel,target)
        records[key]=dict(run=record['run_id'],commit=record['commit'],artifact_id=a['artifact_id'],
            zip_sha256=a['zip_sha256'],verified_files=len(a['file_sha256']),
            selected_file_sha256={rel:a['file_sha256'][rel] for rel in selected})
    e.dump(out/'source_manifest.json',records)


def run(n,source,imfit_source,out):
    cfg=configuration(n);e.dump(out/'config.json',cfg)
    assert cfg['runtime_versions']==cfg['pins']
    verified_inputs(source,imfit_source,out,n)
    psfs=out/'parent/grid/parent/psfs.npz'
    workers=[];rows=[];starts=[];images={};pairs=[]
    (out/'comparisons').mkdir();(out/'pairwise').mkdir()
    for case,module,arm in itertools.product(p.cases(n),('A','B'),ARMS):
        name=f"{case['name']}_{module}_{arm}";directory=out/'renders'/name
        w=run_worker(case,module,arm,psfs,directory);workers.append(w)
        e.dump(out/'worker_progress.json',workers)
        print(dict(worker=name,success=w['success'],seconds=w['wall_seconds']),flush=True)
        if not w['success']:continue
        with np.load(directory/'images.npz',allow_pickle=False) as f:image=f['image'].copy()
        images[case['name'],module,arm]=image
        if arm=='no_cell':
            with np.load(out/f"parent/grid/renders/{case['name']}_{module}_grid1536_k4/images.npz") as f:
                np.testing.assert_allclose(image,f['image'],rtol=0,atol=1e-12)
        for sampling in SAMPLES:
            with np.load(out/f"parent/imfit/parent/renders/{case['name']}_{module}_s{sampling}/native.npz") as f:reference=f['image'].copy()
            row,prediction=p.amplitude_comparison(reference,image)
            label=name+f'_imfit{sampling}'
            row.update(case=label,render=name,shape=case['name'],n=case['n'],q=case['q'],
                module=module,arm=arm,imfit_sampling=sampling,
                matched_cell=(arm==f'cell{sampling}'))
            rows.append(row);starts.append(dict(**row,start=0,start_type='one direct NNLS projection'))
            p.save_arrays(out/'comparisons'/(label+'.npz'),reference=reference,template=image,
                prediction=prediction,residual=prediction-reference)
    for case,module in itertools.product(p.cases(n),('A','B')):
        for left,right in itertools.combinations(ARMS,2):
            a,b=images.get((case['name'],module,left)),images.get((case['name'],module,right))
            if a is None or b is None:continue
            name=f"{case['name']}_{module}_{left}_vs_{right}"
            pairs.append(dict(case=name,shape=case['name'],module=module,left=left,right=right,
                left_sha256=e.digest(a),right_sha256=e.digest(b),**p.comparison(a,b)))
            p.save_arrays(out/'pairwise'/(name+'.npz'),residual=a-b)
    e.write_csv(out/'metrics.csv',rows);e.write_csv(out/'fit_starts.csv',starts)
    e.write_csv(out/'pairwise.csv',pairs);e.manifest(out)
    complete=len(workers)==16 and all(w['success'] for w in workers) and len(rows)==48 and len(pairs)==24
    e.dump(out/'summary.json',dict(config=cfg,complete=complete,workers=workers,results=rows,starts=starts,pairwise=pairs))
    if not complete:raise RuntimeError('incomplete C5l; all attempts and failures retained')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--worker',type=Path)
    parser.add_argument('--host-n',type=int,choices=(1,4));parser.add_argument('--source',type=Path)
    parser.add_argument('--imfit-source',type=Path);parser.add_argument('--out',type=Path);a=parser.parse_args()
    if a.worker:return worker(a.worker.resolve())
    if any(x is None for x in (a.host_n,a.source,a.imfit_source,a.out)):parser.error('all parent/output arguments required')
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);start=time.monotonic()
    try:run(a.host_n,a.source.resolve(),a.imfit_source.resolve(),out)
    except Exception as error:
        e.dump(out/'failure.json',dict(exception_type=type(error).__name__,message=str(error)));raise
    finally:e.dump(out/'runtime.json',dict(wall_seconds=time.monotonic()-start,peak_parent_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    return 0


if __name__=='__main__':sys.exit(main())
