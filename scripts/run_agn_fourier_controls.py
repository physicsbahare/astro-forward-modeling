#!/usr/bin/env python3
"""C5j: thin GalSim numerical-control adapter; not a new renderer or shape fitter."""
import argparse
from contextlib import contextmanager
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

import run_agn_compact_renderer as parent
from run_agn_empirical_psf_phase import PINS, digest
from run_agn_empirical_psf_transfer import dump, draw, NATIVE_SCALE, PSF_SCALE
from run_agn_nuclear_fraction_noiseless import write_csv

ROOT, TIMEOUT, ADDRESS_SPACE_BYTES = parent.ROOT, parent.TIMEOUT, parent.ADDRESS_SPACE_BYTES
PARENT_RUN = 33766246396
PARENT_COMMIT = '169018474ae502a537bc736a64ead778f24e42cd'
AUDIT = ROOT/'benchmarks/zhuang_shen_2024/compact_renderer_33766246396.json'
PROTOCOL = ROOT/'benchmarks/zhuang_shen_2024/C5J_PROTOCOL.md'
ARMS = ('coarse','folding_only','maxk_only','kvalue_only','xvalue_only','fine',
        'fine_hankel','fine_psf_extent','fine_psf_bandlimit')
SOURCE_BLOBS = {
    'src/SBSersic.cpp':'a8d1968253b408cf062afa47fb95b3dbad307d0f',
    'galsim/interpolatedimage.py':'9ed6d853f0eb63dc6ca6bd6c8bc3a12d9611abbf',
    'galsim/convolve.py':'a34ebd5565ac3a400a9b7e94dd008f9c7c0404f0',
    'galsim/gsobject.py':'84c935bc5b23b5a115ecb222473388b33c221e73'}


def read(path):
    return json.loads(path.read_text())


def arm_config(arm):
    if arm not in ARMS:
        raise ValueError('outside frozen intervention list')
    settings = dict(parent.SETTINGS['fine' if arm.startswith('fine') else 'coarse'])
    keys = dict(folding_only='folding_threshold', maxk_only='maxk_threshold',
                kvalue_only='kvalue_accuracy', xvalue_only='xvalue_accuracy')
    if arm in keys:
        key = keys[arm]
        settings[key] = parent.SETTINGS['fine'][key]
    if arm == 'fine_hankel':
        settings.update(integration_relerr=1e-8, integration_abserr=1e-10)
    return dict(settings=settings, calculate_stepk=arm!='fine_psf_extent',
        calculate_maxk=arm!='fine_psf_bandlimit')


def configuration(host_n):
    return dict(stage='C5j compact-profile Fourier-control diagnosis',
        github_run_id=os.getenv('GITHUB_RUN_ID'), github_sha=os.getenv('GITHUB_SHA'),
        parent_run=PARENT_RUN, parent_commit=PARENT_COMMIT,
        parent_audit_sha256=parent.sha(AUDIT), protocol_sha256=parent.sha(PROTOCOL),
        host_n=host_n, cases=parent.cases(host_n), modules=('A','B'),
        arms={a:arm_config(a) for a in ARMS}, convention='nominal_hlr',
        inherited_coarse_fine=parent.SETTINGS, pins=PINS,
        runtime_versions={k:importlib.metadata.version(k) for k in PINS},
        source_tag='GalSim v2.8.4', source_blobs=SOURCE_BLOBS,
        stamp=201, native_scale_arcsec=NATIVE_SCALE, psf_sample_scale_arcsec=PSF_SCALE,
        analytic_flux=1., pa_degrees=45., truncation=0., draw_method='no_pixel',
        interpolation=dict(x='quintic', k='quintic', pad_factor=4.,
            depixelize=False, noise_pad_size=0, use_true_center=True),
        psf='unchanged signed A/B empirical inputs; no clipping, recentering or output normalization',
        convolution_gsparams_propagation=True,
        probes=dict(directions_degrees=(0,45,90,135), radial_zero=True,
            positive_radial_count=64, minimum_inverse_arcsec=1e-3,
            maximum_inverse_arcsec=float(8*np.pi/PSF_SCALE), spacing='geomspace'),
        worker_timeout_seconds=TIMEOUT, kill_grace_seconds=5,
        worker_address_space_bytes=ADDRESS_SPACE_BYTES, workers_sequential=True,
        expected_workers=36, expected_sersic_images=36,
        expected_gaussian_images=36 if host_n==1 else 0, expected_direct_starts=36,
        objective='inherited NNLS projection onto archived C5i fine; no shape fit or amplitude ceiling',
        acceptance='complete finite provenance/bookkeeping only; no new numerical recovery band',
        limitations='finite Fourier probes; same renderer controls; signed PSFs are not photon-ready')


