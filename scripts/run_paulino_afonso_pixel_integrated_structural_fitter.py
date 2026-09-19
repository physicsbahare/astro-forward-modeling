#!/usr/bin/env python3
"""Test a pixel-integrated structural fitter on the C2 concentrated high-n scene.

This follows the objective-surface diagnostic showing that the established
point-sampled fitter creates a low-Re/low-n minimum for the phase-corrected
noiseless n=4 full-chain image, while a 4x detector-pixel-integrated template
moves the structural minimum back to the truth neighborhood.

This script changes only the model-rendering semantics in a separate diagnostic:
all structural fit bounds, generic multistart locations, 3-point finite-difference
Jacobian, x_scale='jac', and lowest-cost winner rule are retained from the
established noiseless full-chain morphology benchmark.  The historical fitter
record is not overwritten and no acceptance tolerance is introduced.

Only the concentrated n=4 case is fitted here because it is the known sampling
blocker.  If this operational free-centroid/free-q pixel-integrated fit is
numerically clean across the four target redshifts, the next scientific step is
to expand the same fitter to the full single-Sersic truth set before returning
to noisy morphology interpretation.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_paulino_afonso_full_chain_califa import (
    CASES,
    TARGET_PIXEL_SCALE,
    TARGET_Z,
    transfer_to_target,
)
from scripts.run_paulino_afonso_high_n_pixel_integration_surface import (
    _pixel_integrated_unit_template,
    _profile_flux_and_sky,
)
from verification.paulino_afonso_sersic_floor import (
    _kpc_per_arcsec,
    adaptive_stamp_size,
    flux_in_depth_units,
    mag_from_depth_units,
    pixel_noise_from_point_depth,
)

START_N = (1.0, 2.5, 5.5, 7.0)
START_RE_MULTIPLIER_OF_ESTIMATE = (0.8, 1.2)
INITIAL_RE_MULTIPLIER = 1.08
INITIAL_FLUX_MULTIPLIER = 0.93
INITIAL_Q_OFFSET = 0.04
MAX_NFEV = 1800


def _q_to_u(q: float) -> float:
    qmin, qmax = 0.15, 1.0
    t = np.clip((q - qmin) / (qmax - qmin), 1e-8, 1.0 - 1e-8)
    return float(np.log(t / (1.0 - t)))


def _u_to_q(u: float) -> float:
    qmin, qmax = 0.15, 1.0
    t = 1.0 / (1.0 + np.exp(-u))
    return float(qmin + (qmax - qmin) * t)


def _central_crop(image: np.ndarray, size: int) -> np.ndarray:
    size = min(int(size), image.shape[0], image.shape[1])
    if size % 2 == 0:
        size -= 1
    y0 = (image.shape[0] - size) // 2
    x0 = (image.shape[1] - size) // 2
    return np.asarray(image[y0:y0 + size, x0:x0 + size], dtype=float)


def _model(shape, total_flux, re_pix, n, q, x0, y0, sky):
    return (
        float(total_flux)
        * _pixel_integrated_unit_template(shape, float(re_pix), float(n), float(q), float(x0), float(y0))
        + float(sky)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--z-target", type=float, required=True, choices=list(TARGET_Z))
    args = parser.parse_args()
    z = float(args.z_target)

    case = next(c for c in CASES if str(c["case"]) == "concentrated")
    sigma = pixel_noise_from_point_depth()
    kpc_arcsec = _kpc_per_arcsec(z)
    source_flux = flux_in_depth_units(float(case["source_mag_ab"]))
    transferred, _, _, _, source_equiv, kernel_fwhm, flux_ratio = transfer_to_target(case, z, source_flux)

    true_re_pix = float(case["re_kpc"]) / kpc_arcsec / TARGET_PIXEL_SCALE
    image = _central_crop(transferred, adaptive_stamp_size(true_re_pix))
    ny, nx = image.shape
    cx = 0.5 * (nx - 1)
    cy = 0.5 * (ny - 1)
    transferred_flux = float(np.sum(image))

    # Objective floor at exact structural truth with flux and sky profiled.
    truth_template = _pixel_integrated_unit_template(
        image.shape,
        true_re_pix,
        float(case["n"]),
        float(case["q"]),
        cx,
        cy,
    )
    truth_amp, truth_sky, truth_cost, truth_l1 = _profile_flux_and_sky(truth_template, image, sigma)

    ire = true_re_pix * INITIAL_RE_MULTIPLIER
    iflux = max(transferred_flux, 1e-12) * INITIAL_FLUX_MULTIPLIER
    iq = min(0.95, max(0.2, float(case["q"]) + INITIAL_Q_OFFSET))

    lower = np.array([np.log(1e-8), np.log(0.15), np.log(0.2), -12.0, -2.0, -2.0, -5.0])
    upper = np.array([np.log(1e8), np.log(120.0), np.log(8.0), 12.0, 2.0, 2.0, 5.0])

    def decode(p):
        return (
            float(np.exp(p[0])),
            float(np.exp(p[1])),
            float(np.exp(p[2])),
            _u_to_q(float(p[3])),
            cx + float(p[4]),
            cy + float(p[5]),
            float(p[6]) * sigma,
        )

    def residual(p):
        return ((_model(image.shape, *decode(p)) - image) / sigma).ravel()

    rows = []
    for rm in START_RE_MULTIPLIER_OF_ESTIMATE:
        for ns in START_N:
            p0 = np.array([
                np.log(max(iflux, 1e-12)),
                np.log(max(ire * rm, 0.2)),
                np.log(ns),
                _q_to_u(iq),
                0.0,
                0.0,
                0.0,
            ])
            result = least_squares(
                residual,
                p0,
                bounds=(lower, upper),
                method="trf",
                jac="3-point",
                x_scale="jac",
                ftol=1e-9,
                xtol=1e-9,
                gtol=1e-9,
                max_nfev=MAX_NFEV,
            )
            rf, rr, rn, rq, rx, ry, rsky = decode(result.x)
            rows.append({
                "z_target": z,
                "case": str(case["case"]),
                "start_re_multiplier_of_estimate": float(rm),
                "start_n": float(ns),
                "success": bool(result.success),
                "status": int(result.status),
                "nfev": int(result.nfev),
                "cost": float(result.cost),
                "optimality": float(result.optimality),
                "input_re_kpc": float(case["re_kpc"]),
                "input_n": float(case["n"]),
                "input_q": float(case["q"]),
                "recovered_re_kpc": float(rr * TARGET_PIXEL_SCALE * kpc_arcsec),
                "re_ratio": float(rr / true_re_pix),
                "recovered_n": float(rn),
                "n_ratio": float(rn / float(case["n"])),
                "recovered_q": float(rq),
                "q_difference": float(rq - float(case["q"])),
                "centroid_error_pixels": float(np.hypot(rx - cx, ry - cy)),
                "recovered_flux": float(rf),
                "recovered_mag": float(mag_from_depth_units(rf)),
                "sky_sigma_units": float(rsky / sigma),
                "hit_re_lower_bound": bool(rr <= 0.15 * (1 + 5e-5)),
                "hit_re_upper_bound": bool(rr >= 120.0 * (1 - 5e-5)),
                "hit_n_lower_bound": bool(rn <= 0.2 * (1 + 5e-5)),
                "hit_n_upper_bound": bool(rn >= 8.0 * (1 - 5e-5)),
            })

    best = min(rows, key=lambda r: float(r["cost"]))
    out = Path("benchmark_output/paulino_afonso_2017/pixel_integrated_structural_fitter") / (
        "z_" + str(z).replace(".", "p")
    )
    out.mkdir(parents=True, exist_ok=True)
    with (out / "all_starts.csv").open("w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    payload = {
        "experiment": "C2 operational 4x pixel-integrated structural fitter on concentrated high-n scene",
        "scientific_status": "separate verification diagnostic; historical point-sampled fitter record retained",
        "z_target": z,
        "n_starts": len(rows),
        "jacobian_scheme": "3-point",
        "x_scale": "jac",
        "max_nfev": MAX_NFEV,
        "selection_rule": "lowest residual cost only; never closeness to truth or literature",
        "bounds": "identical physical Re/n/q/centroid/sky bounds to established noiseless full-chain benchmark",
        "source_psf_equivalent_at_target_arcsec": float(source_equiv),
        "matching_kernel_fwhm_arcsec": float(kernel_fwhm),
        "truth_structure_profiled_objective": {
            "profiled_flux": float(truth_amp),
            "sky_sigma_units": float(truth_sky / sigma),
            "cost": float(truth_cost),
            "normalized_l1": float(truth_l1),
        },
        "best_fit": best,
        "all_starts": rows,
        "decision_rule": (
            "Do not define or widen a morphology tolerance from these results. If the lowest-cost free structural fit "
            "lands in the truth neighborhood with a cost comparable to the precomputed truth-structure objective and "
            "without structural bound hits, treat the former high-n noiseless bias as a point-sampled fitter-rendering "
            "floor. Then expand this same renderer to the full noiseless single-Sersic set before interpreting noisy n."
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
