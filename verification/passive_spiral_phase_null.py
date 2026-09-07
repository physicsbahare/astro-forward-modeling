"""Passive Spiral P3: raw-scene phase/orientation null test.

Verification harness only; this is not production code and not a classifier.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

import numpy as np

from .passive_spiral_real_context import (
    P2_TARGET_Z,
    _patch_slices,
    ab_to_total_mjysr_pixels,
    inject_stamp_copy,
    weighted_template_fit,
)
from .passive_spiral_redshift import (
    ARM_AMPLITUDE,
    BULGE_AMPLITUDE,
    BULGE_SIGMA_KPC,
    DISK_SCALE_KPC,
    TARGET_PIXEL_SCALE_ARCSEC,
    TARGET_PSF_FWHM_ARCSEC,
    _convolve_gaussian,
    _physical_grid,
    _spiral_phase,
)
from .reference import FlatLCDMReference

P3_PHASE_OFFSETS_DEG = (0.0, 45.0, 90.0, 135.0)


@dataclass
class P3Case:
    crowding_class: str
    placement_index: int
    x: int
    y: int
    distance_to_source_pixel: float
    ab_mag: float
    raw_phase_fits: list[dict]
    paired_phase_fits: list[dict]
    raw_best_phase_offset_deg: float
    raw_true_phase_rank: int
    raw_true_minus_best_score: float
    raw_true_arm_coefficient: float
    paired_best_phase_offset_deg: float
    paired_true_phase_rank: int
    relative_flux_error: float

    def to_dict(self) -> dict:
        return asdict(self)


def _phase_scene(x_kpc: np.ndarray, y_kpc: np.ndarray, phase_offset_deg: float) -> np.ndarray:
    radius = np.hypot(x_kpc, y_kpc)
    disk = np.exp(-radius / DISK_SCALE_KPC)
    bulge = BULGE_AMPLITUDE * np.exp(-0.5 * (radius / BULGE_SIGMA_KPC) ** 2)
    inner_taper = 1.0 - np.exp(-((radius / 1.5) ** 4))
    outer_taper = np.exp(-((radius / 12.0) ** 6))
    phase = _spiral_phase(x_kpc, y_kpc) + np.deg2rad(float(phase_offset_deg))
    modulation = 1.0 + ARM_AMPLITUDE * inner_taper * outer_taper * np.cos(phase)
    return np.asarray(disk * modulation + bulge, dtype=float)


def phase_bank_templates(
    cosmology: FlatLCDMReference | None = None,
) -> tuple[np.ndarray, dict[float, np.ndarray], np.ndarray]:
    """Return unit-total true spiral, phase arm-residual bank, and unit-total smooth template."""
    cosmology = cosmology or FlatLCDMReference()
    _, xx, yy = _physical_grid(P2_TARGET_Z, TARGET_PIXEL_SCALE_ARCSEC, cosmology)

    radius = np.hypot(xx, yy)
    smooth_latent = np.exp(-radius / DISK_SCALE_KPC) + BULGE_AMPLITUDE * np.exp(
        -0.5 * (radius / BULGE_SIGMA_KPC) ** 2
    )
    smooth_obs = smooth_latent / (1.0 + P2_TARGET_Z) ** 4
    smooth = _convolve_gaussian(
        smooth_obs, TARGET_PSF_FWHM_ARCSEC, TARGET_PIXEL_SCALE_ARCSEC
    )
    smooth = np.asarray(smooth, dtype=float)
    smooth /= float(np.sum(smooth))

    bank: dict[float, np.ndarray] = {}
    true_spiral: np.ndarray | None = None
    for phase_deg in P3_PHASE_OFFSETS_DEG:
        latent = _phase_scene(xx, yy, phase_deg)
        observed = latent / (1.0 + P2_TARGET_Z) ** 4
        spiral = _convolve_gaussian(
            observed, TARGET_PSF_FWHM_ARCSEC, TARGET_PIXEL_SCALE_ARCSEC
        )
        spiral = np.asarray(spiral, dtype=float)
        spiral /= float(np.sum(spiral))
        bank[float(phase_deg)] = spiral - smooth
        if phase_deg == 0.0:
            true_spiral = spiral

    if true_spiral is None:
        raise RuntimeError("P3 frozen phase bank is missing the true zero phase")
    return true_spiral, bank, smooth


def _fit_phase_bank(
    patch: np.ndarray,
    err_patch: np.ndarray,
    smooth_basis: np.ndarray,
    arm_bases: Mapping[float, np.ndarray],
) -> list[dict]:
    rows: list[dict] = []
    for phase_deg in P3_PHASE_OFFSETS_DEG:
        fit = weighted_template_fit(
            patch, err_patch, smooth_basis, arm_bases[float(phase_deg)]
        )
        score = float(fit.weighted_residual_norm**2)
        row = fit.to_dict()
        row["phase_offset_deg"] = float(phase_deg)
        row["physical_orientation_deg_mod_signed_degeneracy"] = float(phase_deg / 2.0)
        row["weighted_residual_score"] = score
        rows.append(row)
    return rows


def _rank_true(rows: Sequence[dict]) -> tuple[float, int, float, float]:
    scores = np.asarray([float(r["weighted_residual_score"]) for r in rows], dtype=float)
    phases = np.asarray([float(r["phase_offset_deg"]) for r in rows], dtype=float)
    best_index = int(np.argmin(scores))
    true_index = int(np.where(phases == 0.0)[0][0])
    true_score = float(scores[true_index])
    rank = int(1 + np.count_nonzero(scores < true_score))
    true_arm = float(rows[true_index]["arm_coefficient"])
    return float(phases[best_index]), rank, float(true_score - scores[best_index]), true_arm


def evaluate_p3_case(
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
    templates: tuple[np.ndarray, dict[float, np.ndarray], np.ndarray] | None = None,
) -> P3Case:
    sci = np.asarray(science, dtype=float)
    er = np.asarray(err, dtype=float)
    true_spiral, arm_bank_unit, smooth_unit = templates or phase_bank_templates()
    scale = ab_to_total_mjysr_pixels(ab_mag, pixar_sr)
    injected_stamp = true_spiral * scale
    smooth_basis = smooth_unit * scale
    arm_bases = {phase: basis * scale for phase, basis in arm_bank_unit.items()}

    injected = inject_stamp_copy(sci, injected_stamp, int(x), int(y))
    ys, xs = _patch_slices(sci.shape, injected_stamp.shape, int(x), int(y))
    original_patch = sci[ys, xs]
    injected_patch = injected[ys, xs]
    paired_patch = injected_patch - original_patch
    err_patch = er[ys, xs]

    raw_rows = _fit_phase_bank(injected_patch, err_patch, smooth_basis, arm_bases)
    paired_rows = _fit_phase_bank(paired_patch, err_patch, smooth_basis, arm_bases)
    raw_best, raw_rank, raw_delta, raw_arm = _rank_true(raw_rows)
    paired_best, paired_rank, _, _ = _rank_true(paired_rows)

    requested_total = float(scale)
    realized_total = float(np.sum(paired_patch))
    rel_flux_error = float(abs(realized_total / requested_total - 1.0))

    return P3Case(
        crowding_class=str(crowding_class),
        placement_index=int(placement_index),
        x=int(x),
        y=int(y),
        distance_to_source_pixel=float(distance_to_source_pixel),
        ab_mag=float(ab_mag),
        raw_phase_fits=raw_rows,
        paired_phase_fits=paired_rows,
        raw_best_phase_offset_deg=raw_best,
        raw_true_phase_rank=raw_rank,
        raw_true_minus_best_score=raw_delta,
        raw_true_arm_coefficient=raw_arm,
        paired_best_phase_offset_deg=paired_best,
        paired_true_phase_rank=paired_rank,
        relative_flux_error=rel_flux_error,
    )


def run_p3_grid(
    science: np.ndarray,
    err: np.ndarray,
    matrix: Mapping,
    pixar_sr: float,
) -> list[dict]:
    templates = phase_bank_templates()
    rows: list[dict] = []
    magnitudes: Sequence[float] = matrix["source_model"]["ab_magnitudes"]
    for crowding_class, placements in matrix["placements"].items():
        for placement_index, placement in enumerate(placements):
            x, y, distance = placement
            for mag in magnitudes:
                rows.append(
                    evaluate_p3_case(
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
