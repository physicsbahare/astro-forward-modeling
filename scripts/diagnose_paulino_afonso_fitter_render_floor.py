#!/usr/bin/env python3
"""Diagnose the full-chain structural floor caused by the fitter renderer.

The established CALIFA-like truth path pixel-integrates the source and direct
target observation, while the operational structural fitter currently samples
the intrinsic Sersic law at detector-pixel centres. The dedicated sampling
audit showed that this distinction can be severe for compact/high-n profiles.

This diagnostic keeps the true Re, n and q fixed and asks a narrower question:
how well can the existing point-sampled fitter renderer match each noiseless
full-chain image if only its allowed nuisance freedom (flux, constant sky and
centroid) is used? It compares that residual floor with the already-defined
direct pixel-integrated target image. No morphology parameters, bounds or
optimizer tolerances are altered, and no literature acceptance band is added.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_paulino_afonso_full_chain_califa import (
    CASES,
    TARGET_Z,
    crop_common,
    direct_target,
    transfer_to_target,
)
from verification.paulino_afonso_sersic_floor import (
    PIXEL_SCALE_ARCSEC,
    _convolved_model,
    _kpc_per_arcsec,
    adaptive_stamp_size,
    flux_in_depth_units,
    pixel_noise_from_point_depth,
)

OUT = Path("benchmark_output/paulino_afonso_2017/fitter_render_floor")
CENTROID_LIMIT = 2.0
COARSE_STEP = 0.25
REFINE_HALF_WIDTH = 0.25
REFINE_STEP = 0.05
SKY_LIMIT_SIGMA = 5.0


def central_crop(image: np.ndarray, size: int) -> np.ndarray:
    size = min(int(size), image.shape[0], image.shape[1])
    if size % 2 == 0:
        size -= 1
    y0 = (image.shape[0] - size) // 2
    x0 = (image.shape[1] - size) // 2
    return np.asarray(image[y0:y0 + size, x0:x0 + size], dtype=float)


def fit_linear_nuisance(template: np.ndarray, image: np.ndarray, sigma: float):
    """Fit positive template amplitude and bounded constant sky by least squares."""
    m = np.asarray(template, dtype=float).ravel()
    d = np.asarray(image, dtype=float).ravel()
    n = float(m.size)
    mm = float(np.dot(m, m))
    ms = float(np.sum(m))
    md = float(np.dot(m, d))
    ds = float(np.sum(d))
    mat = np.array([[mm, ms], [ms, n]], dtype=float)
    rhs = np.array([md, ds], dtype=float)
    try:
        amp, sky = np.linalg.solve(mat, rhs)
    except np.linalg.LinAlgError:
        amp, sky = 1.0, 0.0
    amp = max(float(amp), 1e-12)
    limit = SKY_LIMIT_SIGMA * float(sigma)
    sky = float(np.clip(sky, -limit, limit))
    amp = max(float(np.dot(m, d - sky) / max(mm, 1e-300)), 1e-12)
    model = amp * np.asarray(template, dtype=float) + sky
    residual = model - image
    l2 = float(np.sum((residual / sigma) ** 2))
    l1 = float(np.sum(np.abs(residual)) / max(np.sum(np.abs(image)), 1e-300))
    return amp, sky, l2, l1


def offset_grid(center_x: float, center_y: float, half: float, step: float):
    xs = np.arange(center_x - half, center_x + half + 0.5 * step, step)
    ys = np.arange(center_y - half, center_y + half + 0.5 * step, step)
    for dx in xs:
        for dy in ys:
            if abs(dx) <= CENTROID_LIMIT + 1e-12 and abs(dy) <= CENTROID_LIMIT + 1e-12:
                yield float(dx), float(dy)


def best_point_sampled_at_true_structure(
    image: np.ndarray,
    re_pix: float,
    n: float,
    q: float,
    sigma: float,
):
    ny, nx = image.shape
    cx = 0.5 * (nx - 1)
    cy = 0.5 * (ny - 1)
    best = None

    def evaluate(dx: float, dy: float):
        template = _convolved_model(
            image.shape, 1.0, float(re_pix), float(n), float(q), cx + dx, cy + dy, 0.0
        )
        amp, sky, l2, l1 = fit_linear_nuisance(template, image, sigma)
        return {"dx": dx, "dy": dy, "amp": amp, "sky": sky, "l2": l2, "l1": l1}

    for dx, dy in offset_grid(0.0, 0.0, CENTROID_LIMIT, COARSE_STEP):
        row = evaluate(dx, dy)
        if best is None or row["l2"] < best["l2"]:
            best = row

    assert best is not None
    for dx, dy in offset_grid(best["dx"], best["dy"], REFINE_HALF_WIDTH, REFINE_STEP):
        row = evaluate(dx, dy)
        if row["l2"] < best["l2"]:
            best = row
    return best


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sigma = pixel_noise_from_point_depth()
    rows: list[dict[str, object]] = []

    for z0 in TARGET_Z:
        z = float(z0)
        kpc_arcsec = _kpc_per_arcsec(z)
        for case in CASES:
            source_flux = flux_in_depth_units(float(case["source_mag_ab"]))
            transferred, tx, ty, kpc_t, source_equiv, kernel_fwhm, flux_ratio = transfer_to_target(
                case, z, source_flux
            )
            expected_target_flux = source_flux * flux_ratio
            direct = direct_target(case, z, expected_target_flux, tx, ty, kpc_t)
            transferred, direct = crop_common(transferred, direct)

            true_re_pix = float(case["re_kpc"]) / kpc_arcsec / PIXEL_SCALE_ARCSEC
            size = adaptive_stamp_size(true_re_pix)
            image = central_crop(transferred, size)
            direct_fit = central_crop(direct, image.shape[0])

            direct_amp, direct_sky, direct_l2, direct_l1 = fit_linear_nuisance(
                direct_fit, image, sigma
            )
            point = best_point_sampled_at_true_structure(
                image, true_re_pix, float(case["n"]), float(case["q"]), sigma
            )

            rows.append(
                {
                    "case": str(case["case"]),
                    "z_target": z,
                    "input_re_kpc": float(case["re_kpc"]),
                    "input_re_pix": float(true_re_pix),
                    "input_n": float(case["n"]),
                    "input_q": float(case["q"]),
                    "fit_stamp_size": int(image.shape[0]),
                    "source_psf_equivalent_at_target_arcsec": float(source_equiv),
                    "matching_kernel_fwhm_arcsec": float(kernel_fwhm),
                    "direct_target_best_amplitude": float(direct_amp),
                    "direct_target_sky_sigma_units": float(direct_sky / sigma),
                    "direct_target_normalized_l1": float(direct_l1),
                    "direct_target_chi2": float(direct_l2),
                    "point_truth_structure_best_flux": float(point["amp"]),
                    "point_truth_structure_sky_sigma_units": float(point["sky"] / sigma),
                    "point_truth_structure_centroid_dx_pix": float(point["dx"]),
                    "point_truth_structure_centroid_dy_pix": float(point["dy"]),
                    "point_truth_structure_centroid_error_pix": float(np.hypot(point["dx"], point["dy"])),
                    "point_truth_structure_normalized_l1": float(point["l1"]),
                    "point_truth_structure_chi2": float(point["l2"]),
                    "point_l1_over_direct_l1": float(point["l1"] / max(direct_l1, 1e-300)),
                }
            )

    with (OUT / "rows.csv").open("w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    by_n = []
    for n0 in sorted({float(r["input_n"]) for r in rows}):
        s = [r for r in rows if float(r["input_n"]) == n0]
        by_n.append(
            {
                "input_n": n0,
                "n_rows": len(s),
                "median_direct_target_normalized_l1": float(np.median([r["direct_target_normalized_l1"] for r in s])),
                "median_point_truth_structure_normalized_l1": float(np.median([r["point_truth_structure_normalized_l1"] for r in s])),
                "max_point_truth_structure_normalized_l1": float(np.max([r["point_truth_structure_normalized_l1"] for r in s])),
                "median_point_centroid_error_pix": float(np.median([r["point_truth_structure_centroid_error_pix"] for r in s])),
                "max_point_centroid_error_pix": float(np.max([r["point_truth_structure_centroid_error_pix"] for r in s])),
            }
        )

    payload = {
        "experiment": "Paulino-Afonso C2 full-chain fitter render floor",
        "scientific_status": "diagnostic only; fixed true Re/n/q, no literature tuning",
        "n_rows": len(rows),
        "centroid_search": {
            "allowed_bound_pix": CENTROID_LIMIT,
            "coarse_step_pix": COARSE_STEP,
            "refine_half_width_pix": REFINE_HALF_WIDTH,
            "refine_step_pix": REFINE_STEP,
        },
        "nuisance_parameters": "positive flux plus constant sky bounded to the established +/-5 sigma range",
        "by_input_n": by_n,
        "rows": rows,
        "decision_rule": (
            "If the point-sampled renderer has a materially larger residual floor than the direct pixel-integrated target, "
            "especially together with nuisance centroid displacement, the next structural comparison must use a separate "
            "pixel-integrated fitter renderer. Do not rewrite or retune the existing benchmark record."
        ),
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
