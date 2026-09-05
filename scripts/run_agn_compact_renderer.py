#!/usr/bin/env python3
"""C5i: reuse GalSim to diagnose archived compact Imfit sampling, not fit shape."""
import argparse
import importlib.metadata
import itertools
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time
import warnings

import galsim
import numpy as np
from scipy.special import gammaincinv

from run_agn_imfit_renderer import (ROOT, SAMPLES, STAMP, sha, imfit_bn,
    image_stats, comparison, structural_cases)
from run_agn_empirical_psf_phase import PINS, digest
from run_agn_empirical_psf_transfer import (effective_psf, draw, dump, SETTINGS,
    NATIVE_SCALE, PSF_SCALE, normalize_psf)
from run_agn_nuclear_fraction_noiseless import profile_flux, write_csv

PARENT_RUN = 33759931812
PARENT_COMMIT = '391efc236c440e76ed5dcd7c7b7e71e444fea012'
AUDIT = ROOT/'benchmarks/zhuang_shen_2024/imfit_renderer_33759931812.json'
PROTOCOL = ROOT/'benchmarks/zhuang_shen_2024/C5I_PROTOCOL.md'
CONVENTIONS = ('nominal_hlr', 'imfit_bn_equivalent')
TIMEOUT = 120
ADDRESS_SPACE_BYTES = 6*1024**3


def cases(host_n):
    return [c for c in structural_cases(host_n) if c['re']==.5]


def configuration(host_n):
    return dict(stage='C5i compact-boundary GalSim/archived-Imfit diagnosis',
        github_run_id=os.getenv('GITHUB_RUN_ID'),github_sha=os.getenv('GITHUB_SHA'),
        parent_run=PARENT_RUN,parent_commit=PARENT_COMMIT,parent_audit_sha256=sha(AUDIT),
        protocol_sha256=sha(PROTOCOL),host_n=host_n,cases=cases(host_n),
        modules=('A','B'),conventions=CONVENTIONS,archived_imfit_sampling=SAMPLES,
        gsparams=SETTINGS,pins=PINS,runtime_versions={k:importlib.metadata.version(k) for k in PINS},
        native_scale_arcsec=NATIVE_SCALE,psf_sample_scale_arcsec=PSF_SCALE,stamp=STAMP,
        analytic_flux=1.,pa_degrees=45.,profile_truncation=0.,
        psf='signed inherited Quintic effective PSF; no clipping, shift or renormalization',
        draw_method='no_pixel',output_dtype='float64',
        radius_conversion='Re_G = Re_I * (gammaincinv(2*n,0.5)/imfit_bn(n))**n',
        imfit_source_blobs={'function_objects/func_sersic.cpp':'f886512a9cdafeb480d838d14dcd0154801388c5',
            'function_objects/helper_funcs.cpp':'2100fabceeeb70186675af76b6ed73f64d86bec9'},
        worker_timeout_seconds=TIMEOUT,worker_kill_grace_seconds=5,
        worker_address_space_bytes=ADDRESS_SPACE_BYTES,workers_sequential=True,
        expected_workers=8,expected_sersic_images=16,expected_gaussian_images=16 if host_n==1 else 0,
        expected_refinements=8,expected_direct_fits=24,
        amplitude_solver='inherited scipy.optimize.nnls, one nonnegative amplitude, no ceiling',
        objective='inherited full-crop RMS-normalized squared residual; GalSim reference is not truth',
        acceptance='complete finite provenance/bookkeeping; no cross-renderer or Gaussian-recovery band',
        limitations='shared empirical PSF; no AGN/noise/shape fit; signed wings are not photon-ready')


def radius_convention(case,convention):
    if convention not in CONVENTIONS or case not in cases(1)+cases(4):
        raise ValueError('outside frozen compact cases or conventions')
    exact=float(gammaincinv(2*case['n'],.5)); approximate=imfit_bn(case['n'])
    factor=1. if convention=='nominal_hlr' else (exact/approximate)**case['n']
    re=case['re']*factor
    return dict(convention=convention,imfit_bn=approximate,exact_bn=exact,
        radius_factor=factor,nominal_re_native_pix=case['re'],
        galsim_semimajor_hlr_native_pix=re,
        circularized_hlr_arcsec=float(re*NATIVE_SCALE*np.sqrt(case['q'])))


