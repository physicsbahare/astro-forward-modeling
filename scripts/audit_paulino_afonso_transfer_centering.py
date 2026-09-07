#!/usr/bin/env python3
"""Audit centering/phase consistency in the Paulino-Afonso CALIFA-like transfer.

This is a targeted numerical diagnostic motivated by the fitter render-floor
result.  That experiment found that a fixed-structure point-sampled model could
match the transferred image only after nuisance centroid shifts of roughly
1--2 target pixels for several redshifts.  Before changing any fitter or
morphology bounds, this script checks whether those shifts are already present
in the source detector binning / transfer geometry.

No acceptance threshold is introduced.  The observables are the flux-weighted
centroids of the source detector image, the transferred target image and the
direct pixel-integrated target image, plus the shift predicted by the assigned
source physical coordinates.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_paulino_afonso_full_chain_califa import (
    CASES,
    SOURCE_Z,
    TARGET_PIXEL_SCALE,
    TARGET_Z,
    crop_common,
    direct_target,
    source_detector_image,
    transfer_to_target,
)
from verification.paulino_afonso_sersic_floor import (
    _kpc_per_arcsec,
    flux_in_depth_units,
)


def pixel_centroid(image: np.ndarray) -> tuple[float, float]:
    image = np.asarray(image, dtype=float)
    total = float(np.sum(image))
    yy, xx = np.indices(image.shape, dtype=float)
    return float(np.sum(xx * image) / total), float(np.sum(yy * image) / total)


def offset_from_array_center(image: np.ndarray) -> tuple[float, float]:
    x, y = pixel_centroid(image)
    cx = 0.5 * (image.shape[1] - 1)
    cy = 0.5 * (image.shape[0] - 1)
    return float(x - cx), float(y - cy)


def physical_centroid(image: np.ndarray, xcoord: np.ndarray, ycoord: np.ndarray) -> tuple[float, float]:
    total = float(np.sum(image))
    wx = np.sum(image, axis=0)
    wy = np.sum(image, axis=1)
    return float(np.sum(xcoord * wx) / total), float(np.sum(ycoord * wy) / total)


def main() -> None:
    out = Path("benchmark_output/paulino_afonso_2017/transfer_centering_audit")
    out.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    for case in CASES:
        source_flux = flux_in_depth_units(float(case["source_mag_ab"]))
        xcoord, ycoord, source, kpc_source_pix = source_detector_image(case, source_flux)
        sdx, sdy = offset_from_array_center(source)
        sx_kpc, sy_kpc = physical_centroid(source, xcoord, ycoord)

        for z0 in TARGET_Z:
            z = float(z0)
            transferred, tx, ty, kpc_t, source_equiv, kernel_fwhm, flux_ratio = transfer_to_target(
                case, z, source_flux
            )
            direct = direct_target(case, z, source_flux * flux_ratio, tx, ty, kpc_t)
            transferred_c, direct_c = crop_common(transferred, direct)
            tdx, tdy = offset_from_array_center(transferred_c)
            ddx, ddy = offset_from_array_center(direct_c)

            predicted_dx = float(sx_kpc / kpc_t)
            predicted_dy = float(sy_kpc / kpc_t)
            rows.append(
                {
                    "case": str(case["case"]),
                    "z_source": SOURCE_Z,
                    "z_target": z,
                    "source_detector_shape": int(source.shape[0]),
                    "source_detector_centroid_dx_pix": sdx,
                    "source_detector_centroid_dy_pix": sdy,
                    "source_assigned_centroid_x_kpc": sx_kpc,
                    "source_assigned_centroid_y_kpc": sy_kpc,
                    "target_kpc_per_pixel": float(kpc_t),
                    "predicted_target_dx_pix_from_source_centroid": predicted_dx,
                    "predicted_target_dy_pix_from_source_centroid": predicted_dy,
                    "transferred_centroid_dx_pix": tdx,
                    "transferred_centroid_dy_pix": tdy,
                    "direct_target_centroid_dx_pix": ddx,
                    "direct_target_centroid_dy_pix": ddy,
                    "transfer_minus_direct_dx_pix": float(tdx - ddx),
                    "transfer_minus_direct_dy_pix": float(tdy - ddy),
                    "source_psf_equivalent_at_target_arcsec": float(source_equiv),
                    "matching_kernel_fwhm_arcsec": float(kernel_fwhm),
                }
            )

    with (out / "rows.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    transfer_offsets = [
        float(np.hypot(float(r["transfer_minus_direct_dx_pix"]), float(r["transfer_minus_direct_dy_pix"])))
        for r in rows
    ]
    prediction_residuals = [
        float(
            np.hypot(
                float(r["transferred_centroid_dx_pix"]) - float(r["predicted_target_dx_pix_from_source_centroid"]),
                float(r["transferred_centroid_dy_pix"]) - float(r["predicted_target_dy_pix_from_source_centroid"]),
            )
        )
        for r in rows
    ]
    payload = {
        "experiment": "Paulino-Afonso C2 transfer centering audit",
        "scientific_status": "diagnostic only; no tolerance or morphology bound changes",
        "n_rows": len(rows),
        "median_transfer_minus_direct_centroid_pix": float(np.median(transfer_offsets)),
        "max_transfer_minus_direct_centroid_pix": float(np.max(transfer_offsets)),
        "median_transferred_vs_source_prediction_residual_pix": float(np.median(prediction_residuals)),
        "rows": rows,
        "decision_rule": (
            "If the transferred centroid displacement tracks the centroid implied by the source detector binning/assigned "
            "physical coordinates, diagnose and repair that geometry before changing the fitter renderer.  If it does not, "
            "continue downstream through interpolation/PSF phase diagnostics.  Never absorb the shift by widening centroid bounds."
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
