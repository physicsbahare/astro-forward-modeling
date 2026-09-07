import importlib.util
from pathlib import Path
import numpy as np
import pytest
pytest.importorskip("astropy")

SCRIPT = Path(__file__).parents[1] / "scripts" / "run_gate_d_cosmosweb_forced_recovery.py"
spec = importlib.util.spec_from_file_location("gate_d_rec", SCRIPT)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


def test_bounds_are_scientifically_frozen():
    assert mod.PATCH == 65
    assert np.allclose(mod.BOUNDS_LO[1:3], [-2.0, -2.0])
    assert np.allclose(mod.BOUNDS_HI[1:3], [2.0, 2.0])
    assert np.isclose(np.exp(mod.BOUNDS_LO[3]), 1.0)
    assert np.isclose(np.exp(mod.BOUNDS_HI[3]), 20.0)
    assert np.isclose(mod.BOUNDS_LO[4], 0.3) and np.isclose(mod.BOUNDS_HI[4], 6.0)
    assert np.isclose(mod.BOUNDS_LO[5], 0.2) and np.isclose(mod.BOUNDS_HI[5], 1.0)


def test_insufficient_valid_weights_remain_failure_observable():
    image = np.zeros((129,129), float)
    err = np.ones_like(image)
    err[32:97,32:97] = np.nan
    out = mod.fit_one(image, err, 64, 64, np.ones((3,3))/9.0, 2.1e-14)
    assert out["optimizer_success"] is False
    assert out["reason"] == "insufficient_valid_weight_pixels"
