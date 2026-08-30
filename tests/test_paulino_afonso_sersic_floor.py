"""Invariant tests for the Paulino-Afonso image-level diagnostic floor.

These are numerical/semantic checks only.  They intentionally do not assert
that a pure single-Sersic experiment must reproduce the paper's Table-2 bias.
They also do not require every low-S/N fit to converge: Paulino-Afonso et al.
explicitly report non-convergence fractions and exclude those objects from the
structural sample, so convergence is itself a benchmark observable.
"""

from __future__ import annotations

import numpy as np

from verification.paulino_afonso_sersic_floor import (
    POINT_DEPTH_AB_5SIGMA,
    TARGET_REDSHIFTS,
    TRUTH_CASES,
    _normalized_psf_stamp,
    flux_in_depth_units,
    mag_from_depth_units,
    pixel_noise_from_point_depth,
    run_recovery_ensemble,
)


def test_depth_normalization_gives_exact_matched_filter_snr_five() -> None:
    psf = _normalized_psf_stamp()
    sigma = pixel_noise_from_point_depth()
    flux = flux_in_depth_units(POINT_DEPTH_AB_5SIGMA)
    snr = flux * np.sqrt(np.sum(psf**2)) / sigma
    assert np.isclose(snr, 5.0, rtol=2e-15, atol=0.0)


def test_magnitude_flux_round_trip() -> None:
    for mag in (23.5, 24.5, 26.0, POINT_DEPTH_AB_5SIGMA):
        recovered = mag_from_depth_units(flux_in_depth_units(mag))
        assert np.isclose(recovered, mag, rtol=0.0, atol=8e-15)


def test_small_recovery_smoke_run_preserves_row_identity_and_finite_outputs() -> None:
    rows = run_recovery_ensemble(realizations=1, base_seed=2717, stamp_size=61)
    assert len(rows) == len(TARGET_REDSHIFTS) * len(TRUTH_CASES)
    assert {(r.case, r.z_target) for r in rows} == {
        (str(case["case"]), float(z)) for z in TARGET_REDSHIFTS for case in TRUTH_CASES
    }
    for row in rows:
        # Fit success/status is archived rather than thresholded here because
        # non-convergence is a physically meaningful low-S/N outcome in the
        # literature experiment itself.
        assert isinstance(row.fit_success, bool)
        assert isinstance(row.fit_status, int)
        assert np.isfinite(row.fit_cost) and row.fit_cost >= 0
        assert np.isfinite(row.re_ratio) and row.re_ratio > 0
        assert np.isfinite(row.n_ratio) and row.n_ratio > 0
        assert np.isfinite(row.q_difference)
        assert np.isfinite(row.mag_difference)
