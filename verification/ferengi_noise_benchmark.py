"""Noise/background extension of the controlled FERENGI-style benchmark.

The deterministic FERENGI baseline verifies the redshift, bandpass, PSF and
pixel-sampling operators without stochastic terms.  This module adds the final
controlled detector-noise step *after* the target image has been rendered.

It intentionally uses a synthetic Gaussian target background.  Injection into a
real noisy survey blank sky belongs to Gate D; the production code must not
re-noise such a background.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .ferengi_synthetic import (
    _artificial_target_image,
    _source_observed_cube,
    _target_grid,
)
from .reference import FlatLCDMReference
from .target_noise import inject_target_detector_noise


@dataclass
class FerengiNoiseMetrics:
    z_source: float
    z_target: float
    realizations: int
    expected_total_source_electrons: float
    gaussian_background_sigma_e: float
    target_pixels: int
    source_total_mean_relative_bias: float
    total_image_mean_relative_bias: float
    total_image_variance_relative_error: float
    center_source_variance_over_mean: float
    center_neighbor_source_correlation: float
    center_neighbor_background_correlation: float

    def to_dict(self) -> dict:
        return asdict(self)


def _expected_target_electron_image(
    *,
    z_source: float,
    z_target: float,
    expected_total_source_electrons: float,
) -> np.ndarray:
    cosmology = FlatLCDMReference(H0_km_s_Mpc=70.0, Om0=0.3)
    source_coord, source_observed_cube = _source_observed_cube(
        z_source,
        source_pixels=241,
        source_pixel_scale_arcsec=0.20,
        source_psf_fwhm_arcsec=0.70,
        cosmology=cosmology,
    )
    source_rest_cube_psf = source_observed_cube * (1.0 + z_source) ** 5
    _, tx, ty = _target_grid(
        source_coord,
        z_target,
        target_pixel_scale_arcsec=0.05,
        cosmology=cosmology,
    )
    image, _, _ = _artificial_target_image(
        source_rest_cube_psf,
        source_coord,
        tx,
        ty,
        z_source,
        z_target,
        source_psf_fwhm_arcsec=0.70,
        target_psf_fwhm_arcsec=0.25,
        target_pixel_scale_arcsec=0.05,
        center_um=0.62,
        sigma_um=0.035,
        cosmology=cosmology,
    )
    image = np.clip(np.asarray(image, dtype=float), 0.0, None)
    total = float(np.sum(image))
    if total <= 0.0:
        raise RuntimeError("Artificial target image has non-positive flux.")
    return image / total * float(expected_total_source_electrons)


def run_ferengi_noise_benchmark(
    *,
    z_target: float = 0.5,
    z_source: float = 0.05,
    realizations: int = 600,
    expected_total_source_electrons: float = 120_000.0,
    gaussian_background_sigma_e: float = 2.5,
    seed: int = 20260830,
) -> FerengiNoiseMetrics:
    """Verify the stochastic target-detector step on a FERENGI-rendered scene."""
    if realizations < 50:
        raise ValueError("Use at least 50 realizations for the ensemble benchmark.")
    if expected_total_source_electrons <= 0:
        raise ValueError("Expected source electrons must be positive.")
    if gaussian_background_sigma_e < 0:
        raise ValueError("Background sigma must be non-negative.")

    expectation = _expected_target_electron_image(
        z_source=z_source,
        z_target=z_target,
        expected_total_source_electrons=expected_total_source_electrons,
    )
    rng = np.random.default_rng(seed)

    peak_y, peak_x = np.unravel_index(np.argmax(expectation), expectation.shape)
    neighbor_x = peak_x + 1 if peak_x + 1 < expectation.shape[1] else peak_x - 1

    source_totals = np.empty(realizations, dtype=float)
    image_totals = np.empty(realizations, dtype=float)
    source_center = np.empty(realizations, dtype=float)
    source_neighbor = np.empty(realizations, dtype=float)
    background_center = np.empty(realizations, dtype=float)
    background_neighbor = np.empty(realizations, dtype=float)

    for i in range(realizations):
        sample = inject_target_detector_noise(
            expectation,
            rng=rng,
            gaussian_background_sigma_e=gaussian_background_sigma_e,
        )
        source_totals[i] = np.sum(sample.source_electrons)
        image_totals[i] = np.sum(sample.image_electrons)
        source_center[i] = sample.source_electrons[peak_y, peak_x]
        source_neighbor[i] = sample.source_electrons[peak_y, neighbor_x]
        background_center[i] = sample.background_electrons[peak_y, peak_x]
        background_neighbor[i] = sample.background_electrons[peak_y, neighbor_x]

    expected_total_variance = expected_total_source_electrons + (
        expectation.size * gaussian_background_sigma_e**2
    )
    measured_total_variance = float(np.var(image_totals, ddof=1))

    return FerengiNoiseMetrics(
        z_source=z_source,
        z_target=z_target,
        realizations=realizations,
        expected_total_source_electrons=expected_total_source_electrons,
        gaussian_background_sigma_e=gaussian_background_sigma_e,
        target_pixels=int(expectation.shape[0]),
        source_total_mean_relative_bias=float(
            abs(np.mean(source_totals) - expected_total_source_electrons)
            / expected_total_source_electrons
        ),
        total_image_mean_relative_bias=float(
            abs(np.mean(image_totals) - expected_total_source_electrons)
            / expected_total_source_electrons
        ),
        total_image_variance_relative_error=float(
            abs(measured_total_variance - expected_total_variance) / expected_total_variance
        ),
        center_source_variance_over_mean=float(
            np.var(source_center, ddof=1) / np.mean(source_center)
        ),
        center_neighbor_source_correlation=float(
            np.corrcoef(source_center, source_neighbor)[0, 1]
        ),
        center_neighbor_background_correlation=float(
            np.corrcoef(background_center, background_neighbor)[0, 1]
        ),
    )