def models(case, normalized, arm, gaussian=False):
    settings = arm_config(arm)
    source, radius = parent.galaxy(case, settings['settings'], 'nominal_hlr', gaussian)
    psf = galsim.InterpolatedImage(galsim.Image(np.array(normalized, dtype=float), scale=PSF_SCALE),
        normalization='flux', x_interpolant='quintic', k_interpolant='quintic', pad_factor=4.,
        depixelize=False, use_true_center=True, noise_pad_size=0,
        calculate_stepk=settings['calculate_stepk'], calculate_maxk=settings['calculate_maxk'],
        gsparams=galsim.GSParams(**settings['settings']))
    convolution = galsim.Convolve(source, psf, propagate_gsparams=True)
    assert source.gsparams == psf.gsparams == convolution.gsparams
    return source, psf, convolution, radius


def probe_coordinates():
    radial = np.r_[0., np.geomspace(1e-3, 8*np.pi/PSF_SCALE, 64)]
    angles = np.deg2rad([0.,45.,90.,135.])
    return (radial[:,None]*np.cos(angles)).ravel(), (radial[:,None]*np.sin(angles)).ravel()


def sample_k(obj, kx, ky):
    return np.array([obj.kValue(galsim.PositionD(float(x),float(y))) for x,y in zip(kx,ky)],
                    dtype=np.complex128)


def profile_record(obj):
    return dict(flux=float(obj.flux), stepk_inverse_arcsec=float(obj.stepk),
        maxk_inverse_arcsec=float(obj.maxk), gsparams=repr(obj.gsparams))


@contextmanager
def observe_fft(records, destination):
    """Observe the documented helper; never replace its grid or computed objects."""
    original = galsim.GSObject.drawFFT_makeKImage
    def traced(obj, image):
        kimage, wrap = original(obj, image)
        records.append(dict(target_shape=list(image.array.shape), image_scale=float(image.scale),
            k_shape=list(kimage.array.shape), k_dtype=str(kimage.array.dtype),
            k_spacing=float(kimage.scale), wrap_size=int(wrap),
            stepk=float(obj.stepk), maxk=float(obj.maxk),
            coordinates='actual internal draw coordinates; native image pixel units'))
        dump(destination, records)
        return kimage, wrap
    galsim.GSObject.drawFFT_makeKImage = traced
    try:
        yield
    finally:
        galsim.GSObject.drawFFT_makeKImage = original


def verified_inputs(source, out, host_n):
    audit = read(AUDIT)
    receipt = audit['github_confirmation']
    assert audit['run_id'] == PARENT_RUN and audit['commit'] == PARENT_COMMIT
    assert receipt['status'] == 'completed' and receipt['conclusion'] == 'success'
    assert len(receipt['jobs']) == 2 and all(j['conclusion']=='success' for j in receipt['jobs'])
    record = next(a for a in audit['artifacts'] if a['host_n']==host_n)
    for rel, expected in record['file_sha256'].items():
        if parent.sha(source/rel) != expected:
            raise RuntimeError('C5i source checksum mismatch: '+rel)
    selected = ['config.json','summary.json','source_manifest.json','image_manifest.json','psfs.npz']
    selected += [p for p in record['file_sha256'] if p.startswith('parent/parent/source/')]
    for case, module in itertools.product(parent.cases(host_n), ('A','B')):
        selected += [f"renders/{case['name']}_{module}_{level}/nominal_hlr.npz" for level in ('coarse','fine')]
        selected.append(f"parent/renders/{case['name']}_{module}_s8/native.npz")
    target = out/'parent'; target.mkdir()
    for rel in selected:
        path = target/rel; path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source/rel, path)
    dump(out/'source_manifest.json', dict(run=PARENT_RUN,commit=PARENT_COMMIT,
        artifact_id=record['artifact_id'],zip_sha256=record['zip_sha256'],
        parent_audit_sha256=parent.sha(AUDIT),verified_parent_files=len(record['file_sha256']),
        selected_file_sha256={p:record['file_sha256'][p] for p in selected}))
    return target


