"""Passive Spiral P2: deterministic spiral injection into real COSMOS-Web context.

Verification harness only; this is not production code and not a classifier.

P2 deliberately reuses the frozen P1 z=2 direct-target morphology and the
frozen Gate-D real-mosaic placements.  Existing survey background/noise is
retained.  No new sky noise or source-shot noise is generated, ERR/WHT are not
modified, and no additional Tolman factor is applied after observed-flux
normalization.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

import numpy as np

from .passive_spiral_redshift import _direct_target
from .reference import FlatLCDMReference

AB_ZERO_JY = 3631.0
P2_TARGET_Z = 2.0


@dataclass
class LinearTemplateFit:
    constant: float
    x_gradient: float
    y_gradient: float
    smooth_coefficient: float
    arm_coefficient: float
    arm_over_smooth: float | None
    rank: int
    n_valid: int
    raw_weighted_design_condition: float
    column_normalized_design_condition: float
    weighted_residual_norm: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class P2Case:
    crowding_class: str
    placement_index: int
    x: int
    y: int
    distance_to_source_pixel: float
    ab_mag: float
    requested_flux_jy: float
    requested_total_mjysr_pixels: float
    realized_flux_jy: float
    relative_flux_error: float
    original_fit: dict
    injected_fit: dict
    paired_difference_fit: dict
    injected_arm_bias_from_truth: float
    injected_smooth_bias_from_truth: float
    background_arm_equivalent: float
    background_smooth_equivalent: float
    coefficient_closure_max_abs: float

    def to_dict(self) -> dict:
        return asdict(self)


def ab_to_jy(mag: float) -> float:
    return float(AB_ZERO_JY * 10.0 ** (-0.4 * float(mag)))


def ab_to_total_mjysr_pixels(mag: float, pixar_sr: float) -> float:
    if not np.isfinite(pixar_sr) or pixar_sr <= 0:
        raise ValueError("PIXAR_SR must be positive and finite")
    return float(ab_to_jy(mag) / (1.0e6 * float(pixar_sr)))


def p2_target_templates(
    cosmology: FlatLCDMReference | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return unit-total spiral, smooth, and signed arm-residual P1 z=2 templates."""
    cosmology = cosmology or FlatLCDMReference()
    spiral, _, _ = _direct_target(P2_TARGET_Z, spiral=True, cosmology=cosmology)
    smooth, _, _ = _direct_target(P2_TARGET_Z, spiral=False, cosmology=cosmology)

    spiral = np.asarray(spiral, dtype=float)
    smooth = np.asarray(smooth, dtype=float)
    if spiral.shape != smooth.shape or spiral.ndim != 2:
        raise RuntimeError("P1 spiral and smooth target templates are not co-grid 2-D arrays")
    if spiral.shape[0] != spiral.shape[1] or spiral.shape[0] % 2 != 1:
        raise RuntimeError("P2 requires an odd square target template")
    if not np.all(np.isfinite(spiral)) or not np.all(np.isfinite(smooth)):
        raise RuntimeError("P1 target template contains non-finite values")
    if float(spiral.sum()) <= 0 or float(smooth.sum()) <= 0:
        raise RuntimeError("P1 target template has non-positive total flux")

    spiral = spiral / float(spiral.sum())
    smooth = smooth / float(smooth.sum())
    arm = spiral - smooth
    return spiral, smooth, arm


def _patch_slices(shape: tuple[int, int], stamp_shape: tuple[int, int], x: int, y: int) -> tuple[slice, slice]:
    if len(shape) != 2 or len(stamp_shape) != 2:
        raise ValueError("science and stamp arrays must be two-dimensional")
    if stamp_shape[0] != stamp_shape[1] or stamp_shape[0] % 2 != 1:
        raise ValueError("stamp must be odd and square")
    h = stamp_shape[0] // 2
    if x - h < 0 or y - h < 0 or x + h >= shape[1] or y + h >= shape[0]:
        raise ValueError(f"placement {(x, y)} would truncate the frozen P2 template")
    return slice(y - h, y + h + 1), slice(x - h, x + h + 1)


def inject_stamp_copy(science: np.ndarray, stamp: np.ndarray, x: int, y: int) -> np.ndarray:
    """Return SCI+stamp without mutating the input SCI array."""
    sci = np.asarray(science, dtype=float)
    st = np.asarray(stamp, dtype=float)
    if not np.all(np.isfinite(st)):
        raise ValueError("injection stamp contains non-finite values")
    ys, xs = _patch_slices(sci.shape, st.shape, int(x), int(y))
    out = np.array(sci, copy=True)
    out[ys, xs] += st
    return out


def _linear_design(shape: tuple[int, int], smooth_basis: np.ndarray, arm_basis: np.ndarray) -> np.ndarray:
    ny, nx = shape
    yy, xx = np.indices((ny, nx), dtype=float)
    xscale = max((nx - 1) / 2.0, 1.0)
    yscale = max((ny - 1) / 2.0, 1.0)
    xx = (xx - (nx - 1) / 2.0) / xscale
    yy = (yy - (ny - 1) / 2.0) / yscale
    return np.column_stack(
        [
            np.ones(ny * nx, dtype=float),
            xx.ravel(),
            yy.ravel(),
            np.asarray(smooth_basis, dtype=float).ravel(),
            np.asarray(arm_basis, dtype=float).ravel(),
        ]
    )


