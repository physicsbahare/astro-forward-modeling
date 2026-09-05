import importlib.util
from pathlib import Path
import numpy as np

P = Path(__file__).resolve().parents[1] / "scripts" / "run_gate_d_cosmosweb_psf_field_bracket.py"
spec = importlib.util.spec_from_file_location("d1n", P); d1n = importlib.util.module_from_spec(spec); spec.loader.exec_module(d1n)


def test_bracket_is_frozen_and_interior():
    assert [p for _, p in d1n.BRACKET_POSITIONS] == [(256,256),(1792,256),(256,1792),(1792,1792)]
    assert all(0 < x < 2047 and 0 < y < 2047 for _, (x,y) in d1n.BRACKET_POSITIONS)


def test_psf_metrics_normalized_symmetric_control():
    y, x = np.indices((31,31), dtype=float); p = np.exp(-((x-15)**2+(y-15)**2)/(2*2.0**2))
    m = d1n.psf_metrics(p)
    assert abs(m["sum"] - 1.0) < 1e-12
    assert m["centroid_offset_from_array_center_pix"] < 1e-10
    assert abs(m["axis_ratio_moment"] - 1.0) < 1e-10
    assert m["ee80_radius_pix"] > m["ee50_radius_pix"] > 0


def test_identical_comparison_is_zero_l1_unit_correlation():
    p = np.zeros((9,9)); p[4,4] = 1.0
    c = d1n.compare_psfs(p, p)
    assert c["normalized_l1"] == 0.0
    assert abs(c["normalized_cross_correlation"] - 1.0) < 1e-12


def test_common_centered_handles_different_shapes_without_flux_change():
    a = np.ones((4,6)); b = np.ones((5,3))
    aa, bb = d1n.common_centered(a,b)
    assert aa.shape == bb.shape == (5,6)
    assert aa.sum() == a.sum() and bb.sum() == b.sum()