def worker(config_path):
    cfg = read(config_path); directory = config_path.parent
    captured = []; trace = []; start = time.monotonic()
    dump(directory/'warnings.json', captured); dump(directory/'fft_trace.json', trace)
    try:
        resource.setrlimit(resource.RLIMIT_AS, (ADDRESS_SPACE_BYTES,ADDRESS_SPACE_BYTES))
        with warnings.catch_warnings():
            warnings.simplefilter('always')
            original = warnings.showwarning
            def record_warning(message, category, filename, lineno, file=None, line=None):
                captured.append(dict(category=category.__name__,message=str(message)))
                dump(directory/'warnings.json', captured)
                original(message, category, filename, lineno, file, line)
            warnings.showwarning = record_warning
            with np.load(cfg['psf_path'], allow_pickle=False) as f:
                normalized = f[cfg['module']].copy()
            source, psf, convolution, radius = models(cfg['case'], normalized, cfg['arm'])
            profiles = dict(source=profile_record(source), psf=profile_record(psf),
                            convolution=profile_record(convolution))
            dump(directory/'profiles.json', profiles)
            kx, ky = probe_coordinates()
            probes = dict(kx=kx, ky=ky, host=sample_k(source,kx,ky), psf=sample_k(psf,kx,ky),
                          convolution=sample_k(convolution,kx,ky))
            probes['product'] = probes['host']*probes['psf']
            product_error = float(np.abs(probes['convolution']-probes['product']).max())
            assert product_error <= 1e-12
            with observe_fft(trace, directory/'fft_trace.json'):
                image = draw(convolution)
                bundle = dict(image=image)
                row = dict(radius=radius, profiles=profiles, image_sha256=digest(image),
                    image_stats=parent.image_stats(image), fourier_product_max_error=product_error)
                if cfg['case']['n'] == .5:
                    gaussian, gpsf, control, _ = models(cfg['case'],normalized,cfg['arm'],True)
                    gaussian_image = draw(control)
                    bundle.update(gaussian=gaussian_image,gaussian_residual=image-gaussian_image)
                    probes.update(gaussian=sample_k(gaussian,kx,ky),
                                  gaussian_convolution=sample_k(control,kx,ky))
                    row.update(gaussian_sha256=digest(gaussian_image),
                        gaussian_stats=parent.image_stats(gaussian_image),
                        gaussian_comparison=parent.comparison(image,gaussian_image))
            parent.save_arrays(directory/'images.npz', **bundle)
            parent.save_arrays(directory/'probes.npz', **probes)
            dump(directory/'result.json',dict(success=True,render=row))
        return 0
    except Exception as error:
        dump(directory/'result.json',dict(success=False,exception_type=type(error).__name__,message=str(error)))
        return 1
    finally:
        dump(directory/'runtime.json',dict(wall_seconds=time.monotonic()-start,
            peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            address_space_bytes=ADDRESS_SPACE_BYTES))


def run_worker(case, module, arm, psf_path, directory):
    directory.mkdir(parents=True,exist_ok=False)
    cfg = dict(case=case,module=module,arm=arm,arm_config=arm_config(arm),psf_path=str(psf_path),
        timeout_seconds=TIMEOUT,address_space_bytes=ADDRESS_SPACE_BYTES)
    config = directory/'worker_config.json'; dump(config,cfg)
    command = ['/usr/bin/timeout','--kill-after=5s',str(TIMEOUT),sys.executable,
               str(Path(__file__).resolve()),'--worker',str(config)]
    dump(directory/'command.json',command)
    start = time.monotonic()
    try:
        with (directory/'stdout.txt').open('w') as out, (directory/'stderr.txt').open('w') as err:
            completed = subprocess.run(command,stdout=out,stderr=err,check=False)
        result = directory/'result.json'
        row = read(result) if result.exists() else dict(success=False,message='no worker result')
        row['returncode'] = completed.returncode
        if completed.returncode:
            row.update(success=False,process_error='timeout' if completed.returncode in (124,137) else 'worker failed')
    except Exception as error:
        row = dict(success=False,exception_type=type(error).__name__,message=str(error))
    row.update(name=directory.name,case=case,module=module,arm=arm,wall_seconds=time.monotonic()-start)
    dump(directory/'process_result.json',row)
    return row


