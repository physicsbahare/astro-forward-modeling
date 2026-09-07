"""Passive Spiral P5: frozen Huber robust-loss contamination control.

Verification harness only; not production code and not a classifier.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

import numpy as np
from scipy.optimize import least_squares

from .passive_spiral_phase_null import (
    P3_PHASE_OFFSETS_DEG,
    _fit_phase_bank,
    _rank_true,
    phase_bank_templates,
)
from .passive_spiral_real_context import (
    _linear_design,
    _patch_slices,
    ab_to_total_mjysr_pixels,
    inject_stamp_copy,
    weighted_template_fit,
)

P5_LOSS = "huber"
P5_F_SCALE = 1.0


@dataclass
class P5Case:
    crowding_class: str
    placement_index: int
    x: int
    y: int
    distance_to_source_pixel: float
    ab_mag: float
    p3_true_phase_rank: int
    p5_true_phase_rank: int
    p5_best_phase_offset_deg: float
    p5_true_minus_best_objective: float
    p5_true_arm_coefficient: float
    p5_phase_fits: list[dict]
    paired_p5_true_phase_rank: int
    paired_p5_phase_fits: list[dict]
    relative_flux_error: float

    def to_dict(self) -> dict:
        return asdict(self)


def robust_template_fit(
    data: np.ndarray,
    err: np.ndarray,
    smooth_basis: np.ndarray,
    arm_basis: np.ndarray,
) -> dict:
    """Fit plane + smooth + signed arm basis with frozen Huber residual loss."""
    data = np.asarray(data, dtype=float)
    err = np.asarray(err, dtype=float)
    smooth_basis = np.asarray(smooth_basis, dtype=float)
    arm_basis = np.asarray(arm_basis, dtype=float)
    if not (data.shape == err.shape == smooth_basis.shape == arm_basis.shape):
        raise ValueError("data, ERR, smooth basis, and arm basis must be co-grid")

    design = _linear_design(data.shape, smooth_basis, arm_basis)
    flat_data = data.ravel()
    flat_err = err.ravel()
    finite_design = np.all(np.isfinite(design), axis=1)
    valid = np.isfinite(flat_data) & np.isfinite(flat_err) & (flat_err > 0) & finite_design
    n_valid = int(np.count_nonzero(valid))
    if n_valid <= design.shape[1]:
        raise ValueError("too few finite positive-ERR pixels for the frozen P5 model")

    # Frozen deterministic numerical starting point: the ordinary diagonal-ERR
    # weighted solution for the same phase. It is not substituted for failure.
    initial = weighted_template_fit(data, err, smooth_basis, arm_basis)
    x0 = np.asarray(
        [
            initial.constant,
            initial.x_gradient,
            initial.y_gradient,
            initial.smooth_coefficient,
            initial.arm_coefficient,
        ],
        dtype=float,
    )

    d = design[valid]
    y = flat_data[valid]
    sigma = flat_err[valid]
    jacobian = d / sigma[:, None]

    def residual(coeff: np.ndarray) -> np.ndarray:
        return (d @ coeff - y) / sigma

    def jac(_coeff: np.ndarray) -> np.ndarray:
        return jacobian

    result = least_squares(
        residual,
        x0,
        jac=jac,
        loss=P5_LOSS,
        f_scale=P5_F_SCALE,
        bounds=(-np.inf, np.inf),
    )
    coeff = np.asarray(result.x, dtype=float)
    finite_solution = bool(np.all(np.isfinite(coeff)) and np.isfinite(result.cost))
    smooth_coeff = float(coeff[3])
    arm_coeff = float(coeff[4])
    ratio = None if smooth_coeff == 0 else float(arm_coeff / smooth_coeff)

    return {
        "constant": float(coeff[0]),
        "x_gradient": float(coeff[1]),
        "y_gradient": float(coeff[2]),
        "smooth_coefficient": smooth_coeff,
        "arm_coefficient": arm_coeff,
        "arm_over_smooth": ratio,
        "n_valid": n_valid,
        "loss": P5_LOSS,
        "f_scale": P5_F_SCALE,
        "objective_cost": float(result.cost),
        "optimizer_success": bool(result.success),
        "optimizer_status": int(result.status),
        "optimizer_nfev": int(result.nfev),
        "optimizer_njev": None if result.njev is None else int(result.njev),
        "optimizer_optimality": float(result.optimality),
        "finite_solution": finite_solution,
        "initial_weighted_residual_norm": float(initial.weighted_residual_norm),
    }


def _fit_robust_phase_bank(
    patch: np.ndarray,
    err_patch: np.ndarray,
    smooth_basis: np.ndarray,
    arm_bases: Mapping[float, np.ndarray],
) -> list[dict]:
    rows: list[dict] = []
    for phase_deg in P3_PHASE_OFFSETS_DEG:
        fit = robust_template_fit(
            patch, err_patch, smooth_basis, arm_bases[float(phase_deg)]
        )
        fit["phase_offset_deg"] = float(phase_deg)
        fit["physical_orientation_deg_mod_signed_degeneracy"] = float(phase_deg / 2.0)
        rows.append(fit)
    return rows


def _rank_true_robust(rows: Sequence[dict]) -> tuple[float, int, float, float]:
    costs = np.asarray([float(r["objective_cost"]) for r in rows], dtype=float)
    phases = np.asarray([float(r["phase_offset_deg"]) for r in rows], dtype=float)
    best_index = int(np.argmin(costs))
    true_index = int(np.where(phases == 0.0)[0][0])
    true_cost = float(costs[true_index])
    rank = int(1 + np.count_nonzero(costs < true_cost))
    true_arm = float(rows[true_index]["arm_coefficient"])
    return float(phases[best_index]), rank, float(true_cost - costs[best_index]), true_arm


def evaluate_p5_case(
    science: np.ndarray,
    err: np.ndarray,
    *,
    x: int,
    y: int,
    ab_mag: float,
    pixar_sr: float,
    crowding_class: str,
    placement_index: int,
    distance_to_source_pixel: float,
    templates=None,
) -> P5Case:
    sci = np.asarray(science, dtype=float)
    er = np.asarray(err, dtype=float)
    if sci.shape != er.shape:
        raise ValueError("SCI and ERR must be co-grid")

    true_spiral, arm_bank_unit, smooth_unit = templates or phase_bank_templates()
    scale = ab_to_total_mjysr_pixels(ab_mag, pixar_sr)
    stamp = true_spiral * scale
    smooth_basis = smooth_unit * scale
    arm_bases = {p: b * scale for p, b in arm_bank_unit.items()}

    injected = inject_stamp_copy(sci, stamp, int(x), int(y))
    ys, xs = _patch_slices(sci.shape, stamp.shape, int(x), int(y))
    original_patch = sci[ys, xs]
    injected_patch = injected[ys, xs]
    paired_patch = injected_patch - original_patch
    err_patch = er[ys, xs]

    p3_rows = _fit_phase_bank(injected_patch, err_patch, smooth_basis, arm_bases)
    _, p3_rank, _, _ = _rank_true(p3_rows)

    p5_rows = _fit_robust_phase_bank(injected_patch, err_patch, smooth_basis, arm_bases)
    paired_rows = _fit_robust_phase_bank(paired_patch, err_patch, smooth_basis, arm_bases)
    best, rank, delta, arm = _rank_true_robust(p5_rows)
    _, paired_rank, _, _ = _rank_true_robust(paired_rows)

    realized = float(np.sum(paired_patch))
    rel_flux_error = float(abs(realized / float(scale) - 1.0))

    return P5Case(
        crowding_class=str(crowding_class),
        placement_index=int(placement_index),
        x=int(x),
        y=int(y),
        distance_to_source_pixel=float(distance_to_source_pixel),
        ab_mag=float(ab_mag),
        p3_true_phase_rank=int(p3_rank),
        p5_true_phase_rank=int(rank),
        p5_best_phase_offset_deg=float(best),
        p5_true_minus_best_objective=float(delta),
        p5_true_arm_coefficient=float(arm),
        p5_phase_fits=p5_rows,
        paired_p5_true_phase_rank=int(paired_rank),
        paired_p5_phase_fits=paired_rows,
        relative_flux_error=rel_flux_error,
    )


def run_p5_grid(
    science: np.ndarray, err: np.ndarray, matrix: Mapping, pixar_sr: float
) -> list[dict]:
    templates = phase_bank_templates()
    rows: list[dict] = []
    magnitudes: Sequence[float] = matrix["source_model"]["ab_magnitudes"]
    for crowding_class, placements in matrix["placements"].items():
        for placement_index, placement in enumerate(placements):
            x, y, distance = placement
            for mag in magnitudes:
                rows.append(
                    evaluate_p5_case(
                        science,
                        err,
                        x=int(x),
                        y=int(y),
                        ab_mag=float(mag),
                        pixar_sr=float(pixar_sr),
                        crowding_class=str(crowding_class),
                        placement_index=placement_index,
                        distance_to_source_pixel=float(distance),
                        templates=templates,
                    ).to_dict()
                )
    return rows
