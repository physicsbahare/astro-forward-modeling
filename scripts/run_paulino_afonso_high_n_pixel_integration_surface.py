#!/usr/bin/env python3
"""Isolate the high-n fitter-rendering floor in the Paulino-Afonso C2 chain.

The phase-corrected full-chain rerun recovers disk-like n=1 scenes almost
exactly without target noise, but the concentrated n=4 scene remains biased by
roughly 20--26 per cent in Re and n.  This diagnostic does *not* alter the
established fitter or reinterpret its historical benchmark.  Instead it asks a
narrow question: on the same phase-corrected transferred n=4 image, where is
the Re/n objective minimum when the fit template is (a) the established
point-sampled Sersic renderer and (b) a detector-pixel-integrated 4x renderer
matching the truth-generation semantics?

To keep this a renderer diagnostic rather than another optimizer experiment,
centroid and q are fixed to their known noiseless truth.  Flux and constant sky
are profiled linearly at every grid node.  The Re/n grid is declared in code
before seeing the result and no morphology acceptance threshold is introduced.
The exact truth node is included.  A direct-target control is also evaluated at
truth with the pixel-integrated renderer.

This is controlled synthetic-equivalent verification, not a literal
Paulino-Afonso et al. survey reproduction and not production code.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_paulino_afonso_full_chain_califa import (
    CASES,
    OVERSAMPLE,
    TARGET_PIXEL_SCALE,
    TARGET_Z,
    crop_common,
    direct_target,
    transfer_to_target,
)
from verification.paulino_afonso_sersic_floor import (
    _bn,
    _convolved_model,
    _kpc_per_arcsec,
    _psf_sigma_pix,
    _sersic_total_normalization,
    adaptive_stamp_size,
    flux_in_depth_units,
    pixel_noise_from_point_depth,
)

# Pre-declared local surface around the concentrated truth.  Step 0.025 puts the
# exact truth (1.0, 1.0) on the grid while spanning the bias seen in the
# established point-sampled fit.  These are diagnostic coordinates, not pass
# tolerances.
RE_RATIO_GRID = np.arange(0.65, 1.0500001, 0.025)
N_RATIO_GRID = np.arange(0.65, 1.0500001, 0.025)
SKY_BOUND_SIGMA = 5.0
PA_RAD = 0.37


def _central_crop(image: np.ndarray, size: int) -> np.ndarray:
    size = min(int(size), image.shape[0], image.shape[1])
    if size % 2 == 0:
        size -= 1
    y0 = (image.shape[0] - size) // 2
    x0 = (image.shape[1] - size) // 2
    return np.asarray(image[y0:y0 + size, x0:x0 + size], dtype=float)


def _block_sum(image: np.ndarray, factor: int) -> np.ndarray:
    ny, nx = image.shape
    if ny % factor or nx % factor:
        raise RuntimeError("fine grid is not exactly divisible by oversampling factor")
    return image.reshape(ny // factor, factor, nx // factor, factor).sum(axis=(1, 3))


def _pixel_integrated_unit_template(
    shape: tuple[int, int], re_pix: float, n: float, q: float, x0: float, y0: float
) -> np.ndarray:
    """Unit-total-flux analytic Sersic, detector-integrated at 4x, then PSF-convolved."""
    factor = int(OVERSAMPLE)
    offsets = (np.arange(factor, dtype=float) + 0.5) / factor - 0.5
    fy = (np.arange(shape[0], dtype=float)[:, None] + offsets[None, :]).reshape(-1)
    fx = (np.arange(shape[1], dtype=float)[:, None] + offsets[None, :]).reshape(-1)
    yy, xx = np.meshgrid(fy, fx, indexing="ij")

    dx = xx - float(x0)
    dy = yy - float(y0)
    c, s = np.cos(PA_RAD), np.sin(PA_RAD)
    xp = c * dx + s * dy
    yp = -s * dx + c * dy
    r = np.sqrt(xp**2 + (yp / float(q)) ** 2)
    b = _bn(float(n))
    ie = 1.0 / _sersic_total_normalization(float(re_pix), float(n), float(q))
    # Surface brightness evaluated at sub-pixel centers times sub-pixel area in
    # detector-pixel units.  Do not renormalize within the finite stamp: the
    # model parameter retains the same analytic total-flux meaning as the
    # established point-sampled renderer.
    fine = ie * np.exp(-b * ((r / float(re_pix)) ** (1.0 / float(n)) - 1.0)) / factor**2
    fine = gaussian_filter(
        fine,
        _psf_sigma_pix() * factor,
        mode="constant",
        cval=0.0,
        truncate=7.0,
    )
    return _block_sum(fine, factor)


def _point_unit_template(
    shape: tuple[int, int], re_pix: float, n: float, q: float, x0: float, y0: float
) -> np.ndarray:
    return _convolved_model(shape, 1.0, re_pix, n, q, x0, y0, 0.0)


def _profile_flux_and_sky(template: np.ndarray, image: np.ndarray, sigma: float):
    """Profile positive flux and bounded constant sky for a fixed structure."""
    t = np.asarray(template, dtype=float).ravel()
    y = np.asarray(image, dtype=float).ravel()
    A = np.column_stack((t, np.ones_like(t)))
    amp, sky = np.linalg.lstsq(A, y, rcond=None)[0]
    amp = max(float(amp), 1e-12)
    sky_lim = SKY_BOUND_SIGMA * float(sigma)
    sky_clipped = float(np.clip(float(sky), -sky_lim, sky_lim))
    if sky_clipped != float(sky):
        sky = sky_clipped
        denom = float(np.dot(t, t))
        amp = max(float(np.dot(t, y - sky) / max(denom, 1e-300)), 1e-12)
    else:
        sky = float(sky)
    model = amp * template + sky
    resid = model - image
    cost = float(0.5 * np.sum((resid / sigma) ** 2))
    l1 = float(np.sum(np.abs(resid)) / max(np.sum(np.abs(image)), 1e-300))
    return amp, sky, cost, l1


def _evaluate_renderer(
    renderer: str,
    image: np.ndarray,
    true_re_pix: float,
    true_n: float,
    true_q: float,
    cx: float,
    cy: float,
    sigma: float,
):
    rows = []
    for re_ratio in RE_RATIO_GRID:
        re_pix = float(true_re_pix * re_ratio)
        for n_ratio in N_RATIO_GRID:
            n = float(true_n * n_ratio)
            if renderer == "point_sampled":
                template = _point_unit_template(image.shape, re_pix, n, true_q, cx, cy)
            elif renderer == "pixel_integrated_4x":
                template = _pixel_integrated_unit_template(image.shape, re_pix, n, true_q, cx, cy)
            else:
                raise ValueError(renderer)
            amp, sky, cost, l1 = _profile_flux_and_sky(template, image, sigma)
            rows.append({
                "renderer": renderer,
                "re_ratio_grid": float(re_ratio),
                "n_ratio_grid": float(n_ratio),
                "profiled_flux": amp,
                "sky_sigma_units": float(sky / sigma),
                "cost": cost,
                "normalized_l1": l1,
            })
    best = min(rows, key=lambda r: float(r["cost"]))
    truth = min(
        rows,
        key=lambda r: abs(float(r["re_ratio_grid"]) - 1.0) + abs(float(r["n_ratio_grid"]) - 1.0),
    )
    return rows, best, truth


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--z-target", type=float, required=True, choices=list(TARGET_Z))
    args = parser.parse_args()
    z = float(args.z_target)

    case = next(c for c in CASES if str(c["case"]) == "concentrated")
    source_flux = flux_in_depth_units(float(case["source_mag_ab"]))
    transferred, tx, ty, kpc_t, source_equiv, kernel_fwhm, flux_ratio = transfer_to_target(
        case, z, source_flux
    )
    direct = direct_target(case, z, source_flux * flux_ratio, tx, ty, kpc_t)
    transferred, direct = crop_common(transferred, direct)

    true_re_pix = float(case["re_kpc"]) / _kpc_per_arcsec(z) / TARGET_PIXEL_SCALE
    size = adaptive_stamp_size(true_re_pix)
    image = _central_crop(transferred, size)
    direct_image = _central_crop(direct, size)
    ny, nx = image.shape
    cx = 0.5 * (nx - 1)
    cy = 0.5 * (ny - 1)
    sigma = pixel_noise_from_point_depth()

    all_rows = []
    summaries = []
    for renderer in ("point_sampled", "pixel_integrated_4x"):
        rows, best, truth = _evaluate_renderer(
            renderer,
            image,
            true_re_pix,
            float(case["n"]),
            float(case["q"]),
            cx,
            cy,
            sigma,
        )
        for r in rows:
            r.update({"z_target": z, "image_kind": "transferred"})
        all_rows.extend(rows)
        summaries.append({
            "renderer": renderer,
            "best_re_ratio": float(best["re_ratio_grid"]),
            "best_n_ratio": float(best["n_ratio_grid"]),
            "best_cost": float(best["cost"]),
            "best_normalized_l1": float(best["normalized_l1"]),
            "truth_cost": float(truth["cost"]),
            "truth_normalized_l1": float(truth["normalized_l1"]),
            "truth_to_best_cost_ratio": float(truth["cost"] / max(float(best["cost"]), 1e-300)),
        })

    # Direct-target control at exact structural truth.  This is not used to
    # select any grid result; it checks the pixel-integrated model semantics.
    direct_template = _pixel_integrated_unit_template(
        direct_image.shape, true_re_pix, float(case["n"]), float(case["q"]), cx, cy
    )
    d_amp, d_sky, d_cost, d_l1 = _profile_flux_and_sky(direct_template, direct_image, sigma)

    out = Path("benchmark_output/paulino_afonso_2017/high_n_pixel_integration_surface") / (
        "z_" + str(z).replace(".", "p")
    )
    out.mkdir(parents=True, exist_ok=True)
    with (out / "surface.csv").open("w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=list(all_rows[0].keys()))
        w.writeheader(); w.writerows(all_rows)

    payload = {
        "experiment": "C2 concentrated high-n point-vs-pixel-integrated objective surface",
        "scientific_status": "diagnostic only; established fitter record is not replaced",
        "z_target": z,
        "case": str(case["case"]),
        "input_re_kpc": float(case["re_kpc"]),
        "input_n": float(case["n"]),
        "input_q": float(case["q"]),
        "fit_stamp_size": int(image.shape[0]),
        "source_psf_equivalent_at_target_arcsec": float(source_equiv),
        "matching_kernel_fwhm_arcsec": float(kernel_fwhm),
        "grid": {
            "re_ratio_min": float(RE_RATIO_GRID.min()),
            "re_ratio_max": float(RE_RATIO_GRID.max()),
            "re_ratio_step": 0.025,
            "n_ratio_min": float(N_RATIO_GRID.min()),
            "n_ratio_max": float(N_RATIO_GRID.max()),
            "n_ratio_step": 0.025,
        },
        "fixed_for_isolation": "centroid and q fixed to noiseless truth; flux and +/-5 sigma sky profiled linearly",
        "renderers": summaries,
        "direct_target_pixel_integrated_truth_control": {
            "profiled_flux": float(d_amp),
            "sky_sigma_units": float(d_sky / sigma),
            "cost": float(d_cost),
            "normalized_l1": float(d_l1),
        },
        "decision_rule": (
            "Do not tune toward literature. If the point-sampled surface prefers the previously observed low-Re/low-n "
            "region while the 4x pixel-integrated surface moves its minimum to the truth neighborhood and the direct-target "
            "truth control is clean, classify the residual high-n noiseless bias as a fitter-rendering sampling floor. "
            "Then test a pixel-integrated structural fitter in a separate benchmark before interpreting noisy n trends."
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