def manifest(out):
    result = {}
    for path in sorted(out.rglob('*.npz')):
        if path.relative_to(out).parts[0] == 'parent':
            continue
        with np.load(path,allow_pickle=False) as f:
            assert all(np.isfinite(f[k]).all() for k in f.files)
            result[str(path.relative_to(out))] = dict(file_sha256=parent.sha(path),
                arrays={k:dict(shape=list(f[k].shape),dtype=str(f[k].dtype),sha256=digest(f[k])) for k in f.files})
    dump(out/'image_manifest.json',result)


def run(host_n, source, out):
    cfg = configuration(host_n); dump(out/'config.json',cfg)
    if cfg['pins'] != cfg['runtime_versions']:
        raise RuntimeError('dependency pin mismatch')
    copied = verified_inputs(source,out,host_n)
    workers = []; rows = []; starts = []
    comparisons = out/'comparisons'; comparisons.mkdir()
    for case, module, arm in itertools.product(parent.cases(host_n),('A','B'),ARMS):
        name = f"{case['name']}_{module}_{arm}"
        directory = out/'renders'/name
        process = run_worker(case,module,arm,copied/'psfs.npz',directory)
        workers.append(process); dump(out/'worker_progress.json',workers)
        print(json.dumps(dict(worker=name,success=process['success'],wall_seconds=process['wall_seconds'])),flush=True)
        if not process['success']:
            continue
        with np.load(directory/'images.npz',allow_pickle=False) as f:
            image = f['image'].copy()
        references = {}
        for level in ('coarse','fine'):
            with np.load(copied/f"renders/{case['name']}_{module}_{level}/nominal_hlr.npz") as f:
                references[level] = f['sersic'].copy()
        with np.load(copied/f"parent/renders/{case['name']}_{module}_s8/native.npz") as f:
            imfit = f['image'].copy()
        if arm in ('coarse','fine'):
            np.testing.assert_allclose(image,references[arm],rtol=0,atol=1e-12)
        row, prediction = parent.amplitude_comparison(references['fine'],image)
        row.update(case=name,shape=case['name'],n=case['n'],re=case['re'],q=case['q'],module=module,arm=arm,
            comparison_to_coarse=parent.comparison(image,references['coarse']),
            comparison_to_imfit8=parent.comparison(image,imfit),
            replay_max_abs_error=float(np.abs(image-references[arm]).max()) if arm in ('coarse','fine') else None)
        rows.append(row); starts.append(dict(**row,start=0,start_type='one direct NNLS, not nonlinear multistart'))
        parent.save_arrays(comparisons/(name+'.npz'),reference=references['fine'],template=image,
            prediction=prediction,residual=prediction-references['fine'])
    write_csv(out/'metrics.csv',rows); write_csv(out/'fit_starts.csv',starts)
    complete = len(workers)==36 and all(w['success'] for w in workers) and len(rows)==36
    manifest(out)
    dump(out/'summary.json',dict(config=cfg,complete=complete,workers=workers,results=rows,starts=starts,
        interpretation='Numerical interventions only, not global convergence or physical host recovery'))
    if not complete:
        raise RuntimeError('incomplete C5j diagnostic; all attempted workers/failures retained')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker',type=Path)
    parser.add_argument('--source',type=Path)
    parser.add_argument('--host-n',type=int,choices=(1,4))
    parser.add_argument('--out',type=Path)
    args = parser.parse_args()
    if args.worker:
        return worker(args.worker.resolve())
    if args.source is None or args.host_n is None or args.out is None:
        parser.error('--source, --host-n and --out are required')
    out = args.out.resolve(); out.mkdir(parents=True,exist_ok=False)
    start = time.monotonic()
    try:
        run(args.host_n,args.source.resolve(),out)
    except Exception as error:
        dump(out/'failure.json',dict(exception_type=type(error).__name__,message=str(error)))
        raise
    finally:
        dump(out/'runtime.json',dict(wall_seconds=time.monotonic()-start,
            peak_parent_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    return 0


if __name__ == '__main__':
    sys.exit(main())
