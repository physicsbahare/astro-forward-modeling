import importlib.util
from pathlib import Path
import numpy as np
import pytest
pytest.importorskip("astropy")

SCRIPT = Path(__file__).parents[1] / "scripts" / "run_gate_d_cosmosweb_neighbour_mask_control.py"
spec = importlib.util.spec_from_file_location("gate_d_mask", SCRIPT)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


def test_mask_definition_reuses_d1c_five_sigma_without_dilation():
    orig = np.zeros((129, 129), float)
    err = np.ones_like(orig)
    orig[20, 30] = 6.0
    orig[40, 50] = 4.9
    mask, bg = mod.build_scene_mask(orig, err)
    assert np.isfinite(bg)
    assert mod.THRESHOLD_SIGMA == 5.0
    assert mask[20, 30]
    assert not mask[40, 50]
    assert mask.sum() == 1


def test_existing_fitter_mask_keeps_insufficient_pixels_as_failure():
    image = np.zeros((129, 129), float)
    err = np.ones_like(image)
    mask = np.zeros_like(image, dtype=bool)
    mask[32:97, 32:97] = True
    out = mod.rec.fit_one(image, err, 64, 64, np.ones((3,3))/9.0, 2.1e-14, exclude_mask=mask)
    assert out["optimizer_success"] is False
    assert out["reason"] == "insufficient_valid_weight_pixels"
    assert out["valid_fraction"] == 0.0


def test_frozen_recovery_bounds_unchanged():
    assert np.allclose(mod.rec.BOUNDS_LO[1:3], [-2.0, -2.0])
    assert np.allclose(mod.rec.BOUNDS_HI[1:3], [2.0, 2.0])
    assert np.isclose(np.exp(mod.rec.BOUNDS_LO[3]), 1.0)
    assert np.isclose(np.exp(mod.rec.BOUNDS_HI[3]), 20.0)
    assert np.isclose(mod.rec.BOUNDS_LO[4], 0.3) and np.isclose(mod.rec.BOUNDS_HI[4], 6.0)
    assert np.isclose(mod.rec.BOUNDS_LO[5], 0.2) and np.isclose(mod.rec.BOUNDS_HI[5], 1.0)
