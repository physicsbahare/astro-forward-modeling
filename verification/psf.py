"""Controlled PSF-matching experiments with analytic Gaussian truth.

The goal is not to select a universal regularization parameter.  The experiments
quantify reconstruction error, negative kernel weight, and noise amplification
as functions of sampling and regularization.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from scipy.signal import fftconvolve


@dataclass
class PSFMatchMetrics:
    method: str
    sigma_source_pix: float
    sigma_target_pix: float
    shape: int
    regularization: float | None
    l1_reconstruction_error_D: float
    negative_kernel_weight_Wminus: float
    kernel_sum_error: float
    white_noise_variance_factor: float
    second_moment_relative_error: float

    def to_dict(self) -> dict:
        return asdict(self)


def gaussian_psf(shape: int, sigma_pix: float) -> np.ndarray:
    if shape % 2 == 0:
        raise ValueError("PSF shape must be odd.")
    if sigma_pix <= 0:
        raise ValueError("sigma_pix must be positive.")
    c = shape // 2
    y, x = np.mgrid[:shape, :shape]
    r2 = (x - c) ** 2 + (y - c) ** 2
    psf = np.exp(-0.5 * r2 / sigma_pix**2)
    psf /= psf.sum()
    return psf


def second_moment_sigma(psf: np.ndarray) -> float:
    p = np.asarray(psf, dtype=float)
    p = p / p.sum()
    y, x = np.indices(p.shape)
    cx = np.sum(x * p)
    cy = np.sum(y * p)
    var_x = np.sum((x - cx) ** 2 * p)
    var_y = np.sum((y - cy) ** 2 * p)
    return float(np.sqrt(0.5 * (var_x + var_y)))


def kernel_metrics(source: np.ndarray, target: np.ndarray, kernel: np.ndarray) -> tuple[float, float, float, float, float]:
    k = np.asarray(kernel, dtype=float)
    ksum = k.sum()
    convolved = fftconvolve(source, k, mode="same")
    if convolved.sum() != 0:
        convolved_cmp = convolved / convolved.sum()
    else:
        convolved_cmp = convolved
    target_cmp = target / target.sum()
    D = float(np.sum(np.abs(target_cmp - convolved_cmp)))
    Wminus = float(0.5 * (np.sum(np.abs(k)) - np.sum(k)))
    ksum_err = float(abs(ksum - 1.0))
    white_var_factor = float(np.sum(k**2))
    sigma_target = second_moment_sigma(target_cmp)
    sigma_recon = second_moment_sigma(convolved_cmp)
    sigma_err = float(abs(sigma_recon - sigma_target) / sigma_target)
    return D, Wminus, ksum_err, white_var_factor, sigma_err


def analytic_gaussian_matching_kernel(shape: int, sigma_source_pix: float, sigma_target_pix: float) -> np.ndarray:
    if sigma_target_pix <= sigma_source_pix:
        raise ValueError("A direct Gaussian degradation kernel exists only when target sigma is broader than source sigma.")
    sigma_kernel = np.sqrt(sigma_target_pix**2 - sigma_source_pix**2)
    return gaussian_psf(shape, sigma_kernel)


def wiener_matching_kernel(source_psf: np.ndarray, target_psf: np.ndarray, regularization: float) -> np.ndarray:
    """Reference scalar-Tikhonov/Wiener PSF-matching kernel."""
    if regularization <= 0:
        raise ValueError("regularization must be positive")
    if source_psf.shape != target_psf.shape:
        raise ValueError("PSFs must share shape")

    s = np.fft.fft2(np.fft.ifftshift(source_psf / source_psf.sum()))
    t = np.fft.fft2(np.fft.ifftshift(target_psf / target_psf.sum()))
    source_power = np.abs(s) ** 2
    reg_term = regularization * np.max(source_power)
    k_otf = t * np.conj(s) / (source_power + reg_term)
    k = np.fft.fftshift(np.fft.ifft2(k_otf).real)
    if abs(k.sum()) < 1e-30:
        raise FloatingPointError("Wiener kernel normalization vanished")
    return k / k.sum()


def run_gaussian_reference(sigma_source_pix: float = 2.5, sigma_target_pix: float = 5.0, shape: int = 101) -> PSFMatchMetrics:
    source = gaussian_psf(shape, sigma_source_pix)
    target = gaussian_psf(shape, sigma_target_pix)
    kernel = analytic_gaussian_matching_kernel(shape, sigma_source_pix, sigma_target_pix)
    D, Wm, se, nv, sme = kernel_metrics(source, target, kernel)
    return PSFMatchMetrics("analytic_gaussian", sigma_source_pix, sigma_target_pix, shape, None, D, Wm, se, nv, sme)


def run_wiener_reference(sigma_source_pix: float = 2.5, sigma_target_pix: float = 5.0, shape: int = 101, regularization: float = 1e-6) -> PSFMatchMetrics:
    source = gaussian_psf(shape, sigma_source_pix)
    target = gaussian_psf(shape, sigma_target_pix)
    kernel = wiener_matching_kernel(source, target, regularization)
    D, Wm, se, nv, sme = kernel_metrics(source, target, kernel)
    return PSFMatchMetrics("wiener_scalar_tikhonov", sigma_source_pix, sigma_target_pix, shape, regularization, D, Wm, se, nv, sme)


def convergence_table() -> list[dict]:
    rows: list[dict] = []
    for sigma_s, sigma_t in ((1.2, 2.4), (2.5, 5.0), (4.0, 5.0)):
        for shape in (51, 101, 201):
            rows.append(run_gaussian_reference(sigma_s, sigma_t, shape).to_dict())
            for reg in (1e-10, 1e-8, 1e-6, 1e-4, 1e-2):
                rows.append(run_wiener_reference(sigma_s, sigma_t, shape, reg).to_dict())
    return rows


def impossible_case_is_detected() -> bool:
    try:
        analytic_gaussian_matching_kernel(101, sigma_source_pix=5.0, sigma_target_pix=3.0)
    except ValueError:
        return True
    return False
