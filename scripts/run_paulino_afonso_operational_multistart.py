#!/usr/bin/env python3
"""Test an operational, truth-independent multistart numerical floor for Gate C2.

The previous all-case noiseless diagnostic established that a fixed 3-point
Jacobian plus generic multistart grid can recover the exact zero-residual
solution for all 20 synthetic cases when the Re starts are expressed relative
to the known synthetic truth.  That is sufficient to diagnose basin selection,
but it is not yet an operational fitting strategy because a real fitter does
not know the truth Re.

This diagnostic therefore keeps the same image model, physical bounds,
residual definition, solver, Jacobian scheme and convergence tolerances, but
expresses the Re multistart grid relative to the *input estimate supplied to the
fitter*.  In the controlled synthetic benchmark that estimate is deliberately
perturbed to 1.08 times the truth Re, matching the existing noisy-floor setup.
The n starts are fixed generic values and the winning solution is selected by
minimum residual cost only.

No scientific tolerance or morphology acceptance threshold is changed here.
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
START_RE_MULTIPLIER_OF_ESTIMATE = (0.8, 1.2)
INITIAL_RE_MULTIPLIER = 1.08
INITIAL_FLUX_MULTIPLIER = 0.93
INITIAL_Q_OFFSET = 0.04
MAX_NFEV = 1800


def _q_to_u(q: float) -> float:
    qmin, qmax = 0.15, 1.0
    t = np.clip((q - qmin) / (qmax - qmin), 1e-8, 1 - 1e-8)
    return float(np.log(t / (1 - t)))


def _u_to_q(u: float) -> float:
    qmin, qmax = 0.15, 1.0
    t = 1.0 / (1.0 + np.exp(-u))
    return float(qmin + (qmax - qmin) * t)


def main() -> None:
    out = Path("benchmark_output/paulino_afonso_2017/operational_multistart_noiseless")
    out.mkdir(parents=True, exist_ok=True)
    sigma = pixel_noise_from_point_depth()
    rows: list[dict[str, object]] = []
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
                (stamp_size, stamp_size), flux, re_pix, float(truth["n"]),
                float(truth["q"]), center, center, 0.0,
            )

            initial_re_estimate = re_pix * INITIAL_RE_MULTIPLIER
            initial_flux_estimate = flux * INITIAL_FLUX_MULTIPLIER
            initial_q_estimate = min(0.95, max(0.2, float(truth["q"]) + INITIAL_Q_OFFSET))

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
                    float(np.exp(p[0])), float(np.exp(p[1])), float(np.exp(p[2])),
                    _u_to_q(float(p[3])), center + float(p[4]), center + float(p[5]),
                    float(p[6]) * sigma,
                )

            def residual(p: np.ndarray) -> np.ndarray:
                return ((_convolved_model(image.shape, *decode(p)) - image) / sigma).ravel()

            case_rows: list[dict[str, object]] = []
            for re_mult in START_RE_MULTIPLIER_OF_ESTIMATE:
                for n_start in START_N:
                    p0 = np.array([
                        np.log(max(initial_flux_estimate, 1e-12)),
                        np.log(max(initial_re_estimate * re_mult, 0.2)),
                        np.log(n_start),
                        _q_to_u(initial_q_estimate),
                        0.0, 0.0, 0.0,
                    ])
                    result = least_squares(
                        residual, p0, bounds=(lower, upper), method="trf",
                        jac="3-point", x_scale="jac",
                        ftol=1e-9, xtol=1e-9, gtol=1e-9, max_nfev=MAX_NFEV,
                    )
                    rec_flux, rec_re, rec_n, rec_q, x0, y0, sky = decode(result.x)
                    row = {
                        "case": str(truth["case"]),
                        "z_target": z,
                        "input_n": float(truth["n"]),
                        "input_re_kpc": float(truth["re_kpc"]),
                        "start_re_multiplier_of_estimate": re_mult,
                        "start_n": n_start,
                        "success": bool(result.success),
                        "status": int(result.status),
                        "nfev": int(result.nfev),
                        "cost": float(result.cost),
                        "optimality": float(result.optimality),
                        "re_ratio": float(rec_re / re_pix),
                        "n_ratio": float(rec_n / float(truth["n"])),
                        "q_difference": float(rec_q - float(truth["q"])),
                        "flux_ratio": float(rec_flux / flux),
                        "centroid_error_pixels": float(np.hypot(x0 - center, y0 - center)),
                        "sky_sigma_units": float(sky / sigma),
                    }
                    rows.append(row)
                    case_rows.append(row)
            best_rows.append(min(case_rows, key=lambda r: float(r["cost"])))

    with (out / "all_starts.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    with (out / "best_starts.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(best_rows[0].keys()))
        writer.writeheader()
        writer.writerows(best_rows)

    payload = {
        "experiment": "truth-independent operational multistart noiseless floor",
        "scientific_status": "numerical integrity only; no scientific tolerance changed",
        "n_cases": len(best_rows),
        "jacobian_scheme": "3-point",
        "x_scale": "jac",
        "max_nfev": MAX_NFEV,
        "initial_re_multiplier": INITIAL_RE_MULTIPLIER,
        "initial_flux_multiplier": INITIAL_FLUX_MULTIPLIER,
        "initial_q_offset": INITIAL_Q_OFFSET,
        "start_n": list(START_N),
        "start_re_multiplier_of_estimate": list(START_RE_MULTIPLIER_OF_ESTIMATE),
        "selection_rule": "lowest residual cost only; never closeness to truth or literature",
        "all_best_success": bool(all(bool(r["success"]) for r in best_rows)),
        "max_abs_re_ratio_minus_one": float(max(abs(float(r["re_ratio"]) - 1.0) for r in best_rows)),
        "max_abs_n_ratio_minus_one": float(max(abs(float(r["n_ratio"]) - 1.0) for r in best_rows)),
        "max_abs_q_difference": float(max(abs(float(r["q_difference"])) for r in best_rows)),
        "max_abs_flux_ratio_minus_one": float(max(abs(float(r["flux_ratio"]) - 1.0) for r in best_rows)),
        "max_centroid_error_pixels": float(max(float(r["centroid_error_pixels"]) for r in best_rows)),
        "best_rows": best_rows,
        "decision_rule": (
            "If all 20 cases again recover the exact common zero-residual solution when starts are defined relative to a perturbed input estimate rather than truth, the strategy is operationally truth-independent enough to promote into the controlled fitter and rerun the noisy ensemble. Otherwise do not promote it."
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