def weighted_template_fit(
    data: np.ndarray,
    err: np.ndarray,
    smooth_basis: np.ndarray,
    arm_basis: np.ndarray,
) -> LinearTemplateFit:
    """Fit plane + smooth + signed arm template using diagonal ERR weights.

    Coefficients are deliberately unconstrained.  Column normalization is used
    only to improve numerical conditioning of the linear solve; returned source
    coefficients retain the physical basis normalization supplied by the caller.
    """
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
        raise ValueError("too few finite positive-ERR pixels for the frozen P2 linear model")

    weights = 1.0 / flat_err[valid]
    weighted_design = design[valid] * weights[:, None]
    weighted_data = flat_data[valid] * weights

    norms = np.sqrt(np.sum(weighted_design * weighted_design, axis=0))
    if np.any(~np.isfinite(norms)) or np.any(norms <= 0):
        raise RuntimeError("degenerate weighted P2 design column")
    normalized_design = weighted_design / norms[None, :]

    scaled_coeff, _, rank, _ = np.linalg.lstsq(normalized_design, weighted_data, rcond=None)
    coeff = scaled_coeff / norms
    model = design[valid] @ coeff
    weighted_resid = (flat_data[valid] - model) * weights

    smooth_coeff = float(coeff[3])
    arm_coeff = float(coeff[4])
    ratio = None if smooth_coeff == 0 else float(arm_coeff / smooth_coeff)

    return LinearTemplateFit(
        constant=float(coeff[0]),
        x_gradient=float(coeff[1]),
        y_gradient=float(coeff[2]),
        smooth_coefficient=smooth_coeff,
        arm_coefficient=arm_coeff,
        arm_over_smooth=ratio,
        rank=int(rank),
        n_valid=n_valid,
        raw_weighted_design_condition=float(np.linalg.cond(weighted_design)),
        column_normalized_design_condition=float(np.linalg.cond(normalized_design)),
        weighted_residual_norm=float(np.linalg.norm(weighted_resid)),
    )


def evaluate_p2_case(
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
    templates: tuple[np.ndarray, np.ndarray, np.ndarray] | None = None,
) -> P2Case:
    sci = np.asarray(science, dtype=float)
    er = np.asarray(err, dtype=float)
    if sci.shape != er.shape or sci.ndim != 2:
        raise ValueError("SCI and ERR must be co-grid 2-D arrays")

    spiral, smooth, arm = templates or p2_target_templates()
    requested_jy = ab_to_jy(ab_mag)
    scale = ab_to_total_mjysr_pixels(ab_mag, pixar_sr)
    spiral_stamp = spiral * scale
    smooth_basis = smooth * scale
    arm_basis = arm * scale

    injected = inject_stamp_copy(sci, spiral_stamp, int(x), int(y))
    ys, xs = _patch_slices(sci.shape, spiral_stamp.shape, int(x), int(y))
    original_patch = sci[ys, xs]
    injected_patch = injected[ys, xs]
    err_patch = er[ys, xs]
    paired_patch = injected_patch - original_patch

    original_fit = weighted_template_fit(original_patch, err_patch, smooth_basis, arm_basis)
    injected_fit = weighted_template_fit(injected_patch, err_patch, smooth_basis, arm_basis)
    paired_fit = weighted_template_fit(paired_patch, err_patch, smooth_basis, arm_basis)

    realized_total = float(np.sum(paired_patch))
    realized_jy = float(realized_total * 1.0e6 * pixar_sr)
    rel_flux_error = float(abs(realized_jy / requested_jy - 1.0))

    closure = np.asarray(
        [
            injected_fit.constant - original_fit.constant - paired_fit.constant,
            injected_fit.x_gradient - original_fit.x_gradient - paired_fit.x_gradient,
            injected_fit.y_gradient - original_fit.y_gradient - paired_fit.y_gradient,
            injected_fit.smooth_coefficient - original_fit.smooth_coefficient - paired_fit.smooth_coefficient,
            injected_fit.arm_coefficient - original_fit.arm_coefficient - paired_fit.arm_coefficient,
        ],
        dtype=float,
    )

    return P2Case(
        crowding_class=str(crowding_class),
        placement_index=int(placement_index),
        x=int(x),
        y=int(y),
        distance_to_source_pixel=float(distance_to_source_pixel),
        ab_mag=float(ab_mag),
        requested_flux_jy=requested_jy,
        requested_total_mjysr_pixels=scale,
        realized_flux_jy=realized_jy,
        relative_flux_error=rel_flux_error,
        original_fit=original_fit.to_dict(),
        injected_fit=injected_fit.to_dict(),
        paired_difference_fit=paired_fit.to_dict(),
        injected_arm_bias_from_truth=float(injected_fit.arm_coefficient - 1.0),
        injected_smooth_bias_from_truth=float(injected_fit.smooth_coefficient - 1.0),
        background_arm_equivalent=float(original_fit.arm_coefficient),
        background_smooth_equivalent=float(original_fit.smooth_coefficient),
        coefficient_closure_max_abs=float(np.max(np.abs(closure))),
    )


def run_p2_grid(
    science: np.ndarray,
    err: np.ndarray,
    matrix: Mapping,
    pixar_sr: float,
) -> list[dict]:
    templates = p2_target_templates()
    rows: list[dict] = []
    magnitudes: Sequence[float] = matrix["source_model"]["ab_magnitudes"]
    for crowding_class, placements in matrix["placements"].items():
        for placement_index, placement in enumerate(placements):
            x, y, distance = placement
            for mag in magnitudes:
                row = evaluate_p2_case(
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
                )
                rows.append(row.to_dict())
    return rows
