"""Regression tests for the independent pre-implementation verification suite.

These tolerances are verification-suite tolerances, not yet the public package's
scientific acceptance limits. Public acceptance thresholds will be frozen only
after cross-code and literature-benchmark validation.
"""

from verification.chromatic import run_chromatic_check
from verification.noise import run_noise_check
from verification.psf import impossible_case_is_detected, run_gaussian_reference
from verification.radiometry import run_radiometry_check
from verification.resampling import sampling_density_table
from verification.spectral_support import run_spectral_support_check


def test_radiometry_identities():
    r = run_radiometry_check(z=2.0, grid_points=10001)
    assert r.distance_duality_relative_error < 1e-13
    assert r.fnu_bolometric_relative_error < 1e-12
    assert r.flambda_bolometric_relative_error < 2e-8
    assert r.photon_rate_relative_disagreement < 5e-10
    assert r.tolman_relative_error < 1e-12


def test_analytic_gaussian_psf_matching():
    r = run_gaussian_reference(sigma_source_pix=2.5, sigma_target_pix=5.0, shape=101)
    assert r.kernel_sum_error < 1e-14
    assert r.l1_reconstruction_error_D < 1e-12
    assert r.negative_kernel_weight_Wminus < 1e-14
    assert r.second_moment_relative_error < 1e-12
    assert impossible_case_is_detected()


def test_exact_overlap_conserves_flux():
    rows = sampling_density_table()
    assert max(row["flux_relative_error"] for row in rows) < 1e-12


def test_well_sampled_pixel_transfer_is_small_but_not_magically_exact():
    rows = sampling_density_table()
    well = [r for r in rows if r["input_sigma_pixels"] >= 15.0]
    assert max(r["l1_image_error"] for r in well) < 0.003
    assert max(r["second_moment_relative_error"] for r in well) < 0.001


def test_chromatic_psf_is_not_equivalent_to_one_global_psf():
    r = run_chromatic_check(wavelength_samples=513)
    assert r.single_psf_flux_relative_error < 1e-12
    assert r.l1_normalized_image_difference > 0.02
    assert r.disk_effective_psf_sigma_pix != r.bulge_effective_psf_sigma_pix


def test_poisson_noise_ordering():
    r = run_noise_check(realizations=30000)
    assert abs(r.physical_center_variance_over_mean - 1.0) < 0.05
    assert abs(r.physical_neighbor_correlation) < 0.03
    assert r.pre_psf_neighbor_correlation > 0.99
    assert abs(r.double_background_variance_ratio - 2.0) < 0.03


def test_spectral_wavelength_coverage_is_not_enough():
    r = run_spectral_support_check()
    assert r.wavelength_coverage_fraction > 0.999
    assert r.target_posterior_fractional_sigma > 0.10
    assert r.target_prior_fraction > 0.20
