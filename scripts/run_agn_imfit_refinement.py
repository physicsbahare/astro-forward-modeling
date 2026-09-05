#!/usr/bin/env python3
"""C5m: reuse Imfit with a frozen finer numerical grid, not a new renderer."""
import argparse
from contextlib import contextmanager
import itertools
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time
import numpy as np
from astropy.io import fits
import run_agn_cell_response as c
import run_agn_imfit_renderer as h

SAMPLES=(8,16)
PROTOCOL=h.ROOT/'benchmarks/zhuang_shen_2024/C5M_PROTOCOL.md'
AUDIT=h.ROOT/'benchmarks/zhuang_shen_2024/cell_response_33798675379.json'


@contextmanager
def sampling_scope():
    old=h.SAMPLES
    try:
        h.SAMPLES=SAMPLES
        yield
    finally:h.SAMPLES=old


def configuration(n):
    return dict(stage='C5m bounded Imfit sampling refinement',host_n=n,cases=c.p.cases(n),
        samples=SAMPLES,github_run_id=os.getenv('GITHUB_RUN_ID'),github_sha=os.getenv('GITHUB_SHA'),
        parent_run=33798675379,parent_commit='094de88e88b668015658536d13583c201cfaaaf2',
        parent_audit_sha256=h.sha(AUDIT),protocol_sha256=h.sha(PROTOCOL),
        producer_sha256=h.sha(Path(__file__)),historical_adapter_sha256=h.sha(Path(h.__file__)),
        pins=h.PINS,runtime_versions={k:h.importlib.metadata.version(k) for k in h.PINS},
        binary_sha256=h.IMFIT_BINARY_SHA,timeout_seconds=c.e.TIMEOUT,
        address_space_bytes=c.e.ADDRESS_SPACE_BYTES,expected_workers=8,expected_starts=16,
        expected_pairs=4,expected_new_arrays=84,acceptance='complete provenance and inherited algebra only')


def load_psf(path,module):
    with np.load(path,allow_pickle=False) as f:
        if set(f.files)!={'A','B'}:raise ValueError('unexpected C5l PSF archive schema')
        image=f[module].copy()
    if image.shape!=(401,401) or not np.isfinite(image).all():raise ValueError('invalid PSF')
    return image


def worker(path):
    cfg=c.e.read(path);directory=path.parent
    resource.setrlimit(resource.RLIMIT_AS,(c.e.ADDRESS_SPACE_BYTES,)*2)
    start=time.monotonic()
    try:
        if cfg['sampling'] not in SAMPLES:raise ValueError('outside frozen sampling')
        binary=Path(cfg['binary'])
        if h.sha(binary)!=h.IMFIT_BINARY_SHA:raise ValueError('wrong binary')
        with sampling_scope():
            normalized=load_psf(cfg['psfs'],cfg['module'])
            kernel=h.psf_kernel(normalized,cfg['sampling'])
            kernel_path=directory/'kernel.fits';fits.writeto(kernel_path,kernel,overwrite=False)
            c.p.save_arrays(directory/'kernel.npz',image=kernel)
            image,result=h.run_renderer(binary,cfg['case'],cfg['sampling'],kernel_path,directory/'imfit')
        if image is None:raise RuntimeError('Imfit failure; see retained imfit/result.json and logs')
        result.update(kernel_sha256=c.e.digest(kernel),kernel_stats=dict(sum=float(kernel.sum()),
            negative_pixels=int((kernel<0).sum()),shape=list(kernel.shape)),
            total_worker_seconds=time.monotonic()-start)
        c.e.dump(directory/'worker_result.json',result);return 0
    except Exception as exc:
        c.e.dump(directory/'worker_result.json',dict(success=False,error_type=type(exc).__name__,
            message=str(exc),wall_seconds=time.monotonic()-start));return 1


def run_worker(case,module,sampling,binary,psfs,directory):
    directory.mkdir(parents=True,exist_ok=False)
    path=directory/'worker_config.json'
    c.e.dump(path,dict(case=case,module=module,sampling=sampling,binary=str(binary),psfs=str(psfs)))
    command=['/usr/bin/timeout','--kill-after=5s',str(c.e.TIMEOUT),sys.executable,
             str(Path(__file__).resolve()),'--worker',str(path)]
    c.e.dump(directory/'command.json',command);start=time.monotonic()
    with (directory/'stdout.txt').open('w') as stdout,(directory/'stderr.txt').open('w') as stderr:
        process=subprocess.run(command,stdout=stdout,stderr=stderr,check=False)
    result_path=directory/'worker_result.json'
    result=c.e.read(result_path) if result_path.exists() else dict(success=False,message='worker produced no receipt')
    result.update(returncode=process.returncode,wall_seconds=time.monotonic()-start,
        name=directory.name,case=case,module=module,sampling=sampling)
    result['success']=result['success'] and process.returncode==0
    c.e.dump(directory/'process_result.json',result);return result


