import numpy as np
import pytest

from verification.nircam_throughput_sensitivity import (
    pivot_wavelength_um,
    fnu_response_moments,
    mapped_target_moments,
    interpolation_weights,
    combine_images,
)


def test_pivot_for_tophat_is_finite_and_inside_band():
    lam = np.linspace(1.0, 2.0, 10001)
    thr = np.ones_like(lam)
    p = pivot_wavelength_um(lam, thr)
    assert 1.0 < p < 2.0


def test_linear_band_averages_are_recovered_exactly():
    lam1 = np.linspace(1.0, 1.5, 1001)
    lam2 = np.linspace(2.0, 2.8, 1001)
    t1 = np.ones_like(lam1)
    t2 = np.ones_like(lam2)
    A = np.vstack([
        fnu_response_moments(lam1, t1, 1),
        fnu_response_moments(lam2, t2, 1),
    ])
    target = np.array([1.0, 1.8])
    weights = interpolation_weights(A, target)
    coeff = np.array([3.0, 2.0])
    source_means = A @ coeff
    assert np.dot(weights, source_means) == pytest.approx(np.dot(target, coeff), rel=1e-12)
    assert weights.sum() == pytest.approx(1.0, abs=1e-12)


def test_quadratic_band_averages_are_recovered_exactly():
    bands = []
    for lo, hi in [(0.9, 1.2), (1.3, 1.7), (2.3, 3.1)]:
        lam = np.linspace(lo, hi, 1001)
        bands.append(fnu_response_moments(lam, np.ones_like(lam), 2))
    A = np.vstack(bands)
    target = np.array([1.0, 1.9, 1.9**2 + 0.02])
    weights = interpolation_weights(A, target)
    coeff = np.array([1.2, -0.4, 0.3])
    source_means = A @ coeff
    assert np.dot(weights, source_means) == pytest.approx(np.dot(target, coeff), rel=1e-12)
    assert weights.sum() == pytest.approx(1.0, abs=1e-12)


def test_redshift_mapping_scales_moment_order():
    m = np.array([1.0, 4.0, 18.0])
    out = mapped_target_moments(m, z_source=0.5, z_target=2.0)
    s = 1.5 / 3.0
    assert np.allclose(out, [1.0, 4.0*s, 18.0*s*s])


def test_combine_images():
    a = np.ones((3, 3))
    b = np.full((3, 3), 2.0)
    out = combine_images([a, b], np.array([0.25, 0.75]))
    assert np.allclose(out, 1.75)
