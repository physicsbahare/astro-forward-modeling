#!/usr/bin/env python3
"""C5h: thin Imfit/GalSim convention adapter, not a new renderer or fitter.

Frozen protocol: benchmarks/zhuang_shen_2024/C5H_PROTOCOL.md.
Imfit supplies profile subsampling and convolution; GalSim supplies the same
PSF interpolant as C5d. The comparison is independent only in the host renderer.
"""
import argparse
import hashlib
import importlib.metadata
import itertools
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import time
import warnings

import galsim
import numpy as np
from astropy.io import fits
from scipy.special import gammaln, gammaincinv
from run_agn_empirical_agn_centroid import load_parent, ROOT
from run_agn_empirical_psf_phase import PINS, digest
from run_agn_empirical_psf_transfer import (effective_psf, SETTINGS, dump, solve_fluxes,
    gaussian_effective_samples, normalize_psf, NATIVE_SCALE, PSF_SCALE, CONTROL_FWHMS)
from run_agn_nuclear_fraction_noiseless import write_csv

IMFIT_URL = 'https://www.mpe.mpg.de/~erwin/resources/imfit/binaries/imfit-1.9.0-linux-64.tar.gz'
IMFIT_ARCHIVE_SHA = '9eb10a62baab87de98744c247f7a10ea02b05d32996760b7cef100f5f02a7089'
IMFIT_BINARY_SHA = '4fe27a3d3e48f0c4931ee3fb5ad571330fdbf27f6c327f48990418bdcb965984'
SAMPLES = (2,4,8)
STAMP = 201
TIMEOUT = 120
AUDIT = ROOT/'benchmarks/zhuang_shen_2024/nuclear_centroid_33740141863.json'
PROTOCOL = ROOT/'benchmarks/zhuang_shen_2024/C5H_PROTOCOL.md'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def structural_cases(host_n):
    if host_n not in (1,4):
        raise ValueError('host n must be 1 or 4')
    cases=[dict(name='truth',n=float(host_n),re=16.,q=.6)]
    edge_n=.5 if host_n==1 else 6.
    cases += [dict(name=f'corner_re{re:g}_q{q:g}',n=edge_n,re=re,q=q)
              for re,q in itertools.product((.5,60.),(.15,1.))]
    return cases


def configuration(host_n):
    return dict(stage='C5h independent host-renderer convention/resource preflight',
        github_run_id=os.getenv('GITHUB_RUN_ID'),github_sha=os.getenv('GITHUB_SHA'),
        prerequisite_run=33740141863,prerequisite_commit='de3ed949d3497263c458a897f703d5a5e9a6f295',
        prerequisite_audit_sha256=sha(AUDIT),protocol_sha256=sha(PROTOCOL),
        host_n=host_n,cases=structural_cases(host_n),samples=SAMPLES,stamp=STAMP,
        native_scale_arcsec=NATIVE_SCALE,psf_sample_scale_arcsec=PSF_SCALE,
        imfit_archive_url=IMFIT_URL,imfit_archive_sha256=IMFIT_ARCHIVE_SHA,
        imfit_binary_sha256=IMFIT_BINARY_SHA,imfit_version='1.9.0',
        pins=PINS,runtime_versions={k:importlib.metadata.version(k) for k in PINS},
        psf='same fine-Quintic continuous effective PSF; eight original-sample zero rows per edge',
        kernel='surface-brightness samples times h^2; no renormalization or clipping',
        detector='s^2 * fine[::s,::s], no second native-pixel integration',
        imfit_subsampling=True,imfit_threads=1,render_timeout_seconds=TIMEOUT,
        controls=dict(source_sigma_arcsec=.12,optical_fwhm_arcsec=CONTROL_FWHMS),
        expected_render_cases=36,expected_direct_fits=36,
        objective='inherited full-crop RMS-normalized NNLS with both amplitudes >=0; no ceiling',
        acceptance='complete finite provenance/algebra; no cross-renderer recovery band',
        limitations='shared PSF interpolation; no free shape, noise, physical PSF or global-optimality claim')


def imfit_bn(n):
    """Unit conversion only: Ciotti & Bertin formula used by pinned Imfit.

    Source: perwin/imfit v1.9, function_objects/helper_funcs.cpp.
    This is NOT used to implement the Sérsic image or its integration.
    """
    if not .5 <= n <= 6:
        raise ValueError('outside frozen n box')
    return (2*n - .333333333333333 + .009876543209876543/n
            + .0018028610621203215/n**2 + .00011409410586365319/n**3
            - 7.1510122958919723e-5/n**4)