def galaxy(case,settings,convention,gaussian=False):
    values=radius_convention(case,convention)
    if gaussian and case['n']!=.5:
        raise ValueError('Gaussian identity is only for n=0.5')
    kwargs=dict(half_light_radius=values['circularized_hlr_arcsec'],flux=1.,
                gsparams=galsim.GSParams(**settings))
    model=galsim.Gaussian(**kwargs) if gaussian else galsim.Sersic(n=case['n'],trunc=0.,**kwargs)
    return model.shear(q=case['q'],beta=45*galsim.degrees),values


def verify_manifest(source,manifest):
    for rel,expected in manifest.items():
        if sha(source/rel)!=expected:
            raise RuntimeError('C5h artifact checksum mismatch: '+rel)


def save_arrays(path,**arrays):
    """Write/validate a temporary NumPy archive, then atomically publish it.

    No custom ZIP writer or recovery: failed temporary products remain visible.
    """
    if path.exists():
        raise FileExistsError(path)
    partial=path.with_suffix(path.suffix+'.partial')
    with partial.open('xb') as handle:
        np.savez_compressed(handle,allow_pickle=False,**arrays)
        handle.flush();os.fsync(handle.fileno())
    with np.load(partial,allow_pickle=False) as saved:
        if set(saved.files)!=set(arrays):
            raise RuntimeError('incomplete NPZ members: '+str(path))
        for key,value in arrays.items():
            np.testing.assert_array_equal(saved[key],value)
            if not np.isfinite(saved[key]).all():
                raise RuntimeError('nonfinite NPZ array: '+str(path)+'/'+key)
    os.replace(partial,path)


def verified_inputs(source,out,host_n):
    audit=json.loads(AUDIT.read_text())
    receipt=audit['github_confirmation']
    if (audit['run_id']!=PARENT_RUN or audit['commit']!=PARENT_COMMIT
        or receipt['status']!='completed' or receipt['conclusion']!='success'
        or len(receipt['jobs'])!=2 or any(j['conclusion']!='success' for j in receipt['jobs'])):
        raise RuntimeError('unreviewed C5h prerequisite')
    parent=next(a for a in audit['artifacts'] if a['host_n']==host_n)
    verify_manifest(source,parent['file_sha256'])
    selected=['config.json','binary.json','kernel_manifest.json','source_manifest.json',
              'parent/input_manifest.json','parent/psf_input_records.json','parent/templates.npz']
    selected += [p for p in parent['file_sha256'] if p.startswith('parent/source/')]
    selected += [f"renders/{case['name']}_{module}_s{s}/native.npz"
                 for case,module,s in itertools.product(cases(host_n),('A','B'),SAMPLES)]
    copy=out/'parent';copy.mkdir()
    for rel in selected:
        target=copy/rel;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source/rel,target)
    dump(out/'source_manifest.json',dict(run=PARENT_RUN,commit=PARENT_COMMIT,
        artifact_id=parent['artifact_id'],zip_sha256=parent['zip_sha256'],
        parent_audit_sha256=sha(AUDIT),verified_parent_files=len(parent['file_sha256']),
        selected_file_sha256={p:parent['file_sha256'][p] for p in selected}))
    with np.load(copy/'parent/templates.npz') as f:
        normalized={m:f[m+'_normalized_input'].copy() for m in ('A','B')}
    for module,image in normalized.items():
        from astropy.io import fits
        raw=fits.getdata(copy/f'parent/source/CEERS_PSF/Pointings12_F444W_Module_{module}.fits')
        np.testing.assert_array_equal(image,normalize_psf(raw)[0])
    save_arrays(out/'psfs.npz',**normalized)
    return copy


