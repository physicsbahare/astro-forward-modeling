"""Gate-B checks for JWST NIRCam photometric-calibration semantics.

These tests deliberately exercise the maintained ``jwst`` calibration code
rather than reproduce its implementation in the future package.  Synthetic
PHOTOM/AREA references provide a deterministic arithmetic test; a separate CI
script exercises live CRDS selection under a pinned context.
"""

from __future__ import annotations

from importlib.metadata import version

import numpy as np


def _make_nircam_input(shape=(12, 16)):
    from stdatamodels.jwst import datamodels

    data = np.arange(1, np.prod(shape) + 1, dtype=np.float32).reshape(shape) / 10.0
    err = np.full(shape, 0.4, dtype=np.float32)
    dq = np.zeros(shape, dtype=np.uint32)
    model = datamodels.ImageModel(data=data, err=err, dq=dq)
    model.var_poisson = np.full(shape, 0.16, dtype=np.float32)
    model.var_rnoise = np.full(shape, 0.09, dtype=np.float32)
    model.var_flat = np.full(shape, 0.04, dtype=np.float32)

    model.meta.instrument.name = "NIRCAM"
    # The JWST pipeline/CRDS datamodel uses NRCALONG for the module-A long-wave
    # detector; STPSF calls the same physical SCA NRCA5.  Keeping this
    # translation explicit prevents instrument-model identifiers from leaking
    # across package boundaries.
    model.meta.instrument.detector = "NRCALONG"
    model.meta.instrument.filter = "F444W"
    model.meta.instrument.pupil = "CLEAR"
    model.meta.exposure.type = "NRC_IMAGE"
    model.meta.subarray.name = "FULL"
    model.meta.subarray.xstart = 1
    model.meta.subarray.ystart = 1
    model.meta.subarray.xsize = shape[1]
    model.meta.subarray.ysize = shape[0]
    model.meta.observation.date = "2026-08-01"
    model.meta.observation.time = "00:00:00"
    model.meta.target.source_type = "EXTENDED"
    return model


def _make_nircam_photom(photmjsr: float):
    from stdatamodels.jwst import datamodels

    dtype = np.dtype(
        [
            ("filter", "S12"),
            ("pupil", "S12"),
            ("photmjsr", "<f4"),
            ("uncertainty", "<f4"),
        ]
    )
    table = np.array([("F444W", "CLEAR", photmjsr, 0.0)], dtype=dtype)
    ref = datamodels.NrcImgPhotomModel(phot_table=table)
    ref.meta.description = "Gate-B synthetic NIRCam PHOTOM reference"
    ref.meta.reftype = "photom"
    ref.meta.author = "verification harness"
    ref.meta.pedigree = "GROUND"
    ref.meta.useafter = "2026-01-01"
    ref.meta.instrument.name = "NIRCAM"
    return ref


def _make_area(shape, area_sr: float, area_a2: float):
    from stdatamodels.jwst import datamodels

    ref = datamodels.PixelAreaModel(data=np.ones(shape, dtype=np.float32))
    ref.meta.photometry.pixelarea_steradians = area_sr
    ref.meta.photometry.pixelarea_arcsecsq = area_a2
    return ref


def test_jwst_pipeline_release_is_pinned():
    assert version("jwst") == "3.0.0"


def test_nircam_photom_scales_science_error_and_variances_and_roundtrips():
    """Verify the calibration operator and inverse on all uncertainty planes."""
    from jwst.photom import photom

    input_model = _make_nircam_input()
    original = input_model.copy()
    conversion = 3.25
    area_sr = 2.31e-14
    area_a2 = 9.827e-4
    ftab = _make_nircam_photom(conversion)
    area_ref = _make_area(input_model.data.shape, area_sr, area_a2)

    calibrated = photom.DataSet(input_model).apply_photom(ftab, area_ref)

    np.testing.assert_allclose(calibrated.data, original.data * conversion, rtol=2e-7)
    np.testing.assert_allclose(calibrated.err, original.err * conversion, rtol=2e-7)
    for name in ("var_poisson", "var_rnoise", "var_flat"):
        np.testing.assert_allclose(
            getattr(calibrated, name),
            getattr(original, name) * conversion**2,
            rtol=3e-7,
        )

    assert calibrated.meta.bunit_data == "MJy/sr"
    assert calibrated.meta.bunit_err == "MJy/sr"
    np.testing.assert_allclose(
        calibrated.meta.photometry.pixelarea_steradians, area_sr, rtol=1e-7
    )
    np.testing.assert_allclose(
        calibrated.meta.photometry.pixelarea_arcsecsq, area_a2, rtol=1e-7
    )
    assert calibrated.area.shape == calibrated.data.shape

    restored = photom.DataSet(calibrated.copy(), inverse=True).apply_photom(ftab, area_ref)
    np.testing.assert_allclose(restored.data, original.data, rtol=4e-7)
    np.testing.assert_allclose(restored.err, original.err, rtol=4e-7)
    for name in ("var_poisson", "var_rnoise", "var_flat"):
        np.testing.assert_allclose(getattr(restored, name), getattr(original, name), rtol=6e-7)

    original.close()
    calibrated.close()
    restored.close()
    ftab.close()
    area_ref.close()


def test_mjysr_to_pixel_flux_conversion_uses_pixel_solid_angle_once():
    """Freeze the unit boundary needed by later artificial-redshift rendering.

    NIRCam imaging after ``photom`` is in MJy/sr.  Converting to flux per
    pixel requires multiplication by the pixel solid angle exactly once.
    """
    from astropy import units as u

    surface_brightness = np.array([0.1, 1.0, 7.5]) * u.MJy / u.sr
    pixel_area = 2.31e-14 * u.sr

    explicit = (surface_brightness * pixel_area).to(u.uJy)
    scalar = surface_brightness.value * pixel_area.value * 1.0e12
    np.testing.assert_allclose(explicit.value, scalar, rtol=2e-15)

    # A factor-of-pixel-area error is catastrophic and must not be silently
    # conflated with the resampling operator.
    assert explicit[1].value < 0.1