def unit_sersic_ie(n,re,q,sampling):
    if not .5 <= re <= 60 or not .15 <= q <= 1 or sampling not in SAMPLES:
        raise ValueError('outside frozen geometry or sampling')
    b=imfit_bn(n)
    return float(np.exp(2*n*np.log(b)-np.log(2*np.pi*q*n)-b-gammaln(2*n)
                        -2*np.log(re*sampling)))


def model_text(case,sampling):
    center=100*sampling+1  # Imfit is 1-based; coincident native centers.
    lines=[f'X0 {center}',f'Y0 {center}']
    if 'sigma_arcsec' in case:
        sigma=case['sigma_arcsec']/NATIVE_SCALE*sampling
        lines += ['FUNCTION Gaussian','PA -45','ell 0',
                  f'I_0 {1/(2*np.pi*sigma**2):.17g}',f'sigma {sigma:.17g}']
    else:
        lines += ['FUNCTION Sersic','PA -45',f"ell {1-case['q']:.17g}",
                  f"n {case['n']:.17g}",
                  f"I_e {unit_sersic_ie(case['n'],case['re'],case['q'],sampling):.17g}",
                  f"r_e {case['re']*sampling:.17g}"]
    return '\n'.join(lines)+'\n'


def psf_kernel(normalized,sampling):
    if sampling not in SAMPLES or normalized.shape!=(401,401) or not np.isfinite(normalized).all():
        raise ValueError('invalid input grid')
    h=NATIVE_SCALE/sampling
    model=effective_psf(normalized,SETTINGS['fine'])
    # SB rendering evaluates the SAME interpolant, without another pixel.
    sb=model.drawImage(nx=208*sampling+1,ny=208*sampling+1,scale=h,
        method='sb',dtype=np.float64,use_true_center=True).array
    return sb*h*h


def native_from_fine(fine,sampling):
    expected=(200*sampling+1,)*2
    if sampling not in SAMPLES or fine.shape!=expected or not np.isfinite(fine).all():
        raise ValueError('invalid fine image')
    return np.array(fine[::sampling,::sampling],dtype=np.float64)*sampling**2


def image_stats(image):
    yy,xx=np.indices(image.shape,dtype=float)
    xx-=100; yy-=100
    total=float(image.sum())
    absolute=float(np.abs(image).sum())
    if not np.isfinite(image).all() or absolute==0 or total==0:
        raise RuntimeError('nonfinite or zero image normalization')
    cx=float((xx*image).sum()/total); cy=float((yy*image).sum()/total)
    return dict(signed_sum=total,absolute_sum=absolute,negative_pixels=int((image<0).sum()),
        negative_absolute_fraction=float(np.abs(image[image<0]).sum()/absolute),
        signed_centroid_x_pix=cx,signed_centroid_y_pix=cy,
        signed_mxx_pix2=float(((xx-cx)**2*image).sum()/total),
        signed_myy_pix2=float(((yy-cy)**2*image).sum()/total),
        signed_mxy_pix2=float(((xx-cx)*(yy-cy)*image).sum()/total))


def comparison(image,reference):
    return dict(l1_over_reference_l1=float(np.abs(image-reference).sum()/np.abs(reference).sum()),
        max_abs_difference=float(np.max(np.abs(image-reference))),
        signed_sum_difference=float(image.sum()-reference.sum()))


def run_renderer(binary,case,sampling,kernel_path,directory):
    directory.mkdir(parents=True,exist_ok=False)
    config=directory/'model.dat'; config.write_text(model_text(case,sampling))
    output=directory/'fine.fits'; timing=directory/'time.txt'
    side=200*sampling+1
    # GNU timeout terminates the process group, including the renderer child.
    # A relocated GNU time executable is allowed for minimal local containers.
    command=['/usr/bin/timeout','--kill-after=5s',str(TIMEOUT),
        os.getenv('GNU_TIME','/usr/bin/time'),'-f','%e %M','-o',str(timing),str(binary),str(config),
        '--psf',str(kernel_path),'--no-normalize','--max-threads','1',
        '--ncols',str(side),'--nrows',str(side),'-o',str(output)]
    dump(directory/'command.json',command)
    start=time.monotonic()
    try:
        # A fixed timeout is a resource observable, never an astrophysical cut.
        with (directory/'stdout.txt').open('w') as out,(directory/'stderr.txt').open('w') as err:
            result=subprocess.run(command,stdout=out,stderr=err,check=False)
        if result.returncode in (124,137):
            raise subprocess.TimeoutExpired(command,TIMEOUT)
        if result.returncode:
            raise RuntimeError(f'makeimage exited {result.returncode}; retained logs')
        with fits.open(output,memmap=False) as hdus:
            fine=np.asarray(hdus[0].data,dtype=np.float64)
            bitpix=int(hdus[0].header['BITPIX'])
        native=native_from_fine(fine,sampling)
        timing_fields=timing.read_text().split()
        record=dict(success=True,wall_seconds=time.monotonic()-start,
            imfit_wall_seconds=float(timing_fields[-2]),peak_child_rss_kib=int(timing_fields[-1]),
            fits_bitpix=bitpix,fine_sha256=sha(output),fine_shape=list(fine.shape),
            native_sha256=digest(native),**image_stats(native))
        if 'n' in case:
            record.update(imfit_bn=imfit_bn(case['n']),exact_bn=float(gammaincinv(2*case['n'],.5)))
        np.savez_compressed(directory/'native.npz',image=native)
        dump(directory/'result.json',record)
        return native,record
    except Exception as error:
        record=dict(success=False,wall_seconds=time.monotonic()-start,
                    exception_type=type(error).__name__,message=str(error))
        dump(directory/'result.json',record)
        return None,record


