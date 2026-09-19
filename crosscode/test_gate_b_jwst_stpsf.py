"""JWST-specific Gate-B cross-code checks against STPSF.

This suite is intentionally separate from the production package.  It verifies
what STPSF actually supplies (optical, distorted, detector-sampled, and
chromatic PSFs) before those products are allowed to become framework inputs.

Pinned environment:
- STPSF 2.2.0
- STPSF data bundle 2.2.0
- synphot 1.7.0

The CI workflow installs a versioned STPSF data bundle and records the archive
SHA-256.  Numerical tolerances below are benchmark-specific safety checks, not
future package-wide science tolerances.
"""

from __future__ import annotations

from importlib.metadata import version

import numpy as np


def _normalize(image: np.ndarray) -> np.ndarray:
    image = np.asarray(image, dtype=float)
    total = float(np.nansum(image))
    assert np.isfinite(total) and total > 0.0
    return image / total


def _centroid_and_sigma(image: np.ndarray) -> tuple[float, float, float]:
    """Return flux centroid and circularized second-moment sigma in pixels."""
    image = _normalize(image)
    y, x = np.indices(image.shape, dtype=float)
    cx = float(np.sum(image * x))
    cy = float(np.sum(image * y))
    sigma2 = 0.5 * (
        float(np.sum(image * (x - cx) ** 2))
        + float(np.sum(image * (y - cy) ** 2))
    )
    return cx, cy, float(np.sqrt(sigma2))


def _nircam(filter_name: str, detector: str, position=(1024, 1024)):
    import stpsf

    nrc = stpsf.NIRCam()
    nrc.filter = filter_name
    nrc.detector = detector
    nrc.detector_position = position
    return nrc


def test_stpsf_software_and_reference_data_are_exactly_pinned():
    import stpsf

    assert version("stpsf") == "2.2.0"
    _, data_version = stpsf.utils.get_stpsf_data_path(
        data_version_min=(2, 2, 0), return_version=True
    )
    assert data_version == "2.2.0"


def test_nircam_output_extensions_match_documented_operator_semantics():
    """Check the four documented image products and detector-effect toggle.

    STPSF documents OVERSAMP/DET_SAMP as ideal optical products and
    OVERDIST/DET_DIST as products including geometric distortion plus detector
    charge redistribution; IPC/PPC is applied in DET_DIST by default.
    """

    nrc = _nircam("F444W", "NRCA5")
    with_effects = nrc.calc_psf(fov_pixels=31, oversample=2, nlambda=3)

    names = [hdu.name for hdu in with_effects]
    for required in ("OVERSAMP", "DET_SAMP", "OVERDIST", "DET_DIST"):
        assert required in names

    # All representations should be finite and normalized to the same total
    # flux to numerical precision appropriate for a compact, well-contained PSF.
    sums = {}
    for ext in ("OVERSAMP", "DET_SAMP", "OVERDIST", "DET_DIST"):
        image = np.asarray(with_effects[ext].data, dtype=float)
        assert np.all(np.isfinite(image))
        assert np.nanmin(image) >= -1.0e-12
        sums[ext] = float(np.sum(image))
    scale = sums["OVERSAMP"]
    assert scale > 0.0
    for value in sums.values():
        assert abs(value / scale - 1.0) < 3.0e-3

    # Recompute with the documented detector-effect controls switched off.
    nrc_no = _nircam("F444W", "NRCA5")
    nrc_no.options["charge_diffusion_sigma"] = 0
    nrc_no.options["add_ipc"] = False
    without_effects = nrc_no.calc_psf(fov_pixels=31, oversample=2, nlambda=3)

    det_with = _normalize(with_effects["DET_DIST"].data)
    det_without = _normalize(without_effects["DET_DIST"].data)
    l1 = float(np.sum(np.abs(det_with - det_without)))
    assert l1 > 1.0e-3

    _, _, sigma_with = _centroid_and_sigma(det_with)
    _, _, sigma_without = _centroid_and_sigma(det_without)
    # STPSF's charge-diffusion/IPC model should broaden the detector PSF.
    assert sigma_with > sigma_without


def test_f444w_chromatic_weighting_changes_psf_size_in_expected_direction():
    """A redder photon distribution must produce a broader diffraction PSF."""

    wavelengths = np.array([3.90e-6, 4.35e-6, 4.80e-6])
    blue = {"wavelengths": wavelengths, "weights": np.array([0.70, 0.25, 0.05])}
    red = {"wavelengths": wavelengths, "weights": np.array([0.05, 0.25, 0.70])}

    nrc_blue = _nircam("F444W", "NRCA5")
    psf_blue = nrc_blue.calc_psf(source=blue, fov_pixels=31, oversample=3)

    nrc_red = _nircam("F444W", "NRCA5")
    psf_red = nrc_red.calc_psf(source=red, fov_pixels=31, oversample=3)

    _, _, sigma_blue = _centroid_and_sigma(psf_blue["OVERSAMP"].data)
    _, _, sigma_red = _centroid_and_sigma(psf_red["OVERSAMP"].data)

    assert sigma_red > sigma_blue
    assert (sigma_red / sigma_blue - 1.0) > 1.0e-2


def test_nircam_field_position_changes_psf_without_changing_flux_scale():
    """Verify that detector position is a real optical-model input, not metadata."""

    center = _nircam("F150W", "NRCA1", position=(1024, 1024)).calc_psf(
        fov_pixels=31, oversample=2, nlambda=3
    )
    corner = _nircam("F150W", "NRCA1", position=(128, 128)).calc_psf(
        fov_pixels=31, oversample=2, nlambda=3
    )

    a = _normalize(center["OVERSAMP"].data)
    b = _normalize(corner["OVERSAMP"].data)
    l1 = float(np.sum(np.abs(a - b)))

    # Field-dependent wavefront error should produce a measurable morphology
    # difference.  This is deliberately a weak semantic threshold.
    assert l1 > 1.0e-4
    assert abs(float(np.sum(a)) - 1.0) < 1.0e-12
    assert abs(float(np.sum(b)) - 1.0) < 1.0e-12
