"""Scientific sanity checks for the controlled FERENGI-style benchmark."""

import numpy as np
import pytest

from verification.ferengi_synthetic import run_ferengi_synthetic_benchmark


@pytest.mark.parametrize("z_target", [0.20, 0.50, 1.00])
def test_ferengi_synthetic_observation_only_baseline(z_target):
    result = run_ferengi_synthetic_benchmark(z_target)

    assert result.mode == "observation_only"
    assert result.target_pixels > 20
    assert result.source_psf_equivalent_at_target_arcsec < result.target_psf_fwhm_arcsec
    assert result.added_matching_kernel_fwhm_arcsec > 0.0

    # This radiometric identity is analytic for matched rest-frame filters and
    # should be limited only by floating-point arithmetic.
    assert result.radiometric_flux_scaling_relative_error < 5.0e-12

    # These are deliberately broad scientific sanity bounds for the first
    # deterministic benchmark, not frozen production tolerances.  Tighter
    # quantity-specific acceptance limits belong to Gate E after the literature
    # and real-survey experiments are complete.
    assert np.isfinite(result.normalized_l1_image_error)
    assert result.normalized_l1_image_error < 0.12
    assert result.total_flux_relative_error < 0.05
    assert result.centroid_error_arcsec < 0.03
    assert result.second_moment_relative_error < 0.08
    assert result.radial_flux_profile_l1_error < 0.10
    assert result.color_gradient_error_mag < 0.05
