"""Passive-spiral spiral-feature survival under controlled artificial redshifting.

Verification harness only; this is not production code and not a classifier.

P1 deliberately isolates a non-axisymmetric morphology feature that is not
captured by the existing global FERENGI metrics or by a single-Sersic summary.
The scene is a fixed rest-frame band-integrated surface-brightness field, so
Tolman dimming is applied exactly once as (1+z)^-4.  No target noise, source-shot
noise, K-correction, luminosity evolution, or PSF sharpening is allowed here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import gaussian_filter

from .reference import FlatLCDMReference

ARCSEC_TO_RAD = np.deg2rad(1.0 / 3600.0)
KPC_M = 3.085_677_581_491_367e19
FWHM_TO_SIGMA = 1.0 / 2.354_820_045_030_9493

SOURCE_Z = 0.10
TARGET_Z = (0.50, 1.00, 2.00, 3.00)
SOURCE_PIXEL_SCALE_ARCSEC = 0.03
SOURCE_PSF_FWHM_ARCSEC = 0.05
TARGET_PIXEL_SCALE_ARCSEC = 0.03
TARGET_PSF_FWHM_ARCSEC = 0.145
HALF_EXTENT_KPC = 15.0
DISK_SCALE_KPC = 4.0
BULGE_SIGMA_KPC = 0.9
BULGE_AMPLITUDE = 0.5
ARM_AMPLITUDE = 0.38
PITCH_DEG = 22.0
ARM_R0_KPC = 2.5
ARM_METRIC_RMIN_KPC = 2.5
ARM_METRIC_RMAX_KPC = 9.0


@dataclass
class PassiveSpiralRow:
    z_source: float
    z_target: float
    source_pixel_scale_arcsec: float
    target_pixel_scale_arcsec: float
    source_psf_fwhm_arcsec: float
    source_psf_equivalent_at_target_arcsec: float
    target_psf_fwhm_arcsec: float
    target_psf_fwhm_kpc: float
    matching_kernel_fwhm_arcsec: float
    tolman_source_to_target_ratio: float
    latent_spiral_amplitude: float
    direct_target_spiral_amplitude: float
    artificial_target_spiral_amplitude: float
    smooth_direct_spiral_amplitude: float
    smooth_artificial_spiral_amplitude: float
    arm_retention_direct_over_latent: float
    arm_artificial_over_direct: float
    arm_artificial_minus_direct_abs: float
    normalized_l1_artificial_vs_direct: float
    total_flux_relative_difference: float

    def to_dict(self) -> dict:
        return asdict(self)


def _kpc_per_arcsec(cosmology: FlatLCDMReference, z: float) -> float:
    return cosmology.angular_diameter_distance_m(z) * ARCSEC_TO_RAD / KPC_M


def surface_brightness_ratio(z_source: float, z_target: float) -> float:
    """Band-integrated Tolman ratio from an already observed source to target."""
    if z_source < 0 or z_target < 0:
        raise ValueError("Redshifts must be non-negative.")
    return ((1.0 + z_source) / (1.0 + z_target)) ** 4


def _physical_grid(
    z: float,
    pixel_scale_arcsec: float,
    cosmology: FlatLCDMReference,
    half_extent_kpc: float = HALF_EXTENT_KPC,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    kpc_per_pixel = pixel_scale_arcsec * _kpc_per_arcsec(cosmology, z)
    half_pixels = int(np.ceil(half_extent_kpc / kpc_per_pixel))
    coord = np.arange(-half_pixels, half_pixels + 1, dtype=float) * kpc_per_pixel
    yy, xx = np.meshgrid(coord, coord, indexing="ij")
    return coord, xx, yy


def _spiral_phase(x_kpc: np.ndarray, y_kpc: np.ndarray) -> np.ndarray:
    radius = np.hypot(x_kpc, y_kpc)
    theta = np.arctan2(y_kpc, x_kpc)
    pitch = np.deg2rad(PITCH_DEG)
    safe_radius = np.maximum(radius, 0.3)
    return 2.0 * (
        theta - np.log(safe_radius / ARM_R0_KPC) / np.tan(pitch)
    )


def physical_scene(
    x_kpc: np.ndarray,
    y_kpc: np.ndarray,
    *,
    spiral: bool,
) -> np.ndarray:
    """Fixed disk+bulge scene with or without a two-arm logarithmic perturbation."""
    radius = np.hypot(x_kpc, y_kpc)
    disk = np.exp(-radius / DISK_SCALE_KPC)
    bulge = BULGE_AMPLITUDE * np.exp(-0.5 * (radius / BULGE_SIGMA_KPC) ** 2)

    if spiral:
        inner_taper = 1.0 - np.exp(-((radius / 1.5) ** 4))
        outer_taper = np.exp(-((radius / 12.0) ** 6))
        modulation = 1.0 + (
            ARM_AMPLITUDE
            * inner_taper
            * outer_taper
            * np.cos(_spiral_phase(x_kpc, y_kpc))
        )
        disk = disk * modulation

    return np.asarray(disk + bulge, dtype=float)


def matched_spiral_amplitude(
    image: np.ndarray,
    x_kpc: np.ndarray,
    y_kpc: np.ndarray,
) -> float:
    """Matched logarithmic m=2 amplitude in the frozen physical annulus."""
    data = np.clip(np.asarray(image, dtype=float), 0.0, None)
    radius = np.hypot(x_kpc, y_kpc)
    mask = (radius >= ARM_METRIC_RMIN_KPC) & (radius < ARM_METRIC_RMAX_KPC)
    weights = data[mask]
    total = float(np.sum(weights))
    if total <= 0:
        raise RuntimeError("Non-positive flux in spiral-metric annulus.")
    phase = _spiral_phase(x_kpc, y_kpc)[mask]
    complex_amp = np.sum(weights * np.exp(-1j * phase)) / total
    return float(np.abs(complex_amp))


def _convolve_gaussian(
    image: np.ndarray,
    fwhm_arcsec: float,
    pixel_scale_arcsec: float,
) -> np.ndarray:
    if fwhm_arcsec < 0:
        raise ValueError("PSF FWHM must be non-negative.")
    if fwhm_arcsec == 0:
        return np.asarray(image, dtype=float).copy()
    sigma_pix = fwhm_arcsec * FWHM_TO_SIGMA / pixel_scale_arcsec
    return gaussian_filter(
        np.asarray(image, dtype=float),
        sigma=sigma_pix,
        mode="constant",
        cval=0.0,
        truncate=6.0,
    )


def _resample_physical(
    image: np.ndarray,
    source_coord_kpc: np.ndarray,
    target_x_kpc: np.ndarray,
    target_y_kpc: np.ndarray,
) -> np.ndarray:
    interpolator = RegularGridInterpolator(
        (source_coord_kpc, source_coord_kpc),
        np.asarray(image, dtype=float),
        method="linear",
        bounds_error=False,
        fill_value=0.0,
    )
    points = np.column_stack((target_y_kpc.ravel(), target_x_kpc.ravel()))
    return interpolator(points).reshape(target_x_kpc.shape)


def psf_matching_kernel_fwhm(
    z_source: float,
    z_target: float,
    source_psf_fwhm_arcsec: float,
    target_psf_fwhm_arcsec: float,
    cosmology: FlatLCDMReference,
) -> tuple[float, float]:
    """Return redshifted-equivalent source PSF and positive degradation kernel."""
    source_equivalent = source_psf_fwhm_arcsec * (
        _kpc_per_arcsec(cosmology, z_source)
        / _kpc_per_arcsec(cosmology, z_target)
    )
    if target_psf_fwhm_arcsec <= source_equivalent:
        raise ValueError(
            "Target PSF is not broader than the redshifted-equivalent source PSF; "
            "P1 forbids sharpening/deconvolution."
        )
    kernel = float(
        np.sqrt(target_psf_fwhm_arcsec**2 - source_equivalent**2)
    )
    return float(source_equivalent), kernel


def _direct_target(
    z_target: float,
    *,
    spiral: bool,
    cosmology: FlatLCDMReference,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    _, xx, yy = _physical_grid(
        z_target, TARGET_PIXEL_SCALE_ARCSEC, cosmology
    )
    latent = physical_scene(xx, yy, spiral=spiral)
    observed = latent / (1.0 + z_target) ** 4
    convolved = _convolve_gaussian(
        observed, TARGET_PSF_FWHM_ARCSEC, TARGET_PIXEL_SCALE_ARCSEC
    )
    return convolved, xx, yy


def _artificial_target(
    z_target: float,
    *,
    spiral: bool,
    cosmology: FlatLCDMReference,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, float]:
    source_coord, source_x, source_y = _physical_grid(
        SOURCE_Z, SOURCE_PIXEL_SCALE_ARCSEC, cosmology
    )
    source_latent = physical_scene(source_x, source_y, spiral=spiral)
    source_observed = source_latent / (1.0 + SOURCE_Z) ** 4
    source_convolved = _convolve_gaussian(
        source_observed, SOURCE_PSF_FWHM_ARCSEC, SOURCE_PIXEL_SCALE_ARCSEC
    )

    _, target_x, target_y = _physical_grid(
        z_target, TARGET_PIXEL_SCALE_ARCSEC, cosmology
    )
    transferred = _resample_physical(
        source_convolved, source_coord, target_x, target_y
    )
    transferred *= surface_brightness_ratio(SOURCE_Z, z_target)

    source_equivalent, matching_kernel = psf_matching_kernel_fwhm(
        SOURCE_Z,
        z_target,
        SOURCE_PSF_FWHM_ARCSEC,
        TARGET_PSF_FWHM_ARCSEC,
        cosmology,
    )
    transferred = _convolve_gaussian(
        transferred, matching_kernel, TARGET_PIXEL_SCALE_ARCSEC
    )
    return transferred, target_x, target_y, source_equivalent, matching_kernel


def benchmark_row(
    z_target: float,
    cosmology: FlatLCDMReference | None = None,
) -> PassiveSpiralRow:
    cosmology = cosmology or FlatLCDMReference()

    source_coord, source_x, source_y = _physical_grid(
        SOURCE_Z, SOURCE_PIXEL_SCALE_ARCSEC, cosmology
    )
    del source_coord
    latent_spiral = matched_spiral_amplitude(
        physical_scene(source_x, source_y, spiral=True), source_x, source_y
    )

    direct, xx, yy = _direct_target(z_target, spiral=True, cosmology=cosmology)
    artificial, ax, ay, source_equiv, matching_kernel = _artificial_target(
        z_target, spiral=True, cosmology=cosmology
    )
    smooth_direct, sx, sy = _direct_target(
        z_target, spiral=False, cosmology=cosmology
    )
    smooth_artificial, sax, say, _, _ = _artificial_target(
        z_target, spiral=False, cosmology=cosmology
    )

    if direct.shape != artificial.shape:
        raise RuntimeError("Direct and artificial target shapes differ.")

    direct_amp = matched_spiral_amplitude(direct, xx, yy)
    artificial_amp = matched_spiral_amplitude(artificial, ax, ay)
    smooth_direct_amp = matched_spiral_amplitude(smooth_direct, sx, sy)
    smooth_artificial_amp = matched_spiral_amplitude(
        smooth_artificial, sax, say
    )

    direct_flux = float(np.sum(direct))
    artificial_flux = float(np.sum(artificial))
    if direct_flux <= 0:
        raise RuntimeError("Direct target has non-positive total flux.")

    normalized_l1 = float(
        np.sum(np.abs(artificial - direct)) / np.sum(np.abs(direct))
    )
    flux_rel = float((artificial_flux - direct_flux) / direct_flux)

    return PassiveSpiralRow(
        z_source=SOURCE_Z,
        z_target=float(z_target),
        source_pixel_scale_arcsec=SOURCE_PIXEL_SCALE_ARCSEC,
        target_pixel_scale_arcsec=TARGET_PIXEL_SCALE_ARCSEC,
        source_psf_fwhm_arcsec=SOURCE_PSF_FWHM_ARCSEC,
        source_psf_equivalent_at_target_arcsec=source_equiv,
        target_psf_fwhm_arcsec=TARGET_PSF_FWHM_ARCSEC,
        target_psf_fwhm_kpc=float(
            TARGET_PSF_FWHM_ARCSEC * _kpc_per_arcsec(cosmology, z_target)
        ),
        matching_kernel_fwhm_arcsec=matching_kernel,
        tolman_source_to_target_ratio=surface_brightness_ratio(SOURCE_Z, z_target),
        latent_spiral_amplitude=latent_spiral,
        direct_target_spiral_amplitude=direct_amp,
        artificial_target_spiral_amplitude=artificial_amp,
        smooth_direct_spiral_amplitude=smooth_direct_amp,
        smooth_artificial_spiral_amplitude=smooth_artificial_amp,
        arm_retention_direct_over_latent=float(direct_amp / latent_spiral),
        arm_artificial_over_direct=float(artificial_amp / direct_amp),
        arm_artificial_minus_direct_abs=float(abs(artificial_amp - direct_amp)),
        normalized_l1_artificial_vs_direct=normalized_l1,
        total_flux_relative_difference=flux_rel,
    )


def benchmark_grid() -> list[dict]:
    return [benchmark_row(z).to_dict() for z in TARGET_Z]
