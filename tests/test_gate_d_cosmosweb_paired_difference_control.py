import importlib.util
from pathlib import Path
import numpy as np
import pytest
pytest.importorskip("astropy")
pytest.importorskip("scipy")

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("gate_d_delta", ROOT / "scripts" / "run_gate_d_cosmosweb_paired_difference_control.py")
mod = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)


def test_control_semantics_are_explicit(tmp_path):
    # Unit-test only the declared semantics here; the targeted workflow exercises
    # the real frozen FITS artifact and pinned STPSF data.
    assert mod.rec.BOUNDS_LO[1] == -2.0
    assert mod.rec.BOUNDS_HI[1] == 2.0
    assert mod.rec.BOUNDS_LO[4] == 0.3
    assert mod.rec.BOUNDS_HI[4] == 6.0


def test_same_renderer_recovers_noiseless_source_without_bound_hit():
    psf = np.zeros((9, 9), dtype=float); psf[4, 4] = 1.0
    pixar_sr = (0.03 / 206265.0) ** 2
    base_flux = mod.rec.inj.ab_to_jy(27.5)
    base_amp = base_flux / (1e6 * pixar_sr)
    truth = np.array([0.0, 0.0, 0.0, np.log(6.0), 1.0, 0.65, 20.0, 0.0, 0.0, 0.0])
    patch = mod.rec._render(truth, psf, 0.03, base_amp)
    image = np.zeros((129, 129), dtype=float)
    image[32:97, 32:97] = patch
    err = np.ones_like(image) * 1e-4
    fit = mod.rec.fit_one(image, err, 64, 64, psf, pixar_sr)
    assert fit["optimizer_success"]
    assert not fit["any_bound_hit"]
    assert abs(fit["recovered_re_pix"] - 6.0) < 0.2
    assert abs(fit["recovered_n"] - 1.0) < 0.1
    assert abs(fit["recovered_q"] - 0.65) < 0.05
