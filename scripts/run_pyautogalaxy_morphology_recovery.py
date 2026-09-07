#!/usr/bin/env python3
"""B9b: common-scene morphology recovery using independent and PyAutoGalaxy renderers."""
from __future__ import annotations
import argparse, importlib.metadata, json, math
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.signal import convolve2d
from scipy.special import gamma, gammaincinv
import autogalaxy as ag

AG_VERSION = "2026.8.14.1"
AA_VERSION = "2026.8.14.1"
SHAPE = (81, 81)
PIXEL_SCALE = 1.0
ANGLE = 37.0
PSF_SIGMA = 1.2
PSF_SIZE = 9
CROP = PSF_SIZE // 2
TRUTH_CENTRE = (0.35, -0.25)
TRUTH_Q = 0.6
TRUTH_RE = 8.0
TRUTH_IE = 0.03
SCENES = (
    {"name": "n1", "n": 1.0},
    {"name": "n4", "n": 4.0},
)
STARTS = (
    {"label": "balanced", "p": [0.0, 0.0, 0.70, 2.0, 7.0, 0.025]},
    {"label": "compact", "p": [0.60, -0.60, 0.45, 0.8, 4.0, 0.060]},
    {"label": "extended", "p": [-0.50, 0.50, 0.85, 4.5, 13.0, 0.012]},
)
LOW = np.array([-1.5, -1.5, 0.25, 0.5, 2.0, 0.003], dtype=float)
HIGH = np.array([1.5, 1.5, 0.95, 6.0, 20.0, 0.2], dtype=float)


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def configuration():
    return {
        "stage": "B9b PyAutoGalaxy common-scene morphology recovery",
        "autogalaxy_version": AG_VERSION,
        "autoarray_version": AA_VERSION,
        "shape": list(SHAPE), "pixel_scale": PIXEL_SCALE, "angle_deg_fixed": ANGLE,
        "truth_centre_yx": list(TRUTH_CENTRE), "truth_q": TRUTH_Q,
        "truth_re": TRUTH_RE, "truth_ie": TRUTH_IE,
        "scenes": list(SCENES), "starts": list(STARTS),
        "bounds": {"centre_yx": [-1.5, 1.5], "q": [0.25, 0.95], "n": [0.5, 6.0], "re": [2.0, 20.0], "ie": [0.003, 0.2]},
        "optimizer": {"name": "scipy.optimize.least_squares", "max_nfev": 120, "ftol": 1e-9, "xtol": 1e-9, "gtol": 1e-9},
        "psf_sigma_pixels": PSF_SIGMA, "psf_size": PSF_SIZE,
        "objective": "central crop excluding four-pixel PSF radius; full-frame residuals retained",
        "acceptance": "completeness/finiteness/algebra only; no morphology recovery band",
    }


def gaussian_psf():
    ax = np.arange(PSF_SIZE, dtype=float) - PSF_SIZE // 2
    yy, xx = np.meshgrid(ax, ax, indexing="ij")
    p = np.exp(-0.5 * (xx * xx + yy * yy) / PSF_SIGMA**2)
    return p / p.sum()


def unpack(p):
    return {"cy": float(p[0]), "cx": float(p[1]), "q": float(p[2]), "n": float(p[3]), "re": float(p[4]), "ie": float(p[5])}


def analytic_total_flux(n, re, ie):
    bn = float(gammaincinv(2.0 * n, 0.5))
    return float(ie * 2.0 * math.pi * n * re**2 * math.exp(bn) * gamma(2.0 * n) * bn ** (-2.0 * n))


def analytic_raw(grid_native, p):
    d = unpack(p)
    y = np.asarray(grid_native[..., 0], dtype=float) - d["cy"]
    x = np.asarray(grid_native[..., 1], dtype=float) - d["cx"]
    phi = math.radians(ANGLE)
    x_major = x * math.cos(phi) + y * math.sin(phi)
    y_minor = -x * math.sin(phi) + y * math.cos(phi)
    r = math.sqrt(d["q"]) * np.sqrt(x_major**2 + (y_minor / d["q"]) ** 2)
    bn = float(gammaincinv(2.0 * d["n"], 0.5))
    return d["ie"] * np.exp(-bn * ((r / d["re"]) ** (1.0 / d["n"]) - 1.0))


def independent_model(grid_native, psf, p):
    raw = analytic_raw(grid_native, p)
    return raw, convolve2d(raw, psf, mode="same", boundary="fill", fillvalue=0.0)


def ag_model(grid, convolver, p):
    d = unpack(p)
    profile = ag.lp.Sersic(
        centre=(d["cy"], d["cx"]),
        ell_comps=ag.convert.ell_comps_from(axis_ratio=d["q"], angle=ANGLE),
        intensity=d["ie"], effective_radius=d["re"], sersic_index=d["n"],
    )
    raw = np.asarray(profile.image_2d_from(grid=grid).native, dtype=float)
    conv = np.asarray(profile.unmasked_blurred_image_2d_from(grid=grid, psf=convolver).native, dtype=float)
    return raw, conv


