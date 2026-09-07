import numpy as np
import pytest

from verification.passive_disk_real_pilot import (
    required_source_wavelength_um,
    linear_wavelength_weight,
    inu_source_to_target_factor,
    degradation_kernel_fwhm,
    interpolate_inu,
    rescale_about_center,
    render_r1_from_homogenized_pair,
    aperture_morphology_proxy,
)


def test_frozen_r1_scalar_values():
    zs = 0.4304
    lam = required_source_wavelength_um(2.776, zs, 1.0)
    assert lam == pytest.approx(1.9853952, abs=5e-7)
    assert linear_wavelength_weight(lam, 1.501, 2.776) == pytest.approx(0.379918, abs=2e-6)
    assert inu_source_to_target_factor(zs, 1.0) == pytest.approx(0.365833, abs=1e-6)
    assert degradation_kernel_fwhm(0.092, 0.064481) == pytest.approx(0.065622, abs=2e-6)


def test_no_extrapolation_or_sharpening():
    with pytest.raises(ValueError):
        linear_wavelength_weight(1.2, 1.501, 2.776)
    with pytest.raises(ValueError):
        degradation_kernel_fwhm(0.05, 0.06)


def test_interpolation_is_native_inu_linear():
    a = np.ones((5, 5))
    b = np.full((5, 5), 3.0)
    assert np.allclose(interpolate_inu(a, b, 0.25), 1.5)


def test_rescaling_surface_brightness_semantics():
    img = np.zeros((51, 51))
    img[25, 25] = 4.0
    out = rescale_about_center(img, 0.7)
    assert out[25, 25] == pytest.approx(4.0)


def test_render_applies_single_inu_factor():
    lo = np.ones((51, 51))
    hi = np.ones((51, 51))
    out = render_r1_from_homogenized_pair(
        lo,
        hi,
        interpolation_weight=0.4,
        angular_scale=1.0,
        inu_factor=0.2,
        target_kernel_fwhm_arcsec=0.0,
        pixel_scale_arcsec=0.03,
    )
    assert np.allclose(out, 0.2)


def test_morphology_proxy_detects_elongation():
    y, x = np.indices((101, 101), dtype=float)
    g = np.exp(-0.5 * (((x - 50) / 10) ** 2 + ((y - 50) / 4) ** 2))
    m = aperture_morphology_proxy(g, center_xy=(50, 50), pixel_scale_arcsec=0.03)
    assert 0.3 < m.axis_ratio < 0.5
    assert m.centroid_offset_arcsec < 1e-10
    assert 0 < m.concentration < 1
