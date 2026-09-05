import importlib.util
from pathlib import Path
import numpy as np
import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "run_gate_d_cosmosweb_real_injection.py"
spec = importlib.util.spec_from_file_location("gate_d_real_injection", SCRIPT)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


def test_sersic_and_convolution_are_normalized_and_nonnegative():
    prof = mod.sersic_profile(65, re_pix=5.0, n=1.0, q=0.65, pa_deg=30.0, oversample=3)
    psf = np.ones((5,5), dtype=float); psf /= psf.sum()
    out = mod.convolve_normalized(prof, psf)
    assert np.all(out >= 0)
    assert out.sum() == pytest.approx(1.0, abs=1e-12)


def test_ab_surface_brightness_conversion_round_trip():
    unit = np.zeros((11,11)); unit[5,5] = 1.0
    pixar_sr = 2.11539874851881e-14
    stamp, jy = mod.surface_brightness_stamp(unit, 29.0, pixar_sr)
    realized = stamp.sum() * 1e6 * pixar_sr
    assert realized == pytest.approx(jy, rel=1e-14)


def test_injection_adds_source_once_and_never_background():
    sci = np.arange(41*41, dtype=float).reshape(41,41) / 1000.0
    stamp = np.ones((9,9), dtype=float) / 81.0
    out = mod.inject_stamp(sci, stamp, 20, 20)
    delta = out - sci
    assert delta.sum() == pytest.approx(1.0, abs=1e-12)
    assert np.count_nonzero(delta) == 81
    assert np.all(delta[:10,:10] == 0)


def test_truncated_frozen_position_is_hard_failure():
    with pytest.raises(ValueError, match="truncate"):
        mod.inject_stamp(np.zeros((31,31)), np.ones((15,15)), 4, 15)
