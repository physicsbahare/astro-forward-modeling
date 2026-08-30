"""Invariant tests for the Paulino-Afonso image-level diagnostic floor.

These are numerical/semantic checks only. They intentionally do not assert
that a pure single-Sersic experiment must reproduce the paper's Table-2 bias.
Convergence and parameter-bound hits remain benchmark observables rather than
pass/fail morphology thresholds.
"""

from __future__ import annotations

import numpy as np

from verification.paulino_afonso_2017 import luminosity_evolution_ratio
from verification.paulino_afonso_sersic_floor import (
    MIN_HALF_WIDTH_RE,
    POINT_DEPTH_AB_5SIGMA,
    SOURCE_REDSHIFT,
    TARGET_REDSHIFTS,
    TRUTH_CASES,
    _cosmology,
    _kpc_per_arcsec,
    _normalized_psf_stamp,
    adaptive_stamp_size,
    flux_in_depth_units,
    mag_from_depth_units,
    pixel_noise_from_point_depth,
    run_recovery_ensemble,
    target_flux_ratio_from_source,
    target_mag_from_source_mag,
)


def test_depth_normalization_gives_exact_matched_filter_snr_five() -> None:
    psf = _normalized_psf_stamp()
    sigma = pixel_noise_from_point_depth()
    flux = flux_in_depth_units(POINT_DEPTH_AB_5SIGMA)
    snr = flux * np.sqrt(np.sum(psf**2)) / sigma
    assert np.isclose(snr, 5.0, rtol=2e-15, atol=0.0)


def test_magnitude_flux_round_trip() -> None:
    for mag in (16.5, 22.0, 24.5, 27.2):
        recovered = mag_from_depth_units(flux_in_depth_units(mag))
        assert np.isclose(recovered, mag, rtol=0.0, atol=8e-15)


def test_target_flux_mapping_is_distance_squared_times_separate_evolution() -> None:
    cosmology = _cosmology()
    dl_s = cosmology.luminosity_distance_m(SOURCE_REDSHIFT)
    for z in TARGET_REDSHIFTS:
        expected = (
            (dl_s / cosmology.luminosity_distance_m(float(z))) ** 2
            * luminosity_evolution_ratio(SOURCE_REDSHIFT, float(z))
        )
        actual = target_flux_ratio_from_source(SOURCE_REDSHIFT, float(z))
        assert np.isclose(actual, expected, rtol=2e-15, atol=0.0)


def test_target_magnitude_is_exact_flux_ratio_representation() -> None:
    source_mag = 17.0
    for z in TARGET_REDSHIFTS:
        target_mag = target_mag_from_source_mag(source_mag, float(z))
        observed_flux_ratio = flux_in_depth_units(target_mag) / flux_in_depth_units(source_mag)
        expected = target_flux_ratio_from_source(SOURCE_REDSHIFT, float(z))
        assert np.isclose(observed_flux_ratio, expected, rtol=8e-15, atol=0.0)


def test_adaptive_footprint_never_repeats_old_re_truncation() -> None:
    for z in TARGET_REDSHIFTS:
        kpc_per_arcsec = _kpc_per_arcsec(float(z))
        for case in TRUTH_CASES:
            re_pix = float(case["re_kpc"]) / kpc_per_arcsec / 0.03
            size = adaptive_stamp_size(re_pix)
            half_width_over_re = (size - 1) / 2.0 / re_pix
            assert size % 2 == 1
            assert half_width_over_re >= MIN_HALF_WIDTH_RE


def test_small_recovery_smoke_run_preserves_identity_and_diagnostics() -> None:
    rows = run_recovery_ensemble(realizations=1, base_seed=2717)
    assert len(rows) == len(TARGET_REDSHIFTS) * len(TRUTH_CASES)
    assert {(r.case, r.z_target) for r in rows} == {
        (str(case["case"]), float(z)) for z in TARGET_REDSHIFTS for case in TRUTH_CASES
    }
    for row in rows:
        assert row.z_source == SOURCE_REDSHIFT
        assert row.half_width_over_re >= MIN_HALF_WIDTH_RE
        assert isinstance(row.fit_success, bool)
        assert isinstance(row.fit_status, int)
        assert isinstance(row.hit_n_lower_bound, bool)
        assert isinstance(row.hit_n_upper_bound, bool)
        assert np.isfinite(row.fit_cost) and row.fit_cost >= 0
        assert np.isfinite(row.re_ratio) and row.re_ratio > 0
        assert np.isfinite(row.n_ratio) and row.n_ratio > 0
        assert np.isfinite(row.q_difference)
        assert np.isfinite(row.mag_difference)
