#!/usr/bin/env python3
"""Gate D1n-f: paired-difference PSF-mismatch oracle for two frozen AB=26 failures."""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage, optimize, signal
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rec = _load("gate_d_forced", "scripts/run_gate_d_cosmosweb_forced_recovery.py")
pub = _load("gate_d_published_psf", "scripts/run_gate_d_cosmosweb_published_empirical_psf.py")
inj = rec.inj

PSF_NAMES = ("stpsf", "broad", "global", "narrow")
SELECTED = (
    ("near_source_2_5", 0, 168, 66),
    ("relatively_isolated_ge30", 1, 69, 195),
)
TARGET_MAX_NFEV = 500
TARGET_NAMES = ["log_amp_ratio", "dx", "dy", "log_re", "n", "q", "pa", "b0", "bx", "by"]


def signed_normalize_psf(psf: np.ndarray) -> np.ndarray:
    p = np.asarray(psf, dtype=float)
    if p.ndim != 2 or not np.all(np.isfinite(p)):
        raise ValueError("PSF must be finite and two-dimensional")
    total = float(p.sum())
    if not np.isfinite(total) or total <= 0:
        raise ValueError("PSF signed sum must be positive")
    return p / total


def signed_convolve_normalized(profile: np.ndarray, psf: np.ndarray) -> np.ndarray:
    p = signed_normalize_psf(psf)
    model = signal.fftconvolve(np.asarray(profile, dtype=float), p, mode="same")
    total = float(model.sum())
    if not np.all(np.isfinite(model)) or not np.isfinite(total) or total <= 0:
        raise ValueError("invalid signed PSF convolution")
    return model / total


def render(theta: np.ndarray, psf: np.ndarray, base_amp: float) -> np.ndarray:
    log_ratio, dx, dy, log_re, n, q, pa, b0, bx, by = [float(v) for v in theta]
    profile = inj.sersic_profile(129, math.exp(log_re), n, q, pa, 4)
    model = signed_convolve_normalized(profile, psf)
    model = ndimage.shift(model, shift=(dy, dx), order=1, mode="constant", cval=0.0, prefilter=False)
    c = model.shape[0] // 2
    source = model[c-rec.HALF:c+rec.HALF+1, c-rec.HALF:c+rec.HALF+1]
    source = source * (base_amp * math.exp(log_ratio))
    yy, xx = np.indices(source.shape, dtype=float)
    xx = (xx - rec.HALF) / rec.HALF
    yy = (yy - rec.HALF) / rec.HALF
    return source + b0 + bx * xx + by * yy


def bound_hits(values: np.ndarray) -> list[str]:
    tol = 1e-5
    hits = []
    for i, name in enumerate(TARGET_NAMES):
        if np.isfinite(rec.BOUNDS_LO[i]) and np.isfinite(rec.BOUNDS_HI[i]):
            span = rec.BOUNDS_HI[i] - rec.BOUNDS_LO[i]
            if values[i] - rec.BOUNDS_LO[i] <= tol * span or rec.BOUNDS_HI[i] - values[i] <= tol * span:
                hits.append(name)
    return hits


def fit_difference(data: np.ndarray, sigma: np.ndarray, psf: np.ndarray, pixar_sr: float) -> dict:
    valid = np.isfinite(data) & np.isfinite(sigma) & (sigma > 0)
    if valid.sum() < 0.8 * data.size:
        return {"optimizer_success": False, "finite_solution": False,
                "reason": "insufficient_valid_weight_pixels", "valid_fraction": float(valid.mean())}
    base_flux_jy = inj.ab_to_jy(27.5)
    base_amp = base_flux_jy / (1e6 * float(pixar_sr))
    med = float(np.nanmedian(data[valid]))
    p0 = np.array([0.0, 0.0, 0.0, math.log(5.0), 1.5, 0.7, 0.0, med, 0.0, 0.0])

    def residual(p):
        return ((render(p, psf, base_amp) - data) / sigma)[valid]

    result = optimize.least_squares(residual, p0, bounds=(rec.BOUNDS_LO, rec.BOUNDS_HI),
        method="trf", loss="linear", x_scale="jac", max_nfev=TARGET_MAX_NFEV)
    p = result.x
    chi2 = float(np.sum(result.fun ** 2))
    dof = max(1, int(valid.sum()) - len(p))
    hits = bound_hits(p)
    amp_total = base_amp * math.exp(float(p[0]))
    flux_jy = amp_total * 1e6 * float(pixar_sr)
    recovered_ab = float(-2.5 * math.log10(flux_jy / inj.AB_ZERO_JY)) if flux_jy > 0 else float("nan")
    return {"optimizer_success": bool(result.success), "optimizer_status": int(result.status),
        "optimizer_message": str(result.message), "nfev": int(result.nfev),
        "valid_fraction": float(valid.mean()), "chi2": chi2, "reduced_chi2_proxy": chi2 / dof,
        "target_bound_hits": hits, "any_bound_hit": bool(hits),
        "finite_solution": bool(np.all(np.isfinite(p)) and np.isfinite(chi2)),
        "recovered_ab_mag": recovered_ab, "delta_mag": recovered_ab - 26.0,
        "recovered_dx_pix": float(p[1]), "recovered_dy_pix": float(p[2]),
        "centroid_excursion_pix": float(math.hypot(float(p[1]), float(p[2]))),
        "recovered_re_pix": float(math.exp(p[3])), "recovered_re_arcsec": float(math.exp(p[3]) * 0.03),
        "recovered_n": float(p[4]), "recovered_q": float(p[5]), "recovered_pa_deg": float(p[6])}


