from __future__ import annotations

import numpy as np
import pytest

from verification.passive_spiral_real_context import (
    inject_stamp_copy,
    p2_target_templates,
    weighted_template_fit,
)


def test_p2_templates_preserve_unit_total_and_signed_zero_total_arm_residual() -> None:
    spiral, smooth, arm = p2_target_templates()
    assert spiral.shape == smooth.shape == arm.shape
    assert spiral.ndim == 2
    assert spiral.shape[0] == spiral.shape[1]
    assert spiral.shape[0] % 2 == 1
    assert float(spiral.sum()) == pytest.approx(1.0, rel=0.0, abs=2e-14)
    assert float(smooth.sum()) == pytest.approx(1.0, rel=0.0, abs=2e-14)
    assert float(arm.sum()) == pytest.approx(0.0, rel=0.0, abs=2e-14)


def test_injection_returns_copy_without_mutating_input_science() -> None:
    sci = np.zeros((31, 31), dtype=float)
    stamp = np.ones((5, 5), dtype=float)
    before = sci.copy()
    out = inject_stamp_copy(sci, stamp, 15, 15)
    assert np.array_equal(sci, before)
    assert float(out.sum()) == pytest.approx(25.0)


def test_exact_constructed_spiral_recovers_unbounded_unit_coefficients() -> None:
    _, smooth, arm = p2_target_templates()
    err = np.ones_like(smooth)
    constructed = smooth + arm
    fit = weighted_template_fit(constructed, err, smooth, arm)
    assert fit.rank == 5
    assert fit.smooth_coefficient == pytest.approx(1.0, rel=0.0, abs=2e-11)
    assert fit.arm_coefficient == pytest.approx(1.0, rel=0.0, abs=2e-11)


def test_negative_arm_coefficient_is_preserved_not_clipped() -> None:
    _, smooth, arm = p2_target_templates()
    err = np.ones_like(smooth)
    constructed = 0.7 * smooth - 0.4 * arm
    fit = weighted_template_fit(constructed, err, smooth, arm)
    assert fit.smooth_coefficient == pytest.approx(0.7, rel=0.0, abs=2e-11)
    assert fit.arm_coefficient == pytest.approx(-0.4, rel=0.0, abs=2e-11)
    assert fit.arm_coefficient < 0.0
