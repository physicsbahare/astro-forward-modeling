"""Initial JWST drizzle/resampling Gate-B checks.

These tests exercise ``jwst.resample.ResampleStep`` on an analytic sky scene
with a hand-built GWCS.  They freeze the distinction between calibrated
surface-brightness units (MJy/sr), pixel solid angle, integrated source flux,
and morphology under a change of output pixel scale.

The tolerances are test-specific diagnostics, not production defaults.
"""

from __future__ import annotations

import numpy as np
from astropy import coordinates as coord
from astropy import units as u
from astropy.modeling import models
from gwcs import coordinate_frames as cf
from gwcs import wcs


def _simple_tan_wcs(shape, pixel_scale_arcsec=0.063, ra_ref=150.0, dec_ref=2.0):
    """Build a distortion-free tangent-plane GWCS for a small imaging cutout."""
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


def _analytic_nircam_model(shape=(64, 64), pixel_scale_arcsec=0.063):
    from stdatamodels.jwst import datamodels

    ny, nx = shape
    y, x = np.indices(shape, dtype=float)
    x0, y0 = 31.35, 30.70
    sigma = 3.2
    source = np.exp(-0.5 * ((x - x0) ** 2 + (y - y0) ** 2) / sigma**2)

    model = datamodels.ImageModel(shape)
    model.data = source.astype(np.float32)
    model.dq = np.zeros(shape, dtype=np.uint32)
    model.var_poisson = np.full(shape, 0.010, dtype=np.float32)
    model.var_rnoise = np.full(shape, 0.004, dtype=np.float32)
    model.var_flat = np.full(shape, 0.001, dtype=np.float32)
    model.err = np.sqrt(model.var_poisson + model.var_rnoise + model.var_flat).astype(np.float32)

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

    pixel_area_arcsec2 = pixel_scale_arcsec**2
    pixel_area_sr = (pixel_scale_arcsec * u.arcsec) ** 2
    model.meta.photometry.pixelarea_arcsecsq = pixel_area_arcsec2
    model.meta.photometry.pixelarea_steradians = pixel_area_sr.to_value(u.sr)

    model.meta.wcs = _simple_tan_wcs(shape, pixel_scale_arcsec=pixel_scale_arcsec)
    return model


def _source_moments(model):
    data = np.nan_to_num(np.asarray(model.data, dtype=float), nan=0.0)
    data = np.clip(data, 0.0, None)
    total = float(np.sum(data))
    assert total > 0.0
    y, x = np.indices(data.shape, dtype=float)
    cx = float(np.sum(data * x) / total)
    cy = float(np.sum(data * y) / total)
    sigma_pix = float(
        np.sqrt(
            0.5
            * (
                np.sum(data * (x - cx) ** 2) / total
                + np.sum(data * (y - cy) ** 2) / total
            )
        )
    )
    area_sr = float(model.meta.photometry.pixelarea_steradians)
    pixel_scale_arcsec = np.sqrt(area_sr) * u.rad.to(u.arcsec)
    flux_proxy = total * area_sr
    return cx, cy, sigma_pix * pixel_scale_arcsec, flux_proxy


def test_resample_pixel_scale_preserves_sky_flux_centroid_and_size():
    from jwst.resample import ResampleStep

    model = _analytic_nircam_model()
    native = ResampleStep.call(
        model,
        pixel_scale_ratio=1.0,
        pixfrac=1.0,
        kernel="square",
        weight_type="exptime",
    )
    fine = ResampleStep.call(
        model,
        pixel_scale_ratio=0.5,
        pixfrac=1.0,
        kernel="square",
        weight_type="exptime",
    )

    # Output pixel area must follow the square of the requested linear scale.
    area_native = float(native.meta.photometry.pixelarea_steradians)
    area_fine = float(fine.meta.photometry.pixelarea_steradians)
    np.testing.assert_allclose(area_fine, area_native * 0.5**2, rtol=2.0e-5)

    cx1, cy1, sigma1_arcsec, flux1 = _source_moments(native)
    cx2, cy2, sigma2_arcsec, flux2 = _source_moments(fine)

    # For calibrated MJy/sr images, integrated flux is sum(I_nu * Omega_pix).
    np.testing.assert_allclose(flux2, flux1, rtol=8.0e-3)

    # Compare centroids in sky coordinates rather than raw output pixels.
    ra1, dec1 = native.meta.wcs(cx1, cy1)
    ra2, dec2 = fine.meta.wcs(cx2, cy2)
    c1 = coord.SkyCoord(ra1 * u.deg, dec1 * u.deg)
    c2 = coord.SkyCoord(ra2 * u.deg, dec2 * u.deg)
    assert c1.separation(c2).to_value(u.arcsec) < 3.0e-3

    # The same analytic source must retain its angular second-moment size.
    np.testing.assert_allclose(sigma2_arcsec, sigma1_arcsec, rtol=1.5e-2)

    # Variance/error products should remain present, finite where covered, and
    # physically non-negative after the pipeline's drizzle propagation.
    finite = np.isfinite(fine.data)
    assert np.any(finite)
    for name in ("err", "var_poisson", "var_rnoise", "var_flat"):
        arr = np.asarray(getattr(fine, name), dtype=float)
        assert arr.shape == fine.data.shape
        assert np.all(arr[finite] >= 0.0)
        assert np.all(np.isfinite(arr[finite]))

    assert fine.meta.resample.pixel_scale_ratio == 0.5
    assert native.meta.resample.pixel_scale_ratio == 1.0

    model.close()
    native.close()
    fine.close()