def worker(config_path):
    """One bounded GalSim call group; preserve warnings immediately, including before timeout."""
    cfg=json.loads(config_path.read_text());directory=config_path.parent
    rows=[];captured=[];start=time.monotonic()
    dump(directory/'warnings.json',captured)
    try:
        resource.setrlimit(resource.RLIMIT_AS,(ADDRESS_SPACE_BYTES,ADDRESS_SPACE_BYTES))
        with warnings.catch_warnings():
            warnings.simplefilter('always')
            original=warnings.showwarning
            def record_warning(message,category,filename,lineno,file=None,line=None):
                captured.append(dict(category=category.__name__,message=str(message)))
                dump(directory/'warnings.json',captured)
                original(message,category,filename,lineno,file,line)
            warnings.showwarning=record_warning
            with np.load(cfg['psf_path']) as f:
                psf=effective_psf(f[cfg['module']],SETTINGS[cfg['accuracy']])
            for convention in CONVENTIONS:
                model,values=galaxy(cfg['case'],SETTINGS[cfg['accuracy']],convention)
                print(json.dumps(dict(rendering=values,case=cfg['case'],module=cfg['module'],
                                      accuracy=cfg['accuracy'])),flush=True)
                image=draw(galsim.Convolve(model,psf))
                bundle=dict(sersic=image)
                row=dict(**values,case=cfg['case'],module=cfg['module'],accuracy=cfg['accuracy'],
                         sersic_sha256=digest(image),sersic_stats=image_stats(image))
                if cfg['case']['n']==.5:
                    control,_=galaxy(cfg['case'],SETTINGS[cfg['accuracy']],convention,gaussian=True)
                    gaussian=draw(galsim.Convolve(control,psf))
                    bundle.update(gaussian=gaussian,gaussian_residual=image-gaussian)
                    row.update(gaussian_sha256=digest(gaussian),gaussian_stats=image_stats(gaussian),
                               gaussian_comparison=comparison(image,gaussian))
                save_arrays(directory/(convention+'.npz'),**bundle)
                rows.append(row);dump(directory/'render_progress.json',rows)
        dump(directory/'result.json',dict(success=True,renders=rows))
        return 0
    except Exception as error:
        dump(directory/'result.json',dict(success=False,renders=rows,
            exception_type=type(error).__name__,message=str(error)))
        return 1
    finally:
        dump(directory/'runtime.json',dict(wall_seconds=time.monotonic()-start,
            peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            address_space_bytes=ADDRESS_SPACE_BYTES))


def run_worker(case,module,accuracy,psf_path,directory):
    directory.mkdir(parents=True,exist_ok=False)
    cfg=dict(case=case,module=module,accuracy=accuracy,psf_path=str(psf_path),
        timeout_seconds=TIMEOUT,address_space_bytes=ADDRESS_SPACE_BYTES)
    config=directory/'worker_config.json';dump(config,cfg)
    command=['/usr/bin/timeout','--kill-after=5s',str(TIMEOUT),sys.executable,
             str(Path(__file__).resolve()),'--worker',str(config)]
    dump(directory/'command.json',command)
    start=time.monotonic()
    try:
        with (directory/'stdout.txt').open('w') as out,(directory/'stderr.txt').open('w') as err:
            result=subprocess.run(command,stdout=out,stderr=err,check=False)
        path=directory/'result.json'
        row=json.loads(path.read_text()) if path.exists() else dict(success=False,renders=[])
        row.update(returncode=result.returncode)
        if result.returncode:
            row.update(success=False,
                process_error='timeout' if result.returncode in (124,137) else 'worker failed')
        if not path.exists():
            row['process_error']='worker produced no result; see retained stdout/stderr'
    except Exception as error:
        row=dict(success=False,renders=[],exception_type=type(error).__name__,message=str(error))
    row.update(case=case,module=module,accuracy=accuracy,wall_seconds=time.monotonic()-start,
               name=directory.name)
    dump(directory/'process_result.json',row)
    return row


def amplitude_comparison(reference,template):
    """A descriptive one-parameter projection, not structural recovery."""
    amplitude,prediction=profile_flux(reference,template)
    residual=prediction-reference
    row=dict(solver='scipy.optimize.nnls',success=True,amplitude=float(amplitude[0]),
        hit_amplitude_zero=bool(amplitude[0]==0),
        cost=float(.5*np.sum(residual**2)/np.mean(reference**2)),
        gradient=float(np.sum(template*residual)),
        scaled_l1_over_reference_l1=comparison(prediction,reference)['l1_over_reference_l1'],
        template_sha256=digest(template),reference_sha256=digest(reference),
        **comparison(template,reference))
    return row,prediction


