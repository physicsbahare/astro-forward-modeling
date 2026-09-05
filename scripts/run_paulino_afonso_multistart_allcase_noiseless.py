#!/usr/bin/env python3
"""All-case noiseless numerical floor for Gate C2 using the predeclared robust strategy.

This follows the preceding high-n diagnosis.  The model family, PSF, sampling,
physical bounds, and convergence tolerances are unchanged.  The numerical
strategy under test is fixed before looking at the Paulino-Afonso morphology
anchors: central finite-difference Jacobians plus a generic multi-start grid,
with the lowest residual cost selected.

Unlike the first high-n-only multi-start diagnostic, this experiment covers all
five predeclared truth profiles at all four target redshifts and restores the
same deliberate initial perturbations used by the original controlled floor:
flux x0.93, q +0.04 (clipped), and a base Re estimate 1.08 times the input Re.
The multi-start Re multipliers are applied around that perturbed estimate.

This is a numerical-integrity test, not a literature-agreement test.  No
scientific tolerance is introduced or relaxed.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

from verification.paulino_afonso_sersic_floor import (
    PIXEL_SCALE_ARCSEC,
    TARGET_REDSHIFTS,
    TRUTH_CASES,
    _convolved_model,
    _kpc_per_arcsec,
    adaptive_stamp_size,
    flux_in_depth_units,
    pixel_noise_from_point_depth,
    target_mag_from_source_mag,
)

START_N = (1.0, 2.5, 5.5, 7.0)
START_RE_MULTIPLIER = (0.8, 1.2)
BASE_RE_PERTURBATION = 1.08
BASE_FLUX_PERTURBATION = 0.93
BASE_Q_OFFSET = 0.04
MAX_NFEV = 1800


def _fit_one(image, sigma, re_base, flux_base, q_base, center):
    qmin, qmax = 0.15, 1.0

    def q_to_u(q: float) -> float:
        t = np.clip((q - qmin) / (qmax - qmin), 1e-8, 1 - 1e-8)
        return float(np.log(t / (1 - t)))

    def u_to_q(u: float) -> float:
        t = 1.0 / (1.0 + np.exp(-u))
        return float(qmin + (qmax - qmin) * t)

    lower = np.array([
        np.log(1e-8), np.log(0.15), np.log(0.2), -12.0,
        -2.0, -2.0, -5.0,
    ])
    upper = np.array([
        np.log(1e8), np.log(120.0), np.log(8.0), 12.0,
        2.0, 2.0, 5.0,
    ])

    def decode(p: np.ndarray):
        return (
            float(np.exp(p[0])),
            float(np.exp(p[1])),
            float(np.exp(p[2])),
            u_to_q(float(p[3])),
            center + float(p[4]),
            center + float(p[5]),
            float(p[6]) * sigma,
        )

    def residual(p: np.ndarray) -> np.ndarray:
        return ((_convolved_model(image.shape, *decode(p)) - image) / sigma).ravel()

    rows = []
    for re_multiplier in START_RE_MULTIPLIER:
        for n_start in START_N:
            p0 = np.array([
                np.log(max(flux_base, 1e-12)),
                np.log(max(re_base * re_multiplier, 0.2)),
                np.log(n_start),
                q_to_u(q_base),
                0.0, 0.0, 0.0,
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
            rows.append((result, decode(result.x), re_multiplier, n_start))
    return min(rows, key=lambda item: float(item[0].cost)), rows


def main() -> None:
    out = Path("benchmark_output/paulino_afonso_2017/multistart_allcase_noiseless")
    out.mkdir(parents=True, exist_ok=True)

    sigma = pixel_noise_from_point_depth()
    all_rows: list[dict[str, object]] = []
    best_rows: list[dict[str, object]] = []

    for z0 in TARGET_REDSHIFTS:
        z = float(z0)
        kpc_arcsec = _kpc_per_arcsec(z)
        for truth in TRUTH_CASES:
            re_pix = float(truth["re_kpc"]) / kpc_arcsec / PIXEL_SCALE_ARCSEC
            stamp_size = adaptive_stamp_size(re_pix)
            center = 0.5 * (stamp_size - 1)
            target_mag = target_mag_from_source_mag(float(truth["source_mag_ab"]), z)
            flux = flux_in_depth_units(target_mag)
            image = _convolved_model(
                (stamp_size, stamp_size),
                flux,
                re_pix,
                float(truth["n"]),
                float(truth["q"]),
                center,
                center,
                0.0,
            )

            re_base = re_pix * BASE_RE_PERTURBATION
            flux_base = flux * BASE_FLUX_PERTURBATION
            q_base = min(0.95, max(0.2, float(truth["q"]) + BASE_Q_OFFSET))
            best, starts = _fit_one(image, sigma, re_base, flux_base, q_base, center)

            for result, fit, re_mult, n_start in starts:
                recovered_flux, recovered_re, recovered_n, recovered_q, x0, y0, sky = fit
                row = {
                    "case": str(truth["case"]),
                    "z_target": z,
                    "start_re_multiplier": re_mult,
                    "start_n": n_start,
                    "success": bool(result.success),
                    "status": int(result.status),
                    "nfev": int(result.nfev),
                    "njev": int(result.njev) if result.njev is not None else -1,
                    "cost": float(result.cost),
                    "optimality": float(result.optimality),
                    "re_ratio": float(recovered_re / re_pix),
                    "n_ratio": float(recovered_n / float(truth["n"])),
                    "q_difference": float(recovered_q - float(truth["q"])),
                    "flux_ratio": float(recovered_flux / flux),
                    "centroid_error_pixels": float(np.hypot(x0 - center, y0 - center)),
                    "sky_sigma_units": float(sky / sigma),
                }
                all_rows.append(row)

            result, fit, re_mult, n_start = best
            recovered_flux, recovered_re, recovered_n, recovered_q, x0, y0, sky = fit
            best_rows.append({
                "case": str(truth["case"]),
                "z_target": z,
                "input_n": float(truth["n"]),
                "input_re_kpc": float(truth["re_kpc"]),
                "best_start_re_multiplier": re_mult,
                "best_start_n": n_start,
                "success": bool(result.success),
                "status": int(result.status),
                "nfev": int(result.nfev),
                "cost": float(result.cost),
                "optimality": float(result.optimality),
                "re_ratio": float(recovered_re / re_pix),
                "n_ratio": float(recovered_n / float(truth["n"])),
                "q_difference": float(recovered_q - float(truth["q"])),
                "flux_ratio": float(recovered_flux / flux),
                "centroid_error_pixels": float(np.hypot(x0 - center, y0 - center)),
                "sky_sigma_units": float(sky / sigma),
            })

    with (out / "all_starts.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_rows)

    with (out / "best_starts.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(best_rows[0].keys()))
        writer.writeheader()
        writer.writerows(best_rows)

    payload = {
        "experiment": "all-case noiseless robust multistart numerical floor",
        "scientific_status": "numerical integrity only; no scientific tolerance changed",
        "jacobian_scheme": "3-point",
        "x_scale": "jac",
        "max_nfev": MAX_NFEV,
        "start_n": list(START_N),
        "start_re_multiplier": list(START_RE_MULTIPLIER),
        "base_initial_perturbations": {
            "re_multiplier": BASE_RE_PERTURBATION,
            "flux_multiplier": BASE_FLUX_PERTURBATION,
            "q_offset": BASE_Q_OFFSET,
        },
        "selection_rule": "lowest residual cost only; never closeness to truth or literature",
        "n_cases": len(best_rows),
        "all_best_success": bool(all(row["success"] for row in best_rows)),
        "max_abs_re_ratio_minus_one": float(max(abs(float(row["re_ratio"]) - 1.0) for row in best_rows)),
        "max_abs_n_ratio_minus_one": float(max(abs(float(row["n_ratio"]) - 1.0) for row in best_rows)),
        "max_abs_q_difference": float(max(abs(float(row["q_difference"])) for row in best_rows)),
        "max_abs_flux_ratio_minus_one": float(max(abs(float(row["flux_ratio"]) - 1.0) for row in best_rows)),
        "max_centroid_error_pixels": float(max(float(row["centroid_error_pixels"]) for row in best_rows)),
        "best_rows": best_rows,
        "decision_rule": (
            "If all 20 exact-model cases recover the common zero-residual solution from the fixed generic strategy, "
            "promote this strategy to the controlled numerical fitter and rerun the noisy floor. Otherwise continue numerical diagnosis."
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
