#!/usr/bin/env python3
"""C5e: thin GalSim/Photutils adapters for signed effective-PSF pixel phases.

Frozen protocol: benchmarks/zhuang_shen_2024/REVIEW.md. No galaxy fitting,
PSF reconstruction, clipping, pixel reintegration or output normalization.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import shutil
import time
import warnings

import galsim
import numpy as np
from astropy.io import fits
from photutils.psf import ImagePSF
from scipy.special import erf

from run_agn_empirical_psf_transfer import (
    PINS as TRANSFER_PINS, PSF_SCALE, NATIVE_SCALE, SETTINGS,
    CONTROL_FWHMS, SOURCE_FILES, normalize_psf, effective_psf,
    gaussian_effective_samples, l1, dump,
)
from fetch_zhuang_shen_benchmark import git_blob_sha1
from run_agn_nuclear_fraction_noiseless import profile_flux, write_csv

ROOT = Path(__file__).resolve().parents[1]
PARENT_RUN = 33717899427
PARENT_COMMIT = '88f3fb646a0b89e6cb9b8b8ee1aacae377edca56'
PARENT_ARTIFACT = 9880481087  # n=1; both modules' original PSFs are archived here
AUDIT = ROOT/'benchmarks/zhuang_shen_2024/empirical_transfer_33717899427.json'
PINS = dict(TRANSFER_PINS, photutils='3.0.0')
PHASES = (0., .25, .5, .75)
METHODS = ('galsim_quintic', 'galsim_lanczos4', 'photutils_cubic')
STAMP, FIT_STAMP, ZERO_PAD = 211, 201, 8
APERTURES = (.1, .2, .5, 1., 2., 3.)
FIT_SLICE = slice((STAMP-FIT_STAMP)//2, (STAMP+FIT_STAMP)//2)


def digest(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def configuration(module):
    return dict(stage='C5e signed effective-PSF phase / interpolation diagnostic',
        module=module, parent_run=PARENT_RUN, parent_commit=PARENT_COMMIT,
        parent_artifact_id=PARENT_ARTIFACT, parent_audit_sha256=hashlib.sha256(AUDIT.read_bytes()).hexdigest(),
        github_run_id=os.environ.get('GITHUB_RUN_ID'), github_sha=os.environ.get('GITHUB_SHA'),
        package_pins=PINS, runtime_versions={k:importlib.metadata.version(k) for k in PINS},
        phase_x_native_pix=PHASES, phase_y_native_pix=PHASES,
        phase_convention='positive shifts source toward increasing array x/y',
        methods=METHODS, psf_sample_scale_arcsec=PSF_SCALE,
        effective_pixel_scale_arcsec=NATIVE_SCALE, full_stamp=STAMP, fit_stamp=FIT_STAMP,
        photutils=dict(oversampling=2, input_factor=4., zero_pad=ZERO_PAD,
            origin='padded geometric center', interpolation='public cubic ImagePSF', fill_value=0.),
        galsim=dict(gsparams=SETTINGS['fine'], draw_method='no_pixel',
            x_interpolants=['quintic','lanczos4'], depixelize=False, pad_factor=4.),
        normalization='C5d full signed input sum; no clipping/recentering/output renormalization',
        scene='unit point source; no host, added noise, free center or structural inference',
        objective='one nonnegative NNLS amplitude on 201-pixel crop; inherited RMS-normalized cost; no ceiling',
        reference='same-input GalSim fine-Quintic; not independent physical truth',
        apertures_arcsec=APERTURES, aperture_membership='pixel centers around declared source position',
        rows_per_module=48, control_rows_per_module=96, gaussian_fwhm_arcsec=CONTROL_FWHMS,
        acceptance='finite complete products and provenance/algebra only; no new off-grid recovery band',
        limitations='signed empirical models are not photon intensities; interpolation agreement is not PSF validity')


def load_parent(source, out, module):
    audit=json.loads(AUDIT.read_text())
    if audit['run_id']!=PARENT_RUN or audit['commit']!=PARENT_COMMIT:
        raise RuntimeError('wrong pinned parent review')
    record=next(a for a in audit['artifacts'] if a['artifact_id']==PARENT_ARTIFACT)
    selected=['commit.txt','config.json','input_manifest.json','templates.npz']
    selected += ['source/'+path for path in SOURCE_FILES]
    observed={}
    for rel in selected:
        raw=(source/rel).read_bytes()
        observed[rel]=hashlib.sha256(raw).hexdigest()
        if observed[rel]!=record['file_sha256'][rel]:
            raise RuntimeError('parent file checksum mismatch: '+rel)
        dest=out/'parent'/rel; dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source/rel,dest)
    if (source/'commit.txt').read_text().strip()!=PARENT_COMMIT:
        raise RuntimeError('wrong parent commit')
    config=json.loads((source/'config.json').read_text())
    if config['github_run_id']!=str(PARENT_RUN) or config['host_n']!=1:
        raise RuntimeError('wrong parent run/shard')
    for rel,expected in SOURCE_FILES.items():
        if git_blob_sha1((source/'source'/rel).read_bytes())!=expected:
            raise RuntimeError('author Git blob mismatch: '+rel)
    raw=np.asarray(fits.getdata(source/f'source/CEERS_PSF/Pointings12_F444W_Module_{module}.fits'),dtype=float)
    normalized,total=normalize_psf(raw)
    with np.load(source/'templates.npz') as bundle:
        if not np.array_equal(normalized,bundle[module+'_normalized_input']):
            raise RuntimeError('parent normalization mismatch')
        point=bundle[module+'_fine_quintic_point'].copy()
    dump(out/'source_manifest.json',dict(run_id=PARENT_RUN,commit=PARENT_COMMIT,
        artifact_id=PARENT_ARTIFACT,file_sha256=observed,raw_signed_sum=total,
        original_input_shape=list(raw.shape),normalized_array_sha256=digest(normalized)))
    return normalized,point


def models(normalized):
    # Photutils expects native-pixel response samples, whose 2x oversampled
    # array sum is 4. GalSim's flux-per-sample array sum is 1. No second pixel.
    padded=4*np.pad(normalized,ZERO_PAD,mode='constant')
    origin=tuple((np.array(padded.shape[::-1])-1)/2)
    return dict(galsim_quintic=effective_psf(normalized,SETTINGS['fine'],'quintic'),
        galsim_lanczos4=effective_psf(normalized,SETTINGS['fine'],'lanczos4'),
        photutils_cubic=ImagePSF(padded,flux=1.,oversampling=2,origin=origin,fill_value=0.))


def render(model,method,phase):
    dx,dy=phase
    if method=='photutils_cubic':
        shifted=model.copy()
        shifted.x_0=(STAMP-1)/2+dx; shifted.y_0=(STAMP-1)/2+dy
        yy,xx=np.indices((STAMP,STAMP),dtype=float)
        return np.asarray(shifted(xx,yy),dtype=float)
    return model.shift(dx*NATIVE_SCALE,dy*NATIVE_SCALE).drawImage(
        nx=STAMP,ny=STAMP,scale=NATIVE_SCALE,method='no_pixel',
        dtype=np.float64,use_true_center=True).array


def scalar_fit(data,template):
    flux,prediction=profile_flux(data,template)
    residual=prediction-data
    scale2=float(np.mean(data**2))
    if scale2<=0: raise ValueError('zero reference norm')
    row=dict(solver='scipy.optimize.nnls',success=True,flux=float(flux[0]),
        flux_bias=float(flux[0]-1),hit_flux_zero=bool(flux[0]==0),
        cost=float(.5*np.sum(residual**2)/scale2),
        residual_l1_over_data_l1=l1(prediction,data),
        template_squared_norm=float(np.sum(template**2)),
        kkt_gradient=float(np.sum(template*residual)))
    return row,prediction,residual


def image_stats(image,phase):
    yy,xx=np.indices(image.shape,dtype=float)
    xx=(xx-(image.shape[1]-1)/2-phase[0])*NATIVE_SCALE
    yy=(yy-(image.shape[0]-1)/2-phase[1])*NATIVE_SCALE
    signed=float(image.sum()); absolute=float(np.abs(image).sum())
    radius=np.hypot(xx,yy)
    apertures=[]
    for r in APERTURES:
        arr=image[radius<=r]
        apertures.append(dict(radius_arcsec=r,signed_sum=float(arr.sum()),
            absolute_sum=float(np.abs(arr).sum()),negative_abs_sum=float(np.abs(arr[arr<0]).sum())))
    return dict(signed_sum=signed,absolute_sum=absolute,min=float(image.min()),
        negative_pixels=int((image<0).sum()),negative_absolute_fraction=float(np.abs(image[image<0]).sum()/absolute) if absolute else None,
        signed_centroid_dx_arcsec=float((xx*image).sum()/signed) if signed else None,
        signed_centroid_dy_arcsec=float((yy*image).sum()/signed) if signed else None,
        apertures=apertures)


def gaussian_exact(sigma,phase):
    x=(np.arange(STAMP)-(STAMP-1)/2-phase[0])*NATIVE_SCALE
    y=(np.arange(STAMP)-(STAMP-1)/2-phase[1])*NATIVE_SCALE
    def axis(z):
        return .5*(erf((z+NATIVE_SCALE/2)/(np.sqrt(2)*sigma))
                   -erf((z-NATIVE_SCALE/2)/(np.sqrt(2)*sigma)))
    return np.outer(axis(y),axis(x))


def controls(out):
    rows=[]
    for fwhm in CONTROL_FWHMS:
        sigma=fwhm/np.sqrt(8*np.log(2))
        sampled=gaussian_effective_samples(sigma,401,PSF_SCALE)
        normalized,_=normalize_psf(sampled); implementations=models(normalized)
        for dx in PHASES:
            for dy in PHASES:
                phase=(dx,dy); exact=gaussian_exact(sigma,phase)
                data=exact[FIT_SLICE,FIT_SLICE]; bundle=dict(exact=exact)
                for method in METHODS:
                    image=render(implementations[method],method,phase)
                    fit,pred,residual=scalar_fit(data,image[FIT_SLICE,FIT_SLICE])
                    rows.append(dict(optical_fwhm_arcsec=fwhm,phase_x=dx,phase_y=dy,
                        method=method,image_l1_to_exact=l1(image,exact),signed_sum=float(image.sum()),**fit))
                    bundle[method]=image; bundle[method+'_prediction']=pred
                    bundle[method+'_residual']=residual
                if not all(np.isfinite(a).all() for a in bundle.values()):
                    raise RuntimeError('nonfinite Gaussian control')
                np.savez_compressed(out/f'control_fwhm{fwhm:g}_x{dx:g}_y{dy:g}.npz',**bundle)
                write_csv(out/'control_metrics.csv',rows)
    return rows


def run(module,source,out):
    config=configuration(module); dump(out/'config.json',config)
    if config['runtime_versions']!=PINS: raise RuntimeError('package pin mismatch')
    normalized,parent_point=load_parent(source,out,module)
    implementations=models(normalized)
    np.savez_compressed(out/'input_models.npz',normalized_input=normalized,
        photutils_padded_input=4*np.pad(normalized,ZERO_PAD))
    parity=[dict(x_parity=x,y_parity=y,native_signed_sum=float(4*normalized[y::2,x::2].sum()))
            for x in (0,1) for y in (0,1)]
    parity_mean=float(np.mean([r['native_signed_sum'] for r in parity]))
    # Identity on a disjoint array partition, not an empirical recovery cut.
    np.testing.assert_allclose(parity_mean,normalized.sum(),rtol=0,atol=1e-14)
    dump(out/'input_parity.json',dict(rows=parity,mean=parity_mean,
        identity_difference=float(parity_mean-normalized.sum())))
    control_rows=controls(out)
    rows=[]; aperture_rows=[]; zero_phase_drift=None
    for dx in PHASES:
        for dy in PHASES:
            phase=(dx,dy)
            rendered={k:render(v,k,phase) for k,v in implementations.items()}
            data=rendered['galsim_quintic'][FIT_SLICE,FIT_SLICE].copy()
            if phase==(0.,0.):
                zero_phase_drift=float(np.max(np.abs(data-parent_point)))
                np.testing.assert_allclose(data,parent_point,rtol=0,atol=1e-12)
            bundle=dict(data=data,**rendered)
            for method in METHODS:
                image=rendered[method]; crop=image[FIT_SLICE,FIT_SLICE]
                fit,pred,residual=scalar_fit(data,crop)
                stats=image_stats(image,phase)
                for ap in stats.pop('apertures'):
                    aperture_rows.append(dict(module=module,phase_x=dx,phase_y=dy,method=method,**ap))
                row=dict(module=module,phase_x=dx,phase_y=dy,method=method,
                    data_sha256=digest(data),template_sha256=digest(image),
                    crop_signed_sum=float(crop.sum()),full_minus_crop_signed_sum=float(image.sum()-crop.sum()),
                    image_l1_to_reference=l1(image,rendered['galsim_quintic']),**stats,**fit)
                rows.append(row)
                bundle[method+'_prediction']=pred; bundle[method+'_residual']=residual
                write_csv(out/'metrics.csv',rows); write_csv(out/'fit_starts.csv',rows)
                write_csv(out/'aperture_metrics.csv',aperture_rows)
                print(json.dumps(row,allow_nan=False),flush=True)
            if not all(np.isfinite(a).all() for a in bundle.values()):
                raise RuntimeError('nonfinite phase product')
            np.savez_compressed(out/f'phase_x{dx:g}_y{dy:g}.npz',**bundle)
    if len(rows)!=48 or len(control_rows)!=96 or len(aperture_rows)!=288:
        raise RuntimeError('incomplete frozen Cartesian product')
    ranges=[]
    for method in METHODS:
        subset=[r for r in rows if r['method']==method]
        ranges.append(dict(method=method,
            min_native_sum=min(r['signed_sum'] for r in subset),
            max_native_sum=max(r['signed_sum'] for r in subset),
            min_fit_flux=min(r['flux'] for r in subset),max_fit_flux=max(r['flux'] for r in subset),
            maximum_l1_to_reference=max(r['image_l1_to_reference'] for r in subset),
            zero_amplitude_count=sum(r['hit_flux_zero'] for r in subset)))
    dump(out/'summary.json',dict(config=config,results=rows,apertures=aperture_rows,
        gaussian_controls=control_rows,input_parity=parity,phase_ranges=ranges,
        zero_phase_max_abs_parent_drift=zero_phase_drift,
        interpretation='signed-model interpolation diagnostic; no physical PSF/centroid/morphology acceptance'))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--module',choices=('A','B'),required=True)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path('benchmark_output/agn_empirical_psf_phase'))
    args=parser.parse_args(); out=args.output; out.mkdir(parents=True,exist_ok=True)
    if (out/'config.json').exists(): raise FileExistsError('refusing to overwrite a previous experiment')
    start=time.perf_counter(); captured=[]
    try:
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter('always')
            run(args.module,args.source,out)
    except Exception as error:
        dump(out/'failure.json',dict(error_type=type(error).__name__,error=str(error)))
        raise
    finally:
        usage=resource.getrusage(resource.RUSAGE_SELF)
        dump(out/'runtime.json',dict(wall_seconds=time.perf_counter()-start,
            max_resident_set_kib_linux=int(usage.ru_maxrss),user_cpu_seconds=usage.ru_utime,
            system_cpu_seconds=usage.ru_stime))
        dump(out/'warnings.json',[dict(category=w.category.__name__,message=str(w.message),
            filename=w.filename,lineno=w.lineno) for w in captured])


if __name__=='__main__': main()
