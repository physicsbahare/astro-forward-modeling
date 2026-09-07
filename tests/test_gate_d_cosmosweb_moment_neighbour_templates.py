import importlib.util
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("astropy")
pytest.importorskip("scipy")

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "d1j", ROOT / "scripts" / "run_gate_d_cosmosweb_moment_neighbour_templates.py"
)
d1j = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(d1j)


def test_moment_template_is_finite_normalized_and_smooth():
    orig = np.zeros((21, 21), dtype=float)
    labels = np.zeros((21, 21), dtype=int)
    labels[10, 10] = 1
    orig[10, 10] = 5.0
    templates, meta = d1j.moment_gaussian_templates(orig, labels, 0.0)
    assert templates.shape == (1, 21, 21)
    assert np.all(np.isfinite(templates))
    assert np.isclose(np.sqrt(np.sum(templates[0] ** 2)), 1.0)
    assert meta[0]["sigma_minor_pix"] >= d1j.MIN_SIGMA_PIX
    assert meta[0]["sigma_major_pix"] >= d1j.MIN_SIGMA_PIX
    assert templates[0, 10, 10] > templates[0, 10, 11] > 0


def test_moment_template_preserves_elliptical_orientation_information():
    orig = np.zeros((31, 31), dtype=float)
    labels = np.zeros((31, 31), dtype=int)
    for x, value in [(12, 1.0), (13, 2.0), (14, 4.0), (15, 5.0), (16, 4.0), (17, 2.0), (18, 1.0)]:
        labels[15, x] = 2
        orig[15, x] = value
    _, meta = d1j.moment_gaussian_templates(orig, labels, 0.0)
    assert len(meta) == 1
    assert meta[0]["sigma_major_pix"] > meta[0]["sigma_minor_pix"]
