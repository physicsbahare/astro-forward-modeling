#!/usr/bin/env python3
"""Separate numerical identifiability from noise-driven C2 morphology bias.

This diagnostic fits noiseless images rendered by the *same* single-Sersic +
PSF model used by the C2 measurement-floor fitter. It therefore asks a narrow
question before any additional source complexity is introduced: can the current
optimizer recover its own latent truth from the adopted adaptive footprint?

No literature tolerance is asserted here. The output is machine-readable and
is reviewed before deciding whether remaining noisy-fit failures are physical
information loss or numerical optimization pathologies.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from verification.paulino_afonso_sersic_floor import (
    PIXEL_SCALE_ARCSEC,
    PSF_FWHM_ARCSEC,
    SOURCE_REDSHIFT,
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


def main() -> None:
    output_root = Path("benchmark_output/paulino_afonso_2017/noiseless_identifiability")
    output_root.mkdir(parents=True, exist_ok=True)
    sigma = pixel_noise_from_point_depth()
    rows: list[dict[str, object]] = []

    for z in TARGET_REDSHIFTS:
        kpc_arcsec = _kpc_per_arcsec(float(z))
        for truth in TRUTH_CASES:
            re_pix = float(truth["re_kpc"]) / kpc_arcsec / PIXEL_SCALE_ARCSEC
            stamp_size = adaptive_stamp_size(re_pix)
            center = 0.5 * (stamp_size - 1)
            target_mag = target_mag_from_source_mag(float(truth["source_mag_ab"]), float(z))
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
            fitted, result = _fit_single_sersic(
                image,
                sigma,
                re_pix * 1.08,
                max(0.25, float(truth["n"]) * 0.90),
                min(0.95, max(0.2, float(truth["q"]) + 0.04)),
                flux * 0.93,
            )
            recovered_flux, recovered_re_pix, recovered_n, recovered_q, recovered_x, recovered_y, sky = fitted
            recovered_mag = mag_from_depth_units(float(recovered_flux))
            row = {
                "case": str(truth["case"]),
                "z_source": SOURCE_REDSHIFT,
                "z_target": float(z),
                "target_mag_ab": target_mag,
                "target_re_pixels": re_pix,
                "stamp_size": stamp_size,
                "psf_fwhm_pixels": PSF_FWHM_ARCSEC / PIXEL_SCALE_ARCSEC,
                "fit_success": bool(result.success),
                "fit_status": int(result.status),
                "nfev": int(result.nfev),
                "fit_cost": float(result.cost),
                "re_ratio": float(recovered_re_pix / re_pix),
                "n_ratio": float(recovered_n / float(truth["n"])),
                "q_difference": float(recovered_q - float(truth["q"])),
                "mag_difference": float(recovered_mag - target_mag),
                "centroid_error_pixels": float(np.hypot(recovered_x - center, recovered_y - center)),
                "sky": float(sky),
                "max_abs_weighted_residual": float(
                    np.max(np.abs((_convolved_model(
                        image.shape,
                        recovered_flux,
                        recovered_re_pix,
                        recovered_n,
                        recovered_q,
                        recovered_x,
                        recovered_y,
                        sky,
                    ) - image) / sigma))
                ),
            }
            if not all(np.isfinite(float(row[key])) for key in (
                "fit_cost", "re_ratio", "n_ratio", "q_difference", "mag_difference",
                "centroid_error_pixels", "sky", "max_abs_weighted_residual"
            )):
                raise RuntimeError(f"Non-finite noiseless identifiability result: {row}")
            rows.append(row)

    csv_path = output_root / "rows.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "experiment": "same-model noiseless numerical identifiability",
        "scientific_status": "diagnostic; no literature acceptance threshold",
        "n_rows": len(rows),
        "fit_success_fraction": float(np.mean([bool(row["fit_success"]) for row in rows])),
        "max_abs_re_ratio_minus_one": float(max(abs(float(row["re_ratio"]) - 1.0) for row in rows)),
        "max_abs_n_ratio_minus_one": float(max(abs(float(row["n_ratio"]) - 1.0) for row in rows)),
        "max_abs_q_difference": float(max(abs(float(row["q_difference"])) for row in rows)),
        "max_abs_mag_difference": float(max(abs(float(row["mag_difference"])) for row in rows)),
        "max_centroid_error_pixels": float(max(float(row["centroid_error_pixels"]) for row in rows)),
        "max_abs_weighted_residual": float(max(float(row["max_abs_weighted_residual"]) for row in rows)),
        "interpretation": (
            "If these same-model noiseless fits do not return close to truth, diagnose the optimizer/rendering geometry before attributing noisy-fit behavior to surface-brightness information loss."
        ),
    }
    (output_root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
