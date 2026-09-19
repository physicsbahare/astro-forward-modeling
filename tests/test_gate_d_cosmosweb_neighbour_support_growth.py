import importlib.util
from pathlib import Path
import numpy as np
import pytest

pytest.importorskip("astropy")
ROOT = Path(__file__).resolve().parents[1]

hspec = importlib.util.spec_from_file_location(
    "d1h", ROOT / "scripts" / "run_gate_d_cosmosweb_simultaneous_neighbour_templates.py"
)
d1h = importlib.util.module_from_spec(hspec)
hspec.loader.exec_module(d1h)

ispec = importlib.util.spec_from_file_location(
    "d1i", ROOT / "scripts" / "run_gate_d_cosmosweb_neighbour_support_growth.py"
)
d1i = importlib.util.module_from_spec(ispec)
ispec.loader.exec_module(d1i)


def test_zero_growth_is_exact_d1h_support():
    orig = np.arange(49, dtype=float).reshape(7, 7) / 10.0
    labels = np.zeros((7, 7), dtype=int)
    labels[3, 3] = 1
    labels[1:3, 5] = 2
    a, ma = d1h.component_templates(orig, labels, 0.0)
    b, mb = d1i.grown_component_templates(orig, labels, 0.0, 0)
    assert np.array_equal(a, b)
    assert [m["label"] for m in ma] == [m["label"] for m in mb]


def test_growth_never_shrinks_support_and_never_changes_component_identity():
    orig = np.ones((9, 9), dtype=float)
    labels = np.zeros((9, 9), dtype=int)
    labels[4, 4] = 7
    _, m0 = d1i.grown_component_templates(orig, labels, 0.0, 0)
    t2, m2 = d1i.grown_component_templates(orig, labels, 0.0, 2)
    assert m2[0]["label"] == m0[0]["label"] == 7
    assert m2[0]["support_pixels"] >= m0[0]["support_pixels"]
    assert np.all(t2 >= 0)


def test_negative_growth_rejected():
    orig = np.ones((5, 5), dtype=float)
    labels = np.zeros((5, 5), dtype=int)
    labels[2, 2] = 1
    with pytest.raises(ValueError):
        d1i.grown_component_templates(orig, labels, 0.0, -1)


def test_frozen_target_bounds_are_unchanged():
    assert np.array_equal(d1i.rec.BOUNDS_LO, d1h.rec.BOUNDS_LO)
    assert np.array_equal(d1i.rec.BOUNDS_HI, d1h.rec.BOUNDS_HI)
    assert d1i.GROWTH_PIXELS == (0, 2, 4)
