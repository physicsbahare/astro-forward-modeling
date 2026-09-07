#!/usr/bin/env python3
"""Quantify noise covariance introduced by JWST imaging drizzle/resampling.

This is a Gate-B diagnostic, not a production implementation. It pushes a
stationary white-noise field with known input variance through the maintained
``jwst.resample.ResampleStep`` and records output pixel covariance, empirical
aperture variance, and the pipeline's approximate propagated variance products.

The JWST/stcal documentation explicitly notes that drizzle does not propagate a
full covariance matrix and that the resampled variance approximation generally
overestimates the true per-pixel error.  We therefore keep two effects separate:
(1) covariance amplification relative to the *empirical* output-pixel variance,
and (2) the ratio of the measured aperture variance to the sum of the pipeline's
diagonal variance plane.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from astropy import coordinates as coord
from astropy import units as u
from astropy.modeling import models
from gwcs import coordinate_frames as cf
from gwcs import wcs
from scipy.signal import convolve2d
from stcal.alignment.util import compute_s_region_imaging


def _simple_tan_wcs(shape, pixel_scale_arcsec=0.063, ra_ref=150.0, dec_ref=2.0):
    ny, nx = shape
    crpix1 = (nx + 1.0) / 2.0
    crpix2 = (ny + 1.0) / 2.0
    scale_deg = pixel_scale_arcsec / 3600.0

    shift = models.Shift(-crpix1 + 1.0) & models.Shift(-crpix2 + 1.0)
    cd = np.array([[-scale_deg, 0.0], [0.0, scale_deg]])
    linear = models.AffineTransformation2D(cd, translation=[0.0, 0.0])
    tan = models.Pix2Sky_TAN()
    rotate = models.RotateNative2Celestial(ra_ref, dec_ref, 180.0)
    det2sky = shift | linear | tan | rotate

    detector_frame = cf.Frame2D(name="detector", axes_names=("x", "y"))
    sky_frame = cf.CelestialFrame(reference_frame=coord.ICRS(), name="world")
    result = wcs.WCS([(detector_frame, det2sky), (sky_frame, None)])
    result.bounding_box = ((-0.5, nx - 0.5), (-0.5, ny - 0.5))
    result.array_shape = shape
    result.pixel_shape = shape[::-1]
    return result


def _white_noise_model(shape=(256, 256), pixel_scale_arcsec=0.063, seed=20260830):
    from stdatamodels.jwst import datamodels

    ny, nx = shape
    rng = np.random.default_rng(seed)
    model = datamodels.ImageModel(shape)
    model.data = rng.normal(0.0, 1.0, size=shape).astype(np.float32)
    model.dq = np.zeros(shape, dtype=np.uint32)
    model.var_rnoise = np.ones(shape, dtype=np.float32)
    model.var_poisson = np.zeros(shape, dtype=np.float32)
    model.var_flat = np.zeros(shape, dtype=np.float32)
    model.err = np.ones(shape, dtype=np.float32)

    model.meta.instrument.name = "NIRCAM"
    model.meta.instrument.detector = "NRCALONG"
    model.meta.instrument.channel = "LONG"
    model.meta.instrument.module = "A"
    model.meta.instrument.filter = "F444W"
    model.meta.instrument.pupil = "CLEAR"
    model.meta.exposure.type = "NRC_IMAGE"
    model.meta.exposure.exposure_time = 1000.0
    model.meta.exposure.duration = 1000.0
    model.meta.exposure.measurement_time = 1000.0
    model.meta.exposure.start_time = 60000.0
    model.meta.exposure.mid_time = 60000.0058
    model.meta.exposure.end_time = 60000.0116
    model.meta.subarray.name = "FULL"
    model.meta.subarray.xstart = 1
    model.meta.subarray.ystart = 1
    model.meta.subarray.xsize = nx
    model.meta.subarray.ysize = ny
    model.meta.observation.date = "2026-08-01"
    model.meta.observation.time = "00:00:00"
    model.meta.bunit_data = "MJy/sr"
    model.meta.bunit_err = "MJy/sr"

    pixel_area_sr = ((pixel_scale_arcsec * u.arcsec) ** 2).to_value(u.sr)
    model.meta.photometry.pixelarea_arcsecsq = pixel_scale_arcsec**2
    model.meta.photometry.pixelarea_steradians = pixel_area_sr

    ra_ref = 150.0
    dec_ref = 2.0
    model.meta.wcs = _simple_tan_wcs(
        shape,
        pixel_scale_arcsec=pixel_scale_arcsec,
        ra_ref=ra_ref,
        dec_ref=dec_ref,
    )
    model.meta.wcsinfo.ra_ref = ra_ref
    model.meta.wcsinfo.dec_ref = dec_ref
    model.meta.wcsinfo.roll_ref = 0.0
    model.meta.wcsinfo.v3yangle = 0.0
    model.meta.wcsinfo.vparity = -1
    model.meta.wcsinfo.s_region = compute_s_region_imaging(model.meta.wcs, shape=shape)
    return model


def _central_finite_crop(array: np.ndarray, border_fraction: float = 0.12) -> np.ndarray:
    arr = np.asarray(array, dtype=float)
    by = max(2, int(round(arr.shape[0] * border_fraction)))
    bx = max(2, int(round(arr.shape[1] * border_fraction)))
    crop = arr[by:-by, bx:-bx]
    if crop.size == 0 or not np.all(np.isfinite(crop)):
        raise RuntimeError("Expected a fully covered finite central drizzle region.")
    return crop


def _lag_correlation(array: np.ndarray, dy: int, dx: int) -> float:
    a = np.asarray(array, dtype=float)
    if dy >= 0:
        ya = slice(0, a.shape[0] - dy if dy else None)
        yb = slice(dy, None)
    else:
        ya = slice(-dy, None)
        yb = slice(0, a.shape[0] + dy)
    if dx >= 0:
        xa = slice(0, a.shape[1] - dx if dx else None)
        xb = slice(dx, None)
    else:
        xa = slice(-dx, None)
        xb = slice(0, a.shape[1] + dx)
    p = a[ya, xa].ravel()
    q = a[yb, xb].ravel()
    p = p - np.mean(p)
    q = q - np.mean(q)
    denom = np.sqrt(np.mean(p * p) * np.mean(q * q))
    if denom <= 0:
        raise RuntimeError("Degenerate variance while estimating drizzle correlation.")
    return float(np.mean(p * q) / denom)


def _aperture_variance_metrics(
    data: np.ndarray,
    diagonal_variance: np.ndarray,
    empirical_pixel_variance: float,
    width: int = 5,
) -> dict[str, float]:
    if width < 1 or width % 2 == 0:
        raise ValueError("Aperture width must be a positive odd integer.")
    kernel = np.ones((width, width), dtype=float)
    aperture_sums = convolve2d(data, kernel, mode="valid")
    pipeline_diagonal_sum = convolve2d(diagonal_variance, kernel, mode="valid")

    empirical_aperture_variance = float(np.var(aperture_sums, ddof=1))
    mean_pipeline_diagonal_aperture_variance = float(np.mean(pipeline_diagonal_sum))
    independent_empirical_prediction = float(width * width * empirical_pixel_variance)
    if mean_pipeline_diagonal_aperture_variance <= 0 or independent_empirical_prediction <= 0:
        raise RuntimeError("Non-positive aperture-variance prediction.")

    return {
        "empirical_aperture_variance": empirical_aperture_variance,
        "independent_empirical_pixel_prediction": independent_empirical_prediction,
        "covariance_amplification_relative_to_empirical_pixel_variance": (
            empirical_aperture_variance / independent_empirical_prediction
        ),
        "mean_pipeline_diagonal_aperture_variance": mean_pipeline_diagonal_aperture_variance,
        "empirical_aperture_to_pipeline_diagonal_ratio": (
            empirical_aperture_variance / mean_pipeline_diagonal_aperture_variance
        ),
    }


def _metrics(model, pixel_scale_ratio: float) -> dict[str, object]:
    from jwst.resample import ResampleStep

    result = ResampleStep.call(
        model,
        pixel_scale_ratio=pixel_scale_ratio,
        pixfrac=1.0,
        kernel="square",
        weight_type="exptime",
    )
    data = _central_finite_crop(result.data)
    var_rnoise = _central_finite_crop(result.var_rnoise)

    empirical_pixel_variance = float(np.var(data, ddof=1))
    propagated_pixel_variance = float(np.mean(var_rnoise))
    if propagated_pixel_variance <= 0:
        raise RuntimeError("Non-positive mean propagated read-noise variance.")

    metrics: dict[str, object] = {
        "pixel_scale_ratio": float(pixel_scale_ratio),
        "output_shape": list(result.data.shape),
        "output_pixelarea_arcsec2": float(result.meta.photometry.pixelarea_arcsecsq),
        "adjacent_rho_x": _lag_correlation(data, 0, 1),
        "adjacent_rho_y": _lag_correlation(data, 1, 0),
        "lag5_rho_x": _lag_correlation(data, 0, 5),
        "lag5_rho_y": _lag_correlation(data, 5, 0),
        "empirical_pixel_variance": empirical_pixel_variance,
        "mean_propagated_var_rnoise": propagated_pixel_variance,
        "pipeline_diagonal_to_empirical_pixel_variance_ratio": (
            propagated_pixel_variance / empirical_pixel_variance
        ),
        "aperture_5x5": _aperture_variance_metrics(
            data,
            var_rnoise,
            empirical_pixel_variance,
            width=5,
        ),
    }
    result.close()
    return metrics


def main() -> None:
    base = _white_noise_model()
    input_crop = _central_finite_crop(base.data)
    input_metrics = {
        "shape": list(base.data.shape),
        "pixel_scale_arcsec": 0.063,
        "adjacent_rho_x": _lag_correlation(input_crop, 0, 1),
        "adjacent_rho_y": _lag_correlation(input_crop, 1, 0),
        "lag5_rho_x": _lag_correlation(input_crop, 0, 5),
        "lag5_rho_y": _lag_correlation(input_crop, 5, 0),
        "empirical_pixel_variance": float(np.var(input_crop, ddof=1)),
    }

    native = _metrics(base, 1.0)
    fine = _metrics(base, 0.5)
    base.close()

    checks = {
        "input_is_effectively_white": bool(
            abs(input_metrics["adjacent_rho_x"]) < 0.03
            and abs(input_metrics["adjacent_rho_y"]) < 0.03
        ),
        "native_scale_remains_effectively_uncorrelated": bool(
            abs(native["adjacent_rho_x"]) < 0.03 and abs(native["adjacent_rho_y"]) < 0.03
        ),
        "half_scale_has_strong_nearest_neighbor_covariance": bool(
            fine["adjacent_rho_x"] > 0.5 and fine["adjacent_rho_y"] > 0.5
        ),
        "half_scale_correlation_is_short_range": bool(
            abs(fine["lag5_rho_x"]) < 0.03 and abs(fine["lag5_rho_y"]) < 0.03
        ),
        "half_scale_apertures_show_covariance_amplification": bool(
            fine["aperture_5x5"]["covariance_amplification_relative_to_empirical_pixel_variance"]
            > 3.0
        ),
        "pipeline_diagonal_variance_is_conservative_for_this_case": bool(
            fine["aperture_5x5"]["empirical_aperture_to_pipeline_diagonal_ratio"] < 1.0
        ),
    }

    payload = {
        "purpose": "Quantify covariance introduced by JWST ResampleStep for a white-noise field.",
        "software_target": "jwst==3.0.0 / stcal==1.20.0",
        "configuration": {
            "instrument": "NIRCam",
            "filter": "F444W",
            "input_pixel_scale_arcsec": 0.063,
            "kernel": "square",
            "pixfrac": 1.0,
            "weight_type": "exptime",
            "input_noise_variance": 1.0,
            "seed": 20260830,
        },
        "input": input_metrics,
        "output_native_scale": native,
        "output_half_scale": fine,
        "checks": checks,
        "interpretation": (
            "Drizzling to half the native linear pixel scale introduces strong short-range "
            "pixel covariance. The covariance amplification must be evaluated relative to the "
            "empirical output-pixel variance. Separately, the JWST pipeline's resampled variance "
            "planes are approximate diagonal products and are conservative for this controlled "
            "configuration, consistent with the stcal resample error-propagation documentation."
        ),
    }

    out = Path("benchmark_output/jwst_drizzle_covariance")
    out.mkdir(parents=True, exist_ok=True)
    path = out / "jwst_resample_white_noise_covariance.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))

    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise RuntimeError(f"JWST drizzle covariance regression checks failed: {failed}")


if __name__ == "__main__":
    main()
