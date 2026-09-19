#!/usr/bin/env python3
"""Gate D1d: inject controlled Sérsic sources into a frozen real COSMOS-Web cutout."""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
from scipy import ndimage, signal
from astropy.io import fits

AB_ZERO_JY = 3631.0


def sersic_profile(size: int, re_pix: float, n: float, q: float, pa_deg: float, oversample: int) -> np.ndarray:
    if size % 2 != 1 or size < 5:
        raise ValueError("profile stamp size must be odd and >=5")
    if not (re_pix > 0 and n > 0 and 0 < q <= 1 and oversample >= 1):
        raise ValueError("invalid Sersic geometry")
    c = (size - 1) / 2.0
    sub = oversample
    off = (np.arange(sub) + 0.5) / sub - 0.5
    y0, x0 = np.indices((size, size), dtype=float)
    theta = np.deg2rad(pa_deg)
    bn = 2.0 * n - 1.0 / 3.0 + 4.0 / (405.0 * n) + 46.0 / (25515.0 * n * n)
    acc = np.zeros((size, size), dtype=float)
    for dy in off:
        for dx in off:
            x = x0 + dx - c; y = y0 + dy - c
            xr = x * np.cos(theta) + y * np.sin(theta)
            yr = -x * np.sin(theta) + y * np.cos(theta)
            r = np.sqrt(xr * xr + (yr / q) ** 2)
            acc += np.exp(-bn * ((r / re_pix) ** (1.0 / n) - 1.0))
    acc /= float(sub * sub)
    total = float(acc.sum())
    if not np.isfinite(total) or total <= 0:
        raise ValueError("non-positive Sersic profile")
    return acc / total


def convolve_normalized(profile: np.ndarray, psf: np.ndarray) -> np.ndarray:
    p = np.asarray(psf, dtype=float)
    if p.ndim != 2 or not np.all(np.isfinite(p)) or np.any(p < 0) or p.sum() <= 0:
        raise ValueError("PSF must be finite, non-negative, two-dimensional, and positive-sum")
    p = p / p.sum()
    out = signal.fftconvolve(profile, p, mode="same")
    floor = -1e-12 * max(1.0, float(np.max(out)))
    if float(np.min(out)) < floor:
        raise ValueError("convolution produced material negative flux")
    out = np.maximum(out, 0.0)
    return out / out.sum()


def ab_to_jy(mag: float) -> float:
    return AB_ZERO_JY * 10.0 ** (-0.4 * float(mag))


def surface_brightness_stamp(unit_profile: np.ndarray, mag: float, pixar_sr: float) -> tuple[np.ndarray, float]:
    flux_jy = ab_to_jy(mag)
    total_mjysr_pixels = flux_jy / (1.0e6 * pixar_sr)
    return unit_profile * total_mjysr_pixels, flux_jy


def inject_stamp(sci: np.ndarray, stamp: np.ndarray, x: int, y: int) -> np.ndarray:
    if stamp.shape[0] != stamp.shape[1] or stamp.shape[0] % 2 != 1:
        raise ValueError("injection stamp must be odd and square")
    h = stamp.shape[0] // 2
    if x - h < 0 or y - h < 0 or x + h >= sci.shape[1] or y + h >= sci.shape[0]:
        raise ValueError(f"injection at {(x,y)} would truncate the frozen stamp")
    out = np.array(sci, copy=True)
    out[y-h:y+h+1, x-h:x+h+1] += stamp
    return out


def build_stpsf(matrix: dict, target_scale_arcsec: float) -> tuple[np.ndarray, dict]:
    import stpsf
    cfg = matrix["psf"]
    nrc = stpsf.NIRCam(); nrc.filter = cfg["filter"]; nrc.detector = cfg["detector"]
    nrc.detector_position = tuple(cfg["detector_position_xy"])
    sw = cfg["spectral_weighting"]
    source = {"wavelengths": np.asarray(sw["wavelength_m"], dtype=float), "weights": np.asarray(sw["weights"], dtype=float)}
    hdul = nrc.calc_psf(source=source, fov_pixels=int(cfg["fov_pixels"]), oversample=int(cfg["calc_oversample"]))
    hdu = hdul[cfg["extension"]]
    raw = np.asarray(hdu.data, dtype=float)
    if float(np.min(raw)) < -1.0e-12:
        raise ValueError("STPSF output contains material negative values")
    raw = np.maximum(raw, 0.0); raw /= raw.sum()
    psf_scale = float(hdu.header["PIXELSCL"])
    zoom = psf_scale / target_scale_arcsec
    resampled = ndimage.zoom(raw, zoom=zoom, order=1, mode="constant", cval=0.0, prefilter=False)
    resampled = np.maximum(resampled, 0.0); resampled /= resampled.sum()
    prov = {"input_pixel_scale_arcsec": psf_scale, "target_pixel_scale_arcsec": target_scale_arcsec,
            "resample_zoom": zoom, "input_shape": list(raw.shape), "output_shape": list(resampled.shape),
            "extension": cfg["extension"], "sum_after_resample": float(resampled.sum())}
    return resampled, prov