def run(n,source,binary,out):
    cfg=configuration(n);c.e.dump(out/'config.json',cfg)
    if cfg['runtime_versions']!=cfg['pins']:raise ValueError('dependency pin mismatch')
    if h.sha(binary)!=h.IMFIT_BINARY_SHA:raise ValueError('wrong makeimage binary')
    receipt=c.e.read(AUDIT)
    assert receipt['run_id']==33798675379 and receipt['github_confirmation']['conclusion']=='success'
    parent=next(x for x in receipt['artifacts'] if x['host_n']==n)
    c.p.verify_manifest(source,parent['file_sha256'])
    selected=['parent/grid/parent/psfs.npz']
    for case,module in itertools.product(c.p.cases(n),('A','B')):
        selected += [f"parent/imfit/parent/renders/{case['name']}_{module}_s8/native.npz",
                     f"renders/{case['name']}_{module}_no_cell/images.npz"]
    for rel in selected:
        dest=out/'parent'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/rel,dest)
    c.e.dump(out/'source_manifest.json',{rel:parent['file_sha256'][rel] for rel in selected})
    software=out/'software';software.mkdir()
    for name in ('README.txt','COPYING.txt'):shutil.copy2(binary.parent/name,software/name)
    version=subprocess.run([str(binary),'--version'],capture_output=True,text=True,check=False)
    assert 'version 1.9.0' in version.stdout
    c.e.dump(out/'binary.json',dict(sha256=h.sha(binary),stdout=version.stdout,stderr=version.stderr,returncode=version.returncode))
    workers=[];rows=[];starts=[];pairs=[];images={};start=time.monotonic()
    (out/'comparisons').mkdir();(out/'pairwise').mkdir()
    psfs=out/'parent/parent/grid/parent/psfs.npz'
    for case,module,sampling in itertools.product(c.p.cases(n),('A','B'),SAMPLES):
        name=f"{case['name']}_{module}_s{sampling}"
        w=run_worker(case,module,sampling,binary,psfs,out/'renders'/name);workers.append(w)
        c.e.dump(out/'worker_progress.json',workers)
        if not w['success']:continue
        with np.load(out/'renders'/name/'imfit/native.npz') as f:image=f['image'].copy()
        images[name]=image
        refs={'imfit8':out/f"parent/parent/imfit/parent/renders/{case['name']}_{module}_s8/native.npz",
              'galsim_no_cell':out/f"parent/renders/{case['name']}_{module}_no_cell/images.npz"}
        for label,refpath in refs.items():
            with np.load(refpath) as f:ref=f['image'].copy()
            if sampling==8 and label=='imfit8':np.testing.assert_allclose(image,ref,rtol=0,atol=1e-12)
            fit,pred=c.p.amplitude_comparison(ref,image)
            row=dict(**fit,case=name+'_'+label,render=name,n=case['n'],q=case['q'],module=module,sampling=sampling,reference=label)
            rows.append(row);starts.append(dict(**row,start=0,start_type='direct NNLS projection'))
            c.p.save_arrays(out/'comparisons'/(row['case']+'.npz'),template=image,reference=ref,prediction=pred,residual=pred-ref)
    for case,module in itertools.product(c.p.cases(n),('A','B')):
        name=f"{case['name']}_{module}";lo=name+f'_s{SAMPLES[0]}';hi=name+f'_s{SAMPLES[-1]}'
        if lo not in images or hi not in images:continue
        a,b=images[hi],images[lo]
        pairs.append(dict(case=name,left=hi,right=lo,**h.comparison(a,b)))
        c.p.save_arrays(out/'pairwise'/(name+'.npz'),residual=a-b)
    complete=len(rows)==16 and len(pairs)==4 and all(w['success'] for w in workers)
    c.e.dump(out/'summary.json',dict(config=cfg,workers=workers,results=rows,starts=starts,pairwise=pairs,complete=complete))
    for name,data in [('metrics',rows),('fit_starts',starts),('pairwise',pairs)]:
        if data:h.write_csv(out/(name+'.csv'),data)
    c.e.manifest(out)
    c.e.dump(out/'runtime.json',dict(wall_seconds=time.monotonic()-start))
    if not complete:raise RuntimeError('incomplete frozen experiment; failures retained, no retries')


def main():
    p=argparse.ArgumentParser();p.add_argument('--worker',type=Path);p.add_argument('--source',type=Path)
    p.add_argument('--makeimage',type=Path);p.add_argument('--host-n',type=int,choices=(1,4));p.add_argument('--out',type=Path)
    args=p.parse_args()
    if args.worker:raise SystemExit(worker(args.worker))
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    try:run(args.host_n,args.source.resolve(),args.makeimage.resolve(),out)
    except Exception as exc:
        c.e.dump(out/'failure.json',dict(type=type(exc).__name__,message=str(exc)));raise


if __name__=='__main__':main()
