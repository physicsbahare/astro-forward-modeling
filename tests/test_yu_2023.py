from __future__ import annotations

import pytest

from verification.yu_2023 import (
    ASYMMETRY_APERTURE_RP,
    ASYMMETRY_NOISE_F1,
    ASYMMETRY_NOISE_F2,
    ASYMMETRY_NOISE_FORMULA,
    ASYMMETRY_ROBUST_RESOLUTION_ANCHOR,
    CONCENTRATION_COEFFICIENT,
    LOG10_STELLAR_MASS_RANGE,
    N_NEARBY_GALAXIES,
    PETROSIAN_ETA,
    PUBLISHED_MEAN_DELTA_N,
    PUBLISHED_MEAN_DELTA_Q,
    PUBLISHED_QUALITATIVE_TRENDS,
    SERSIC_N_BOUNDS,
    TARGET_REDSHIFT_RANGE,
    TOTAL_LIGHT_APERTURE_RP,
    YU_RESOLUTION_LEVELS,
    literature_anchor_record,
    resolution_level,
    resolution_row,
)


def test_resolution_level_is_intrinsic_rp_over_fwhm() -> None:
    assert resolution_level(10.0, 2.0) == 5.0
    assert resolution_level(2.5, 0.5) == 5.0
    row = resolution_row(7.5, 1.5)
    assert row.rp_true_over_fwhm == 5.0


def test_resolution_level_requires_positive_scales() -> None:
    with pytest.raises(ValueError):
        resolution_level(0.0, 1.0)
    with pytest.raises(ValueError):
        resolution_level(1.0, 0.0)
    with pytest.raises(ValueError):
        resolution_level(-1.0, 1.0)


def test_frozen_yu_2023_literature_anchors() -> None:
    assert N_NEARBY_GALAXIES == 1816
    assert LOG10_STELLAR_MASS_RANGE == (9.75, 11.25)
    assert TARGET_REDSHIFT_RANGE == (0.75, 3.0)
    assert YU_RESOLUTION_LEVELS == (1.98, 3.0, 4.55, 6.89, 10.45, 15.83, 24.0)
    assert ASYMMETRY_ROBUST_RESOLUTION_ANCHOR == 5.0

    assert PETROSIAN_ETA == 0.20
    assert TOTAL_LIGHT_APERTURE_RP == 1.5
    assert ASYMMETRY_APERTURE_RP == 1.5
    assert CONCENTRATION_COEFFICIENT == 5.0
    assert ASYMMETRY_NOISE_F1 == 2.25
    assert ASYMMETRY_NOISE_F2 == 2.10
    assert SERSIC_N_BOUNDS == (0.5, 6.0)
    assert PUBLISHED_MEAN_DELTA_N == -0.11
    assert PUBLISHED_MEAN_DELTA_Q == -0.005

    assert (
        PUBLISHED_QUALITATIVE_TRENDS["petrosian_radius_nonparametric"]
        == "slightly_overestimated_with_psf_smoothing"
    )
    assert (
        PUBLISHED_QUALITATIVE_TRENDS["half_light_radius_model_fit"]
        == "no_significant_bias_reported"
    )
    assert (
        PUBLISHED_QUALITATIVE_TRENDS["sersic_index_model_fit"]
        == "no_significant_bias_reported"
    )
    assert (
        PUBLISHED_QUALITATIVE_TRENDS["asymmetry_intrinsically_asymmetric"]
        == "underestimated_more_at_lower_resolution"
    )
    assert (
        PUBLISHED_QUALITATIVE_TRENDS["concentration"]
        == "underestimated_more_at_lower_resolution_and_higher_intrinsic_concentration"
    )


def test_anchor_record_contains_exact_measurement_definitions() -> None:
    record = literature_anchor_record()
    assert record["resolution_levels"] == list(YU_RESOLUTION_LEVELS)
    assert record["petrosian_definition"]["eta"] == 0.20
    assert record["curve_of_growth_total_aperture_rp"] == 1.5
    assert record["curve_of_growth_radii"] == ["R20", "R50", "R80"]
    assert record["concentration_definition"] == "C = 5 log10(R80/R20)"
    assert record["asymmetry_aperture_rp"] == 1.5
    assert record["asymmetry_center"] == "chosen by minimizing asymmetry"

    noise = record["asymmetry_noise_correction"]
    assert noise["equation"] == ASYMMETRY_NOISE_FORMULA
    assert noise["F1_definition"] == "N(I0 < f1 sigma_bkg) / Nall"
    assert noise["F2_definition"] == "N(|I0-I180| < f2 sigma_bkg) / Nall"
    assert noise["f1"] == 2.25
    assert noise["f2"] == 2.10

    assert record["single_sersic_fit"]["n_bounds"] == [0.5, 6.0]


def test_anchor_record_does_not_promote_literature_cut_to_production_policy() -> None:
    record = literature_anchor_record()
    assert record["asymmetry_robust_resolution_anchor"] == 5.0
    assert "Literature anchors only" in str(record["semantics"])
    assert "not a universal morphology cut" in str(record["semantics"])
