#!/usr/bin/env python3
"""Diagnose whether a fixed generic multi-start strategy resolves the C2 high-n basin problem.

This is a numerical-integrity diagnostic only. It keeps the same noiseless n=4
image model, physical bounds, residual definition, trust-region solver,
parameterization and scientific tolerances as the existing C2 diagnostics.
The only changes under test are:

1. use SciPy's central finite-difference Jacobian (``jac='3-point'``), motivated
   by the preceding Jacobian diagnosis; and
2. evaluate a fixed, truth-independent grid of starting points in (Re, n), then
   select the solution with the lowest residual cost.

The start grid is declared in advance and is not tuned to the published
Paulino-Afonso morphology ratios. No morphology acceptance criterion is
introduced or relaxed here.
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

# Fixed generic starts. None uses the benchmark truth n=4 exactly.
START_N = (1.0, 2.5, 5.5, 7.0)
START_RE_MULTIPLIER = (0.8, 1.2)
MAX_NFEV = 1800


def _problem(z: float):
    truth = next(case for case in TRUTH_CASES if case["case"] == "concentrated")
    sigma = pixel_noise_from_point_depth()
    kpc_arcsec = _kpc_per_arcsec(z)
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

    def p0_from(re_multiplier: float, n_start: float) -> np.ndarray:
        return np.array([
            np.log(flux),
            np.log(re_pix * re_multiplier),
            np.log(n_start),
            q_to_u(float(truth["q"])),
            0.0,
            0.0,
            0.0,
        ])

    return truth, re_pix, flux, center, lower, upper, decode, residual, p0_from


def main() -> None:
    out = Path("benchmark_output/paulino_afonso_2017/multistart_3point")
    out.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    best_rows: list[dict[str, object]] = []

    for z0 in TARGET_REDSHIFTS:
        z = float(z0)
        truth, re_pix, flux, center, lower, upper, decode, residual, p0_from = _problem(z)

        z_rows: list[dict[str, object]] = []
        for re_multiplier in START_RE_MULTIPLIER:
            for n_start in START_N:
                result = least_squares(
                    residual,
                    p0_from(re_multiplier, n_start),
                    bounds=(lower, upper),
                    method="trf",
                    jac="3-point",
                    x_scale="jac",
                    ftol=1e-9,
                    xtol=1e-9,
                    gtol=1e-9,
                    max_nfev=MAX_NFEV,
                )
                recovered_flux, recovered_re_pix, recovered_n, recovered_q, x0, y0, sky = decode(result.x)
                row = {
                    "z_target": z,
                    "start_re_multiplier": re_multiplier,
                    "start_n": n_start,
                    "success": bool(result.success),
                    "status": int(result.status),
                    "nfev": int(result.nfev),
                    "njev": int(result.njev) if result.njev is not None else -1,
                    "cost": float(result.cost),
                    "optimality": float(result.optimality),
                    "re_ratio": float(recovered_re_pix / re_pix),
                    "n_ratio": float(recovered_n / float(truth["n"])),
                    "q_difference": float(recovered_q - float(truth["q"])),
                    "flux_ratio": float(recovered_flux / flux),
                    "centroid_error_pixels": float(np.hypot(x0 - center, y0 - center)),
                    "sky": float(sky),
                }
                rows.append(row)
                z_rows.append(row)

        best_rows.append(min(z_rows, key=lambda row: float(row["cost"])))

    with (out / "all_starts.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with (out / "best_starts.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(best_rows[0].keys()))
        writer.writeheader()
        writer.writerows(best_rows)

    payload = {
        "experiment": "fixed generic multi-start with central finite-difference Jacobian",
        "scientific_status": "numerical diagnosis only; no scientific tolerance or physical bound changed",
        "jacobian_scheme": "3-point",
        "x_scale": "jac",
        "max_nfev": MAX_NFEV,
        "start_n": list(START_N),
        "start_re_multiplier": list(START_RE_MULTIPLIER),
        "selection_rule": "choose the converged-or-not solution with the lowest residual cost; never select by closeness to truth or literature",
        "best_by_redshift": best_rows,
        "decision_rule": (
            "If the fixed generic multi-start grid reaches the same near-zero-residual truth solution across all target redshifts, "
            "the remaining pathology is primarily basin selection and a predeclared multi-start fitter can be tested as the numerical floor. "
            "If low-redshift cases still settle in higher-cost minima, continue numerical diagnosis before interpreting noisy morphology bias physically."
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
