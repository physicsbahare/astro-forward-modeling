import importlib.util
import math
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("astropy")
pytest.importorskip("scipy")
pytest.importorskip("photutils")
pytest.importorskip("skimage")

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "d1l", ROOT / "scripts" / "run_gate_d_cosmosweb_parametric_neighbour_sersic.py"
)
d1l = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(d1l)


def test_d1l_limits_and_target_bounds_are_frozen():
    assert d1l.MAX_NEIGHBOURS == 3
    assert d1l.MAX_NFEV == 500
    np.testing.assert_allclose(
        d1l.rec.BOUNDS_LO[:7],
        [math.log(1e-4), -2, -2, math.log(1), 0.3, 0.2, -90],
    )
    np.testing.assert_allclose(
        d1l.rec.BOUNDS_HI[:7],
        [math.log(1e4), 2, 2, math.log(20), 6, 1, 90],
    )
    np.testing.assert_allclose(
        d1l.NEIGH_LO,
        [math.log(1e-4), -2, -2, math.log(1), 0.3, 0.2, -90],
    )
    np.testing.assert_allclose(
        d1l.NEIGH_HI,
        [math.log(1e4), 2, 2, math.log(20), 6, 1, 90],
    )


def test_three_nearest_children_are_modeled_and_rest_exact_masked():
    shape = (65, 65)
    labels = np.zeros(shape, dtype=int)
    orig = np.zeros(shape, dtype=float)
    centers = {
        1: (34, 32),
        2: (38, 32),
        3: (32, 42),
        4: (20, 32),
        5: (50, 32),
    }
    for label, (x, y) in centers.items():
        labels[y - 1 : y + 2, x - 1 : x + 2] = label
        orig[y - 1 : y + 2, x - 1 : x + 2] = 10.0 - label * 0.1

    catalog = d1l.build_child_catalog(orig, labels, 0.0)
    selected, masked, exact_mask = d1l.select_neighbours(labels, catalog, 32, 32)

    assert [m["label"] for m in selected] == [1, 2, 3]
    assert masked == [4, 5]
    assert np.array_equal(exact_mask, np.isin(labels, [4, 5]))
    assert exact_mask.sum() == int((labels == 4).sum() + (labels == 5).sum())


def test_neighbour_seed_and_render_are_finite_without_psf_double_counting():
    orig = np.zeros((65, 65), dtype=float)
    labels = np.zeros_like(orig, dtype=int)
    labels[30:35, 29:36] = 1
    orig[30:35, 29:36] = 4.0
    catalog = d1l.build_child_catalog(orig, labels, 0.0)
    selected, _, _ = d1l.select_neighbours(labels, catalog, 32, 32)
    assert len(selected) == 1

    theta = d1l.initial_neighbour_theta(selected[0], base_amp=1.0)
    image = d1l.render_neighbour(theta, selected[0], np.array([[1.0]]), base_amp=1.0)
    assert image.shape == (65, 65)
    assert np.all(np.isfinite(image))
    assert np.all(image >= 0)
    assert float(image.sum()) > 0
