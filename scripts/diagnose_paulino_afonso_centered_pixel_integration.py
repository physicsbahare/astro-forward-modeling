#!/usr/bin/env python3
"""Test a detector-centered pixel-integration geometry for the C2 full chain.

The transfer-centering audit showed deterministic sub-pixel offsets already in
legacy source/target rendering.  The legacy renderer builds an odd fine grid and
then trims it to a multiple of the oversampling factor before block summation;
that trim changes detector phase.  This diagnostic does *not* rewrite the
existing benchmark record.  It constructs coarse detector pixels first and
places an exactly symmetric set of sub-pixel centers inside every coarse pixel,
so block summation is phase-preserving by construction.

We compare the corrected source->target transfer with a corrected direct target
observation using the same physical PSFs, angular scale, luminosity-distance
mapping and Paulino-Afonso luminosity evolution.  No morphology tolerance is
introduced and no fitter is used in this stage.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_paulino_afonso_full_chain_califa import (
    CASES,
    HALF_EXTENT_KPC,
    OVERSAMPLE,
    SOURCE_PIXEL_SCALE,
    SOURCE_PSF_FWHM,
    SOURCE_Z,
    TARGET_PIXEL_SCALE,
    TARGET_PSF_FWHM,
    TARGET_Z,
    crop_common,
    sersic_density,
)
from verification.paulino_afonso_sersic_floor import (
    FWHM_TO_SIGMA,
    _kpc_per_arcsec,
    flux_in_depth_units,
    target_flux_ratio_from_source,
)


def coarse_centers(pixel_scale_arcsec: float, z: float, half_extent_kpc: float):
    kpc_pix = pixel_scale_arcsec * _kpc_per_arcsec(z)
    half_n = int(np.ceil(half_extent_kpc / kpc_pix))
    coord = np.arange(-half_n, half_n + 1, dtype=float) * kpc_pix
    return coord, kpc_pix


def subpixel_centers(coarse_coord: np.ndarray, kpc_pix: float, factor: int) -> np.ndarray:
    # Symmetric pixel-internal centers: for factor=4 -> [-3/8,-1/8,+1/8,+3/8] pixel.
    offsets = ((np.arange(factor, dtype=float) + 0.5) / factor - 0.5) * kpc_pix
    return (coarse_coord[:, None] + offsets[None, :]).reshape(-1)


def block_sum_exact(image: np.ndarray, factor: int) -> np.ndarray:
    ny, nx = image.shape
    if ny % factor or nx % factor:
        raise RuntimeError("phase-corrected fine grid must be exactly divisible by oversampling factor")
    return image.reshape(ny // factor, factor, nx // factor, factor).sum(axis=(1, 3))


def integrated_detector_image(
    case: dict,
    total_flux: float,
    z: float,
    pixel_scale_arcsec: float,
    psf_fwhm_arcsec: float,
):
    coarse, kpc_pix = coarse_centers(pixel_scale_arcsec, z, HALF_EXTENT_KPC)
    fine_coord = subpixel_centers(coarse, kpc_pix, OVERSAMPLE)
    yy, xx = np.meshgrid(fine_coord, fine_coord, indexing="ij")
    density = sersic_density(xx, yy, float(case["re_kpc"]), float(case["n"]), float(case["q"]))
    kpc_f = kpc_pix / OVERSAMPLE
    fine = density * kpc_f**2
    fine *= float(total_flux) / float(np.sum(fine))
    sigma_f = psf_fwhm_arcsec * FWHM_TO_SIGMA / (pixel_scale_arcsec / OVERSAMPLE)
    fine = gaussian_filter(fine, sigma_f, mode="constant", cval=0.0, truncate=7.0)
    det = block_sum_exact(fine, OVERSAMPLE)
    return coarse, det, kpc_pix


def corrected_transfer(case: dict, z: float, source_flux: float):
    scoord, source, kpc_source_pix = integrated_detector_image(
        case, source_flux, SOURCE_Z, SOURCE_PIXEL_SCALE, SOURCE_PSF_FWHM
    )
    tcoord, kpc_target_pix = coarse_centers(TARGET_PIXEL_SCALE, z, HALF_EXTENT_KPC)
    ty, tx = np.meshgrid(tcoord, tcoord, indexing="ij")
    source_sb = source / kpc_source_pix**2
    interp = RegularGridInterpolator(
        (scoord, scoord), source_sb, method="linear", bounds_error=False, fill_value=0.0
    )
    target = interp(np.column_stack((ty.ravel(), tx.ravel()))).reshape(tx.shape) * kpc_target_pix**2

    source_equiv = SOURCE_PSF_FWHM * _kpc_per_arcsec(SOURCE_Z) / _kpc_per_arcsec(z)
    if TARGET_PSF_FWHM <= source_equiv:
        raise RuntimeError(f"corrected CALIFA path unexpectedly requires sharpening at z={z}")
    kernel_fwhm = float(np.sqrt(TARGET_PSF_FWHM**2 - source_equiv**2))
    sigma_t = kernel_fwhm * FWHM_TO_SIGMA / TARGET_PIXEL_SCALE
    target = gaussian_filter(target, sigma_t, mode="constant", cval=0.0, truncate=7.0)
    flux_ratio = target_flux_ratio_from_source(SOURCE_Z, z)
    target *= flux_ratio
    return target, tcoord, kpc_target_pix, source_equiv, kernel_fwhm, flux_ratio


def centroid_offset(image: np.ndarray) -> tuple[float, float]:
    yy, xx = np.indices(image.shape, dtype=float)
    total = float(np.sum(image))
    x = float(np.sum(xx * image) / total)
    y = float(np.sum(yy * image) / total)
    cx = 0.5 * (image.shape[1] - 1)
    cy = 0.5 * (image.shape[0] - 1)
    return x - cx, y - cy


def main() -> None:
    out = Path("benchmark_output/paulino_afonso_2017/centered_pixel_integration")
    out.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    for case in CASES:
        source_flux = flux_in_depth_units(float(case["source_mag_ab"]))
        for z0 in TARGET_Z:
            z = float(z0)
            transferred, tcoord, kpc_t, source_equiv, kernel_fwhm, flux_ratio = corrected_transfer(
                case, z, source_flux
            )
            expected_flux = source_flux * flux_ratio
            _, direct, _ = integrated_detector_image(
                case, expected_flux, z, TARGET_PIXEL_SCALE, TARGET_PSF_FWHM
            )
            transferred, direct = crop_common(transferred, direct)
            tdx, tdy = centroid_offset(transferred)
            ddx, ddy = centroid_offset(direct)
            sum_t = float(np.sum(transferred))
            sum_d = float(np.sum(direct))
            denom = max(float(np.sum(np.abs(direct))), 1e-300)
            rows.append(
                {
                    "case": str(case["case"]),
                    "z_target": z,
                    "input_n": float(case["n"]),
                    "input_re_kpc": float(case["re_kpc"]),
                    "input_q": float(case["q"]),
                    "source_psf_equivalent_at_target_arcsec": float(source_equiv),
                    "matching_kernel_fwhm_arcsec": float(kernel_fwhm),
                    "transferred_centroid_dx_pix": float(tdx),
                    "transferred_centroid_dy_pix": float(tdy),
                    "direct_centroid_dx_pix": float(ddx),
                    "direct_centroid_dy_pix": float(ddy),
                    "transfer_minus_direct_centroid_pix": float(np.hypot(tdx - ddx, tdy - ddy)),
                    "transferred_vs_direct_flux_relative_error": float(abs(sum_t - sum_d) / max(abs(sum_d), 1e-300)),
                    "transferred_vs_expected_flux_relative_error": float(abs(sum_t - expected_flux) / max(abs(expected_flux), 1e-300)),
                    "normalized_l1_transferred_vs_direct": float(np.sum(np.abs(transferred - direct)) / denom),
                }
            )

    with (out / "rows.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    payload = {
        "experiment": "Paulino-Afonso C2 detector-centered pixel-integration diagnostic",
        "scientific_status": "diagnostic corrected geometry; legacy benchmark record preserved separately",
        "oversample": OVERSAMPLE,
        "n_rows": len(rows),
        "max_transfer_minus_direct_centroid_pix": float(max(r["transfer_minus_direct_centroid_pix"] for r in rows)),
        "median_transfer_minus_direct_centroid_pix": float(np.median([r["transfer_minus_direct_centroid_pix"] for r in rows])),
        "max_transferred_vs_direct_flux_relative_error": float(max(r["transferred_vs_direct_flux_relative_error"] for r in rows)),
        "max_transferred_vs_expected_flux_relative_error": float(max(r["transferred_vs_expected_flux_relative_error"] for r in rows)),
        "max_normalized_l1_transferred_vs_direct": float(max(r["normalized_l1_transferred_vs_direct"] for r in rows)),
        "rows": rows,
        "decision_rule": (
            "If detector-centered subpixel integration removes the deterministic centroid phase error while preserving the "
            "radiometric mapping, promote this geometry into the full-chain verification helper and rerun downstream "
            "noiseless/noisy morphology diagnostics. Do not loosen morphology or centroid bounds."
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
