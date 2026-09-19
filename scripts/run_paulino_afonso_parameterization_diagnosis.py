#!/usr/bin/env python3
"""Diagnose whether parameter scaling causes the C2 high-n optimizer stall.

This is a numerical-integrity diagnostic only.  It keeps the same image model,
parameter bounds, residual definition, trust-region solver, and convergence
tolerances as the existing C2 fitter.  The sole change is the internal
parameterization of the constant sky term: instead of optimizing sky in image
flux units (whose natural scale is the tiny per-pixel noise sigma), optimize a
dimensionless sky/sigma coordinate.  This asks whether the previous n=4 stall
is caused by poor conditioning rather than missing information.

No morphology acceptance criterion is introduced or relaxed here.
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


def _fit(
    image: np.ndarray,
    sigma: float,
    initial_re_pix: float,
    initial_n: float,
    initial_q: float,
    initial_flux: float,
    *,
    scaled_sky: bool,
    max_nfev: int = 1800,
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
        q_to_u(initial_q),
        0.0,
        0.0,
        0.0,
    ])
    sky_bound = 5.0 if scaled_sky else 5.0 * sigma
    lower = np.array([
        np.log(1e-8), np.log(0.15), np.log(0.2), -12.0,
        -2.0, -2.0, -sky_bound,
    ])
    upper = np.array([
        np.log(1e8), np.log(120.0), np.log(8.0), 12.0,
        2.0, 2.0, sky_bound,
    ])

    def decode(p: np.ndarray):
        sky = float(p[6] * sigma) if scaled_sky else float(p[6])
        return (
            float(np.exp(p[0])),
            float(np.exp(p[1])),
            float(np.exp(p[2])),
            u_to_q(float(p[3])),
            xmid + float(p[4]),
            ymid + float(p[5]),
            sky,
        )

    def residual(p: np.ndarray) -> np.ndarray:
        return ((_convolved_model(image.shape, *decode(p)) - image) / sigma).ravel()

    result = least_squares(
        residual,
        p0,
        bounds=(lower, upper),
        method="trf",
        x_scale="jac",
        ftol=1e-9,
        xtol=1e-9,
        gtol=1e-9,
        max_nfev=max_nfev,
    )
    return decode(result.x), result


def main() -> None:
    out = Path("benchmark_output/paulino_afonso_2017/parameterization_diagnosis")
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
            (stamp_size, stamp_size),
            flux,
            re_pix,
            float(truth["n"]),
            float(truth["q"]),
            center,
            center,
            0.0,
        )
        re_start_multiplier = 1.0 if np.isclose(z, 2.23) else 1.4

        for scaled_sky in (False, True):
            fit, result = _fit(
                image,
                sigma,
                re_pix * re_start_multiplier,
                5.0,
                float(truth["q"]),
                flux,
                scaled_sky=scaled_sky,
            )
            recovered_flux, recovered_re_pix, recovered_n, recovered_q, x0, y0, sky = fit
            rows.append({
                "z_target": z,
                "parameterization": "sky_over_sigma" if scaled_sky else "sky_flux_units",
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
                "sky_sigma_units": float(sky / sigma),
            })

    with (out / "rows.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    comparisons = []
    for z in TARGET_REDSHIFTS:
        subset = [row for row in rows if row["z_target"] == float(z)]
        raw = next(row for row in subset if row["parameterization"] == "sky_flux_units")
        scaled = next(row for row in subset if row["parameterization"] == "sky_over_sigma")
        comparisons.append({
            "z_target": float(z),
            "raw_cost": float(raw["cost"]),
            "scaled_cost": float(scaled["cost"]),
            "cost_ratio_scaled_over_raw": float(scaled["cost"]) / float(raw["cost"]),
            "raw_optimality": float(raw["optimality"]),
            "scaled_optimality": float(scaled["optimality"]),
            "raw_n_ratio": float(raw["n_ratio"]),
            "scaled_n_ratio": float(scaled["n_ratio"]),
            "scaled_fit_success": bool(scaled["fit_success"]),
            "scaled_nfev": int(scaled["nfev"]),
        })

    payload = {
        "experiment": "high-n internal parameterization diagnosis",
        "scientific_status": "numerical diagnosis only; no tolerance or bound changed",
        "change_under_test": "optimize constant sky as dimensionless sky/sigma rather than raw flux units",
        "max_nfev": 1800,
        "comparisons": comparisons,
        "decision_rule": (
            "If sky/sigma scaling materially lowers residual cost and/or permits formal convergence while preserving the same decoded sky bounds and scientific model, treat the earlier stall as optimizer conditioning. Otherwise continue with an independent optimizer/Jacobian diagnosis."
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