def run(real_fits: Path, matrix_path: Path, out_fits: Path, out_json: Path) -> dict:
    matrix = json.loads(matrix_path.read_text())
    with fits.open(real_fits, mode="readonly") as h:
        sci = np.asarray(h["SCI"].data, dtype=float)
        err = np.asarray(h["ERR"].data, dtype=float)
        wht = np.asarray(h["WHT"].data, dtype=float)
        sci_header = h["SCI"].header.copy(); err_header = h["ERR"].header.copy(); wht_header = h["WHT"].header.copy()
    if sci.shape != err.shape or sci.shape != wht.shape:
        raise ValueError("real SCI/ERR/WHT shapes differ")
    if str(sci_header.get("BUNIT", "")).strip().lower() != "mjy/sr":
        raise ValueError(f"expected real SCI BUNIT=MJy/sr, got {sci_header.get('BUNIT')!r}")
    pixar_sr = float(sci_header["PIXAR_SR"])
    if not np.isfinite(pixar_sr) or pixar_sr <= 0:
        raise ValueError("SCI PIXAR_SR must be positive and finite")
    scale_arcsec = float(matrix["pixel_scale_arcsec"])
    psf, psf_prov = build_stpsf(matrix, scale_arcsec)
    sm = matrix["source_model"]
    profile = sersic_profile(int(sm["profile_stamp_pixels"]), float(sm["effective_radius_arcsec"])/scale_arcsec,
                             float(sm["sersic_n"]), float(sm["axis_ratio"]), float(sm["position_angle_deg"]),
                             int(sm["profile_oversample"]))
    model = convolve_normalized(profile, psf)
    hdus = [fits.PrimaryHDU(), fits.ImageHDU(np.asarray(sci, dtype=np.float32), header=sci_header, name="SCI_ORIG"),
            fits.ImageHDU(np.asarray(err, dtype=np.float32), header=err_header, name="ERR"),
            fits.ImageHDU(np.asarray(wht, dtype=np.float32), header=wht_header, name="WHT")]
    rows = []
    for cls, positions in matrix["placements"].items():
        for j, (x, y, distance) in enumerate(positions):
            for mag in sm["ab_magnitudes"]:
                stamp, requested_jy = surface_brightness_stamp(model, float(mag), pixar_sr)
                injected = inject_stamp(sci, stamp, int(x), int(y))
                delta = injected - sci
                realized_jy = float(delta.sum() * 1.0e6 * pixar_sr)
                rel = abs(realized_jy/requested_jy - 1.0)
                if rel > 2.0e-6:
                    raise ValueError(f"injected flux mismatch {rel:.3g} at {cls} {j} AB={mag}")
                tag = f"{cls[:4].upper()}{j}_M{str(mag).replace('.','P')}"
                hdus.append(fits.ImageHDU(np.asarray(injected, dtype=np.float32), header=sci_header, name=tag[:68]))
                h = stamp.shape[0]//2
                epatch = err[int(y)-h:int(y)+h+1, int(x)-h:int(x)+h+1]
                nominal_independent_snr = float(stamp.sum()/math.sqrt(float(np.sum(epatch*epatch))))
                rows.append({"class": cls, "index": j, "x": int(x), "y": int(y), "distance_to_source_pixel": float(distance),
                             "ab_mag": float(mag), "requested_flux_jy": requested_jy, "realized_flux_jy": realized_jy,
                             "relative_flux_error": rel, "nominal_independent_pixel_snr": nominal_independent_snr,
                             "output_extname": tag[:68]})
    out_fits.parent.mkdir(parents=True, exist_ok=True)
    fits.HDUList(hdus).writeto(out_fits, overwrite=True, checksum=True)
    summary = {"claim": matrix["semantics"]["claim"], "input_real_fits": str(real_fits), "matrix": matrix,
               "pixar_sr": pixar_sr, "bunit": sci_header["BUNIT"], "psf_provenance": psf_prov,
               "experiments": rows, "n_experiments": len(rows), "err_modified": False, "wht_modified": False,
               "background_added": False, "source_shot_noise_added": False, "tolman_factor_applied": False,
               "recovery_performed": False}
    out_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def main():
    p = argparse.ArgumentParser(); p.add_argument("--real-fits", type=Path, required=True)
    p.add_argument("--matrix", type=Path, required=True); p.add_argument("--out-fits", type=Path, required=True)
    p.add_argument("--out-json", type=Path, required=True); a = p.parse_args()
    s = run(a.real_fits, a.matrix, a.out_fits, a.out_json)
    print(json.dumps({"n_experiments": s["n_experiments"], "psf_provenance": s["psf_provenance"]}, indent=2))

if __name__ == "__main__": main()
