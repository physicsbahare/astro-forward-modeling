"""Spectral-support experiment showing why wavelength overlap alone is insufficient.

A target band may lie entirely inside the wavelength span of the input photometry
while still being poorly constrained because broadband measurements do not resolve
spectral structure relevant to the target band.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np


@dataclass
class SpectralSupportMetrics:
    wavelength_coverage_fraction: float
    response_matrix_condition_number: float
    target_prediction: float
    target_truth: float
    target_fractional_bias: float
    target_posterior_fractional_sigma: float
    target_prior_fraction: float

    def to_dict(self) -> dict:
        return asdict(self)


def _gaussian_filter(wave: np.ndarray, center: float, sigma: float) -> np.ndarray:
    r = np.exp(-0.5 * ((wave - center) / sigma) ** 2)
    return r / np.trapezoid(r, wave)


def _integrate_response(template: np.ndarray, response: np.ndarray, wave: np.ndarray) -> float:
    return float(np.trapezoid(template * response, wave))


def run_spectral_support_check(seed: int = 8127) -> SpectralSupportMetrics:
    rng = np.random.default_rng(seed)
    wave = np.linspace(0.45, 1.75, 5001)

    t0 = np.ones_like(wave)
    t1 = (wave / 1.0) ** 1.2
    t2 = np.exp(-0.5 * ((wave - 1.05) / 0.025) ** 2)
    templates = np.vstack([t0, t1, t2])

    input_filters = np.vstack([
        _gaussian_filter(wave, 0.70, 0.18),
        _gaussian_filter(wave, 1.05, 0.28),
        _gaussian_filter(wave, 1.42, 0.20),
    ])
    target_filter = _gaussian_filter(wave, 1.05, 0.035)

    R = np.array([[_integrate_response(t, f, wave) for t in templates] for f in input_filters])
    rt = np.array([_integrate_response(t, target_filter, wave) for t in templates])

    coeff_truth = np.array([1.0, 0.55, 1.6])
    y_true = R @ coeff_truth
    sigma_y = 0.03 * np.maximum(y_true, 0.2)
    y_obs = y_true + rng.normal(0.0, sigma_y)
    Cinv = np.diag(1.0 / sigma_y**2)

    prior_sigma = np.array([10.0, 10.0, 1.0])
    prior_precision = np.diag(1.0 / prior_sigma**2)
    posterior_precision_data = R.T @ Cinv @ R
    posterior_precision = posterior_precision_data + prior_precision
    posterior_cov = np.linalg.inv(posterior_precision)
    posterior_mean = posterior_cov @ (R.T @ Cinv @ y_obs)

    pred = float(rt @ posterior_mean)
    truth = float(rt @ coeff_truth)
    pred_sigma = float(np.sqrt(rt @ posterior_cov @ rt))

    try:
        data_cov = np.linalg.inv(posterior_precision_data)
        data_var_unregularized = float(rt @ data_cov @ rt)
    except np.linalg.LinAlgError:
        data_var_unregularized = np.inf
    posterior_var = pred_sigma**2
    if np.isfinite(data_var_unregularized) and data_var_unregularized > 0:
        prior_fraction = float(np.clip(1.0 - posterior_var / data_var_unregularized, 0.0, 1.0))
    else:
        prior_fraction = 1.0

    combined = np.max(input_filters / input_filters.max(axis=1)[:, None], axis=0)
    supported = combined > 0.01
    target_norm = target_filter / np.trapezoid(target_filter, wave)
    coverage = float(np.trapezoid(target_norm * supported.astype(float), wave))

    cond = float(np.linalg.cond(R / sigma_y[:, None]))
    return SpectralSupportMetrics(
        wavelength_coverage_fraction=coverage,
        response_matrix_condition_number=cond,
        target_prediction=pred,
        target_truth=truth,
        target_fractional_bias=float((pred - truth) / truth),
        target_posterior_fractional_sigma=float(pred_sigma / truth),
        target_prior_fraction=prior_fraction,
    )
