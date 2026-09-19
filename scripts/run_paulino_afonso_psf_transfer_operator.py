#!/usr/bin/env python3
"""Controlled C2 source->target PSF transfer operator benchmark.

This stage follows the PSF-feasibility audit.  It deliberately exercises only
physically feasible CALIFA-like source->ACS combinations, for which the
angularly rescaled source PSF is narrower than the target PSF and a positive
convolution kernel exists.  No sharpening or deconvolution is performed.

For each target redshift and three latent single-Sersic profiles, the script:
1. renders an intrinsic physical-coordinate galaxy at the CALIFA median z;
2. samples it on the SDSS g-band 0.396 arcsec/pixel grid;
3. applies a 1.3 arcsec Gaussian source PSF;
4. resamples that observed source image onto the ACS 0.03 arcsec/pixel target
   physical grid;
5. applies the analytically required positive Gaussian matching kernel; and
6. compares the result with a direct target render convolved with the 0.09
   arcsec ACS PSF.

This is an operator-integrity diagnostic, not a literal reproduction of the
Paulino-Afonso et al. galaxy sample and not a morphology acceptance threshold.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import gaussian_filter

from verification.paulino_afonso_sersic_floor import _bn, _kpc_per_arcsec

SOURCE_Z = 0.015  # CALIFA median quoted in the paper
SOURCE_PIXEL_SCALE = 0.396
SOURCE_PSF_FWHM = 1.3
TARGET_PIXEL_SCALE = 0.03
TARGET_PSF_FWHM = 0.09
TARGET_Z = (0.40, 0.84, 1.47, 2.23)
FWHM_TO_SIGMA = 1.0 / 2.3548200450309493

PROFILES = (
    {"name": "disk", "re_kpc": 3.0, "n": 1.0, "q": 0.70},
    {"name": "mixed", "re_kpc": 5.0, "n": 2.0, "q": 0.65},
    {"name": "concentrated", "re_kpc": 5.0, "n": 4.0, "q": 0.75},
)


def sersic_physical(x: np.ndarray, y: np.ndarray, re_kpc: float, n: float, q: float) -> np.ndarray:
    pa = 0.37
    c, s = np.cos(pa), np.sin(pa)
    xp = c * x + s * y
    yp = -s * x + c * y
    r = np.sqrt(xp**2 + (yp / q) ** 2)
    b = _bn(float(n))
    image = np.exp(-b * ((r / re_kpc) ** (1.0 / n) - 1.0))
    image /= np.sum(image)
    return image


def odd_grid(pixel_scale_arcsec: float, z: float, half_extent_kpc: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    kpc_pix = pixel_scale_arcsec * _kpc_per_arcsec(z)
    half_n = int(np.ceil(half_extent_kpc / kpc_pix))
    coord = np.arange(-half_n, half_n + 1, dtype=float) * kpc_pix
    yy, xx = np.meshgrid(coord, coord, indexing="ij")
    return coord, xx, yy


def resample(image: np.ndarray, source_coord: np.ndarray, tx: np.ndarray, ty: np.ndarray) -> np.ndarray:
    interp = RegularGridInterpolator(
        (source_coord, source_coord), image, method="linear", bounds_error=False, fill_value=0.0
    )
    pts = np.column_stack((ty.ravel(), tx.ravel()))
    return interp(pts).reshape(tx.shape)


def moments(image: np.ndarray) -> tuple[float, float, float]:
    data = np.clip(np.asarray(image, dtype=float), 0.0, None)
    total = float(np.sum(data))
    y, x = np.indices(data.shape, dtype=float)
    cx = float(np.sum(data * x) / total)
    cy = float(np.sum(data * y) / total)
    r2 = float(np.sum(data * ((x-cx)**2 + (y-cy)**2)) / total)
    return total, cx, cy, r2


def main() -> None:
    out = Path("benchmark_output/paulino_afonso_2017/psf_transfer_operator")
    out.mkdir(parents=True, exist_ok=True)
    rows = []

    half_extent_kpc = 35.0
    scoord, sx, sy = odd_grid(SOURCE_PIXEL_SCALE, SOURCE_Z, half_extent_kpc)
    source_sigma_pix = SOURCE_PSF_FWHM * FWHM_TO_SIGMA / SOURCE_PIXEL_SCALE

    for profile in PROFILES:
        latent_source = sersic_physical(sx, sy, profile["re_kpc"], profile["n"], profile["q"])
        observed_source = gaussian_filter(
            latent_source, source_sigma_pix, mode="constant", cval=0.0, truncate=6.0
        )

        for z in TARGET_Z:
            tcoord, tx, ty = odd_grid(TARGET_PIXEL_SCALE, z, half_extent_kpc)
            source_equiv = SOURCE_PSF_FWHM * _kpc_per_arcsec(SOURCE_Z) / _kpc_per_arcsec(z)
            feasible = TARGET_PSF_FWHM > source_equiv
            if not feasible:
                raise RuntimeError(f"Unexpected infeasible CALIFA combination at z={z}")
            kernel_fwhm = float(np.sqrt(TARGET_PSF_FWHM**2 - source_equiv**2))
            kernel_sigma_pix = kernel_fwhm * FWHM_TO_SIGMA / TARGET_PIXEL_SCALE

            transferred = resample(observed_source, scoord, tx, ty)
            transferred = gaussian_filter(
                transferred, kernel_sigma_pix, mode="constant", cval=0.0, truncate=6.0
            )
            transferred /= np.sum(transferred)

            direct = sersic_physical(tx, ty, profile["re_kpc"], profile["n"], profile["q"])
            target_sigma_pix = TARGET_PSF_FWHM * FWHM_TO_SIGMA / TARGET_PIXEL_SCALE
            direct = gaussian_filter(direct, target_sigma_pix, mode="constant", cval=0.0, truncate=6.0)
            direct /= np.sum(direct)

            l1 = float(np.sum(np.abs(transferred - direct)))
            ft, cxt, cyt, r2t = moments(transferred)
            fd, cxd, cyd, r2d = moments(direct)
            rows.append({
                "profile": profile["name"],
                "n": profile["n"],
                "re_kpc": profile["re_kpc"],
                "z_source": SOURCE_Z,
                "z_target": z,
                "source_psf_equivalent_at_target_arcsec": source_equiv,
                "matching_kernel_fwhm_arcsec": kernel_fwhm,
                "normalized_l1_image_difference": l1,
                "flux_relative_difference": float(abs(ft-fd)/fd),
                "centroid_difference_pixels": float(np.hypot(cxt-cxd, cyt-cyd)),
                "second_moment_relative_difference": float(abs(r2t-r2d)/r2d),
            })

    with (out / "rows.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)

    payload = {
        "experiment": "CALIFA-feasible source-to-target PSF transfer operator",
        "scientific_status": "controlled operator diagnostic; not literal survey reproduction",
        "n_cases": len(rows),
        "all_paths_use_positive_convolution_kernel": True,
        "max_normalized_l1_image_difference": max(r["normalized_l1_image_difference"] for r in rows),
        "max_flux_relative_difference": max(r["flux_relative_difference"] for r in rows),
        "max_centroid_difference_pixels": max(r["centroid_difference_pixels"] for r in rows),
        "max_second_moment_relative_difference": max(r["second_moment_relative_difference"] for r in rows),
        "rows": rows,
        "next_decision_rule": (
            "If the feasible source->target operator behaves numerically stably without hidden sharpening, "
            "proceed to the image-level recovery experiment with source PSF, angular resampling, target PSF, "
            "radiometric scaling and declared target noise kept in the forward chain. Do not generalize this "
            "CALIFA-only feasibility result to SAMI/MaNGA/NYU-VAGC paths that require source-specific treatment."
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
