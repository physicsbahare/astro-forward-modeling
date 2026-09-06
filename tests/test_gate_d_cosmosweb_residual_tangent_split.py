import importlib.util
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "d1nj", ROOT / "scripts" / "run_gate_d_cosmosweb_residual_tangent_split.py"
)
d1nj = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(d1nj)


def test_modes_and_inherited_frozen_settings():
    assert d1nj.MODES == (
        "none", "tangent_only", "orthogonal_only",
        "background_residualized_full", "original_full"
    )
    assert d1nj.START_NAME == d1nj.d1nh.START_NAME == "d1m_default"
    assert d1nj.TARGET_MAX_NFEV == d1nj.d1nh.TARGET_MAX_NFEV == 500
    np.testing.assert_allclose(d1nj.d1ni.FD_STEPS,
                               np.array([1e-3,1e-3,1e-3,1e-3,1e-3,1e-4,1e-2]))


def test_decomposition_identity_and_orthogonality():
    rng = np.random.default_rng(7)
    m = 80
    bg = np.column_stack([np.ones(m), np.linspace(-1,1,m), np.linspace(1,-.2,m)**2])
    jac = rng.normal(size=(m,7))
    y = rng.normal(size=m)
    out = d1nj.decompose(y, jac, bg)
    np.testing.assert_allclose(out["tangent"] + out["orthogonal"],
                               out["background_residualized"], rtol=0, atol=1e-12)
    # Orthogonal component is least-squares orthogonal to the residualized tangent columns.
    np.testing.assert_allclose(out["jacobian"].T @ out["orthogonal"],
                               np.zeros(7), rtol=0, atol=1e-10)


def test_component_patch_keeps_masked_pixels_and_exact_modes():
    shape = (5,5)
    injected = np.arange(25, dtype=float).reshape(shape)
    model0 = np.full(shape, 10.0)
    delta = np.full(shape, 2.0)
    sigma = np.full(shape, 0.5)
    valid = np.ones(shape, dtype=bool)
    valid[0,0] = False
    n = int(valid.sum())
    original = np.linspace(-1,1,n)
    tangent = original * 0.25
    orth = original * 0.75
    parts = {
        "tangent": tangent,
        "orthogonal": orth,
        "background_residualized": tangent + orth,
    }
    p_none, w_none = d1nj._component_patch(
        injected, model0, delta, sigma, valid, "none", original, parts)
    p_tan, w_tan = d1nj._component_patch(
        injected, model0, delta, sigma, valid, "tangent_only", original, parts)
    p_full, w_full = d1nj._component_patch(
        injected, model0, delta, sigma, valid, "original_full", original, parts)
    assert p_none[0,0] == injected[0,0]
    assert p_tan[0,0] == injected[0,0]
    assert p_full[0,0] == injected[0,0]
    np.testing.assert_allclose(p_none[valid], (model0+delta)[valid])
    np.testing.assert_allclose(p_tan[valid], (model0+delta)[valid] + sigma[valid]*tangent)
    np.testing.assert_allclose(p_full[valid], (model0+delta)[valid] + sigma[valid]*original)
    np.testing.assert_allclose(w_none, 0.0)
    np.testing.assert_allclose(w_tan, tangent)
    np.testing.assert_allclose(w_full, original)
