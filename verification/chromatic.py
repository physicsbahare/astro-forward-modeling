"""Chromatic-PSF verification with analytic Gaussian source components.

The experiment demonstrates that, when different spatial components have different
spectra, a single broadband PSF based on the *global* SED is not generally
identical to wavelength-by-wavelength rendering.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np


@dataclass
class ChromaticMetrics:
    wavelength_samples: int
    correct_flux: float
    single_psf_flux_relative_error: float
    l1_normalized_image_difference: float
    second_moment_relative_difference: float
    disk_effective_psf_sigma_pix: float
    bulge_effective_psf_sigma_pix: float
    global_effective_psf_sigma_pix: float

    def to_dict(self) -> dict:
        return asdict(self)


def _gaussian_map(shape: int, sigma: float) -> np.ndarray:
    c = shape // 2
    y, x = np.mgrid[:shape, :shape]
    g = np.exp(-0.5 * ((x - c) ** 2 + (y - c) ** 2) / sigma**2)
    return g / g.sum()


def _second_moment_sigma(image: np.ndarray) -> float:
    f = image / image.sum()
    y, x = np.indices(f.shape)
    cx = np.sum(f * x)
    cy = np.sum(f * y)
    return float(np.sqrt(0.5 * (np.sum(f * (x - cx) ** 2) + np.sum(f * (y - cy) ** 2))))


def _throughput(lambda_um: np.ndarray) -> np.ndarray:
    lam = np.asarray(lambda_um)
    core = np.exp(-0.5 * ((lam - 3.0) / 1.15) ** 4)
    return np.where((lam >= 1.0) & (lam <= 5.0), core, 0.0)


def _disk_sed(lambda_um: np.ndarray) -> np.ndarray:
    lam = np.asarray(lambda_um)
    return (lam / 2.5) ** -1.8


def _bulge_sed(lambda_um: np.ndarray) -> np.ndarray:
    lam = np.asarray(lambda_um)
    return 0.75 * (lam / 2.5) ** 1.25


def _psf_sigma(lambda_um: np.ndarray) -> np.ndarray:
    return 0.72 * np.asarray(lambda_um)


def _photon_weight(sed_flambda: np.ndarray, throughput: np.ndarray, lambda_um: np.ndarray) -> np.ndarray:
    return sed_flambda * throughput * lambda_um


def run_chromatic_check(wavelength_samples: int = 401, shape: int = 161) -> ChromaticMetrics:
    lam = np.linspace(1.0, 5.0, wavelength_samples)
    throughput = _throughput(lam)
    wd = _photon_weight(_disk_sed(lam), throughput, lam)
    wb = _photon_weight(_bulge_sed(lam), throughput, lam)
    ps = _psf_sigma(lam)

    sigma_disk = 7.0
    sigma_bulge = 1.7

    sigma2_disk_eff = np.trapezoid(wd * ps**2, lam) / np.trapezoid(wd, lam)
    sigma2_bulge_eff = np.trapezoid(wb * ps**2, lam) / np.trapezoid(wb, lam)
    wglobal = wd + wb
    sigma2_global_eff = np.trapezoid(wglobal * ps**2, lam) / np.trapezoid(wglobal, lam)

    fd = np.trapezoid(wd, lam)
    fb = np.trapezoid(wb, lam)
    global_sigma = np.sqrt(sigma2_global_eff)
    single_psf = fd * _gaussian_map(shape, np.hypot(sigma_disk, global_sigma)) + fb * _gaussian_map(shape, np.hypot(sigma_bulge, global_sigma))

    dl = lam[1] - lam[0]
    correct_trap = np.zeros((shape, shape), dtype=float)
    trap_coeff = np.ones(wavelength_samples)
    trap_coeff[[0, -1]] = 0.5
    for i in range(wavelength_samples):
        disk_obs = _gaussian_map(shape, np.hypot(sigma_disk, ps[i]))
        bulge_obs = _gaussian_map(shape, np.hypot(sigma_bulge, ps[i]))
        correct_trap += trap_coeff[i] * dl * (wd[i] * disk_obs + wb[i] * bulge_obs)
    correct = correct_trap

    flux_err = abs(single_psf.sum() - correct.sum()) / correct.sum()
    c = correct / correct.sum()
    s = single_psf / single_psf.sum()
    l1 = float(np.sum(np.abs(c - s)))
    m2c = _second_moment_sigma(c)
    m2s = _second_moment_sigma(s)
    m2diff = abs(m2s - m2c) / m2c

    return ChromaticMetrics(wavelength_samples, float(correct.sum()), float(flux_err), l1, float(m2diff), float(np.sqrt(sigma2_disk_eff)), float(np.sqrt(sigma2_bulge_eff)), float(global_sigma))


def convergence_table() -> list[dict]:
    return [run_chromatic_check(n).to_dict() for n in (9, 17, 33, 65, 129, 257, 513, 1025)]
