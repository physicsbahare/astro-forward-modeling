import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from run_agn_shot_noise import source_noise, WhitenedRenderer, HOST_ELECTRONS, ARMS
from run_agn_nuclear_fraction_noiseless import profile_flux


def test_frozen_counts_and_pairing():
    assert HOST_ELECTRONS == 10000 and len(ARMS) == 2
    truth = np.full((300,300), .01)
    a, noise = source_noise(truth, 20260903, 0)
    b, other = source_noise(truth, 20260903, 0)
    np.testing.assert_array_equal(a, b)
    np.testing.assert_array_equal(noise, other)
    np.testing.assert_allclose(noise + truth, a/HOST_ELECTRONS)
    # Predeclared stochastic-generator sanity checks, not morphology criteria.
    assert abs(a.mean()-100) < .2
    assert abs(a.var()-100) < 2
    with pytest.raises(ValueError):
        source_noise(np.array([-1e-12]), 1, 0)


def test_whitened_templates_preserve_amplitudes():
    class Toy:
        point = np.array([[1.,0.],[0.,0.]])
        def host(self, re, n, q):
            return np.array([[.4,.3],[.2,.1]])
    t = Toy(); sigma = np.array([[2.,1.],[.5,.2]])
    w = WhitenedRenderer(t, sigma)
    data = 3*t.host(1,1,1)+7*t.point
    flux, pred = profile_flux(data/sigma, w.host(1,1,1), w.point)
    np.testing.assert_allclose(flux, [3,7], rtol=1e-12)
    np.testing.assert_allclose(pred*sigma, data, rtol=1e-12)
