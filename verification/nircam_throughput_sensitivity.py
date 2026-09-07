"""Throughput-aware spectral synthesis helpers for passive-disk forward modeling.

The original T1 sensitivity test used these operators diagnostically.  After T1
showed that flux normalization is more sensitive than morphology, all new
passive-disk science runs use the exact supplied NIRCam mean-system throughput
curves and a three-band quadratic Fnu(lambda) model by default.  The old
pivot-linear R1 interpolation remains available only as a frozen historical
reference.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import numpy as np

_TRAPEZOID = getattr(np, "trapezoid", np.trapz)

DEFAULT_THROUGHPUT_FILES = {
    "F115W": "F115W_May2024_mean_system_throughput.txt",
    "F150W": "F150W_May2024_mean_system_throughput.txt",
    "F277W": "F277W_May2024_mean_system_throughput.txt",
    "F444W": "F444W_May2024_mean_system_throughput.txt",
}


@dataclass(frozen=True)
class ThroughputCurve:
    wavelength_um: np.ndarray
    throughput: np.ndarray


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


def load_mean_throughput(band: str, directory: str | Path) -> ThroughputCurve:
    band = str(band).upper()
    if band not in DEFAULT_THROUGHPUT_FILES:
        raise ValueError(f"Unsupported bundled band: {band}")
    root = Path(directory)
    path = root / DEFAULT_THROUGHPUT_FILES[band]
    if not path.exists():
        raise FileNotFoundError(path)
    arr = np.loadtxt(path, skiprows=1)
    if arr.ndim != 2 or arr.shape[1] < 2:
        raise ValueError(f"Malformed throughput file: {path}")
    lam, thr = _validate_curve(arr[:, 0], arr[:, 1])
    return ThroughputCurve(lam, thr)


def pivot_wavelength_um(wavelength_um: np.ndarray, throughput: np.ndarray) -> float:
    lam, thr = _validate_curve(wavelength_um, throughput)
    num = _TRAPEZOID(thr * lam, lam)
    den = _TRAPEZOID(thr / lam, lam)
    if den <= 0:
        raise ValueError("throughput integral is zero")
    return float(np.sqrt(num / den))


def fnu_response_moments(wavelength_um: np.ndarray, throughput: np.ndarray, max_order: int) -> np.ndarray:
    """Photon-counting moments for band-averaged Fnu.

    For Fnu(lambda)=sum c_n lambda^n, the calibrated band average is
    sum c_n mu_n when the photon-counting weights are proportional to
    throughput/lambda. mu_0 is 1 by construction.
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
    cond = np.linalg.cond(A.T)
    if not np.isfinite(cond) or cond > 1e8:
        raise ValueError(f"Spectral interpolation system is ill-conditioned (cond={cond:.3g})")
    return np.linalg.solve(A.T, v)


def combine_images(images: list[np.ndarray], weights: np.ndarray) -> np.ndarray:
    if len(images) == 0:
        raise ValueError("at least one image is required")
    w = np.asarray(weights, dtype=float)
    if w.shape != (len(images),):
        raise ValueError("weights must match image count")
    if not np.all(np.isfinite(w)):
        raise ValueError("weights must be finite")
    arrays = [np.asarray(x, dtype=float) for x in images]
    shape = arrays[0].shape
    if any(a.shape != shape for a in arrays):
        raise ValueError("images must share one grid")
    out = np.zeros(shape, dtype=float)
    for wi, ai in zip(w, arrays):
        out += wi * ai
    return out


def curved_fnu_bandpass_weights(
    *,
    source_bands: tuple[str, str, str],
    target_band: str,
    z_source: float,
    z_target: float,
    directory: str | Path,
) -> np.ndarray:
    """Return exact-throughput quadratic-Fnu image weights.

    Three source band averages constrain a quadratic Fnu(lambda) at each pixel.
    The target filter is mapped to the source-observed wavelength frame by
    (1+z_source)/(1+z_target), and its exact throughput is integrated there.
    No pivot-wavelength approximation is used.
    """
    if len(set(map(str.upper, source_bands))) != 3:
        raise ValueError("three distinct source bands are required for curvature")
    source_rows = []
    for band in source_bands:
        curve = load_mean_throughput(band, directory)
        source_rows.append(fnu_response_moments(curve.wavelength_um, curve.throughput, 2))
    target = load_mean_throughput(target_band, directory)
    target_m = fnu_response_moments(target.wavelength_um, target.throughput, 2)
    mapped = mapped_target_moments(target_m, z_source, z_target)
    return interpolation_weights(np.vstack(source_rows), mapped)


def synthesize_curved_fnu_image(
    images_by_band: dict[str, np.ndarray],
    *,
    target_band: str,
    z_source: float,
    z_target: float,
    source_bands: tuple[str, str, str] = ("F115W", "F150W", "F277W"),
    directory: str | Path,
) -> tuple[np.ndarray, np.ndarray]:
    """Synthesize the source-plane target-band image with SED curvature.

    Input images must already be on one WCS/pixel grid and homogenized to one
    common source PSF. Negative residual pixels are retained; no clipping or
    positivity prior is imposed on the pixel model. The returned weights are
    recorded for provenance because curvature interpolation can use negative
    coefficients and therefore can amplify noise.
    """
    norm = {str(k).upper(): np.asarray(v, dtype=float) for k, v in images_by_band.items()}
    missing = [b for b in source_bands if b.upper() not in norm]
    if missing:
        raise ValueError(f"Missing source bands required for curved SED: {missing}")
    weights = curved_fnu_bandpass_weights(
        source_bands=source_bands,
        target_band=target_band,
        z_source=z_source,
        z_target=z_target,
        directory=directory,
    )
    image = combine_images([norm[b.upper()] for b in source_bands], weights)
    return image, weights