def run(host_n,source,out):
    cfg=configuration(host_n);dump(out/'config.json',cfg)
    if cfg['runtime_versions']!=PINS:
        raise RuntimeError('dependency pin mismatch')
    parent=verified_inputs(source,out,host_n)
    processes=[];images={};renders=[]
    for case,module,accuracy in itertools.product(cases(host_n),('A','B'),('coarse','fine')):
        name=f"{case['name']}_{module}_{accuracy}";directory=out/'renders'/name
        process=run_worker(case,module,accuracy,out/'psfs.npz',directory)
        processes.append(process);dump(out/'worker_progress.json',processes)
        # Partial successful products remain usable diagnostics but never satisfy completeness.
        for row in process['renders']:
            convention=row['convention'];path=directory/(convention+'.npz')
            with np.load(path) as f:
                image=f['sersic'].copy()
                if image.shape!=(STAMP,STAMP) or digest(image)!=row['sersic_sha256']:
                    raise RuntimeError('worker image provenance mismatch')
                if 'gaussian' in f:
                    if digest(f['gaussian'])!=row['gaussian_sha256']:
                        raise RuntimeError('Gaussian control provenance mismatch')
                    np.testing.assert_array_equal(f['sersic']-f['gaussian'],f['gaussian_residual'])
            images[case['name'],module,accuracy,convention]=image
            renders.append(dict(**row,worker=name))
        print(json.dumps(dict(worker=name,success=process['success'],
                              renders=len(process['renders']),wall_seconds=process['wall_seconds'])),flush=True)
    refinements=[];rows=[];starts=[]
    comparison_dir=out/'comparisons';comparison_dir.mkdir()
    for case,module,convention in itertools.product(cases(host_n),('A','B'),CONVENTIONS):
        coarse=images.get((case['name'],module,'coarse',convention))
        fine=images.get((case['name'],module,'fine',convention))
        prefix=f"{case['name']}_{module}_{convention}"
        if coarse is not None and fine is not None:
            refinements.append(dict(case=case,module=module,convention=convention,
                coarse_sha256=digest(coarse),fine_sha256=digest(fine),**comparison(coarse,fine)))
            save_arrays(comparison_dir/(prefix+'_refinement.npz'),
                                coarse=coarse,fine=fine,residual=coarse-fine)
        if fine is None:
            continue
        for sampling in SAMPLES:
            path=parent/f"renders/{case['name']}_{module}_s{sampling}/native.npz"
            with np.load(path) as f:
                imfit=f['image'].copy()
            row,prediction=amplitude_comparison(fine,imfit)
            name=f'{prefix}_imfit_s{sampling}'
            row.update(case=name,shape=case['name'],n=case['n'],re=case['re'],q=case['q'],
                module=module,convention=convention,imfit_sampling=sampling,
                reference='fine GalSim comparison, not independent ground truth')
            rows.append(row);starts.append(dict(**row,start=0,start_type='one direct NNLS, not nonlinear multistart'))
            save_arrays(comparison_dir/(name+'.npz'),reference=fine,template=imfit,
                                prediction=prediction,residual=prediction-fine)
    write_csv(out/'metrics.csv',rows);write_csv(out/'fit_starts.csv',starts)
    gaussian_count=sum('gaussian_sha256' in r for r in renders)
    complete=(len(processes)==8 and all(p['success'] for p in processes) and len(renders)==16
              and gaussian_count==cfg['expected_gaussian_images'] and len(refinements)==8 and len(rows)==24)
    manifest={}
    for path in sorted(out.rglob('*.npz')):
        if path.relative_to(out).parts[0]=='parent':
            continue
        with np.load(path,allow_pickle=False) as f:
            if not all(np.isfinite(f[k]).all() for k in f.files):
                raise RuntimeError('nonfinite saved array in '+str(path))
            manifest[str(path.relative_to(out))]=dict(file_sha256=sha(path),
                arrays={k:dict(shape=list(f[k].shape),dtype=str(f[k].dtype),sha256=digest(f[k])) for k in f.files})
    dump(out/'image_manifest.json',manifest)
    dump(out/'summary.json',dict(config=cfg,complete=complete,workers=processes,renders=renders,
        refinements=refinements,results=rows,starts=starts,
        interpretation='Compact-corner numerical/convention diagnosis only; no shape recovery cut'))
    if not complete:
        raise RuntimeError('incomplete compact preflight; every attempted worker and failure retained')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--worker',type=Path)
    parser.add_argument('--source',type=Path)
    parser.add_argument('--host-n',type=int,choices=(1,4))
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    if args.worker:
        return worker(args.worker.resolve())
    if args.source is None or args.host_n is None or args.out is None:
        parser.error('--source, --host-n and --out are required')
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    start=time.monotonic()
    try:
        run(args.host_n,args.source.resolve(),out)
    except Exception as error:
        dump(out/'failure.json',dict(exception_type=type(error).__name__,message=str(error)))
        raise
    finally:
        dump(out/'runtime.json',dict(wall_seconds=time.monotonic()-start,
            peak_parent_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    return 0


if __name__=='__main__':
    sys.exit(main())
