from __future__ import annotations

import math

import pytest

from verification.yu_2023 import (
    ASYMMETRY_NOISE_F1,
    ASYMMETRY_NOISE_F2,
    asymmetry_noise_corrected_from_terms,
)


def test_yu_equation_28_term_algebra() -> None:
    value = asymmetry_noise_corrected_from_terms(
        galaxy_residual_min=10.0,
        background_residual_min=2.0,
        galaxy_abs_flux_sum=20.0,
        background_abs_flux_sum=4.0,
        F1=0.25,
        F2=0.50,
    )
    assert value == pytest.approx(9.0 / 19.0)


def test_yu_equation_28_does_not_clip_negative_asymmetry() -> None:
    value = asymmetry_noise_corrected_from_terms(
        galaxy_residual_min=1.0,
        background_residual_min=3.0,
        galaxy_abs_flux_sum=20.0,
        background_abs_flux_sum=2.0,
        F1=0.2,
        F2=0.8,
    )
    assert value < 0.0


def test_yu_equation_28_rejects_nonpositive_corrected_denominator() -> None:
    with pytest.raises(ValueError):
        asymmetry_noise_corrected_from_terms(
            galaxy_residual_min=1.0,
            background_residual_min=1.0,
            galaxy_abs_flux_sum=2.0,
            background_abs_flux_sum=4.0,
            F1=0.5,
            F2=0.5,
        )


def test_published_yu_noise_thresholds_are_frozen() -> None:
    assert ASYMMETRY_NOISE_F1 == 2.25
    assert ASYMMETRY_NOISE_F2 == 2.10
    assert math.sqrt(2.0) != ASYMMETRY_NOISE_F2
