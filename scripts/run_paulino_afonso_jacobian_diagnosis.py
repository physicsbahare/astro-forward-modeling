#!/usr/bin/env python3
"""Diagnose Jacobian conditioning in the Gate-C2 high-n Sérsic recovery problem.

This is a numerical-integrity experiment, not a morphology acceptance test. It
keeps the same noiseless n=4 image, PSF, sampling, transformed coordinates,
physical parameter bounds, residual definition, trust-region solver and
convergence tolerances used by the preceding C2 diagnostics.

The experiment asks two questions without changing any scientific tolerance:

1. How ill-conditioned is the residual Jacobian at the exact truth, and how
   sensitive is that estimate to finite-difference step size?
2. Do scipy least_squares 2-point and 3-point Jacobians reach materially
   different solutions from the same pre-declared high-n starting point?

Outputs are machine-readable so the result can be reviewed before any fitter
change is promoted into the C2 recovery benchmark.
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

RELATIVE_STEPS = (1e-3, 1e-4, 1e-5, 1e-6)


def _problem(z: float):
    truth = next(case for case in TRUTH_CASES if case["case"] == "concentrated")
    sigma = pixel_noise_from_point_depth()
    re_pix = float(truth["re_kpc"]) / _kpc_per_arcsec(z) / PIXEL_SCALE_ARCSEC
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
        t = np.clip((q - qmin) / (qmax - qmin), 1e-12, 1.0 - 1e-12)
        return float(np.log(t / (1.0 - t)))

    def u_to_q(u: float) -> float:
        t = 1.0 / (1.0 + np.exp(-u))
        return float(qmin + (qmax - qmin) * t)

    # Keep sky dimensionless while preserving the same decoded physical bounds
    # used by the preceding parameterization/optimizer diagnostics.
    p_truth = np.array([
        np.log(flux),
        np.log(re_pix),
        np.log(float(truth["n"])),
        q_to_u(float(truth["q"])),
        0.0,
        0.0,
        0.0,
    ])
    re_start_multiplier = 1.0 if np.isclose(z, 2.23) else 1.4
    p_start = np.array([
        np.log(flux),
        np.log(re_pix * re_start_multiplier),
        np.log(5.0),
        q_to_u(float(truth["q"])),
        0.0,
        0.0,
        0.0,
    ])
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
        model = _convolved_model(image.shape, *decode(p))
        return ((model - image) / sigma).ravel()

    return truth, sigma, re_pix, flux, center, p_truth, p_start, lower, upper, decode, residual


def _central_jacobian(residual, p: np.ndarray, relative_step: float) -> np.ndarray:
    base = np.asarray(p, dtype=float)
    n_resid = residual(base).size
    jac = np.empty((n_resid, base.size), dtype=float)
    for j in range(base.size):
        h = relative_step * max(1.0, abs(float(base[j])))
        plus = base.copy()
        minus = base.copy()
        plus[j] += h
        minus[j] -= h
        jac[:, j] = (residual(plus) - residual(minus)) / (2.0 * h)
    return jac


def _jacobian_metrics(jac: np.ndarray) -> dict[str, float]:
    singular = np.linalg.svd(jac, compute_uv=False)
    col_norms = np.linalg.norm(jac, axis=0)
    positive_cols = col_norms[col_norms > 0.0]
    smallest = float(singular[-1])
    largest = float(singular[0])
    condition = float(np.inf if smallest == 0.0 else largest / smallest)
    column_spread = float(
        np.inf if positive_cols.size == 0 else np.max(positive_cols) / np.min(positive_cols)
    )
    return {
        "largest_singular_value": largest,
        "smallest_singular_value": smallest,
        "condition_number": condition,
        "column_norm_spread": column_spread,
        "min_column_norm": float(np.min(col_norms)),
        "max_column_norm": float(np.max(col_norms)),
    }


def _fit_metrics(method: str, z: float, result, decode, truth, re_pix, flux, center):
    recovered_flux, recovered_re, recovered_n, recovered_q, x0, y0, sky = decode(result.x)
    return {
        "z_target": z,
        "jacobian_scheme": method,
        "success": bool(result.success),
        "status": int(result.status),
        "nfev": int(result.nfev),
        "njev": None if result.njev is None else int(result.njev),
        "cost": float(result.cost),
        "optimality": float(result.optimality),
        "re_ratio": float(recovered_re / re_pix),
        "n_ratio": float(recovered_n / float(truth["n"])),
        "q_difference": float(recovered_q - float(truth["q"])),
        "flux_ratio": float(recovered_flux / flux),
        "centroid_error_pixels": float(np.hypot(x0 - center, y0 - center)),
        "sky": float(sky),
    }


def main() -> None:
    out = Path("benchmark_output/paulino_afonso_2017/jacobian_diagnosis")
    out.mkdir(parents=True, exist_ok=True)

    condition_rows: list[dict[str, object]] = []
    fit_rows: list[dict[str, object]] = []

    for z0 in TARGET_REDSHIFTS:
        z = float(z0)
        (
            truth, sigma, re_pix, flux, center, p_truth, p_start,
            lower, upper, decode, residual,
        ) = _problem(z)

        truth_residual_norm = float(np.linalg.norm(residual(p_truth)))
        for relative_step in RELATIVE_STEPS:
            jac = _central_jacobian(residual, p_truth, relative_step)
            metrics = _jacobian_metrics(jac)
            condition_rows.append({
                "z_target": z,
                "location": "exact_truth",
                "relative_step": relative_step,
                "truth_residual_l2": truth_residual_norm,
                **metrics,
            })

        for scheme in ("2-point", "3-point"):
            result = least_squares(
                residual,
                p_start,
                jac=scheme,
                bounds=(lower, upper),
                method="trf",
                x_scale="jac",
                ftol=1e-9,
                xtol=1e-9,
                gtol=1e-9,
                max_nfev=1800,
            )
            fit_rows.append(
                _fit_metrics(scheme, z, result, decode, truth, re_pix, flux, center)
            )

    with (out / "jacobian_condition_rows.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(condition_rows[0].keys()))
        writer.writeheader()
        writer.writerows(condition_rows)

    with (out / "fit_rows.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fit_rows[0].keys()))
        writer.writeheader()
        writer.writerows(fit_rows)

    payload = {
        "experiment": "high-n Jacobian and finite-difference conditioning diagnosis",
        "scientific_status": "numerical diagnosis only; no scientific tolerance or physical bound changed",
        "truth_n": 4.0,
        "relative_steps": list(RELATIVE_STEPS),
        "least_squares_jacobian_schemes": ["2-point", "3-point"],
        "condition_rows": condition_rows,
        "fit_rows": fit_rows,
        "decision_rule": (
            "Strong Jacobian condition numbers, large column-norm disparities, finite-difference-step sensitivity, "
            "or disagreement between 2-point and 3-point solutions are evidence of numerical conditioning. "
            "Such behavior must be resolved before noisy Sérsic-n bias is interpreted physically."
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
