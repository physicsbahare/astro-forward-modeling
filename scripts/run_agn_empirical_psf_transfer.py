#!/usr/bin/env python3
"""C5d: published effective PSFs, GalSim transfer, fixed-shape NNLS only.

No empirical PSF reconstruction, deconvolution, clipping or custom optimizer.
Pixel-response conventions and limitations are frozen in the C5 review.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import time
from urllib.request import urlopen
import warnings

import numpy as np
import galsim
from astropy.io import fits
from astropy.table import Table
from scipy.special import erf

from fetch_zhuang_shen_benchmark import UPSTREAM_REPO, UPSTREAM_COMMIT, RAW_ROOT, git_blob_sha1
from run_agn_galsim import profile, SETTINGS
from run_agn_nuclear_fraction_noiseless import profile_flux, write_csv

PINS = dict(numpy='2.5.2', scipy='1.18.1', galsim='2.8.4', astropy='8.0.1')
PARENT_RUN = 33709361250
PARENT_COMMIT = 'ce53c12e50a907c343b067c25545555bec143dcc'
PSF_SCALE = .015  # arcsec per sample, from pinned table/paper, NOT a new pixel response
NATIVE_SCALE = .03  # arcsec; effective response already includes the mosaic pixel
STAMP = 201
TRUE_RE_PIX, TRUE_Q, TRUE_PA = 16., .6, 45.
RATIOS = (.1, 1., 10.)
VARIANTS = {'coarse_quintic': ('coarse', 'quintic'),
            'fine_quintic': ('fine', 'quintic'),
            'fine_lanczos4': ('fine', 'lanczos4')}
FIT_VARIANTS = ('fine_quintic', 'fine_lanczos4')
CONTROL_FWHMS = (.09, .165)
CONTROL_HOST_SIGMA = .12
SOURCE_FILES = {
    'CEERS_PSF/Pointings12_F444W_Module_A.fits': '92053498a5ebdac1fe4d1e2d2d35fbfae629877c',
    'CEERS_PSF/Pointings12_F444W_Module_B.fits': '20c6272707a67898d85aa8417be56849b120d558',
    'CEERS_PSF/PSF_statistics.ipac': '2aedab940a8ea8bbc26f99dc6b09059ef44fb64e',
    'LICENSE': 'd7461b493e660a75b7cba2f4af726e2720511ea2',
}


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def configuration(host_n):
    return dict(stage='C5d empirical effective-PSF transfer; fixed-shape amplitudes',
        parent_run=PARENT_RUN, parent_commit=PARENT_COMMIT,
        github_run_id=os.environ.get('GITHUB_RUN_ID'), github_sha=os.environ.get('GITHUB_SHA'),
        package_pins=PINS, runtime_versions={k:importlib.metadata.version(k) for k in PINS},
        upstream_repository=UPSTREAM_REPO, upstream_commit=UPSTREAM_COMMIT,
        source_files=SOURCE_FILES, filter='F444W', pointings='1+2', modules=['A','B'],
        psf_sample_scale_arcsec=PSF_SCALE, effective_pixel_scale_arcsec=NATIVE_SCALE,
        stamp=STAMP, host_n=host_n, re_native_pix=TRUE_RE_PIX, q=TRUE_Q, pa_deg=TRUE_PA,
        host_analytic_flux=1., agn_to_host=RATIOS,
        psf_normalization='full signed input sum; no negative clipping, recentring, or output renormalization',
        psf_support='published finite 401x401 model; zero outside, unknown physical wings',
        interpolation=dict(variants=VARIANTS, k_interpolant='quintic', pad_factor=4.,
                           depixelize=False, use_true_center=True, noise_pad_size=0),
        gsparams=SETTINGS, draw_method='no_pixel', truth_variant='fine_quintic',
        fit_variants=FIT_VARIANTS, fit='inherited SciPy NNLS amplitudes; no ceiling',
        fixed='intrinsic Re,n,q,center,PA at truth; zero sky; no added noise',
        rows_per_host=24, controls=dict(optical_fwhm_arcsec=CONTROL_FWHMS,
            gaussian_source_sigma_arcsec=CONTROL_HOST_SIGMA,
            negative_control='extra native Pixel convolution; never an empirical science model'),
        acceptance='complete finite trace and provenance/identity checks only; no empirical recovery band',
        limitations='conditional flux fits, not structural inference; same GalSim truth/fitter; no literal survey or published-table reproduction')


def fetch_sources(root):
    """Small immutable-file adapter, sharing the existing Git blob verifier."""
    manifest=[]
    for rel, expected in SOURCE_FILES.items():
        target=root/rel; target.parent.mkdir(parents=True, exist_ok=True)
        url=f'{RAW_ROOT}/{rel}'
        if target.exists():
            raw=target.read_bytes()
        else:
            with urlopen(url, timeout=120) as response:
                raw=response.read()
        observed=git_blob_sha1(raw)
        if observed != expected:
            raise RuntimeError(f'immutable source mismatch: {rel}')
        target.write_bytes(raw)
        manifest.append(dict(path=rel, url=url, git_blob_sha1=observed,
                             sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)))
    return dict(repository=UPSTREAM_REPO, commit=UPSTREAM_COMMIT, files=manifest)


def normalize_psf(raw):
    array=np.asarray(raw, dtype=np.float64)
    if array.ndim!=2 or any(s%2==0 for s in array.shape) or not np.isfinite(array).all():
        raise ValueError('effective PSF must be finite, two-dimensional and odd-sized')
    total=float(array.sum())
    if total<=0:
        raise ValueError('effective PSF has nonpositive signed normalization')
    return array/total, total


def effective_psf(normalized, settings, interpolant='quintic'):
    """Interpolate an ALREADY pixel-response-convolved image; never depixelize."""
    image=galsim.Image(np.array(normalized, dtype=np.float64), scale=PSF_SCALE)
    return galsim.InterpolatedImage(image, normalization='flux', x_interpolant=interpolant,
        k_interpolant='quintic', pad_factor=4., depixelize=False, use_true_center=True,
        noise_pad_size=0, gsparams=galsim.GSParams(**settings))


def draw(obj, stamp=STAMP, method='no_pixel'):
    return obj.drawImage(nx=stamp, ny=stamp, scale=NATIVE_SCALE,
        method=method, dtype=np.float64, use_true_center=True).array


def l1(image, reference):
    return float(np.abs(image-reference).sum()/np.abs(reference).sum())


def image_diagnostics(image, scale):
    yy,xx=np.indices(image.shape, dtype=float)
    xx=(xx-(image.shape[1]-1)/2)*scale
    yy=(yy-(image.shape[0]-1)/2)*scale
    total=float(image.sum()); absolute=float(np.abs(image).sum())
    if not np.isfinite(image).all() or total<=0:
        raise RuntimeError('invalid finite template/positive signed sum')
    cx=float((xx*image).sum()/total); cy=float((yy*image).sum()/total)
    radius=np.hypot(xx,yy)
    return dict(signed_sum=total, min=float(image.min()), max=float(image.max()),
        negative_pixels=int((image<0).sum()),
        negative_absolute_fraction=float(np.abs(image[image<0]).sum()/absolute),
        signed_centroid_x_arcsec=cx, signed_centroid_y_arcsec=cy,
        signed_mxx_arcsec2=float(((xx-cx)**2*image).sum()/total),
        signed_myy_arcsec2=float(((yy-cy)**2*image).sum()/total),
        signed_aperture_fractions={str(r):float(image[radius<=r].sum()/total)
                                  for r in (.1,.2,.5,1.,2.,3.)})


def gaussian_effective_samples(sigma, stamp, sample_scale):
    """Closed-form Gaussian native-pixel integral evaluated on any sample grid.

    The area factor converts native-pixel probabilities to flux-normalized
    samples for GalSim; it does not integrate over the model sampling cell.
    """
    x=(np.arange(stamp)-(stamp-1)/2)*sample_scale
    one=.5*(erf((x+NATIVE_SCALE/2)/(np.sqrt(2)*sigma))
             -erf((x-NATIVE_SCALE/2)/(np.sqrt(2)*sigma)))
    return np.outer(one,one)*(sample_scale/NATIVE_SCALE)**2


def gaussian_controls():
    rows=[]; images={}
    for fwhm in CONTROL_FWHMS:
        key=f'fwhm{fwhm:g}'; sigma=fwhm/np.sqrt(8*np.log(2))
        sampled=gaussian_effective_samples(sigma,401,PSF_SCALE)
        normalized,_=normalize_psf(sampled)
        psf=effective_psf(normalized,SETTINGS['fine'])
        point=draw(psf); expected=gaussian_effective_samples(sigma,STAMP,NATIVE_SCALE)
        galaxy=galsim.Gaussian(sigma=CONTROL_HOST_SIGMA,flux=1.,
                              gsparams=galsim.GSParams(**SETTINGS['fine']))
        host=draw(galsim.Convolve(galaxy,psf))
        host_expected=gaussian_effective_samples(np.hypot(sigma,CONTROL_HOST_SIGMA),STAMP,NATIVE_SCALE)
        extra=draw(psf,method='fft')  # Intentionally wrong pixel convention, isolated control.
        rows.append(dict(optical_fwhm_arcsec=fwhm,point_l1_to_exact=l1(point,expected),
            host_l1_to_exact=l1(host,host_expected),extra_pixel_l1_to_exact=l1(extra,expected),
            point_sum=float(point.sum()),host_sum=float(host.sum()),extra_pixel_sum=float(extra.sum())))
        images.update({f'{key}_{label}':value for label,value in
            [('sampled',sampled),('point',point),('point_exact',expected),('host',host),
             ('host_exact',host_expected),('extra_pixel_negative_control',extra)]})
    return rows,images


def solve_fluxes(data, host, point):
    flux,prediction=profile_flux(data,host,point)
    matrix=np.column_stack((host.ravel(),point.ravel()))
    singular=np.linalg.svd(matrix,compute_uv=False)
    residual=prediction-data
    row=dict(solver='scipy.optimize.nnls',success=True,host_flux=float(flux[0]),
        nuclear_flux=float(flux[1]),hit_host_flux_zero=bool(flux[0]==0),
        hit_nuclear_flux_zero=bool(flux[1]==0),
        cost=float(.5*np.sum(residual**2)/np.mean(data**2)),
        residual_l1_over_data_l1=l1(prediction,data),
        template_singular_max=float(singular[0]),template_singular_min=float(singular[-1]),
        template_condition=float(singular[0]/singular[-1]) if singular[-1]>0 else None,
        kkt_host_gradient=float(np.sum(host*residual)),kkt_nuclear_gradient=float(np.sum(point*residual)))
    return row,prediction


def run_experiment(host_n,out):
    config=configuration(host_n); dump(out/'config.json',config)
    if config['runtime_versions']!=PINS:
        raise RuntimeError('package pin mismatch')
    manifest=fetch_sources(out/'source'); dump(out/'input_manifest.json',manifest)
    table=Table.read(out/'source/CEERS_PSF/PSF_statistics.ipac',format='ascii.ipac')
    controls,control_images=gaussian_controls()
    write_csv(out/'control_metrics.csv',controls)
    np.savez_compressed(out/'control_images.npz',**control_images)
    templates={}; diagnostics=[]; input_records=[]
    for module in ('A','B'):
        path=out/f'source/CEERS_PSF/Pointings12_F444W_Module_{module}.fits'
        with fits.open(path) as hdus:
            raw=np.array(hdus[0].data,dtype=np.float64); header=dict(hdus[0].header)
        if raw.shape!=(401,401): raise RuntimeError('wrong empirical PSF shape')
        normalized,total=normalize_psf(raw)
        metadata=[r for r in table if r['BAND']=='F444W' and r['Pointings']=='1+2' and r['Module']==module]
        if len(metadata)!=1: raise RuntimeError('ambiguous source metadata')
        meta=metadata[0]
        input_records.append(dict(module=module,header=header,raw_signed_sum=total,
            published_fwhm_arcsec=float(meta['FWHM']),published_q=float(meta['q']),
            published_nstar=int(meta['Nstar']),published_win_size=int(meta['WIN_SIZE']),
            normalized_diagnostics=image_diagnostics(normalized,PSF_SCALE)))
        templates[f'{module}_normalized_input']=normalized
        for label,(accuracy,interpolant) in VARIANTS.items():
            psf=effective_psf(normalized,SETTINGS[accuracy],interpolant)
            galaxy=profile(host_n,SETTINGS[accuracy],re=TRUE_RE_PIX*NATIVE_SCALE,q=TRUE_Q)
            host=draw(galsim.Convolve(galaxy,psf)); point=draw(psf)
            templates[f'{module}_{label}_host']=host
            templates[f'{module}_{label}_point']=point
        for label in VARIANTS:
            for kind in ('host','point'):
                image=templates[f'{module}_{label}_{kind}']
                reference=templates[f'{module}_fine_quintic_{kind}']
                diagnostics.append(dict(module=module,variant=label,component=kind,
                    l1_to_fine_quintic=l1(image,reference),**image_diagnostics(image,NATIVE_SCALE)))
    dump(out/'psf_input_records.json',input_records)
    dump(out/'template_diagnostics.json',diagnostics)
    np.savez_compressed(out/'templates.npz',**templates)
    rows=[]
    for truth_module in ('A','B'):
        host=templates[f'{truth_module}_fine_quintic_host']
        point=templates[f'{truth_module}_fine_quintic_point']
        for ratio in RATIOS:
            data=host+ratio*point
            bundle=dict(data=data,host_truth=host,nuclear_truth=ratio*point)
            for fit_module in ('A','B'):
                for label in FIT_VARIANTS:
                    common=dict(true_n=host_n,true_re_native_pix=TRUE_RE_PIX,true_q=TRUE_Q,
                        true_host_flux=1.,true_nuclear_flux=ratio,agn_to_host=ratio,
                        truth_module=truth_module,fit_module=fit_module,fit_variant=label,
                        data_sha256=hashlib.sha256(data.tobytes()).hexdigest(),
                        data_negative_pixels=int((data<0).sum()),data_signed_sum=float(data.sum()))
                    try:
                        row,pred=solve_fluxes(data,templates[f'{fit_module}_{label}_host'],
                                              templates[f'{fit_module}_{label}_point'])
                    except Exception as error:
                        dump(out/'failure.json',dict(**common,error_type=type(error).__name__,error=str(error)))
                        raise
                    row=dict(**common,**row,host_flux_bias=row['host_flux']-1.,
                             nuclear_flux_fractional_bias=row['nuclear_flux']/ratio-1.)
                    rows.append(row)
                    tag=f'{fit_module}_{label}'
                    bundle[f'{tag}_prediction']=pred; bundle[f'{tag}_residual']=pred-data
                    write_csv(out/'metrics.csv',rows); write_csv(out/'fit_starts.csv',rows)
                    print(json.dumps(row,allow_nan=False),flush=True)
            np.savez_compressed(out/f'truth{truth_module}_ratio{ratio:g}.npz',**bundle)
    if len(rows)!=24 or not all(np.isfinite(r['cost']) for r in rows):
        raise RuntimeError('incomplete/nonfinite diagnostic')
    if not all(np.isfinite(v).all() for v in list(templates.values())+list(control_images.values())):
        raise RuntimeError('nonfinite image product')
    dump(out/'summary.json',dict(config=config,input_manifest=manifest,psf_inputs=input_records,
        controls=controls,template_diagnostics=diagnostics,results=rows,
        interpretation='complete execution is not empirical PSF accuracy or morphology recovery'))


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--host-n',type=int,choices=(1,4),required=True)
    p.add_argument('--output',type=Path,default=Path('benchmark_output/agn_empirical_psf_transfer'))
    a=p.parse_args(); out=a.output; out.mkdir(parents=True,exist_ok=True)
    start=time.perf_counter(); captured=[]
    try:
        with warnings.catch_warnings(record=True) as captured:
            # Retain every resource warning, without changing the FFT or accuracy.
            warnings.simplefilter('always',galsim.GalSimFFTSizeWarning)
            run_experiment(a.host_n,out)
    finally:
        usage=resource.getrusage(resource.RUSAGE_SELF)
        dump(out/'runtime.json',dict(wall_seconds=time.perf_counter()-start,
             max_resident_set_kib_linux=int(usage.ru_maxrss),user_cpu_seconds=usage.ru_utime,
             system_cpu_seconds=usage.ru_stime))
        dump(out/'warnings.json',[dict(category=w.category.__name__,message=str(w.message),
             filename=w.filename,lineno=w.lineno) for w in captured])
        for w in captured:
            warnings.showwarning(w.message,w.category,w.filename,w.lineno)


if __name__=='__main__': main()
