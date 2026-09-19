import importlib.metadata, importlib.util
from pathlib import Path
import numpy as np
import pytest

pytest.importorskip("autogalaxy")
pytest.importorskip("autoarray")

PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pyautogalaxy_morphology_recovery.py"
spec = importlib.util.spec_from_file_location("b9b_runner", PATH)
experiment = importlib.util.module_from_spec(spec); spec.loader.exec_module(experiment)


def test_frozen_versions_and_design():
    cfg = experiment.configuration()
    assert importlib.metadata.version("autogalaxy") == "2026.8.14.1"
    assert importlib.metadata.version("autoarray") == "2026.8.14.1"
    assert cfg["acceptance"].startswith("completeness/finiteness")
    assert cfg["bounds"]["n"] == [0.5, 6.0]
    assert len(cfg["starts"]) == 3


def test_truth_renderers_are_finite_and_flux_positive():
    psf = experiment.gaussian_psf()
    assert abs(psf.sum() - 1.0) < 1e-12
    grid = experiment.ag.Grid2D.uniform(shape_native=experiment.SHAPE, pixel_scales=1.0, over_sample_size=1)
    grid_native = np.asarray(grid.native)
    kernel = experiment.ag.Array2D.no_mask(values=psf, pixel_scales=1.0)
    convolver = experiment.ag.Convolver(kernel=kernel, use_fft=False, normalize=False)
    p = np.array([0.35, -0.25, 0.6, 1.0, 8.0, 0.03])
    r0, c0 = experiment.independent_model(grid_native, psf, p)
    r1, c1 = experiment.ag_model(grid, convolver, p)
    assert np.isfinite(r0).all() and np.isfinite(c0).all()
    assert np.isfinite(r1).all() and np.isfinite(c1).all()
    assert experiment.analytic_total_flux(1.0, 8.0, 0.03) > 0
