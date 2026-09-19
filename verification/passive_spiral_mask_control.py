"""Passive Spiral P4: frozen pre-injection source-mask contamination control.

Verification harness only; not production code and not a classifier.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence
import numpy as np

from .passive_spiral_phase_null import (
    _fit_phase_bank,
    _rank_true,
    phase_bank_templates,
)
from .passive_spiral_real_context import (
    _patch_slices,
    ab_to_total_mjysr_pixels,
    inject_stamp_copy,
)

P4_D1C_BACKGROUND_MJYSR = 4.1250608e-4
P4_D1C_SOURCE_SIGMA = 5.0


@dataclass
class P4Case:
    crowding_class: str
    placement_index: int
    x: int
    y: int
    distance_to_source_pixel: float
    ab_mag: float
    masked_fraction: float
    unmasked_true_phase_rank: int
    masked_true_phase_rank: int
    masked_best_phase_offset_deg: float
    masked_true_minus_best_score: float
    masked_true_arm_coefficient: float
    masked_paired_true_phase_rank: int
    masked_phase_fits: list[dict]
    masked_paired_phase_fits: list[dict]
    relative_flux_error: float

    def to_dict(self) -> dict:
        return asdict(self)


def frozen_d1c_source_mask(science: np.ndarray, err: np.ndarray) -> np.ndarray:
    sci = np.asarray(science, dtype=float)
    er = np.asarray(err, dtype=float)
    if sci.shape != er.shape or sci.ndim != 2:
        raise ValueError("SCI and ERR must be co-grid 2-D arrays")
    valid = np.isfinite(sci) & np.isfinite(er) & (er > 0)
    sn = np.full(sci.shape, -np.inf, dtype=float)
    sn[valid] = (sci[valid] - P4_D1C_BACKGROUND_MJYSR) / er[valid]
    return sn > P4_D1C_SOURCE_SIGMA


def evaluate_p4_case(
    science: np.ndarray,
    err: np.ndarray,
    source_mask: np.ndarray,
    *,
    x: int,
    y: int,
    ab_mag: float,
    pixar_sr: float,
    crowding_class: str,
    placement_index: int,
    distance_to_source_pixel: float,
    templates=None,
) -> P4Case:
    sci = np.asarray(science, dtype=float)
    er = np.asarray(err, dtype=float)
    mask = np.asarray(source_mask, dtype=bool)
    if not (sci.shape == er.shape == mask.shape):
        raise ValueError("SCI, ERR, and frozen source mask must be co-grid")

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
    err_patch = np.array(er[ys, xs], dtype=float, copy=True)
    mask_patch = mask[ys, xs]

    unmasked_rows = _fit_phase_bank(injected_patch, err_patch, smooth_basis, arm_bases)
    _, unmasked_rank, _, _ = _rank_true(unmasked_rows)

    fit_err = np.array(err_patch, copy=True)
    fit_err[mask_patch] = np.nan
    masked_rows = _fit_phase_bank(injected_patch, fit_err, smooth_basis, arm_bases)
    masked_paired_rows = _fit_phase_bank(paired_patch, fit_err, smooth_basis, arm_bases)
    best, rank, delta, arm = _rank_true(masked_rows)
    _, paired_rank, _, _ = _rank_true(masked_paired_rows)

    realized = float(np.sum(paired_patch))
    rel_flux_error = float(abs(realized / float(scale) - 1.0))

    return P4Case(
        crowding_class=str(crowding_class),
        placement_index=int(placement_index),
        x=int(x), y=int(y),
        distance_to_source_pixel=float(distance_to_source_pixel),
        ab_mag=float(ab_mag),
        masked_fraction=float(np.mean(mask_patch)),
        unmasked_true_phase_rank=int(unmasked_rank),
        masked_true_phase_rank=int(rank),
        masked_best_phase_offset_deg=float(best),
        masked_true_minus_best_score=float(delta),
        masked_true_arm_coefficient=float(arm),
        masked_paired_true_phase_rank=int(paired_rank),
        masked_phase_fits=masked_rows,
        masked_paired_phase_fits=masked_paired_rows,
        relative_flux_error=rel_flux_error,
    )


def run_p4_grid(science: np.ndarray, err: np.ndarray, matrix: Mapping, pixar_sr: float) -> list[dict]:
    mask = frozen_d1c_source_mask(science, err)
    templates = phase_bank_templates()
    rows: list[dict] = []
    magnitudes: Sequence[float] = matrix["source_model"]["ab_magnitudes"]
    for crowding_class, placements in matrix["placements"].items():
        for placement_index, placement in enumerate(placements):
            x, y, distance = placement
            for mag in magnitudes:
                rows.append(evaluate_p4_case(
                    science, err, mask,
                    x=int(x), y=int(y), ab_mag=float(mag), pixar_sr=float(pixar_sr),
                    crowding_class=str(crowding_class), placement_index=placement_index,
                    distance_to_source_pixel=float(distance), templates=templates,
                ).to_dict())
    return rows
