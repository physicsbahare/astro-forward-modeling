#!/usr/bin/env python3
"""Assemble the next controlled Paulino-Afonso C2 artificial-redshifting chain.

This is still a verification-stage diagnostic, not production code and not a
literal reproduction of the original survey sample.  It combines the pieces
that have already been validated separately for the physically feasible
CALIFA-like path:

1. pixel-integrated source Sersic rendering (4x detector supersampling);
2. SDSS-like 0.396 arcsec/pixel sampling at z=0.015;
3. 1.3 arcsec source PSF;
4. angular resampling onto the ACS 0.03 arcsec/pixel target grid;
5. positive source->target PSF matching to 0.09 arcsec ACS resolution;
6. luminosity-distance flux dimming plus the paper's explicit luminosity
   evolution law; and
7. the declared ACS white-noise depth model (AB=27.2, 5 sigma point source).

The noiseless transferred image is compared with a direct target observation of
the same latent galaxy.  Noise is then added only after that operator-integrity
comparison.  No morphology acceptance threshold is introduced here.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import gaussian_filter

from verification.paulino_afonso_sersic_floor import (
    POINT_DEPTH_AB_5SIGMA,
    FWHM_TO_SIGMA,
    _bn,
    _kpc_per_arcsec,
    flux_in_depth_units,
    mag_from_depth_units,
    pixel_noise_from_point_depth,
    target_flux_ratio_from_source,
)

SOURCE_Z = 0.015
SOURCE_PIXEL_SCALE = 0.396
SOURCE_PSF_FWHM = 1.3
TARGET_PIXEL_SCALE = 0.03
TARGET_PSF_FWHM = 0.09
TARGET_Z = (0.40, 0.84, 1.47, 2.23)
OVERSAMPLE = 4
HALF_EXTENT_KPC = 35.0

CASES = (
    {"case": "disk_bright", "re_kpc": 3.0, "n": 1.0, "q": 0.70, "source_mag_ab": 16.5},
    {"case": "disk_fainter", "re_kpc": 3.0, "n": 1.0, "q": 0.70, "source_mag_ab": 18.0},
    {"case": "mixed", "re_kpc": 5.0, "n": 2.0, "q": 0.65, "source_mag_ab": 17.0},
    {"case": "concentrated", "re_kpc": 5.0, "n": 4.0, "q": 0.75, "source_mag_ab": 17.0},
    {"case": "large_disk", "re_kpc": 9.0, "n": 1.0, "q": 0.60, "source_mag_ab": 17.0},
)


def odd_grid(pixel_scale_arcsec: float, z: float, half_extent_kpc: float):
    kpc_pix = pixel_scale_arcsec * _kpc_per_arcsec(z)
    half_n = int(np.ceil(half_extent_kpc / kpc_pix))
    coord = np.arange(-half_n, half_n + 1, dtype=float) * kpc_pix
    yy, xx = np.meshgrid(coord, coord, indexing="ij")
    return coord, xx, yy, kpc_pix


def sersic_density(x, y, re_kpc: float, n: float, q: float):
    pa = 0.37
    c, s = np.cos(pa), np.sin(pa)
    xp = c * x + s * y
    yp = -s * x + c * y
    r = np.sqrt(xp**2 + (yp / q) ** 2)
    b = _bn(float(n))
    image = np.exp(-b * ((r / re_kpc) ** (1.0 / n) - 1.0))
    return image


def block_sum(image: np.ndarray, factor: int) -> np.ndarray:
    ny, nx = image.shape
    ny2 = (ny // factor) * factor
    nx2 = (nx // factor) * factor
    trimmed = image[:ny2, :nx2]
    return trimmed.reshape(ny2 // factor, factor, nx2 // factor, factor).sum(axis=(1, 3))


def source_detector_image(case: dict, total_flux: float):
    fine_scale = SOURCE_PIXEL_SCALE / OVERSAMPLE
    coord_f, xf, yf, kpc_f = odd_grid(fine_scale, SOURCE_Z, HALF_EXTENT_KPC)
    density = sersic_density(xf, yf, case["re_kpc"], case["n"], case["q"])
    # Convert continuous surface brightness to fine-pixel flux and normalize to
    # the declared observed source flux before PSF convolution.
    fine = density * kpc_f**2
    fine *= total_flux / np.sum(fine)
    sigma_f = SOURCE_PSF_FWHM * FWHM_TO_SIGMA / fine_scale
    fine = gaussian_filter(fine, sigma_f, mode="constant", cval=0.0, truncate=7.0)
    det = block_sum(fine, OVERSAMPLE)
    # Build detector-center physical coordinates from the binned dimensions.
    kpc_det = SOURCE_PIXEL_SCALE * _kpc_per_arcsec(SOURCE_Z)
    cy = 0.5 * (det.shape[0] - 1)
    cx = 0.5 * (det.shape[1] - 1)
    ycoord = (np.arange(det.shape[0]) - cy) * kpc_det
    xcoord = (np.arange(det.shape[1]) - cx) * kpc_det
    return xcoord, ycoord, det, kpc_det


def transfer_to_target(case: dict, z: float, source_flux: float):
    xcoord, ycoord, source, kpc_source_pix = source_detector_image(case, source_flux)
    tcoord, tx, ty, kpc_target_pix = odd_grid(TARGET_PIXEL_SCALE, z, HALF_EXTENT_KPC)

    # Interpolate physical surface brightness, not flux-per-pixel, so angular
    # resampling does not create an artificial flux change.
    source_sb = source / (kpc_source_pix**2)
    interp = RegularGridInterpolator(
        (ycoord, xcoord), source_sb, method="linear", bounds_error=False, fill_value=0.0
    )
    pts = np.column_stack((ty.ravel(), tx.ravel()))
    target = interp(pts).reshape(tx.shape) * (kpc_target_pix**2)

    source_equiv = SOURCE_PSF_FWHM * _kpc_per_arcsec(SOURCE_Z) / _kpc_per_arcsec(z)
    if TARGET_PSF_FWHM <= source_equiv:
        raise RuntimeError(f"CALIFA path unexpectedly requires sharpening at z={z}")
    kernel_fwhm = float(np.sqrt(TARGET_PSF_FWHM**2 - source_equiv**2))
    sigma_t = kernel_fwhm * FWHM_TO_SIGMA / TARGET_PIXEL_SCALE
    target = gaussian_filter(target, sigma_t, mode="constant", cval=0.0, truncate=7.0)

    flux_ratio = target_flux_ratio_from_source(SOURCE_Z, z)
    target *= flux_ratio
    return target, tx, ty, kpc_target_pix, source_equiv, kernel_fwhm, flux_ratio


def direct_target(case: dict, z: float, target_flux: float, tx, ty, kpc_target_pix: float):
    # Pixel-integrated target truth using the same 4x supersampling principle.
    fine_scale = TARGET_PIXEL_SCALE / OVERSAMPLE
    _, xf, yf, kpc_f = odd_grid(fine_scale, z, HALF_EXTENT_KPC)
    density = sersic_density(xf, yf, case["re_kpc"], case["n"], case["q"])
    fine = density * kpc_f**2
    fine *= target_flux / np.sum(fine)
    sigma_f = TARGET_PSF_FWHM * FWHM_TO_SIGMA / fine_scale
    fine = gaussian_filter(fine, sigma_f, mode="constant", cval=0.0, truncate=7.0)
    direct = block_sum(fine, OVERSAMPLE)
    # Shapes can differ by one detector pixel because of independent odd-grid
    # construction. Crop symmetrically to the common central footprint.
    return direct


def crop_common(a: np.ndarray, b: np.ndarray):
    ny = min(a.shape[0], b.shape[0]); nx = min(a.shape[1], b.shape[1])
    def crop(x):
        y0 = (x.shape[0] - ny) // 2; x0 = (x.shape[1] - nx) // 2
        return x[y0:y0+ny, x0:x0+nx]
    return crop(a), crop(b)


def main():
    out = Path("benchmark_output/paulino_afonso_2017/full_chain_califa")
    out.mkdir(parents=True, exist_ok=True)
    sigma_noise = pixel_noise_from_point_depth()
    rows = []

    for iz, z in enumerate(TARGET_Z):
        for icase, case in enumerate(CASES):
            source_flux = flux_in_depth_units(case["source_mag_ab"])
            transferred, tx, ty, kpc_t, source_equiv, kernel_fwhm, flux_ratio = transfer_to_target(
                case, z, source_flux
            )
            expected_target_flux = source_flux * flux_ratio
            direct = direct_target(case, z, expected_target_flux, tx, ty, kpc_t)
            transferred, direct = crop_common(transferred, direct)

            # Normalize neither image: this comparison must preserve the
            # radiometric mapping rather than hiding it with post-hoc scaling.
            sum_t = float(np.sum(transferred)); sum_d = float(np.sum(direct))
            denom = max(float(np.sum(np.abs(direct))), 1e-300)
            l1 = float(np.sum(np.abs(transferred - direct)) / denom)
            flux_err = float(abs(sum_t - sum_d) / max(abs(sum_d), 1e-300))
            expected_err = float(abs(sum_t - expected_target_flux) / max(abs(expected_target_flux), 1e-300))

            target_mag = mag_from_depth_units(expected_target_flux)
            eq_snr = float(5.0 * 10.0 ** (-0.4 * (target_mag - POINT_DEPTH_AB_5SIGMA)))

            seed = int(4027 + iz * 1000 + icase)
            rng = np.random.default_rng(seed)
            noisy = transferred + rng.normal(0.0, sigma_noise, size=transferred.shape)
            rows.append({
                "case": case["case"], "z_source": SOURCE_Z, "z_target": z,
                "n": case["n"], "re_kpc": case["re_kpc"], "q": case["q"],
                "source_mag_ab": case["source_mag_ab"], "target_mag_ab": target_mag,
                "source_psf_equivalent_at_target_arcsec": source_equiv,
                "matching_kernel_fwhm_arcsec": kernel_fwhm,
                "flux_ratio_source_to_target": flux_ratio,
                "expected_target_flux_depth_units": expected_target_flux,
                "transferred_flux_depth_units": sum_t,
                "direct_target_flux_depth_units": sum_d,
                "transferred_vs_direct_flux_relative_error": flux_err,
                "transferred_vs_expected_flux_relative_error": expected_err,
                "normalized_l1_transferred_vs_direct": l1,
                "point_source_equivalent_snr": eq_snr,
                "pixel_noise_sigma_depth_units": sigma_noise,
                "noise_seed": seed,
                "noisy_image_sum_depth_units": float(np.sum(noisy)),
            })

    with (out / "rows.csv").open("w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    payload = {
        "experiment": "CALIFA-feasible full artificial-redshifting chain assembly",
        "scientific_status": "controlled image-level diagnostic; not literal survey reproduction",
        "source_render_oversampling": OVERSAMPLE,
        "n_rows": len(rows),
        "components": [
            "source pixel integration", "source PSF", "angular resampling",
            "positive target PSF matching", "luminosity-distance dimming",
            "Paulino-Afonso luminosity evolution", "declared ACS white-noise depth model"
        ],
        "max_transferred_vs_direct_flux_relative_error": max(r["transferred_vs_direct_flux_relative_error"] for r in rows),
        "max_transferred_vs_expected_flux_relative_error": max(r["transferred_vs_expected_flux_relative_error"] for r in rows),
        "max_normalized_l1_transferred_vs_direct": max(r["normalized_l1_transferred_vs_direct"] for r in rows),
        "rows": rows,
        "next_decision_rule": (
            "If the assembled noiseless chain preserves the declared radiometric mapping and the residual image "
            "difference remains at the validated sampling/transfer floor, proceed to morphology recovery on these "
            "degraded images with the operational multistart fitter. Do not tune any tolerance to the literature."
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
