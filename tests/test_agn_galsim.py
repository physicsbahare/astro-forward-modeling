import sys
from pathlib import Path
import numpy as np
import pytest
from scipy.special import gammaincinv, gamma
pytest.importorskip('galsim')  # Optional for base suite; mandatory in dedicated workflow/script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from run_agn_galsim import profile, render, SETTINGS, VERSION, galsim
from run_agn_nuclear_fraction_noiseless import Renderer


def test_profile_semimajor_radius_flux_and_orientation():
    assert galsim.__version__ == VERSION
    for n in (1,4):
        obj = profile(n, SETTINGS['fine'])
        b = gammaincinv(2*n,.5)
        expected = b**(2*n)/(2*np.pi*n*.6*16**2*gamma(2*n))*np.exp(-b)
        # Both positions lie on the same half-light ellipse, not on a circle.
        for x,y in [(16/np.sqrt(2),16/np.sqrt(2)),(-9.6/np.sqrt(2),9.6/np.sqrt(2))]:
            np.testing.assert_allclose(obj.xValue(galsim.PositionD(x,y)),expected,rtol=1e-7)
        np.testing.assert_allclose(obj.flux,1.,rtol=1e-14)


def test_gaussian_pixel_integration_and_center():
    _, point = render(1, SETTINGS['fine'])
    exact = Renderer(stamp=129,oversample=1).point
    # Algebraic PSF sanity test, frozen before first execution; not a morphology band.
    assert abs(point-exact).sum() < 1e-6
    np.testing.assert_allclose(point,point[::-1,::-1],atol=1e-12)