def verified_input(source,out,host_n):
    audit=json.loads(AUDIT.read_text())
    if audit['run_id']!=33740141863 or audit['github_conclusion']!='success':
        raise RuntimeError('unreviewed C5g prerequisite')
    record=next(a for a in audit['artifacts'] if a['host_n']==host_n)
    for rel,expected in record['file_sha256'].items():
        if sha(source/rel)!=expected:
            raise RuntimeError('C5g artifact checksum mismatch: '+rel)
    dump(out/'c5g_manifest.json',dict(run=audit['run_id'],commit=audit['commit'],
        artifact_id=record['artifact_id'],file_sha256=record['file_sha256']))
    return load_parent(source/'parent',out,host_n)


def run(host_n,source,binary,out):
    cfg=configuration(host_n); dump(out/'config.json',cfg)
    if cfg['runtime_versions']!=PINS:
        raise RuntimeError('dependency pin mismatch')
    if sha(binary)!=IMFIT_BINARY_SHA:
        raise RuntimeError('wrong makeimage executable')
    software=out/'software'; software.mkdir()
    for name in ('README.txt','COPYING.txt'):
        shutil.copy2(binary.parent/name,software/name)
    dump(software/'manifest.json',{name:sha(software/name) for name in ('README.txt','COPYING.txt')})
    # Upstream --version deliberately exits 1; science invocations must exit 0.
    version=subprocess.run([str(binary),'--version'],capture_output=True,text=True,check=False)
    dump(out/'binary.json',dict(sha256=sha(binary),stdout=version.stdout,
                              stderr=version.stderr,version_returncode=version.returncode))
    if 'version 1.9.0' not in version.stdout:
        raise RuntimeError('wrong makeimage version')
    timer=Path(os.getenv('GNU_TIME','/usr/bin/time'))
    timer_version=subprocess.run([str(timer),'--version'],capture_output=True,text=True,check=True)
    dump(software/'timer.json',dict(sha256=sha(timer),stdout=timer_version.stdout,
                                   stderr=timer_version.stderr))
    templates,parent_rows=verified_input(source,out,host_n)
    renders=[]; images={}; kernels={}; kernel_rows=[]
    controls=[dict(name=f'gaussian{f:g}',sigma_arcsec=.12,psf_fwhm=f) for f in CONTROL_FWHMS]
    source_psfs={m:templates[m+'_normalized_input'] for m in ('A','B')}
    for c in controls:
        sigma=c['psf_fwhm']/np.sqrt(8*np.log(2))
        source_psfs[c['name']]=normalize_psf(gaussian_effective_samples(sigma,401,PSF_SCALE))[0]
    kernel_dir=out/'kernels'; kernel_dir.mkdir()
    for label,normalized in source_psfs.items():
        for sampling in SAMPLES:
            kernel=psf_kernel(normalized,sampling)
            path=kernel_dir/f'{label}_s{sampling}.fits'
            fits.writeto(path,kernel,overwrite=False)
            kernels[label,sampling]=path
            kernel_rows.append(dict(label=label,sampling=sampling,sha256=sha(path),shape=list(kernel.shape),
                signed_sum=float(kernel.sum()),absolute_sum=float(np.abs(kernel).sum()),
                negative_pixels=int((kernel<0).sum())))
    dump(out/'kernel_manifest.json',kernel_rows)
    for case in structural_cases(host_n)+controls:
        modules=('A','B') if 'n' in case else (case['name'],)
        for module,sampling in itertools.product(modules,SAMPLES):
            name=f"{case['name']}_{module}_s{sampling}"
            image,row=run_renderer(binary,case,sampling,kernels[module,sampling],out/'renders'/name)
            row.update(case=case,module=module,sampling=sampling,name=name)
            if image is not None:
                images[case['name'],module,sampling]=image
                if case['name']=='truth':
                    reference=templates[module+'_fine_quintic_host']
                    row['comparison_to_C5d']=comparison(image,reference)
                    np.savez_compressed(out/'renders'/name/'comparison.npz',image=image,
                                        reference=reference,residual=image-reference)
                elif 'sigma_arcsec' in case:
                    sigma=np.hypot(case['sigma_arcsec'],case['psf_fwhm']/np.sqrt(8*np.log(2)))
                    reference=gaussian_effective_samples(sigma,STAMP,NATIVE_SCALE)
                    row['comparison_to_exact']=comparison(image,reference)
                    np.savez_compressed(out/'renders'/name/'comparison.npz',image=image,
                                        reference=reference,residual=image-reference)
            renders.append(row); dump(out/'render_progress.json',renders)
            print(json.dumps(row,allow_nan=False),flush=True)
    refinement=[]
    for case in structural_cases(host_n)+controls:
        modules=('A','B') if 'n' in case else (case['name'],)
        for module in modules:
            for low,high in ((2,4),(4,8),(2,8)):
                left=images.get((case['name'],module,low)); right=images.get((case['name'],module,high))
                if left is not None and right is not None:
                    refinement.append(dict(case=case,module=module,coarse=low,fine=high,**comparison(left,right)))
    dump(out/'refinement.json',refinement)
    rows=[]; starts=[]
    for truth,ratio,adopted,sampling in itertools.product(('A','B'),(.1,1.,10.),('A','B'),SAMPLES):
        host=images.get(('truth',adopted,sampling))
        if host is None:
            continue  # Missing rendering is recorded above and fails completeness below.
        with np.load(source/f'parent/truth{truth}_ratio{ratio:g}.npz') as bundle:
            data=bundle['data'].copy()
        point=templates[adopted+'_fine_quintic_point']
        reference=next(r for r in parent_rows if r['truth_module']==truth and r['fit_module']==adopted
            and r['agn_to_host']==ratio and r['fit_variant']=='fine_quintic')
        if digest(data)!=reference['data_sha256']:
            raise RuntimeError('truth image identity failed')
        row,prediction=solve_fluxes(data,host,point)
        name=f'fit_n{host_n}_truth{truth}_fit{adopted}_ratio{ratio:g}_s{sampling}'
        row.update(case=name,truth_module=truth,fit_module=adopted,agn_to_host=ratio,
            true_n=host_n,true_re_native_pix=16.,true_q=.6,sampling=sampling,data_sha256=digest(data),
            parent_cost=reference['cost'],parent_host_flux=reference['host_flux'],
            parent_nuclear_flux=reference['nuclear_flux'],
            cost_change_from_C5d=row['cost']-reference['cost'],
            host_flux_change_from_C5d=row['host_flux']-reference['host_flux'],
            nuclear_flux_change_from_C5d=row['nuclear_flux']-reference['nuclear_flux'])
        rows.append(row); starts.append(dict(**row,start=0,start_type='one direct NNLS, not nonlinear multistart'))
        np.savez_compressed(out/(name+'.npz'),data=data,host=host,point=point,
                            prediction=prediction,residual=prediction-data)
        write_csv(out/'metrics.csv',rows); write_csv(out/'fit_starts.csv',starts)
    complete=(len(renders)==36 and all(r['success'] for r in renders) and len(rows)==36)
    dump(out/'summary.json',dict(config=cfg,complete=complete,renders=renders,
        results=rows,starts=starts,refinement=refinement,
        interpretation='Renderer/refinement/resource diagnostic only; signed PSFs remain non-photon-ready'))
    if not complete:
        raise RuntimeError('incomplete renderer preflight; all attempted cases and failures retained')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--makeimage',type=Path,required=True)
    parser.add_argument('--host-n',type=int,choices=(1,4),required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args(); out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=False)
    start=time.monotonic(); captured=[]
    try:
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter('always')
            run(args.host_n,args.source.resolve(),args.makeimage.resolve(),out)
    except Exception as error:
        dump(out/'failure.json',dict(error_type=type(error).__name__,message=str(error)))
        raise
    finally:
        dump(out/'runtime.json',dict(wall_seconds=time.monotonic()-start,
            max_parent_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        dump(out/'warnings.json',[dict(category=w.category.__name__,message=str(w.message)) for w in captured])


if __name__=='__main__':
    main()