def load_psfs(psf_dir: Path, matrix: dict) -> tuple[dict[str, np.ndarray], dict]:
    scale = float(matrix["pixel_scale_arcsec"])
    stpsf, stpsf_prov = inj.build_stpsf(matrix, scale)
    psfs = {"stpsf": signed_normalize_psf(stpsf)}
    provenance = {"stpsf": {"source": "frozen Gate-D STPSF", "negative_absolute_fraction": 0.0,
        "provenance": stpsf_prov}}
    for name in pub.NAMES:
        path = psf_dir / pub.FILES[name]
        raw, header, hdu = pub.first_image(path)
        source_scale, source_scale_provenance = pub.infer_scale_arcsec(header)
        common = pub.resample_flux(raw, source_scale, scale)
        normalized = signed_normalize_psf(common)
        absolute = float(np.abs(normalized).sum())
        psfs[name] = normalized
        provenance[name] = {"file": pub.FILES[name], "sha256": pub.sha256(path), "hdu": hdu,
            "source_pixel_scale_arcsec": float(source_scale),
            "source_pixel_scale_provenance": source_scale_provenance,
            "comparison_pixel_scale_arcsec": scale,
            "signed_sum_after_resample_and_normalization": float(normalized.sum()),
            "negative_pixel_fraction": float((normalized < 0).mean()),
            "negative_absolute_fraction": float(np.abs(normalized[normalized < 0]).sum() / absolute) if absolute else None,
            "signed_values_preserved": True}
    return psfs, provenance


def run(injected_fits: Path, injection_summary: Path, psf_dir: Path, out_json: Path) -> dict:
    summary = json.loads(injection_summary.read_text())
    matrix = summary["matrix"]
    psfs, psf_provenance = load_psfs(psf_dir, matrix)
    selected_keys = {(cls, idx): (x, y) for cls, idx, x, y in SELECTED}
    experiments = {(str(e["class"]), int(e["index"])): e for e in summary["experiments"]
        if float(e["ab_mag"]) == 26.0 and (str(e["class"]), int(e["index"])) in selected_keys}
    if set(experiments) != set(selected_keys):
        raise RuntimeError(f"frozen selected rows missing: expected {set(selected_keys)}, got {set(experiments)}")

    rows = []
    with fits.open(injected_fits, mode="readonly") as h:
        orig = np.asarray(h["SCI_ORIG"].data, dtype=float)
        err = np.asarray(h["ERR"].data, dtype=float)
        for cls, idx, x, y in SELECTED:
            exp = experiments[(cls, idx)]
            if int(exp["x"]) != x or int(exp["y"]) != y:
                raise RuntimeError("frozen D1m failure coordinate changed")
            image = np.asarray(h[exp["output_extname"]].data, dtype=float)
            difference = rec._crop(image - orig, x, y)
            sigma = rec._crop(err, x, y)
            for psf_name in PSF_NAMES:
                fit = fit_difference(difference, sigma, psfs[psf_name], float(summary["pixar_sr"]))
                rows.append({"class": cls, "index": idx, "x": x, "y": y, "ab_mag": 26.0,
                    "output_extname": exp["output_extname"], "recovery_psf": psf_name, **fit})

    out = {"claim": "paired-difference PSF-mismatch oracle on the two frozen catastrophic AB=26 D1m rows; published OBS_084 PSFs are intentionally used as crossed recovery models against the STPSF-injected truth and are not claimed to be literal DR1 mosaic truth",
        "selected_rows": [{"class": c, "index": i, "x": x, "y": y,
            "selection_reason": "two largest absolute D1m AB=26 delta-mag rows"} for c, i, x, y in SELECTED],
        "n_rows": len(rows), "recovery_psfs": list(PSF_NAMES), "psf_provenance": psf_provenance,
        "target_truth": {"ab_mag": 26.0, "re_arcsec": 0.18, "sersic_n": 1.0, "q": 0.65,
            "centroid_offset_pix": [0.0, 0.0]},
        "target_bounds": {"centroid_offset_pix": [-2, 2], "re_pix": [1, 20], "n": [0.3, 6],
            "q": [0.2, 1], "pa_deg": [-90, 90], "amplitude_positive": True},
        "optimizer": {"implementation": "scipy.optimize.least_squares", "method": "trf", "loss": "linear",
            "x_scale": "jac", "max_nfev": TARGET_MAX_NFEV},
        "semantics": {"paired_difference_used": True, "real_scene_contamination_removed": True,
            "published_psfs_are_crossed_mismatch_models": True, "published_psfs_claimed_literal_mosaic_truth": False,
            "signed_published_psf_values_preserved": True, "psf_sharpening_performed": False,
            "deconvolution_performed": False, "noise_added": False, "err_modified": False, "wht_modified": False,
            "tolman_factor_applied": False, "target_bounds_changed": False, "optimizer_convergence_relaxed": False,
            "acceptance_threshold_defined": False, "bound_hits_retained": True, "optimizer_failures_retained": True},
        "rows": rows}
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--injected-fits", type=Path, required=True)
    p.add_argument("--injection-summary", type=Path, required=True)
    p.add_argument("--psf-dir", type=Path, required=True)
    p.add_argument("--out-json", type=Path, required=True)
    a = p.parse_args()
    out = run(a.injected_fits, a.injection_summary, a.psf_dir, a.out_json)
    print(json.dumps({"n_rows": out["n_rows"],
        "optimizer_success": sum(bool(r.get("optimizer_success")) for r in out["rows"]),
        "bound_hits": sum(bool(r.get("any_bound_hit")) for r in out["rows"])}, indent=2))


if __name__ == "__main__":
    main()
