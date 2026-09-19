#!/usr/bin/env python3
"""Diagnose the noiseless high-n local minimum found in the C2 floor fitter.

The previous same-model noiseless diagnostic recovered n=1 and n=2 cases to
machine precision but stalled near the initial guess for n=4 truth. Before
changing the fitter, this script maps deterministic starting points for the
concentrated synthetic case. It reports every solution and the lowest-cost
solution; it does not alter tolerances or declare a literature pass.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from verification.paulino_afonso_sersic_floor import (
    PIXEL_SCALE_ARCSEC,
    TARGET_REDSHIFTS,
    TRUTH_CASES,
    _convolved_model,
    _fit_single_sersic,
    _kpc_per_arcsec,
    adaptive_stamp_size,
    flux_in_depth_units,
    mag_from_depth_units,
    pixel_noise_from_point_depth,
    target_mag_from_source_mag,
)

START_N = (0.7, 1.5, 3.0, 5.0, 7.0)
START_RE_MULTIPLIER = (0.70, 1.00, 1.40)


def main() -> None:
    truth = next(case for case in TRUTH_CASES if case["case"] == "concentrated")
    sigma = pixel_noise_from_point_depth()
    rows: list[dict[str, object]] = []

    for z in TARGET_REDSHIFTS:
        kpc_arcsec = _kpc_per_arcsec(float(z))
        re_pix = float(truth["re_kpc"]) / kpc_arcsec / PIXEL_SCALE_ARCSEC
        stamp_size = adaptive_stamp_size(re_pix)
        center = 0.5 * (stamp_size - 1)
        target_mag = target_mag_from_source_mag(float(truth["source_mag_ab"]), float(z))
        flux = flux_in_depth_units(target_mag)
        image = _convolved_model(
            (stamp_size, stamp_size), flux, re_pix, float(truth["n"]),
            float(truth["q"]), center, center, 0.0,
        )

        for start_re_mult in START_RE_MULTIPLIER:
            for start_n in START_N:
                fit, result = _fit_single_sersic(
                    image, sigma, re_pix * start_re_mult, start_n,
                    float(truth["q"]), flux,
                )
                fitted_flux, fitted_re, fitted_n, fitted_q, fitted_x, fitted_y, fitted_sky = fit
                rows.append({
                    "z_target": float(z),
                    "start_re_multiplier": start_re_mult,
                    "start_n": start_n,
                    "fit_success": bool(result.success),
                    "fit_status": int(result.status),
                    "nfev": int(result.nfev),
                    "cost": float(result.cost),
                    "re_ratio": float(fitted_re / re_pix),
                    "n_ratio": float(fitted_n / float(truth["n"])),
                    "q_difference": float(fitted_q - float(truth["q"])),
                    "mag_difference": float(mag_from_depth_units(float(fitted_flux)) - target_mag),
                    "centroid_error_pixels": float(np.hypot(fitted_x-center, fitted_y-center)),
                    "sky": float(fitted_sky),
                })

    out = Path("benchmark_output/paulino_afonso_2017/optimizer_diagnosis")
    out.mkdir(parents=True, exist_ok=True)
    with (out / "all_starts.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    best_rows = []
    for z in TARGET_REDSHIFTS:
        subset = [row for row in rows if row["z_target"] == float(z)]
        best_rows.append(min(subset, key=lambda row: float(row["cost"])))
    with (out / "best_starts.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(best_rows[0].keys()))
        writer.writeheader()
        writer.writerows(best_rows)

    payload = {
        "experiment": "deterministic high-n start-point map",
        "scientific_status": "numerical diagnosis only",
        "truth_n": float(truth["n"]),
        "start_n": list(START_N),
        "start_re_multiplier": list(START_RE_MULTIPLIER),
        "best_by_redshift": best_rows,
        "diagnostic_question": (
            "Does at least one ordinary start reach the exact same-model solution, demonstrating that the earlier n~0.9 ratio is an optimizer-basin problem rather than an information-limit effect?"
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
