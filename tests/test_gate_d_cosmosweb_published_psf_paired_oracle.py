import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "d1nf", SCRIPTS / "run_gate_d_cosmosweb_published_psf_paired_oracle.py"
)
d1nf = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(d1nf)


def test_frozen_subset_and_optimizer_are_not_relaxed():
    assert d1nf.SELECTED == (
        ("near_source_2_5", 0, 168, 66),
        ("relatively_isolated_ge30", 1, 69, 195),
    )
    assert d1nf.TARGET_MAX_NFEV == 500
    np.testing.assert_array_equal(d1nf.rec.BOUNDS_LO, d1nf.rec.BOUNDS_LO)
    np.testing.assert_array_equal(d1nf.rec.BOUNDS_HI, d1nf.rec.BOUNDS_HI)


def test_signed_psf_normalization_preserves_negative_support():
    psf = np.array([[0.0, -0.01, 0.0], [0.02, 0.98, 0.02], [0.0, -0.01, 0.0]])
    out = d1nf.signed_normalize_psf(psf)
    assert np.isclose(out.sum(), 1.0)
    assert np.any(out < 0)
    assert np.isfinite(out).all()


def test_signed_convolution_keeps_unit_signed_flux():
    profile = np.zeros((9, 9), dtype=float)
    profile[4, 4] = 1.0
    psf = np.array([[0.0, -0.01, 0.0], [0.02, 0.98, 0.02], [0.0, -0.01, 0.0]])
    out = d1nf.signed_convolve_normalized(profile, psf)
    assert out.shape == profile.shape
    assert np.isfinite(out).all()
    assert np.isclose(out.sum(), 1.0)
    assert np.any(out < 0)
