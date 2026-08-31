#!/usr/bin/env python3
"""Diagnose the high-n discrepancy in the CALIFA->ACS PSF transfer benchmark.

The preceding operator benchmark preserved flux and centroid but showed a large
shape difference for n=4 profiles.  Before adding radiometric scaling or noise,
this diagnostic asks whether that discrepancy is caused by rendering/convolving
a cuspy Sersic profile only at detector-pixel centres.

We repeat the same physically feasible CALIFA paths with detector-pixel
integration approximated by deterministic subpixel supersampling.  Source and
target images are rendered and PSF-convolved on a grid finer than their detector
pixels, then block-averaged back to the detector grid before the source image is
redshift-resampled and matched to the target PSF.  No scientific tolerance is
changed and no deconvolution is introduced.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import gaussian_filter

from verification.paulino_afonso_sersic_floor import _bn, _kpc_per_arcsec

SOURCE_Z = 0.015
SOURCE_PIXEL_SCALE = 0.396
SOURCE_PSF_FWHM = 1.3
TARGET_PIXEL_SCALE = 0.03
TARGET_PSF_FWHM = 0.09
TARGET_Z = (0.40, 0.84, 1.47, 2.23)
FWHM_TO_SIGMA = 1.0 / 2.3548200450309493
HALF_EXTENT_KPC = 35.0
OVERSAMPLE = (1, 2, 4)

PROFILES = (
    {"name": "disk", "re_kpc": 3.0, "n": 1.0, "q": 0.70},
    {"name": "mixed", "re_kpc": 5.0, "n": 2.0, "q": 0.65},
    {"name": "concentrated", "re_kpc": 5.0, "n": 4.0, "q": 0.75},
)


def sersic_intensity(x: np.ndarray, y: np.ndarray, re_kpc: float, n: float, q: float) -> np.ndarray:
    pa = 0.37
    c, s = np.cos(pa), np.sin(pa)
    xp = c * x + s * y
    yp = -s * x + c * y
    r = np.sqrt(xp**2 + (yp / q) ** 2)
    b = _bn(float(n))
    return np.exp(-b * ((r / re_kpc) ** (1.0 / n) - 1.0))


def detector_geometry(pixel_scale_arcsec: float, z: float) -> tuple[np.ndarray, float]:
    kpc_pix = pixel_scale_arcsec * _kpc_per_arcsec(z)
    half_n = int(np.ceil(HALF_EXTENT_KPC / kpc_pix))
    coord = np.arange(-half_n, half_n + 1, dtype=float) * kpc_pix
    return coord, kpc_pix


def render_psf_pixel_integrated(
    pixel_scale_arcsec: float,
    z: float,
    psf_fwhm_arcsec: float,
    profile: dict[str, float | str],
    oversample: int,
) -> tuple[np.ndarray, np.ndarray]:
    coord, kpc_pix = detector_geometry(pixel_scale_arcsec, z)
    n_native = len(coord)
    # Fine-grid centres exactly tile each native detector pixel.  Using an even
    # oversampling factor avoids privileging the central singular/cuspy sample.
    fine_step = kpc_pix / oversample
    native_left_edge = coord[0] - 0.5 * kpc_pix
    fine_coord = native_left_edge + (np.arange(n_native * oversample) + 0.5) * fine_step
    yy, xx = np.meshgrid(fine_coord, fine_coord, indexing="ij")
    fine = sersic_intensity(xx, yy, float(profile["re_kpc"]), float(profile["n"]), float(profile["q"]))
    sigma_fine_pix = psf_fwhm_arcsec * FWHM_TO_SIGMA / pixel_scale_arcsec * oversample
    fine = gaussian_filter(fine, sigma=sigma_fine_pix, mode="constant", cval=0.0, truncate=6.0)
    native = fine.reshape(n_native, oversample, n_native, oversample).mean(axis=(1, 3))
    return coord, native


def resample(image: np.ndarray, source_coord: np.ndarray, target_coord: np.ndarray) -> np.ndarray:
    yy, xx = np.meshgrid(target_coord, target_coord, indexing="ij")
    interp = RegularGridInterpolator(
        (source_coord, source_coord), np.asarray(image, dtype=float), method="linear",
        bounds_error=False, fill_value=0.0,
    )
    pts = np.column_stack((yy.ravel(), xx.ravel()))
    return interp(pts).reshape(xx.shape)


def metrics(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    aa = np.clip(np.asarray(a, dtype=float), 0.0, None)
    bb = np.clip(np.asarray(b, dtype=float), 0.0, None)
    aa /= aa.sum(); bb /= bb.sum()
    l1 = float(np.sum(np.abs(aa - bb)))
    y, x = np.indices(aa.shape, dtype=float)
    def r2(img: np.ndarray) -> float:
        cx = float(np.sum(img*x)); cy = float(np.sum(img*y))
        return float(np.sum(img*((x-cx)**2 + (y-cy)**2)))
    r2a, r2b = r2(aa), r2(bb)
    return l1, float(abs(r2a-r2b)/r2b)


def main() -> None:
    out = Path("benchmark_output/paulino_afonso_2017/psf_transfer_sampling_diagnosis")
    out.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    for osamp in OVERSAMPLE:
        for profile in PROFILES:
            scoord, source = render_psf_pixel_integrated(
                SOURCE_PIXEL_SCALE, SOURCE_Z, SOURCE_PSF_FWHM, profile, osamp
            )
            for z in TARGET_Z:
                tcoord, direct = render_psf_pixel_integrated(
                    TARGET_PIXEL_SCALE, z, TARGET_PSF_FWHM, profile, osamp
                )
                source_equiv = SOURCE_PSF_FWHM * _kpc_per_arcsec(SOURCE_Z) / _kpc_per_arcsec(z)
                if TARGET_PSF_FWHM <= source_equiv:
                    raise RuntimeError(f"Unexpected infeasible CALIFA path at z={z}")
                kernel_fwhm = float(np.sqrt(TARGET_PSF_FWHM**2 - source_equiv**2))
                transferred = resample(source, scoord, tcoord)
                kernel_sigma_pix = kernel_fwhm * FWHM_TO_SIGMA / TARGET_PIXEL_SCALE
                transferred = gaussian_filter(
                    transferred, sigma=kernel_sigma_pix, mode="constant", cval=0.0, truncate=6.0
                )
                l1, m2 = metrics(transferred, direct)
                rows.append({
                    "oversample": osamp,
                    "profile": profile["name"],
                    "n": profile["n"],
                    "re_kpc": profile["re_kpc"],
                    "z_target": z,
                    "normalized_l1_image_difference": l1,
                    "second_moment_relative_difference": m2,
                })

    with (out / "rows.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)

    convergence = []
    for profile in PROFILES:
        for z in TARGET_Z:
            subset = [r for r in rows if r["profile"] == profile["name"] and r["z_target"] == z]
            subset = sorted(subset, key=lambda r: int(r["oversample"]))
            convergence.append({
                "profile": profile["name"],
                "z_target": z,
                "l1_by_oversample": {str(r["oversample"]): r["normalized_l1_image_difference"] for r in subset},
                "moment_by_oversample": {str(r["oversample"]): r["second_moment_relative_difference"] for r in subset},
            })

    n4 = [r for r in rows if r["profile"] == "concentrated"]
    payload = {
        "experiment": "PSF-transfer detector-sampling diagnosis",
        "scientific_status": "diagnostic only; no acceptance tolerance changed",
        "oversampling_factors": list(OVERSAMPLE),
        "n_rows": len(rows),
        "max_n4_l1_at_oversample_1": max(float(r["normalized_l1_image_difference"]) for r in n4 if r["oversample"] == 1),
        "max_n4_l1_at_oversample_4": max(float(r["normalized_l1_image_difference"]) for r in n4 if r["oversample"] == 4),
        "convergence": convergence,
        "decision_rule": (
            "If supersampling materially reduces and stabilizes the n=4 discrepancy, classify the previous large residual as detector-sampling/render-order error and use pixel-integrated rendering in the next image-level C2 benchmark. If it does not, continue operator diagnosis before adding radiometric scaling or noise."
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
