import numpy as np

from verification.passive_spiral_phase_null import (
    P3_PHASE_OFFSETS_DEG,
    _fit_phase_bank,
    _rank_true,
    phase_bank_templates,
)


def test_phase_bank_is_frozen_and_finite():
    true_spiral, bank, smooth = phase_bank_templates()
    assert P3_PHASE_OFFSETS_DEG == (0.0, 45.0, 90.0, 135.0)
    assert set(bank) == set(P3_PHASE_OFFSETS_DEG)
    assert true_spiral.shape == smooth.shape
    assert all(v.shape == smooth.shape for v in bank.values())
    assert np.all(np.isfinite(true_spiral))
    assert np.all(np.isfinite(smooth))
    assert all(np.all(np.isfinite(v)) for v in bank.values())
    assert np.isclose(true_spiral.sum(), 1.0)
    assert np.isclose(smooth.sum(), 1.0)


def test_phase_bank_arm_residuals_are_nearly_zero_sum():
    _, bank, _ = phase_bank_templates()
    for basis in bank.values():
        assert abs(float(np.sum(basis))) < 1e-12


def test_paired_difference_prefers_true_phase():
    true_spiral, bank, smooth = phase_bank_templates()
    scale = 5.0
    data = true_spiral * scale
    err = np.ones_like(data)
    rows = _fit_phase_bank(
        data,
        err,
        smooth * scale,
        {p: b * scale for p, b in bank.items()},
    )
    best, rank, delta, arm = _rank_true(rows)
    assert best == 0.0
    assert rank == 1
    assert delta == 0.0
    assert abs(arm - 1.0) < 1e-10


def test_phase_score_ranking_does_not_clip_signed_coefficients():
    true_spiral, bank, smooth = phase_bank_templates()
    scale = 3.0
    data = smooth * scale - bank[0.0] * scale
    err = np.ones_like(data)
    rows = _fit_phase_bank(
        data,
        err,
        smooth * scale,
        {p: b * scale for p, b in bank.items()},
    )
    true = next(r for r in rows if r["phase_offset_deg"] == 0.0)
    assert true["arm_coefficient"] < 0.0
