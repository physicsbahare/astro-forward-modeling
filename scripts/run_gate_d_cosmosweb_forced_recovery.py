#!/usr/bin/env python3
"""Gate D1e: forced-position Sérsic recovery on frozen real-mosaic injections."""
from __future__ import annotations
import argparse, importlib.util, json, math
from pathlib import Path
import numpy as np
from scipy import ndimage, optimize
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("gate_d_inj", ROOT / "scripts" / "run_gate_d_cosmosweb_real_injection.py")
inj = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(inj)

PATCH = 65
HALF = PATCH // 2
BOUNDS_LO = np.array([math.log(1e-4), -2.0, -2.0, math.log(1.0), 0.3, 0.2, -90.0, -np.inf, -np.inf, -np.inf])
BOUNDS_HI = np.array([math.log(1e4),  2.0,  2.0, math.log(20.0), 6.0, 1.0, 90.0, np.inf, np.inf, np.inf])


def _crop(a, x, y):
    return np.asarray(a[y-HALF:y+HALF+1, x-HALF:x+HALF+1], dtype=float)


def _render(theta, psf, scale, base_amp):
    log_ratio, dx, dy, log_re, n, q, pa, b0, bx, by = theta
    prof = inj.sersic_profile(129, math.exp(log_re), n, q, pa, 4)
    mod = inj.convolve_normalized(prof, psf)
    mod = ndimage.shift(mod, shift=(dy, dx), order=1, mode="constant", cval=0.0, prefilter=False)
    mod = np.maximum(mod, 0.0)
    c = mod.shape[0] // 2
    src = mod[c-HALF:c+HALF+1, c-HALF:c+HALF+1] * (base_amp * math.exp(log_ratio))
    yy, xx = np.indices(src.shape, dtype=float)
    xx = (xx - HALF) / HALF; yy = (yy - HALF) / HALF
    return src + b0 + bx * xx + by * yy


def fit_one(image, err, x, y, psf, pixar_sr, exclude_mask=None):
    data = _crop(image, x, y); sigma = _crop(err, x, y)
    valid = np.isfinite(data) & np.isfinite(sigma) & (sigma > 0)
    if exclude_mask is not None:
        excluded = _crop(np.asarray(exclude_mask, dtype=bool), x, y).astype(bool)
        valid &= ~excluded
    if valid.sum() < 0.8 * data.size:
        return {"optimizer_success": False, "reason": "insufficient_valid_weight_pixels", "valid_fraction": float(valid.mean())}
    base_flux_jy = inj.ab_to_jy(27.5)
    base_amp = base_flux_jy / (1e6 * pixar_sr)
    med = float(np.nanmedian(data[valid]))
    p0 = np.array([0.0, 0.0, 0.0, math.log(5.0), 1.5, 0.7, 0.0, med, 0.0, 0.0])
    def resid(p):
        return ((_render(p, psf, 0.03, base_amp) - data) / sigma)[valid]
    res = optimize.least_squares(resid, p0, bounds=(BOUNDS_LO, BOUNDS_HI), method="trf", loss="linear", x_scale="jac", max_nfev=300)
    p = res.x
    tol = 1e-5
    finite_bounds = np.isfinite(BOUNDS_LO) & np.isfinite(BOUNDS_HI)
    hits = []
    names = ["log_amp_ratio","dx","dy","log_re","n","q","pa","b0","bx","by"]
    for i, name in enumerate(names):
        if finite_bounds[i]:
            span = BOUNDS_HI[i] - BOUNDS_LO[i]
            if p[i] - BOUNDS_LO[i] <= tol * span or BOUNDS_HI[i] - p[i] <= tol * span:
                hits.append(name)
    dof = max(1, int(valid.sum()) - len(p))
    chi2 = float(np.sum(res.fun ** 2))
    amp_total = base_amp * math.exp(float(p[0]))
    flux_jy = amp_total * 1e6 * pixar_sr
    ab = float(-2.5 * math.log10(flux_jy / inj.AB_ZERO_JY)) if flux_jy > 0 else float("nan")
    return {"optimizer_success": bool(res.success), "optimizer_status": int(res.status), "optimizer_message": str(res.message),
            "nfev": int(res.nfev), "valid_fraction": float(valid.mean()), "chi2": chi2, "reduced_chi2_proxy": chi2/dof,
            "bound_hits": hits, "any_bound_hit": bool(hits), "recovered_ab_mag": ab,
            "recovered_dx_pix": float(p[1]), "recovered_dy_pix": float(p[2]), "recovered_re_pix": float(math.exp(p[3])),
            "recovered_re_arcsec": float(math.exp(p[3]) * 0.03), "recovered_n": float(p[4]), "recovered_q": float(p[5]),
            "recovered_pa_deg": float(p[6]), "finite_solution": bool(np.all(np.isfinite(p)) and np.isfinite(chi2))}


def run(injected_fits: Path, injection_summary: Path, out_json: Path):
    summary = json.loads(injection_summary.read_text())
    matrix = summary["matrix"]
    psf, psf_prov = inj.build_stpsf(matrix, float(matrix["pixel_scale_arcsec"]))
    with fits.open(injected_fits) as h:
        err = np.asarray(h["ERR"].data, dtype=float)
        rows = []
        for exp in summary["experiments"]:
            image = np.asarray(h[exp["output_extname"]].data, dtype=float)
            fit = fit_one(image, err, int(exp["x"]), int(exp["y"]), psf, float(summary["pixar_sr"]))
            row = dict(exp); row.update(fit); rows.append(row)
    out = {"claim": "forced-position morphology recovery on synthetic sources injected into a literal real COSMOS-Web mosaic context; not blind detection and not literal survey-source reproduction",
           "n_experiments": len(rows), "patch_pixels": PATCH, "psf_provenance": psf_prov,
           "bounds": {"centroid_offset_pix": [-2,2], "re_pix": [1,20], "n": [0.3,6], "q": [0.2,1], "pa_deg": [-90,90], "amplitude_positive": True},
           "semantics": {"tolman_factor_applied": False, "extra_background_added": False, "source_shot_noise_added": False,
                         "blind_detection_performed": False, "low_snr_failures_retained": True, "bound_hits_retained": True},
           "experiments": rows}
    out_json.parent.mkdir(parents=True, exist_ok=True); out_json.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    return out


def main():
    p = argparse.ArgumentParser(); p.add_argument("--injected-fits", type=Path, required=True)
    p.add_argument("--injection-summary", type=Path, required=True); p.add_argument("--out-json", type=Path, required=True)
    a = p.parse_args(); out = run(a.injected_fits, a.injection_summary, a.out_json)
    print(json.dumps({"n_experiments": out["n_experiments"], "optimizer_success": sum(bool(r.get("optimizer_success")) for r in out["experiments"]),
                      "bound_hits": sum(bool(r.get("any_bound_hit")) for r in out["experiments"])}, indent=2))

if __name__ == "__main__": main()
