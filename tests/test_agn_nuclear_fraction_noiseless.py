"""Algebra and detector-centering checks, not morphology acceptance cuts."""
import numpy as np
import importlib.util
from pathlib import Path

# Also support the repository-wide console-entry-point `pytest` invocation.
# The scripts directory is not an installed package.
_spec = importlib.util.spec_from_file_location(
    "agn_noiseless_diagnostic",
    Path(__file__).resolve().parents[1] / "scripts/run_agn_nuclear_fraction_noiseless.py",
)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
Renderer, profile_flux = _module.Renderer, _module.profile_flux


def test_profiled_flux_recovers_known_nonnegative_mixture():
    host = np.array([[1., 2.], [3., 4.]])
    point = np.array([[4., 1.], [0., 0.]])
    data = 2*host + 7*point
    flux, model = profile_flux(data, host, point)
    np.testing.assert_allclose(flux, [2, 7], rtol=1e-13, atol=1e-13)
    np.testing.assert_allclose(model, data, rtol=1e-13, atol=1e-13)


def test_profiled_flux_does_not_allow_negative_nucleus():
    host = np.array([[1., 0.], [0., 0.]])
    point = np.array([[0., 1.], [0., 0.]])
    flux, _ = profile_flux(host-point, host, point)
    np.testing.assert_array_equal(flux, [1, 0])


def test_psf_and_integrated_host_are_detector_centered():
    renderer = Renderer(stamp=33)
    host = renderer.host(4., 4., .6)
    for image in (renderer.point, host):
        np.testing.assert_allclose(image, image[::-1, ::-1], rtol=1e-12, atol=1e-15)
    np.testing.assert_allclose(renderer.point.sum(), 1, rtol=1e-13)
    # Finite support loss remains explicit, never compensated by renormalization.
    assert 0 < host.sum() < 1
