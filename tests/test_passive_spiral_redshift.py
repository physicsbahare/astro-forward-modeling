from __future__ import annotations

import numpy as np
import pytest

from verification.passive_spiral_redshift import (
    SOURCE_PSF_FWHM_ARCSEC,
    SOURCE_Z,
    TARGET_PSF_FWHM_ARCSEC,
    TARGET_Z,
    benchmark_grid,
    psf_matching_kernel_fwhm,
    surface_brightness_ratio,
)
from verification.reference import FlatLCDMReference


def test_tolman_ratio_is_applied_as_single_band_integrated_factor() -> None:
    ratio = surface_brightness_ratio(0.1, 1.0)
    assert ratio == pytest.approx((1.1 / 2.0) ** 4, rel=0.0, abs=1e-15)


def test_psf_matching_is_degradation_only() -> None:
    cosmology = FlatLCDMReference()
    source_equiv, kernel = psf_matching_kernel_fwhm(
        SOURCE_Z,
        1.0,
        SOURCE_PSF_FWHM_ARCSEC,
        TARGET_PSF_FWHM_ARCSEC,
        cosmology,
    )
    assert source_equiv > 0
    assert kernel > 0
    assert np.hypot(source_equiv, kernel) == pytest.approx(
        TARGET_PSF_FWHM_ARCSEC, rel=0.0, abs=1e-14
    )

    with pytest.raises(ValueError, match="forbids sharpening"):
        psf_matching_kernel_fwhm(
            SOURCE_Z,
            1.0,
            SOURCE_PSF_FWHM_ARCSEC,
            0.001,
            cosmology,
        )


def test_p1_grid_records_all_frozen_targets_without_scientific_thresholding() -> None:
    rows = benchmark_grid()
    assert [row["z_target"] for row in rows] == list(TARGET_Z)

    for row in rows:
        for key in (
            "latent_spiral_amplitude",
            "direct_target_spiral_amplitude",
            "artificial_target_spiral_amplitude",
            "smooth_direct_spiral_amplitude",
            "smooth_artificial_spiral_amplitude",
            "arm_retention_direct_over_latent",
            "arm_artificial_over_direct",
            "arm_artificial_minus_direct_abs",
            "normalized_l1_artificial_vs_direct",
            "total_flux_relative_difference",
        ):
            assert np.isfinite(row[key])

        assert 0.0 <= row["latent_spiral_amplitude"] <= 1.0
        assert 0.0 <= row["direct_target_spiral_amplitude"] <= 1.0
        assert 0.0 <= row["artificial_target_spiral_amplitude"] <= 1.0
        assert row["matching_kernel_fwhm_arcsec"] > 0.0
        assert row["target_psf_fwhm_kpc"] > 0.0

        # This is a scene-definition sanity invariant, not a detection threshold:
        # the declared spiral scene must carry more matched arm power than its
        # otherwise identical smooth control on both observation paths.
        assert row["direct_target_spiral_amplitude"] > row["smooth_direct_spiral_amplitude"]
        assert row["artificial_target_spiral_amplitude"] > row["smooth_artificial_spiral_amplitude"]