def near_bounds(p):
    span = HIGH - LOW
    return [name for name, val, lo, hi, sp in zip(["cy","cx","q","n","re","ie"], p, LOW, HIGH, span) if min(abs(val-lo), abs(val-hi)) <= 1e-5 * max(1.0, sp)]


def fit_one(renderer, data, grid_native, grid, psf, convolver, start):
    sl = (slice(CROP, -CROP), slice(CROP, -CROP))
    def model(p):
        return independent_model(grid_native, psf, p) if renderer == "independent" else ag_model(grid, convolver, p)
    def residual(p):
        return (model(p)[1][sl] - data[sl]).ravel()
    p0 = np.asarray(start["p"], dtype=float)
    initial_raw, initial_conv = model(p0)
    initial_sse = float(np.sum((initial_conv[sl] - data[sl])**2))
    result = least_squares(residual, p0, bounds=(LOW, HIGH), max_nfev=120, ftol=1e-9, xtol=1e-9, gtol=1e-9)
    p = np.asarray(result.x, dtype=float)
    raw, conv = model(p)
    resid = data - conv
    d = unpack(p)
    row = {
        "renderer": renderer, "start_label": start["label"], "success": bool(result.success),
        "status": int(result.status), "message": str(result.message), "nfev": int(result.nfev),
        "initial_interior_sse": initial_sse, "interior_sse": float(np.sum(resid[sl]**2)),
        "full_sse": float(np.sum(resid**2)), "params": d, "bound_hits": near_bounds(p),
        "analytic_total_flux": analytic_total_flux(d["n"], d["re"], d["ie"]),
        "raw_stamp_sum": float(raw.sum()), "convolved_stamp_sum": float(conv.sum()),
        "finite": bool(np.isfinite(raw).all() and np.isfinite(conv).all() and np.isfinite(p).all()),
    }
    return row, raw, conv, resid


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", type=Path, required=True); args = ap.parse_args()
    assert importlib.metadata.version("autogalaxy") == AG_VERSION
    assert importlib.metadata.version("autoarray") == AA_VERSION
    out = args.out; out.mkdir(parents=True, exist_ok=True); dump(out / "config.json", configuration())
    psf = gaussian_psf(); kernel = ag.Array2D.no_mask(values=psf, pixel_scales=PIXEL_SCALE)
    convolver = ag.Convolver(kernel=kernel, use_fft=False, normalize=False)
    grid = ag.Grid2D.uniform(shape_native=SHAPE, pixel_scales=PIXEL_SCALE, over_sample_size=1)
    grid_native = np.asarray(grid.native)
    arrays = {"psf": psf, "grid_native": grid_native}; attempts = []; winners = []; comparisons = []
    for scene in SCENES:
        truth = np.array([TRUTH_CENTRE[0], TRUTH_CENTRE[1], TRUTH_Q, scene["n"], TRUTH_RE, TRUTH_IE], dtype=float)
        truth_raw, data = independent_model(grid_native, psf, truth)
        arrays[f"{scene['name']}__truth_raw"] = truth_raw; arrays[f"{scene['name']}__data"] = data
        scene_winners = {}
        for renderer in ("independent", "pyautogalaxy"):
            local = []
            for start in STARTS:
                row, raw, conv, resid = fit_one(renderer, data, grid_native, grid, psf, convolver, start)
                row["scene"] = scene["name"]; attempts.append(row); local.append((row, raw, conv, resid))
            finite = [x for x in local if x[0]["finite"]]
            if not finite: continue
            win = min(finite, key=lambda x: x[0]["interior_sse"])
            wrow = dict(win[0]); wrow["winner"] = True; winners.append(wrow); scene_winners[renderer] = wrow
            arrays[f"{scene['name']}__{renderer}__winner_raw"] = win[1]
            arrays[f"{scene['name']}__{renderer}__winner_model"] = win[2]
            arrays[f"{scene['name']}__{renderer}__winner_residual"] = win[3]
        truth_flux = analytic_total_flux(scene["n"], TRUTH_RE, TRUTH_IE)
        comp = {"scene": scene["name"], "truth": {"cy": TRUTH_CENTRE[0], "cx": TRUTH_CENTRE[1], "q": TRUTH_Q, "n": scene["n"], "re": TRUTH_RE, "ie": TRUTH_IE, "analytic_total_flux": truth_flux}}
        if len(scene_winners) == 2:
            a = scene_winners["independent"]; b = scene_winners["pyautogalaxy"]
            comp["winner_difference_pyautogalaxy_minus_independent"] = {k: float(b["params"][k] - a["params"][k]) for k in ["cy","cx","q","n","re","ie"]}
            comp["flux_difference"] = float(b["analytic_total_flux"] - a["analytic_total_flux"])
            comp["interior_sse_ratio"] = float(b["interior_sse"] / max(a["interior_sse"], 1e-300))
        comparisons.append(comp)
    np.savez_compressed(out / "arrays.npz", **arrays)
    summary = {"config": configuration(), "psf_sum": float(psf.sum()), "attempts": attempts, "winners": winners, "comparisons": comparisons}
    dump(out / "summary.json", summary); print(json.dumps(summary, indent=2))

if __name__ == "__main__": main()
