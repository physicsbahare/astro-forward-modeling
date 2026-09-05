#!/usr/bin/env python3
"""Diagnose high-n solver convergence without changing scientific tolerances.

This deterministic Gate-C2 diagnostic asks whether the concentrated n=4
same-model/noiseless case reaches the known zero-residual solution when only
numerical optimizer controls are varied.  It deliberately does not change any
morphology acceptance threshold and it does not declare literature agreement.

The starting point is chosen from the previously archived ordinary-start basin
map (n_start=5; Re_start=1.4 Re_truth, except the z=2.23 best ordinary start,
which used 1.0 Re_truth).  We then compare two trust-region scaling choices and
three evaluation budgets.  The truth model itself is exactly representable by
the fitter, so residual cost should approach zero if the numerical optimizer is
able to reach the global solution.
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


def _fit_with_controls(
    image: np.ndarray,
    sigma_pix_noise: float,
    initial_re_pix: float,
    initial_n: float,
    initial_q: float,
    initial_flux: float,
    *,
    max_nfev: int,
    x_scale: str | float,
):
    ny, nx = image.shape
    xmid = 0.5 * (nx - 1)
    ymid = 0.5 * (ny - 1)

    def q_to_u(q: float) -> float:
        qmin, qmax = 0.15, 1.0
        t = np.clip((q - qmin) / (qmax - qmin), 1e-8, 1 - 1e-8)
        return float(np.log(t / (1 - t)))

    def u_to_q(u: float) -> float:
        qmin, qmax = 0.15, 1.0
        t = 1.0 / (1.0 + np.exp(-u))
        return float(qmin + (qmax - qmin) * t)

    p0 = np.array([
        np.log(max(initial_flux, 1e-12)),
        np.log(max(initial_re_pix, 0.2)),
        np.log(max(initial_n, 0.2)),
        q_to_u(initial_q), 0.0, 0.0, 0.0,
    ])
    lower = np.array([
        np.log(1e-8), np.log(0.15), np.log(0.2), -12.0, -2.0, -2.0,
        -5 * sigma_pix_noise,
    ])
    upper = np.array([
        np.log(1e8), np.log(120.0), np.log(8.0), 12.0, 2.0, 2.0,
        5 * sigma_pix_noise,
    ])

    def decode(p: np.ndarray):
        return (
            float(np.exp(p[0])), float(np.exp(p[1])), float(np.exp(p[2])),
            u_to_q(float(p[3])), xmid + float(p[4]), ymid + float(p[5]),
            float(p[6]),
        )

    def residual(p: np.ndarray) -> np.ndarray:
        return ((_convolved_model(image.shape, *decode(p)) - image) /
                sigma_pix_noise).ravel()

    result = least_squares(
        residual,
        p0,
        bounds=(lower, upper),
        method="trf",
        x_scale=x_scale,
        ftol=1e-9,
        xtol=1e-9,
        gtol=1e-9,
        max_nfev=max_nfev,
    )
    return decode(result.x), result


def main() -> None:
    out = Path("benchmark_output/paulino_afonso_2017/solver_convergence")
    out.mkdir(parents=True, exist_ok=True)

    truth = next(case for case in TRUTH_CASES if case["case"] == "concentrated")
    sigma = pixel_noise_from_point_depth()
    rows: list[dict[str, object]] = []

    for z in TARGET_REDSHIFTS:
        z = float(z)
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
        re_start_multiplier = 1.0 if np.isclose(z, 2.23) else 1.4

        for x_scale in ("jac", 1.0):
            for budget in (450, 900, 1800):
                fit, result = _fit_with_controls(
                    image,
                    sigma,
                    re_pix * re_start_multiplier,
                    5.0,
                    float(truth["q"]),
                    flux,
                    max_nfev=budget,
                    x_scale=x_scale,
                )
                recovered_flux, recovered_re_pix, recovered_n, recovered_q, x0, y0, sky = fit
                rows.append({
                    "z_target": z,
                    "x_scale": str(x_scale),
                    "max_nfev": budget,
                    "start_re_multiplier": re_start_multiplier,
                    "start_n": 5.0,
                    "fit_success": bool(result.success),
                    "fit_status": int(result.status),
                    "nfev": int(result.nfev),
                    "cost": float(result.cost),
                    "optimality": float(result.optimality),
                    "re_ratio": float(recovered_re_pix / re_pix),
                    "n_ratio": float(recovered_n / float(truth["n"])),
                    "q_difference": float(recovered_q - float(truth["q"])),
                    "flux_ratio": float(recovered_flux / flux),
                    "centroid_error_pixels": float(np.hypot(x0 - center, y0 - center)),
                    "sky": float(sky),
                })

    with (out / "rows.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    best = []
    for z in TARGET_REDSHIFTS:
        subset = [row for row in rows if row["z_target"] == float(z)]
        best.append(min(subset, key=lambda row: float(row["cost"])))

    payload = {
        "experiment": "high-n solver convergence controls",
        "scientific_status": "numerical diagnosis only; no tolerance changed",
        "truth_n": float(truth["n"]),
        "evaluation_budgets": [450, 900, 1800],
        "x_scale_modes": ["jac", "1.0"],
        "best_by_redshift": best,
        "interpretation_rule": (
            "A lower residual from a larger evaluation budget or alternate numerical scaling is evidence about optimizer conditioning only. It must not be interpreted as relaxed scientific acceptance."
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
