"""Noise-ordering checks for source Poisson statistics and real-image injection."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .psf import gaussian_psf


@dataclass
class NoiseMetrics:
    realizations: int
    expected_total_source_electrons: float
    physical_center_variance_over_mean: float
    physical_neighbor_correlation: float
    pre_psf_center_variance_over_mean: float
    pre_psf_neighbor_correlation: float
    double_background_variance_ratio: float

    def to_dict(self) -> dict:
        return asdict(self)


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.corrcoef(a, b)[0, 1])


def run_noise_check(
    realizations: int = 30000,
    expected_total_source_electrons: float = 5000.0,
    seed: int = 73191,
) -> NoiseMetrics:
    rng = np.random.default_rng(seed)
    psf = gaussian_psf(31, sigma_pix=2.2)
    c = psf.shape[0] // 2
    p0 = psf[c, c]
    p1 = psf[c, c + 1]

    center_phys = rng.poisson(expected_total_source_electrons * p0, size=realizations)
    neigh_phys = rng.poisson(expected_total_source_electrons * p1, size=realizations)

    total_wrong = rng.poisson(expected_total_source_electrons, size=realizations)
    center_wrong = total_wrong * p0
    neigh_wrong = total_wrong * p1

    physical_vm = float(np.var(center_phys, ddof=1) / np.mean(center_phys))
    wrong_vm = float(np.var(center_wrong, ddof=1) / np.mean(center_wrong))
    physical_corr = _corr(center_phys, neigh_phys)
    wrong_corr = _corr(center_wrong, neigh_wrong)

    n = 500_000
    background = rng.normal(0.0, 3.0, size=n)
    extra_background = rng.normal(0.0, 3.0, size=n)
    ratio = float(np.var(background + extra_background) / np.var(background))

    return NoiseMetrics(
        realizations=realizations,
        expected_total_source_electrons=expected_total_source_electrons,
        physical_center_variance_over_mean=physical_vm,
        physical_neighbor_correlation=physical_corr,
        pre_psf_center_variance_over_mean=wrong_vm,
        pre_psf_neighbor_correlation=wrong_corr,
        double_background_variance_ratio=ratio,
    )
