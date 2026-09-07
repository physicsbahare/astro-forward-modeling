#!/usr/bin/env python3
"""Independent optimizer-family cross-check for Gate C2 high-n recovery.

This diagnostic keeps the same noiseless n=4 image, physical parameter bounds,
PSF, sampling, and residual definition, but compares the trust-region
least-squares family against bounded L-BFGS-B minimization of the same
chi-square objective in the same transformed coordinates.  No scientific
acceptance tolerance is changed and this script does not declare literature
agreement.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares, minimize

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
        (stamp_size, stamp_size), flux, re_pix, float(truth["n"]),
        float(truth["q"]), center, center, 0.0,
    )

    qmin, qmax = 0.15, 1.0

    def q_to_u(q: float) -> float:
        t = np.clip((q - qmin) / (qmax - qmin), 1e-8, 1 - 1e-8)
        return float(np.log(t / (1 - t)))

    def u_to_q(u: float) -> float:
        t = 1.0 / (1.0 + np.exp(-u))
        return float(qmin + (qmax - qmin) * t)

    # Dimensionless sky coordinate keeps the physical sky bounds identical:
    # decoded sky = p[6] * sigma, with p[6] in [-5, 5].
    re_start_multiplier = 1.0 if np.isclose(z, 2.23) else 1.4
    p0 = np.array([
        np.log(flux), np.log(re_pix * re_start_multiplier), np.log(5.0),
        q_to_u(float(truth["q"])), 0.0, 0.0, 0.0,
    ])
    lower = np.array([
        np.log(1e-8), np.log(0.15), np.log(0.2), -12.0, -2.0, -2.0, -5.0,
    ])
    upper = np.array([
        np.log(1e8), np.log(120.0), np.log(8.0), 12.0, 2.0, 2.0, 5.0,
    ])

    def decode(p: np.ndarray):
        return (
            float(np.exp(p[0])), float(np.exp(p[1])), float(np.exp(p[2])),
            u_to_q(float(p[3])), center + float(p[4]), center + float(p[5]),
            float(p[6]) * sigma,
        )

    def residual(p: np.ndarray) -> np.ndarray:
        return ((_convolved_model(image.shape, *decode(p)) - image) / sigma).ravel()

    def objective(p: np.ndarray) -> float:
        r = residual(p)
        return float(0.5 * np.dot(r, r))

    return truth, sigma, re_pix, flux, center, p0, lower, upper, decode, residual, objective


def _metrics(method: str, z: float, truth, re_pix: float, flux: float, center: float,
             fit, success: bool, status: int, message: str, n_eval: int, cost: float,
             optimality: float | None):
    recovered_flux, recovered_re_pix, recovered_n, recovered_q, x0, y0, sky = fit
    return {
        "z_target": z,
        "method": method,
        "success": bool(success),
        "status": int(status),
        "message": str(message),
        "n_eval": int(n_eval),
        "cost": float(cost),
        "optimality": None if optimality is None else float(optimality),
        "re_ratio": float(recovered_re_pix / re_pix),
        "n_ratio": float(recovered_n / float(truth["n"])),
        "q_difference": float(recovered_q - float(truth["q"])),
        "flux_ratio": float(recovered_flux / flux),
        "centroid_error_pixels": float(np.hypot(x0 - center, y0 - center)),
        "sky": float(sky),
    }


def main() -> None:
    out = Path("benchmark_output/paulino_afonso_2017/independent_optimizer")
    out.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    for z0 in TARGET_REDSHIFTS:
        z = float(z0)
        truth, sigma, re_pix, flux, center, p0, lower, upper, decode, residual, objective = _problem(z)

        ls = least_squares(
            residual, p0, bounds=(lower, upper), method="trf", x_scale=1.0,
            ftol=1e-9, xtol=1e-9, gtol=1e-9, max_nfev=1800,
        )
        rows.append(_metrics(
            "least_squares_trf", z, truth, re_pix, flux, center, decode(ls.x),
            ls.success, ls.status, ls.message, ls.nfev, ls.cost, ls.optimality,
        ))

        lb = minimize(
            objective,
            p0,
            method="L-BFGS-B",
            bounds=list(zip(lower, upper)),
            options={"maxiter": 1800, "ftol": 1e-15, "gtol": 1e-9, "maxls": 50},
        )
        rows.append(_metrics(
            "minimize_lbfgsb", z, truth, re_pix, flux, center, decode(lb.x),
            lb.success, int(lb.status), lb.message, int(lb.nfev), float(lb.fun),
            float(np.max(np.abs(lb.jac))) if getattr(lb, "jac", None) is not None else None,
        ))

    fields = list(rows[0].keys())
    with (out / "rows.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    by_z = {}
    for z0 in TARGET_REDSHIFTS:
        z = float(z0)
        subset = [r for r in rows if r["z_target"] == z]
        by_z[str(z)] = min(subset, key=lambda r: float(r["cost"]))

    payload = {
        "experiment": "independent optimizer-family cross-check",
        "scientific_status": "numerical diagnosis only; no scientific tolerance changed",
        "methods": ["least_squares_trf", "minimize_lbfgsb"],
        "truth_n": 4.0,
        "best_by_redshift": by_z,
        "interpretation_rule": (
            "Agreement of distinct optimizer families near zero residual supports numerical "
            "identifiability. Disagreement indicates optimizer/parameterization pathology and "
            "must be resolved before interpreting noisy morphology bias physically."
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
