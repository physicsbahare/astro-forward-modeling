import importlib.metadata
import numpy as np
import pytest

pytest.importorskip("astrophot")
torch = pytest.importorskip("torch")

from scripts import run_dewsnap_astrophot_psf_preflight as experiment


def test_frozen_environment_and_claim():
    cfg = experiment.configuration()
    assert importlib.metadata.version("astrophot") == "0.18.0"
    assert torch.__version__ == "2.14.0+cpu"
    assert cfg["negative_psf_samples_clipped"] is False
    assert "preflight only" in cfg["claim"]


def test_signed_asymmetric_psf_roundtrip_and_convolution():
    psf = np.zeros((201, 201), dtype=float)
    psf[100, 100], psf[99, 101], psf[104, 96] = 1.0, 0.2, -0.05
    metrics, public, rendered = experiment.evaluate(psf)
    assert metrics["negative_pixel_count"] == 1
    assert metrics["public_roundtrip_max_abs_error"] == 0
    assert metrics["internal_transpose_max_abs_error"] <= experiment.ATOL
    assert metrics["untransposed_max_abs_error"] > experiment.ATOL
    assert np.min(public) < 0 and np.min(rendered) < 0
