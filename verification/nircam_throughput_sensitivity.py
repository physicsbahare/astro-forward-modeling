"""Small throughput-aware helpers for the passive-disk T1 sensitivity test."""
from __future__ import annotations

import numpy as np

_TRAPEZOID = getattr(np, "trapezoid", np.trapz)


def _validate_curve(wavelength_um: np.ndarray, throughput: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    lam = np.asarray(wavelength_um, dtype=float)
    thr = np.asarray(throughput, dtype=float)
    if lam.ndim != 1 or thr.ndim != 1 or lam.shape != thr.shape or lam.size < 2:
        raise ValueError("wavelength and throughput must be same-length 1D arrays")
    if not np.all(np.isfinite(lam)) or not np.all(np.isfinite(thr)):
        raise ValueError("curve contains non-finite values")
    if np.any(lam <= 0) or np.any(np.diff(lam) <= 0) or np.any(thr < 0):
        raise ValueError("require positive increasing wavelengths and non-negative throughput")
    return lam, thr


def pivot_wavelength_um(wavelength_um: np.ndarray, throughput: np.ndarray) -> float:
    lam, thr = _validate_curve(wavelength_um, throughput)
    num = _TRAPEZOID(thr * lam, lam)
    den = _TRAPEZOID(thr / lam, lam)
    if den <= 0:
        raise ValueError("throughput integral is zero")
    return float(np.sqrt(num / den))


def fnu_response_moments(wavelength_um: np.ndarray, throughput: np.ndarray, max_order: int) -> np.ndarray:
    """Photon-counting moments for band-averaged Fnu.

    A band average of a polynomial Fnu=sum c_n lambda^n is
    sum c_n mu_n with weights proportional to throughput/lambda.
    mu_0 is 1 by construction.
    """
    if max_order < 0:
        raise ValueError("max_order must be non-negative")
    lam, thr = _validate_curve(wavelength_um, throughput)
    weight = thr / lam
    den = _TRAPEZOID(weight, lam)
    if den <= 0:
        raise ValueError("throughput integral is zero")
    out = [1.0]
    for order in range(1, max_order + 1):
        out.append(float(_TRAPEZOID((lam**order) * weight, lam) / den))
    return np.asarray(out, dtype=float)


def mapped_target_moments(target_moments: np.ndarray, z_source: float, z_target: float) -> np.ndarray:
    if z_source < 0 or z_target < 0:
        raise ValueError("redshifts must be non-negative")
    m = np.asarray(target_moments, dtype=float)
    if m.ndim != 1 or m.size < 1 or not np.isclose(m[0], 1.0):
        raise ValueError("moments must start with mu_0=1")
    scale = (1.0 + z_source) / (1.0 + z_target)
    return m * (scale ** np.arange(m.size))


def interpolation_weights(source_moment_rows: np.ndarray, target_moments: np.ndarray) -> np.ndarray:
    A = np.asarray(source_moment_rows, dtype=float)
    v = np.asarray(target_moments, dtype=float)
    if A.ndim != 2 or A.shape[0] != A.shape[1] or v.shape != (A.shape[1],):
        raise ValueError("source moment matrix must be square and match target vector")
    return np.linalg.solve(A.T, v)


def combine_images(images: list[np.ndarray], weights: np.ndarray) -> np.ndarray:
    if len(images) == 0:
        raise ValueError("at least one image is required")
    w = np.asarray(weights, dtype=float)
    if w.shape != (len(images),):
        raise ValueError("weights must match image count")
    arrays = [np.asarray(x, dtype=float) for x in images]
    shape = arrays[0].shape
    if any(a.shape != shape for a in arrays):
        raise ValueError("images must share one grid")
    out = np.zeros(shape, dtype=float)
    for wi, ai in zip(w, arrays):
        out += wi * ai
    return out
