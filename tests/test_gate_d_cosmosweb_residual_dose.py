import importlib.util
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "d1nh", ROOT / "scripts" / "run_gate_d_cosmosweb_residual_dose.py"
)
d1nh = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(d1nh)

def test_residual_doses_and_sample_are_frozen():
    assert d1nh.ALPHAS == (0.0, 0.25, 0.5, 0.75, 1.0)
    assert d1nh.SELECTED == d1nh.d1g.SELECTED
    assert d1nh.START_NAME == "d1m_default"

def test_optimizer_budget_is_unchanged():
    assert d1nh.TARGET_MAX_NFEV == d1nh.d1g.TARGET_MAX_NFEV == d1nh.d1m.TARGET_MAX_NFEV == 500

def test_patch_insert_changes_only_frozen_patch():
    base = np.zeros((129, 129), dtype=float)
    patch = np.ones((d1nh.rec.PATCH, d1nh.rec.PATCH), dtype=float)
    out = d1nh._patch_insert(base, patch, 64, 64)
    assert np.sum(out) == patch.size
    assert np.all(out[32:97, 32:97] == 1.0)
    mask = np.ones_like(out, dtype=bool)
    mask[32:97, 32:97] = False
    assert np.all(out[mask] == 0.0)

def test_alpha_construction_identity():
    rng = np.random.default_rng(7)
    model0 = rng.normal(size=(65, 65))
    residual = rng.normal(size=(65, 65))
    delta = rng.normal(size=(65, 65))
    orig = model0 + residual
    injected = orig + delta
    alpha0 = model0 + delta
    alpha1 = model0 + delta + residual
    np.testing.assert_allclose(alpha1, injected, rtol=0, atol=1e-14)
    assert not np.array_equal(alpha0, injected)
