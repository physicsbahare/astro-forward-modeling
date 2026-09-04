import importlib.metadata, numpy as np, pytest
pytest.importorskip("autogalaxy")
from scripts import run_pyautogalaxy_morphology_preflight as exp

def test_pinned_versions_and_frozen_scope():
    assert importlib.metadata.version("autogalaxy") == "2026.8.14.1"
    assert importlib.metadata.version("autoarray") == "2026.8.14.1"
    c=exp.config(); assert c["over_sample_size"] == 1; assert "no morphology band" in c["acceptance"]

def test_psf_is_normalized_operator_input():
    p=exp.gaussian_psf(); assert p.shape == (9,9); assert np.isfinite(p).all(); assert abs(p.sum()-1) < 1e-12; assert p.min() > 0

def test_analytic_circular_scene_is_rotation_independent():
    import autogalaxy as ag
    g=ag.Grid2D.uniform(shape_native=(21,21),pixel_scales=1.0,over_sample_size=1)
    a=exp.analytic_sersic(np.asarray(g.native),1.0,1.0,0.0)
    b=exp.analytic_sersic(np.asarray(g.native),1.0,1.0,63.0)
    assert np.max(np.abs(a-b)) < 1e-14
