from __future__ import annotations

import pytest

from verification.yu_2023 import (
    ASYMMETRY_ROBUST_RESOLUTION_ANCHOR,
    LOG10_STELLAR_MASS_RANGE,
    N_NEARBY_GALAXIES,
    PUBLISHED_QUALITATIVE_TRENDS,
    TARGET_REDSHIFT_RANGE,
    literature_anchor_record,
    resolution_level,
    resolution_row,
)


def test_resolution_level_is_rp_over_fwhm() -> None:
    assert resolution_level(10.0, 2.0) == 5.0
    assert resolution_level(2.5, 0.5) == 5.0
    row = resolution_row(7.5, 1.5)
    assert row.rp_over_fwhm == 5.0


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
    assert ASYMMETRY_ROBUST_RESOLUTION_ANCHOR == 5.0

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


def test_anchor_record_does_not_promote_literature_cut_to_production_policy() -> None:
    record = literature_anchor_record()
    assert record["asymmetry_robust_resolution_anchor"] == 5.0
    assert "Literature anchors only" in str(record["semantics"])
    assert "production" in str(record["semantics"])
