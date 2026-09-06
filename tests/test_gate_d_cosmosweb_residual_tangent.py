import importlib.util
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "d1ni", ROOT / "scripts" / "run_gate_d_cosmosweb_residual_tangent.py"
)
d1ni = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(d1ni)

def test_sample_and_finite_difference_steps_are_frozen():
    assert d1ni.SELECTED == d1ni.d1nh.SELECTED
    assert d1ni.PARAM_NAMES == ("log_amp_ratio", "dx", "dy", "log_re", "n", "q", "pa")
    np.testing.assert_allclose(d1ni.FD_STEPS, [1e-3, 1e-3, 1e-3, 1e-3, 1e-3, 1e-4, 1e-2])
    assert d1ni.ALPHA_SMALL == 0.25

def test_truth_is_exact_injected_source_definition():
    theta = d1ni.truth_theta()
    assert abs(np.exp(theta[3]) - 6.0) < 1e-14
    assert theta[1] == theta[2] == 0.0
    assert theta[4] == 1.0
    assert theta[5] == 0.65
    assert theta[6] == 30.0

def test_remove_subspace_annihilates_background():
    x = np.linspace(-1, 1, 41)
    b = np.column_stack([np.ones_like(x), x, x*x])
    y = b @ np.array([1.3, -2.1, 0.4])
    residual = d1ni.remove_subspace(y, b)
    assert np.linalg.norm(residual) < 1e-10

def test_tangent_projection_known_seven_parameter_signal():
    rng = np.random.default_rng(13)
    n = 120
    x = np.linspace(-1, 1, n)
    b = np.column_stack([np.ones(n), x, x*x])
    j = rng.normal(size=(n, 7))
    delta = np.array([0.3, -0.1, 0.2, 0.4, -0.25, 0.05, 0.6])
    y = j @ delta + b @ np.array([1.0, -0.4, 0.2])
    out = d1ni.tangent_projection(y, j, b)
    got = np.array([out["delta_theta_per_alpha"][name] for name in d1ni.PARAM_NAMES])
    np.testing.assert_allclose(got, delta, rtol=0, atol=1e-11)
    assert abs(out["target_tangent_power_fraction"] - 1.0) < 1e-12
