import importlib.util
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "d1m", ROOT / "scripts" / "run_gate_d_cosmosweb_frozen_prefit_neighbour_scene.py"
)
d1m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(d1m)


def test_d1m_reuses_frozen_d1l_neighbour_definition():
    assert d1m.MAX_NEIGHBOURS == d1m.d1l.MAX_NEIGHBOURS == 3
    np.testing.assert_allclose(d1m.d1l.NEIGH_LO, d1m.d1l.NEIGH_LO)
    np.testing.assert_allclose(d1m.d1l.NEIGH_HI, d1m.d1l.NEIGH_HI)
    assert d1m.PREFIT_MAX_NFEV == 500
    assert d1m.TARGET_MAX_NFEV == 500


def test_plane_uses_d1e_normalized_patch_coordinates():
    plane = d1m._plane(np.array([2.0, 3.0, -4.0]))
    assert plane.shape == (d1m.rec.PATCH, d1m.rec.PATCH)
    assert plane[d1m.rec.HALF, d1m.rec.HALF] == 2.0
    assert np.isclose(plane[d1m.rec.HALF, -1], 5.0)
    assert np.isclose(plane[-1, d1m.rec.HALF], -2.0)


def test_target_fit_with_empty_frozen_scene_recovers_controlled_target():
    psf = np.zeros((9, 9), dtype=float)
    psf[4, 4] = 1.0
    pixar_sr = (0.03 / 206265.0) ** 2
    base_flux_jy = d1m.rec.inj.ab_to_jy(27.5)
    base_amp = base_flux_jy / (1e6 * pixar_sr)
    truth = np.array([0.0, 0.0, 0.0, math.log(6.0), 1.0, 0.65, 0.0, 0.02, 0.0, 0.0])
    image = d1m.rec._render(truth, psf, 0.03, base_amp)
    err_patch = np.full_like(image, 0.01)
    canvas = np.zeros((129, 129), dtype=float)
    err = np.ones_like(canvas)
    c = 64
    canvas[c-d1m.rec.HALF:c+d1m.rec.HALF+1, c-d1m.rec.HALF:c+d1m.rec.HALF+1] = image
    err[c-d1m.rec.HALF:c+d1m.rec.HALF+1, c-d1m.rec.HALF:c+d1m.rec.HALF+1] = err_patch
    prefit = {
        "_child_mask": np.zeros_like(image, dtype=bool),
        "_frozen_source": np.zeros_like(image),
        "n_neighbour_models": 0,
        "selected_neighbour_labels": [],
        "masked_child_labels": [],
        "masked_child_pixels": 0,
        "optimizer_success": True,
        "finite_solution": True,
        "any_nuisance_bound_hit": False,
    }
    out = d1m.fit_target_with_frozen_scene(canvas, err, c, c, psf, pixar_sr, prefit)
    assert out["optimizer_success"]
    assert out["finite_solution"]
    assert not out["any_bound_hit"]
    assert abs(out["recovered_re_pix"] - 6.0) < 1e-4
    assert abs(out["recovered_n"] - 1.0) < 1e-4
    assert abs(out["recovered_q"] - 0.65) < 1e-4
