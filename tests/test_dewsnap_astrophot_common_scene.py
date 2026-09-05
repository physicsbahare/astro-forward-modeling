import importlib.metadata
import math

import numpy as np
import pytest

pytest.importorskip("astrophot")
torch = pytest.importorskip("torch")

from scripts import run_dewsnap_astrophot_common_scene as experiment


def test_frozen_c6b_configuration():
    cfg = experiment.configuration()
    assert importlib.metadata.version("astrophot") == "0.18.0"
    assert torch.__version__ == "2.14.0+cpu"
    assert cfg["lm"] == {"max_iter": 100, "relative_tolerance": 1e-5}
    assert cfg["shape_bounds"] == {"q": [0.15, 1.0], "n": [0.5, 6.0], "re": [0.5, 60.0]}
    assert "no morphology recovery band" in cfg["acceptance"]
    assert "no manual normalization" in cfg["psf"]


def test_flux_to_ie_roundtrip_formula_is_positive():
    ie = experiment.total_flux_to_ie(1.0, n=1.0, re=16.0, q=0.6)
    assert np.isfinite(ie) and ie > 0
    bn = experiment.sersic_bn(1.0)
    coeff = 2 * math.pi * 0.6 * 16.0**2 * math.exp(bn) * bn**-2 * math.gamma(2.0)
    assert np.isclose(ie * coeff, 1.0, rtol=1e-14, atol=0)


def test_pa_mapping_and_endpoint_representation():
    assert np.isclose(math.degrees(experiment.mapped_pa(-45.0, "negate_imfit")), 45.0)
    assert np.isclose(math.degrees(experiment.mapped_pa(-45.0, "same_imfit")), 135.0)
    assert experiment.mapped_pa(0.0, "negate_imfit") == experiment.PA_ENDPOINT_EPS_RAD
    assert 0 < experiment.interior_pa(0.0) < math.pi


def test_astrophot_model_build_keeps_signed_psf_and_fixed_centers():
    data = np.zeros((201, 201), dtype=float)
    psf = np.zeros((201, 201), dtype=float)
    psf[100, 100] = 1.05
    psf[99, 101] = -0.05
    start = {"pa_rad": math.radians(45), "q": 0.6, "n": 1.0, "re": 16.0, "host_flux": 1.0, "point_flux": 1.0}
    target, psf_image, host, point, model = experiment.build_model(data, psf, start)
    public_psf = psf_image.data.detach().cpu().numpy()
    assert np.array_equal(public_psf, psf)
    assert np.min(public_psf) < 0
    assert host.center.dynamic is False
    assert point.center.dynamic is False
    rendered = model().data.detach().cpu().numpy()
    assert rendered.shape == data.shape
    assert np.isfinite(rendered).all()
