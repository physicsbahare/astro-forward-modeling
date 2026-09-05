"""Regression tests for target-detector noise ordering and background handling."""

import numpy as np
import pytest

from verification.target_noise import inject_target_detector_noise


def test_real_background_is_inserted_once_without_renoising():
    expectation = np.full((32, 32), 12.0)
    background = np.arange(32 * 32, dtype=float).reshape(32, 32) / 100.0
    result = inject_target_detector_noise(
        expectation,
        rng=np.random.default_rng(11),
        real_background_electrons=background,
    )

    # The supplied real background must be preserved bit-for-bit and the final
    # image must be exactly the one arithmetic addition of source + background.
    # Do not test this by subtracting the source back out: floating-point
    # addition followed by subtraction is not bitwise reversible for decimal
    # values such as 0.01, even when no extra noise has been added.
    np.testing.assert_array_equal(result.background_electrons, background)
    np.testing.assert_array_equal(
        result.image_electrons,
        result.source_electrons + background,
    )


def test_synthetic_background_and_source_poisson_statistics():
    expectation = np.full((128, 128), 25.0)
    sigma_bg = 4.0
    result = inject_target_detector_noise(
        expectation,
        rng=np.random.default_rng(90210),
        gaussian_background_sigma_e=sigma_bg,
    )

    # A single large image provides enough independent detector pixels for a
    # stable check of the intended per-pixel source and sky statistics.
    assert abs(np.mean(result.source_electrons) - 25.0) < 0.20
    assert abs(np.var(result.source_electrons, ddof=1) / 25.0 - 1.0) < 0.04
    assert abs(np.mean(result.background_electrons)) < 0.12
    assert abs(np.var(result.background_electrons, ddof=1) / sigma_bg**2 - 1.0) < 0.04

    # Source and independently generated target background should not acquire
    # appreciable covariance merely from being added together.
    corr = np.corrcoef(
        result.source_electrons.ravel(),
        result.background_electrons.ravel(),
    )[0, 1]
    assert abs(corr) < 0.03


def test_background_modes_are_mutually_exclusive():
    with pytest.raises(ValueError, match="either a real background"):
        inject_target_detector_noise(
            np.ones((4, 4)),
            rng=np.random.default_rng(1),
            real_background_electrons=np.zeros((4, 4)),
            gaussian_background_sigma_e=2.0,
        )


def test_negative_expected_electrons_are_rejected():
    image = np.ones((4, 4))
    image[1, 1] = -1.0
    with pytest.raises(ValueError, match="non-negative"):
        inject_target_detector_noise(image, rng=np.random.default_rng(1))
