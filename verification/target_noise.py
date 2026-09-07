"""Target-detector noise insertion primitives for verification experiments.

These routines are deliberately small and explicit.  They enforce the ordering
needed by artificial-redshifting simulations:

1. render/redshift the noiseless source;
2. apply the target PSF and pixel response;
3. convert the final expected source image to detector electrons;
4. draw source Poisson noise independently per detector pixel;
5. add exactly one target-background realization.

A real noisy blank-sky cutout must be supplied *as observed* and is never
re-noised.  A synthetic Gaussian background may be generated instead, but the
two modes are mutually exclusive so that background noise cannot accidentally
be counted twice.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class NoiseRealization:
    image_electrons: np.ndarray
    source_electrons: np.ndarray
    background_electrons: np.ndarray


def inject_target_detector_noise(
    expected_source_electrons: np.ndarray,
    *,
    rng: np.random.Generator,
    real_background_electrons: np.ndarray | None = None,
    gaussian_background_sigma_e: float | None = None,
) -> NoiseRealization:
    """Draw source shot noise and add one target-background realization.

    Parameters
    ----------
    expected_source_electrons
        Non-negative expected source electrons *after* target PSF convolution
        and target pixel sampling.
    rng
        Explicit NumPy random generator for reproducibility.
    real_background_electrons
        Optional observed blank-sky/background cutout in electrons.  It is
        inserted exactly once and is not independently re-noised.
    gaussian_background_sigma_e
        Optional standard deviation of a zero-mean Gaussian synthetic
        background in electrons per pixel.  This is intended only for
        controlled verification experiments.

    Returns
    -------
    NoiseRealization
        Total image and the source/background components used to form it.
    """

    expectation = np.asarray(expected_source_electrons, dtype=float)
    if expectation.ndim != 2:
        raise ValueError("Expected source image must be two-dimensional.")
    if not np.all(np.isfinite(expectation)):
        raise ValueError("Expected source image must be finite.")
    if np.any(expectation < 0.0):
        raise ValueError("Expected source electrons must be non-negative.")

    if real_background_electrons is not None and gaussian_background_sigma_e is not None:
        raise ValueError(
            "Choose either a real background cutout or a synthetic Gaussian background, not both."
        )

    source = rng.poisson(expectation).astype(float)

    if real_background_electrons is not None:
        background = np.asarray(real_background_electrons, dtype=float)
        if background.shape != expectation.shape:
            raise ValueError("Real background shape must match the source image.")
        if not np.all(np.isfinite(background)):
            raise ValueError("Real background must be finite.")
        background = background.copy()
    elif gaussian_background_sigma_e is not None:
        sigma = float(gaussian_background_sigma_e)
        if not np.isfinite(sigma) or sigma < 0.0:
            raise ValueError("Gaussian background sigma must be finite and non-negative.")
        background = rng.normal(0.0, sigma, size=expectation.shape)
    else:
        background = np.zeros_like(expectation, dtype=float)

    return NoiseRealization(
        image_electrons=source + background,
        source_electrons=source,
        background_electrons=background,
    )
