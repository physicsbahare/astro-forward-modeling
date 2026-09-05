#!/usr/bin/env python3
"""Gate D1n-e: compare published COSMOS-Web F444W empirical PSFs to frozen STPSF."""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
from scipy import ndimage
from astropy.io import fits

import run_gate_d_cosmosweb_real_injection as inj

NAMES = ("broad", "global", "narrow")
FILES = {k: f"OBS_084_F444W_{k}_PSF.fits" for k in NAMES}
FROZEN_SOURCE_SCALE_ARCSEC = 0.03


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def first_image(path: Path):
    with fits.open(path, mode="readonly") as h:
        for hdu in h:
            if hdu.data is not None and np.asarray(hdu.data).ndim == 2:
                return np.asarray(hdu.data, dtype=float), hdu.header.copy(), hdu.name
    raise ValueError(f"no 2D image HDU in {path}")


def infer_scale_arcsec(header) -> tuple[float, str]:
    for key in ("PIXELSCL", "PIXSCALE"):
        if key in header and np.isfinite(float(header[key])) and float(header[key]) > 0:
            return float(header[key]), key
    if "CDELT1" in header and float(header["CDELT1"]) != 0:
        return abs(float(header["CDELT1"])) * 3600.0, "CDELT1"
    if "CD1_1" in header and float(header["CD1_1"]) != 0:
        return abs(float(header["CD1_1"])) * 3600.0, "CD1_1"
    return FROZEN_SOURCE_SCALE_ARCSEC, "frozen_release_grid_fallback"


def positive_metrics(a: np.ndarray, scale: float) -> dict:
    x = np.asarray(a, float)
    if x.ndim != 2 or not np.all(np.isfinite(x)):
        raise ValueError("PSF must be finite 2D")
    signed = float(x.sum()); absolute = float(np.abs(x).sum())
    p = np.maximum(x, 0.0); total = float(p.sum())
    if total <= 0: raise ValueError("nonpositive PSF support")
    p /= total
    yy, xx = np.indices(p.shape, dtype=float)
    cx = float((p*xx).sum()); cy = float((p*yy).sum())
    dx, dy = xx-cx, yy-cy
    cov = np.array([[float((p*dx*dx).sum()), float((p*dx*dy).sum())],
                    [float((p*dx*dy).sum()), float((p*dy*dy).sum())]])
    vals = np.sort(np.linalg.eigvalsh(cov))[::-1]
    major = math.sqrt(max(float(vals[0]), 0.0)); minor = math.sqrt(max(float(vals[1]), 0.0))
    rr = np.hypot(dx, dy).ravel(); flux = p.ravel(); order=np.argsort(rr)
    rr, cdf = rr[order], np.cumsum(flux[order])
    def er(f): return float(rr[min(np.searchsorted(cdf, f), len(rr)-1)] * scale)
    center=((p.shape[1]-1)/2,(p.shape[0]-1)/2)
    return dict(shape=list(p.shape), signed_sum=signed, absolute_sum=absolute,
        negative_pixel_fraction=float((x<0).mean()),
        negative_absolute_fraction=float(np.abs(x[x<0]).sum()/absolute) if absolute else None,
        centroid_x_pix=cx, centroid_y_pix=cy,
        centroid_offset_from_array_center_arcsec=float(math.hypot(cx-center[0],cy-center[1])*scale),
        sigma_major_arcsec=major*scale, sigma_minor_arcsec=minor*scale,
        axis_ratio_moment=float(minor/major) if major>0 else None,
        ee50_radius_arcsec=er(.5), ee80_radius_arcsec=er(.8))


def resample_flux(a: np.ndarray, source_scale: float, target_scale: float) -> np.ndarray:
    if np.isclose(source_scale, target_scale, rtol=0, atol=1e-12): return np.asarray(a,float)
    z=source_scale/target_scale
    out=ndimage.zoom(np.asarray(a,float), zoom=z, order=1, mode="constant", cval=0.0, prefilter=False)
    s0=float(np.asarray(a,float).sum()); s1=float(out.sum())
    if s1 != 0: out *= s0/s1
    return out


def center_pad(a, shape):
    out=np.zeros(shape,float); y=(shape[0]-a.shape[0])//2; x=(shape[1]-a.shape[1])//2
    out[y:y+a.shape[0],x:x+a.shape[1]]=a; return out


def compare(a,b):
    shape=(max(a.shape[0],b.shape[0]),max(a.shape[1],b.shape[1]))
    x=center_pad(a,shape); y=center_pad(b,shape)
    # signed normalization is preserved where defined; this is comparison-only.
    if x.sum()==0 or y.sum()==0: raise ValueError("zero signed PSF sum")
    x=x/x.sum(); y=y/y.sum()
    denom=math.sqrt(float((x*x).sum()*(y*y).sum()))
    return dict(normalized_l1=float(np.abs(x-y).sum()),
                normalized_cross_correlation=float((x*y).sum()/denom), common_shape=list(shape))


def run(psf_dir: Path, matrix_path: Path, out_json: Path):
    matrix=json.loads(matrix_path.read_text()); scale=float(matrix["pixel_scale_arcsec"])
    stpsf, prov=inj.build_stpsf(matrix, scale)
    images={"stpsf":stpsf}; rows=[]
    for name in NAMES:
        path=psf_dir/FILES[name]; raw,header,hdu=first_image(path); src_scale,scale_source=infer_scale_arcsec(header)
        if not np.all(np.isfinite(raw)): raise ValueError(f"nonfinite published PSF: {name}")
        common=resample_flux(raw,src_scale,scale)
        images[name]=common
        rows.append(dict(name=name,file=FILES[name],bytes=path.stat().st_size,sha256=sha256(path),
            hdu=hdu,source_shape=list(raw.shape),source_pixel_scale_arcsec=src_scale,
            source_pixel_scale_provenance=scale_source,metrics=positive_metrics(common,scale),
            comparison_to_stpsf=compare(stpsf,common)))
    pairs=[]
    for i,a in enumerate(NAMES):
        for b in NAMES[i+1:]: pairs.append(dict(a=a,b=b,comparison=compare(images[a],images[b])))
    out=dict(claim="published COSMOS-Web observation-level empirical PSF shape bracket; not literal DR1 mosaic effective PSF and not morphology recovery",
        observation="OBS_084",filter="F444W",comparison_pixel_scale_arcsec=scale,
        stpsf=dict(metrics=positive_metrics(stpsf,scale),provenance=prov),published_psfs=rows,
        published_pairwise=pairs,semantics=dict(morphology_recovery_performed=False,source_injection_performed=False,
            psf_sharpening_performed=False,deconvolution_performed=False,noise_added=False,tolman_factor_applied=False,
            target_bounds_changed=False,acceptance_threshold_defined=False,literal_dr1_effective_psf_claimed=False))
    out_json.parent.mkdir(parents=True,exist_ok=True); out_json.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    return out


def main():
    p=argparse.ArgumentParser(); p.add_argument("--psf-dir",type=Path,required=True); p.add_argument("--matrix",type=Path,required=True); p.add_argument("--out-json",type=Path,required=True)
    a=p.parse_args(); r=run(a.psf_dir,a.matrix,a.out_json); print(json.dumps({"n_published":len(r["published_psfs"]),"n_pairwise":len(r["published_pairwise"])},indent=2))
if __name__=="__main__": main()
