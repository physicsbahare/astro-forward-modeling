import importlib.util
from pathlib import Path
import numpy as np
import pytest
pytest.importorskip("astropy")

SCRIPT = Path(__file__).parents[1] / "scripts" / "run_gate_d_cosmosweb_simultaneous_neighbour_templates.py"
spec = importlib.util.spec_from_file_location("gate_d_d1h", SCRIPT)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


def test_connected_components_and_templates_are_preinjection_fixed():
    orig = np.zeros((15, 15), dtype=float)
    err = np.ones_like(orig)
    orig[3:5, 3:5] = 10.0
    orig[10:12, 10:13] = 8.0
    labels, nlab, bg, mask = mod.labelled_scene_components(orig, err)
    assert nlab == 2
    assert mask.sum() == 10
    templates, meta = mod.component_templates(orig, labels, bg)
    assert templates.shape == (2, 15, 15)
    assert [m["pixels"] for m in meta] == [4, 6]
    assert np.all(templates >= 0)
    assert np.allclose(np.sqrt(np.sum(templates * templates, axis=(1, 2))), 1.0)


def test_template_amplitudes_do_not_change_target_bounds():
    assert np.allclose(mod.rec.BOUNDS_LO[:7], [np.log(1e-4), -2, -2, np.log(1), 0.3, 0.2, -90])
    assert np.allclose(mod.rec.BOUNDS_HI[:7], [np.log(1e4), 2, 2, np.log(20), 6, 1, 90])


def test_no_component_returns_empty_template_stack():
    orig = np.zeros((9, 9), dtype=float)
    labels = np.zeros((9, 9), dtype=int)
    t, meta = mod.component_templates(orig, labels, 0.0)
    assert t.shape == (0, 9, 9)
    assert meta == []
