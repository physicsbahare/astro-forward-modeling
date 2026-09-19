"""Minimal verification-only operators for the real passive-disk R1/R2 pilot.

This module is intentionally narrow. It is not a production renderer and does
not perform catalog selection, source detection, deblending, or completeness
classification. It only freezes the scalar/image operations exercised by the
attached-data R1/R2 pilot.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates

FWHM_TO_SIGMA = 1.0 / 2.3548200450309493


def required_source_wavelength_um(target_pivot_um: float, z_source: float, z_target: float) -> float:
    if target_pivot_um <= 0 or z_source < 0 or z_target < 0:
        raise ValueError("Wavelength must be positive and redshifts non-negative.")
    return float(target_pivot_um * (1.0 + z_source) / (1.0 + z_target))


def linear_wavelength_weight(lambda_um: float, lambda_lo_um: float, lambda_hi_um: float) -> float:
    if not (lambda_hi_um > lambda_lo_um > 0):
        raise ValueError("Require 0 < lambda_lo < lambda_hi.")
    t = (lambda_um - lambda_lo_um) / (lambda_hi_um - lambda_lo_um)
    if t < 0.0 or t > 1.0:
        raise ValueError("Requested wavelength is outside source spectral support.")
    return float(t)


def inu_source_to_target_factor(z_source: float, z_target: float) -> float:
    if z_source < 0 or z_target < 0:
        raise ValueError("Redshifts must be non-negative.")
    return float(((1.0 + z_source) / (1.0 + z_target)) ** 3)


def degradation_kernel_fwhm(target_fwhm_arcsec: float, source_equiv_fwhm_arcsec: float) -> float:
    if target_fwhm_arcsec <= 0 or source_equiv_fwhm_arcsec < 0:
        raise ValueError("PSF FWHM values must be non-negative and target positive.")
    if target_fwhm_arcsec <= source_equiv_fwhm_arcsec:
        raise ValueError("Target PSF is not broader; sharpening is unsupported.")
    return float(math.sqrt(target_fwhm_arcsec**2 - source_equiv_fwhm_arcsec**2))


def gaussian_degrade(image: np.ndarray, kernel_fwhm_arcsec: float, pixel_scale_arcsec: float) -> np.ndarray:
    if kernel_fwhm_arcsec < 0 or pixel_scale_arcsec <= 0:
        raise ValueError("Kernel must be non-negative and pixel scale positive.")
    data = np.asarray(image, dtype=float)
    if kernel_fwhm_arcsec == 0:
        return data.copy()
    sigma_pix = kernel_fwhm_arcsec * FWHM_TO_SIGMA / pixel_scale_arcsec
    return gaussian_filter(data, sigma=sigma_pix, mode="constant", cval=0.0, truncate=6.0)


def interpolate_inu(lo_image: np.ndarray, hi_image: np.ndarray, weight: float) -> np.ndarray:
    if weight < 0 or weight > 1:
        raise ValueError("Interpolation weight must lie in [0, 1].")
    lo = np.asarray(lo_image, dtype=float)
    hi = np.asarray(hi_image, dtype=float)
    if lo.shape != hi.shape:
        raise ValueError("Input images must share a common grid.")
    return (1.0 - weight) * lo + weight * hi


def rescale_about_center(image: np.ndarray, angular_scale: float, center_xy: tuple[float, float] | None = None) -> np.ndarray:
    """Resample a surface-brightness image about a fixed center.

    ``angular_scale < 1`` makes the galaxy smaller on the unchanged output grid.
    No flux normalization is applied here because the image is a surface-brightness field.
    """
    if angular_scale <= 0:
        raise ValueError("Angular scale must be positive.")
    data = np.asarray(image, dtype=float)
    ny, nx = data.shape
    if center_xy is None:
        cx, cy = 0.5 * (nx - 1), 0.5 * (ny - 1)
    else:
        cx, cy = map(float, center_xy)
    yy, xx = np.indices(data.shape, dtype=float)
    src_x = cx + (xx - cx) / angular_scale
    src_y = cy + (yy - cy) / angular_scale
    return map_coordinates(data, [src_y, src_x], order=1, mode="constant", cval=0.0, prefilter=False)


def render_r1_from_homogenized_pair(
    lo_image: np.ndarray,
    hi_image: np.ndarray,
    *,
    interpolation_weight: float,
    angular_scale: float,
    inu_factor: float,
    target_kernel_fwhm_arcsec: float,
    pixel_scale_arcsec: float,
    center_xy: tuple[float, float] | None = None,
) -> np.ndarray:
    plane = interpolate_inu(lo_image, hi_image, interpolation_weight)
    plane = rescale_about_center(plane, angular_scale, center_xy=center_xy)
    plane = plane * float(inu_factor)
    return gaussian_degrade(plane, target_kernel_fwhm_arcsec, pixel_scale_arcsec)


@dataclass(frozen=True)
class MorphologyProxy:
    signed_flux: float
    axis_ratio: float
    concentration: float
    centroid_offset_arcsec: float


def aperture_morphology_proxy(
    image: np.ndarray,
    *,
    center_xy: tuple[float, float],
    pixel_scale_arcsec: float,
    aperture_arcsec: float = 1.0,
    inner_arcsec: float = 0.3,
    background_annulus_arcsec: tuple[float, float] = (1.2, 1.5),
) -> MorphologyProxy:
    data = np.asarray(image, dtype=float)
    cx, cy = map(float, center_xy)
    yy, xx = np.indices(data.shape, dtype=float)
    r = np.hypot(xx - cx, yy - cy) * pixel_scale_arcsec
    ap = r <= aperture_arcsec
    ann = (r >= background_annulus_arcsec[0]) & (r < background_annulus_arcsec[1])
    if not np.any(ann):
        raise ValueError("Background annulus contains no pixels.")
    residual = data - float(np.nanmedian(data[ann]))
    signed_flux = float(np.nansum(residual[ap]))
    positive = np.clip(residual, 0.0, None)
    weights = positive * ap
    total = float(np.sum(weights))
    if total <= 0:
        return MorphologyProxy(signed_flux, float("nan"), float("nan"), float("nan"))
    xcen = float(np.sum(weights * xx) / total)
    ycen = float(np.sum(weights * yy) / total)
    dx, dy = xx - xcen, yy - ycen
    cxx = float(np.sum(weights * dx * dx) / total)
    cyy = float(np.sum(weights * dy * dy) / total)
    cxy = float(np.sum(weights * dx * dy) / total)
    eig = np.linalg.eigvalsh(np.array([[cxx, cxy], [cxy, cyy]], dtype=float))
    axis_ratio = float(np.sqrt(max(eig[0], 0.0) / max(eig[1], 1e-30)))
    inner = r <= inner_arcsec
    concentration = float(np.sum(positive[inner]) / np.sum(positive[ap]))
    centroid = float(np.hypot(xcen - cx, ycen - cy) * pixel_scale_arcsec)
    return MorphologyProxy(signed_flux, axis_ratio, concentration, centroid)
