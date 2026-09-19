import numpy as np

from verification.passive_spiral_real_context import weighted_template_fit
from verification.passive_spiral_robust_loss import (
    P5_F_SCALE,
    P5_LOSS,
    evaluate_p5_case,
    robust_template_fit,
)


def test_p5_huber_settings_are_frozen():
    assert P5_LOSS == "huber"
    assert P5_F_SCALE == 1.0


def test_robust_fit_does_not_mutate_inputs_and_records_optimizer_state():
    n = 21
    yy, xx = np.indices((n, n), dtype=float)
    smooth = np.exp(-((xx - 10) ** 2 + (yy - 10) ** 2) / 20.0)
    smooth /= smooth.sum()
    arm = ((xx - 10) / 10.0) * smooth
    data = 0.02 + 2.0 * smooth + 0.7 * arm
    err = np.full_like(data, 0.01)
    data0 = data.copy(); err0 = err.copy()
    fit = robust_template_fit(data, err, smooth, arm)
    assert np.array_equal(data, data0)
    assert np.array_equal(err, err0)
    assert fit["optimizer_success"]
    assert fit["finite_solution"]
    assert fit["optimizer_nfev"] >= 1
    assert np.isfinite(fit["objective_cost"])


def test_huber_reduces_single_large_residual_leverage_without_clipping():
    n = 31
    yy, xx = np.indices((n, n), dtype=float)
    smooth = np.exp(-((xx - 15) ** 2 + (yy - 15) ** 2) / 30.0)
    smooth /= smooth.sum()
    arm = ((xx - 15) / 15.0) * smooth
    truth = 0.01 + 1.4 * smooth + 0.8 * arm
    err = np.full_like(truth, 0.01)
    contaminated = truth.copy()
    contaminated[15, 20] += 2.0

    linear = weighted_template_fit(contaminated, err, smooth, arm)
    robust = robust_template_fit(contaminated, err, smooth, arm)
    assert robust["n_valid"] == contaminated.size
    assert abs(robust["arm_coefficient"] - 0.8) < abs(linear.arm_coefficient - 0.8)


def test_blank_real_context_control_recovers_true_phase_without_extra_noise():
    n = 401
    sci = np.zeros((n, n), dtype=float)
    err = np.ones_like(sci)
    row = evaluate_p5_case(
        sci,
        err,
        x=n // 2,
        y=n // 2,
        ab_mag=26.0,
        pixar_sr=2.11539874851881e-14,
        crowding_class="test",
        placement_index=0,
        distance_to_source_pixel=999.0,
    )
    assert row.p3_true_phase_rank == 1
    assert row.p5_true_phase_rank == 1
    assert row.paired_p5_true_phase_rank == 1
    assert row.relative_flux_error < 1e-12
    assert all(f["optimizer_success"] for f in row.p5_phase_fits)
    assert all(f["optimizer_success"] for f in row.paired_p5_phase_fits)
