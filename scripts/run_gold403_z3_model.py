#!/usr/bin/env python3
"""Batch model-only artificial redshifting of the passive-disk GOLD403 sample to z=3.

This deliberately does NOT use COSMOS-Web mosaics/noise yet.  It uses the
measured single-Sersic morphology of each catalog object and the verified
survey-transfer primitives in verification.passive_disk_real_pilot:

    required_source_wavelength_um
    inu_source_to_target_factor
    rescale_about_center
    gaussian_degrade

The output is meant as the pre-mosaic geometry/PSF/dimming product for later
population diagnostics (mass-z, size-z, resolvedness-z, etc.), not as a
completeness or detectability measurement.

The input 403-row science catalog is intentionally NOT stored in this public
repository.  Pass it with --catalog.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import gammaincinv

from verification.passive_disk_real_pilot import (
    gaussian_degrade,
    inu_source_to_target_factor,
    required_source_wavelength_um,
    rescale_about_center,
)
from verification.reference import FlatLCDMReference


TARGET_Z = 3.0
TARGET_FILTER = "F444W"
TARGET_PIVOT_UM = 4.402
TARGET_PSF_FWHM_ARCSEC = 0.145
PIXEL_SCALE_ARCSEC = 0.03
CUTOUT_SIZE_ARCSEC = 8.0

PIVOT_UM = {
    "F115W": 1.154,
    "F150W": 1.501,
    "F277W": 2.776,
    "F444W": 4.402,
}
MORPH_FILTERS = tuple(PIVOT_UM)


def sersic_image(
    re_arcsec: float,
    n: float,
    q: float,
    *,
    pixel_scale_arcsec: float = PIXEL_SCALE_ARCSEC,
    size_arcsec: float = CUTOUT_SIZE_ARCSEC,
) -> np.ndarray:
    """Unit-sum intrinsic elliptical Sersic surface-brightness model."""
    npix = max(51, int(np.ceil(size_arcsec / pixel_scale_arcsec)))
    if npix % 2 == 0:
        npix += 1

    yy, xx = np.indices((npix, npix), dtype=float)
    c = 0.5 * (npix - 1)
    x = (xx - c) * pixel_scale_arcsec
    y = (yy - c) * pixel_scale_arcsec

    q = float(np.clip(q, 0.08, 1.0))
    n = float(np.clip(n, 0.3, 8.0))
    re_arcsec = max(float(re_arcsec), 0.01)

    # PA is set to zero.  With a circular target PSF this only fixes display
    # orientation; it does not change Re, n, q or the redshift transfer.
    r = np.sqrt(x**2 + (y / q) ** 2)
    bn = float(gammaincinv(2.0 * n, 0.5))
    image = np.exp(-bn * ((r / re_arcsec) ** (1.0 / n) - 1.0))
    image[~np.isfinite(image)] = 0.0
    image = np.clip(image, 0.0, None)

    total = float(np.sum(image))
    if total <= 0:
        raise RuntimeError("Non-positive Sersic model flux.")
    return image / total


def choose_source_filter(z_source: float) -> tuple[str, float]:
    """Nearest available morphology band to the rest wavelength sampled by F444W at z=3."""
    required = required_source_wavelength_um(
        TARGET_PIVOT_UM, float(z_source), TARGET_Z
    )
    source_filter = min(
        MORPH_FILTERS, key=lambda f: abs(PIVOT_UM[f] - required)
    )
    return source_filter, float(required)


def angular_scale_to_z3(z_source: float, cosmology: FlatLCDMReference) -> float:
    da_source = cosmology.angular_diameter_distance_m(float(z_source))
    da_target = cosmology.angular_diameter_distance_m(TARGET_Z)
    if da_source <= 0 or da_target <= 0:
        raise ValueError("Angular-diameter distance must be positive.")
    return float(da_source / da_target)


def transform_one(row: pd.Series, cosmology: FlatLCDMReference) -> tuple[np.ndarray, dict]:
    zs = float(row["z"])
    if not np.isfinite(zs) or not (0.0 < zs < TARGET_Z):
        raise ValueError(f"Require 0 < z_source < {TARGET_Z}; got {zs}")

    source_filter, required_lambda = choose_source_filter(zs)
    suffix = source_filter.lower()

    re_col = f"re_sersic_{suffix}"
    n_col = f"sersic_n_{suffix}"
    q_col = f"q_sersic_{suffix}"

    re_source = float(row[re_col])
    n_source = float(row[n_col])
    q_source = float(row[q_col])

    if not (
        np.isfinite(re_source) and re_source > 0
        and np.isfinite(n_source) and 0.3 <= n_source <= 9
        and np.isfinite(q_source) and 0 < q_source <= 1
    ):
        raise ValueError(
            f"Invalid morphology in {source_filter}: "
            f"Re={re_source}, n={n_source}, q={q_source}"
        )

    # The catalog Sersic parameters are PSF-model-fit morphology parameters.
    # We therefore render an analytic profile, transfer its angular scale and
    # I_nu surface brightness, then apply the z=3 target PSF.  We do not first
    # blur by the source PSF, avoiding an artificial need to deconvolve when
    # D_A turns over at high redshift.
    source_model = sersic_image(re_source, n_source, q_source)

    angular_scale = angular_scale_to_z3(zs, cosmology)
    inu_factor = inu_source_to_target_factor(zs, TARGET_Z)

    target = rescale_about_center(source_model, angular_scale)
    target *= inu_factor
    target = gaussian_degrade(
        target,
        TARGET_PSF_FWHM_ARCSEC,
        PIXEL_SCALE_ARCSEC,
    )

    source_sum = float(np.sum(source_model))
    target_sum = float(np.sum(target))

    re_target = re_source * angular_scale
    flux_factor_expected = inu_factor * angular_scale**2
    flux_factor_measured = target_sum / source_sum

    meta = {
        "id": int(row["id"]),
        "z_source": zs,
        "z_target": TARGET_Z,
        "target_filter": TARGET_FILTER,
        "source_morph_filter": source_filter,
        "required_source_lambda_um": required_lambda,
        "source_filter_pivot_um": PIVOT_UM[source_filter],
        "source_wavelength_mismatch_um": PIVOT_UM[source_filter] - required_lambda,
        "source_re_arcsec": re_source,
        "source_sersic_n": n_source,
        "source_axis_ratio": q_source,
        "angular_scale": angular_scale,
        "target_re_arcsec_noiseless": re_target,
        "target_re_pixels_noiseless": re_target / PIXEL_SCALE_ARCSEC,
        "target_psf_fwhm_arcsec": TARGET_PSF_FWHM_ARCSEC,
        "target_re_over_psf": re_target / TARGET_PSF_FWHM_ARCSEC,
        "inu_surface_brightness_factor": inu_factor,
        "expected_relative_integrated_flux": flux_factor_expected,
        "measured_relative_integrated_flux_cutout": flux_factor_measured,
        "pixel_scale_arcsec": PIXEL_SCALE_ARCSEC,
        "cutout_size_arcsec": CUTOUT_SIZE_ARCSEC,
        "status": "OK",
    }
    return np.asarray(target, dtype=np.float32), meta


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    frame = pd.read_csv(args.catalog)
    if len(frame) != 403:
        raise RuntimeError(f"Expected 403 rows, found {len(frame)}")
    if frame["id"].duplicated().any():
        raise RuntimeError("Input catalog contains duplicate IDs.")

    args.output.mkdir(parents=True, exist_ok=True)

    cosmology = FlatLCDMReference()
    images: list[np.ndarray] = []
    records: list[dict] = []

    for _, row in frame.iterrows():
        try:
            image, meta = transform_one(row, cosmology)
            images.append(image)
            records.append(meta)
        except Exception as exc:
            # Keep row alignment explicit; failed images are NaN arrays.
            npix = max(51, int(np.ceil(CUTOUT_SIZE_ARCSEC / PIXEL_SCALE_ARCSEC)))
            if npix % 2 == 0:
                npix += 1
            images.append(np.full((npix, npix), np.nan, dtype=np.float32))
            records.append({
                "id": int(row["id"]),
                "z_source": float(row["z"]),
                "z_target": TARGET_Z,
                "target_filter": TARGET_FILTER,
                "status": f"FAIL: {exc}",
            })

    metrics = pd.DataFrame(records)

    # Carry the complete original science catalog forward, so the next stage can
    # make mass-z, SFR-z, B/T-z, visual-flag, and other population plots directly.
    merged = frame.merge(metrics, on="id", how="left", validate="one_to_one")

    metrics.to_csv(args.output / "GOLD403_z3_transform_metrics.csv", index=False)
    merged.to_csv(args.output / "GOLD403_z3_catalog_with_properties.csv", index=False)

    cube = np.stack(images, axis=0)
    np.savez_compressed(
        args.output / "GOLD403_z3_model_images.npz",
        images=cube,
        ids=frame["id"].to_numpy(dtype=np.int64),
        z_source=frame["z"].to_numpy(dtype=float),
        z_target=np.full(len(frame), TARGET_Z, dtype=float),
        pixel_scale_arcsec=np.array(PIXEL_SCALE_ARCSEC),
        target_psf_fwhm_arcsec=np.array(TARGET_PSF_FWHM_ARCSEC),
    )

    ok = metrics["status"].eq("OK")
    summary = {
        "input_catalog": str(args.catalog),
        "N_input": int(len(frame)),
        "N_ok": int(ok.sum()),
        "N_failed": int((~ok).sum()),
        "target_redshift": TARGET_Z,
        "target_filter": TARGET_FILTER,
        "target_pivot_um": TARGET_PIVOT_UM,
        "pixel_scale_arcsec": PIXEL_SCALE_ARCSEC,
        "target_psf_fwhm_arcsec": TARGET_PSF_FWHM_ARCSEC,
        "cutout_size_arcsec": CUTOUT_SIZE_ARCSEC,
        "source_filter_counts": {
            str(k): int(v)
            for k, v in metrics.loc[ok, "source_morph_filter"].value_counts().items()
        },
        "notes": [
            "Model-only run: no COSMOS-Web mosaics, backgrounds, neighbors, or noise.",
            "Input single-Sersic morphology is preserved as intrinsic model parameters.",
            "Images carry relative surface-brightness dimming; absolute flux calibration is not claimed.",
            "Intrinsic properties such as stellar mass are copied unchanged to the z=3 analysis catalog.",
            "Use this output for pre-mosaic geometry/PSF and population-property diagnostics, not completeness."
        ],
    }

    with open(args.output / "GOLD403_z3_run_summary.json", "w") as handle:
        json.dump(summary, handle, indent=2)

    print(json.dumps(summary, indent=2))
    print("Output:", args.output.resolve())


if __name__ == "__main__":
    main()
