import importlib.util
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("astropy")
pytest.importorskip("scipy")
pytest.importorskip("photutils")
pytest.importorskip("skimage")

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "d1k", ROOT / "scripts" / "run_gate_d_cosmosweb_deblended_neighbour_templates.py"
)
d1k = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(d1k)


def test_deblend_settings_are_frozen_package_defaults_except_minimum_child_area():
    assert d1k.DEBLEND_N_PIXELS == 3
    assert d1k.DEBLEND_N_LEVELS == 32
    assert d1k.DEBLEND_CONTRAST == 0.001
    assert d1k.DEBLEND_MODE == "exponential"
    assert d1k.DEBLEND_CONNECTIVITY == 8


def test_deblending_never_expands_or_erodes_frozen_parent_support():
    orig = np.zeros((51, 51), dtype=float)
    err = np.ones_like(orig)
    orig[23:28, 13:18] = 10.0
    orig[23:28, 33:38] = 9.0
    orig[25, 18:33] = 6.0
    parent_labels, n_parent, _, parent_mask = d1k.d1h.labelled_scene_components(orig, err)
    labels, _, scene_mask, meta = d1k.deblend_scene_components(orig, err)
    assert n_parent == 1
    assert np.array_equal(scene_mask, parent_mask)
    assert np.array_equal(labels > 0, parent_labels > 0)
    assert meta["deblended_component_count"] >= meta["parent_component_count"]
    assert meta["split_parent_count"] >= 0
