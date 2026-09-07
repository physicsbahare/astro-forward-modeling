"""Controlled FERENGI-style artificial-redshifting benchmark.

This module is part of the *verification harness*, not the future production
package.  It implements a deterministic synthetic analogue of the operator
sequence described by Barden, Jahnke & Haussler (2008): spatially resolved
multi-band spectral interpolation, angular-size transformation, cosmological
surface-brightness transformation, target-band integration, source-to-target
PSF transformation, and target pixel sampling.

The synthetic scene is deliberately constructed so that its spatially varying
SED is piecewise linear between known wavelength knots.  Therefore any error in
recovering the target image can be separated from an unknowable SED truth.  No
intrinsic luminosity or size evolution is applied: this is the observation-only
calibration mode.

Important convention
--------------------
The image planes are specific intensity per unit wavelength, ``I_lambda``.  At
corresponding emitted/observed wavelengths,

    I_lambda,obs = I_lambda,emit / (1 + z)^5.

For a target filter whose wavelength axis is redshifted with the galaxy, the
*band-integrated* surface brightness obeys the Tolman ``(1+z)^-4`` law while the
band-averaged ``I_lambda`` retains the ``(1+z)^-5`` spectral-density factor.
The code therefore never applies an additional K-correction or Tolman factor on
top of the direct spectral transformation.
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

REST_KNOTS_UM = np.array([0.40, 0.50, 0.60, 0.70, 0.80], dtype=float)
# A deliberately blue disk and red bulge.  Values are arbitrary I_lambda
# normalizations at the rest-wavelength knots.
DISK_SED = np.array([1.42, 1.22, 1.00, 0.82, 0.68], dtype=float)
BULGE_SED = np.array([0.52, 0.73, 1.00, 1.30, 1.58], dtype=float)


@dataclass
class FerengiSyntheticMetrics:
    z_source: float
    z_target: float
    mode: str
    source_pixels: int
    target_pixels: int
    source_pixel_scale_arcsec: float
    target_pixel_scale_arcsec: float
    source_psf_fwhm_arcsec: float
    source_psf_equivalent_at_target_arcsec: float
    target_psf_fwhm_arcsec: float
    added_matching_kernel_fwhm_arcsec: float
    radiometric_flux_scaling_relative_error: float
    normalized_l1_image_error: float
    total_flux_relative_error: float
    centroid_error_arcsec: float
    second_moment_relative_error: float
    radial_flux_profile_l1_error: float
    color_gradient_error_mag: float

    def to_dict(self) -> dict:
        return asdict(self)


def _kpc_per_arcsec(cosmology: FlatLCDMReference, z: float) -> float:
    return cosmology.angular_diameter_distance_m(z) * ARCSEC_TO_RAD / KPC_M


def _physical_scene(x_kpc: np.ndarray, y_kpc: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return disk and bulge spatial templates on a physical-coordinate grid."""
    pa = np.deg2rad(27.0)
    xp = x_kpc * np.cos(pa) + y_kpc * np.sin(pa)
    yp = -x_kpc * np.sin(pa) + y_kpc * np.cos(pa)

    q_disk = 0.64
    r_disk = np.sqrt(xp**2 + (yp / q_disk) ** 2)
    disk = np.exp(-r_disk / 4.2)

    q_bulge = 0.82
    r_bulge = np.sqrt(xp**2 + (yp / q_bulge) ** 2)
    # A compact, smooth bulge.  A Gaussian is used rather than a fitted Sersic
    # profile so that this benchmark tests the transfer operators, not a model
    # fitting implementation.
    bulge = 2.1 * np.exp(-0.5 * (r_bulge / 1.15) ** 2)
    return disk, bulge


def _sed_value(wavelength_um: float, values: np.ndarray) -> float:
    lam = float(wavelength_um)
    if lam < REST_KNOTS_UM[0] or lam > REST_KNOTS_UM[-1]:
        raise ValueError("Requested rest wavelength is outside the synthetic SED support.")
    return float(np.interp(lam, REST_KNOTS_UM, values))


def _latent_plane(x_kpc: np.ndarray, y_kpc: np.ndarray, wavelength_um: float) -> np.ndarray:
    disk, bulge = _physical_scene(x_kpc, y_kpc)
    return disk * _sed_value(wavelength_um, DISK_SED) + bulge * _sed_value(
        wavelength_um, BULGE_SED
    )


def _latent_knot_cube(x_kpc: np.ndarray, y_kpc: np.ndarray) -> np.ndarray:
    return np.stack([_latent_plane(x_kpc, y_kpc, lam) for lam in REST_KNOTS_UM], axis=0)


def _interpolated_plane_from_cube(cube: np.ndarray, wavelength_um: float) -> np.ndarray:
    lam = float(wavelength_um)
    if lam < REST_KNOTS_UM[0] or lam > REST_KNOTS_UM[-1]:
        raise ValueError("Requested rest wavelength is outside the source-band support.")
    if lam == REST_KNOTS_UM[-1]:
        return np.asarray(cube[-1], dtype=float)
    upper = int(np.searchsorted(REST_KNOTS_UM, lam, side="right"))
    lower = max(0, upper - 1)
    upper = min(upper, len(REST_KNOTS_UM) - 1)
    if lower == upper:
        return np.asarray(cube[lower], dtype=float)
    t = (lam - REST_KNOTS_UM[lower]) / (REST_KNOTS_UM[upper] - REST_KNOTS_UM[lower])
    return (1.0 - t) * cube[lower] + t * cube[upper]


def _gaussian_band_grid(center_um: float, sigma_um: float, samples: int = 81) -> tuple[np.ndarray, np.ndarray]:
    if sigma_um <= 0:
        raise ValueError("Bandpass sigma must be positive.")
    lam = np.linspace(center_um - 4.0 * sigma_um, center_um + 4.0 * sigma_um, samples)
    if lam[0] < REST_KNOTS_UM[0] or lam[-1] > REST_KNOTS_UM[-1]:
        raise ValueError("Synthetic target band extends outside source spectral support.")
    throughput = np.exp(-0.5 * ((lam - center_um) / sigma_um) ** 2)
    return lam, throughput


def _band_average_from_cube(
    cube: np.ndarray,
    center_um: float,
    sigma_um: float,
    samples: int = 81,
) -> np.ndarray:
    lam, throughput = _gaussian_band_grid(center_um, sigma_um, samples=samples)
    numerator = np.zeros_like(cube[0], dtype=float)
    for i in range(len(lam) - 1):
        l0, l1 = lam[i], lam[i + 1]
        p0 = _interpolated_plane_from_cube(cube, l0)
        p1 = _interpolated_plane_from_cube(cube, l1)
        numerator += 0.5 * (
            p0 * throughput[i] + p1 * throughput[i + 1]
        ) * (l1 - l0)
    denominator = float(np.trapezoid(throughput, lam))
    return numerator / denominator


def _direct_band_average(
    x_kpc: np.ndarray,
    y_kpc: np.ndarray,
    center_um: float,
    sigma_um: float,
    samples: int = 81,
) -> np.ndarray:
    lam, throughput = _gaussian_band_grid(center_um, sigma_um, samples=samples)
    numerator = np.zeros_like(x_kpc, dtype=float)
    for i in range(len(lam) - 1):
        p0 = _latent_plane(x_kpc, y_kpc, lam[i])
        p1 = _latent_plane(x_kpc, y_kpc, lam[i + 1])
        numerator += 0.5 * (
            p0 * throughput[i] + p1 * throughput[i + 1]
        ) * (lam[i + 1] - lam[i])
    denominator = float(np.trapezoid(throughput, lam))
    return numerator / denominator


def _source_observed_cube(
    z_source: float,
    source_pixels: int,
    source_pixel_scale_arcsec: float,
    source_psf_fwhm_arcsec: float,
    cosmology: FlatLCDMReference,
) -> tuple[np.ndarray, np.ndarray]:
    kpc_pix = source_pixel_scale_arcsec * _kpc_per_arcsec(cosmology, z_source)
    coord = (np.arange(source_pixels, dtype=float) - 0.5 * (source_pixels - 1)) * kpc_pix
    yy, xx = np.meshgrid(coord, coord, indexing="ij")
    rest_cube = _latent_knot_cube(xx, yy)

    source_sigma_pix = (
        source_psf_fwhm_arcsec * FWHM_TO_SIGMA / source_pixel_scale_arcsec
    )
    observed = np.empty_like(rest_cube)
    for i, plane in enumerate(rest_cube):
        dimmed = plane / (1.0 + z_source) ** 5
        observed[i] = gaussian_filter(
            dimmed,
            sigma=source_sigma_pix,
            mode="constant",
            cval=0.0,
            truncate=6.0,
        )
    return coord, observed


def _target_grid(
    source_coord_kpc: np.ndarray,
    z_target: float,
    target_pixel_scale_arcsec: float,
    cosmology: FlatLCDMReference,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    target_kpc_pix = target_pixel_scale_arcsec * _kpc_per_arcsec(cosmology, z_target)
    half_extent = float(np.max(np.abs(source_coord_kpc)))
    half_pixels = int(np.floor(half_extent / target_kpc_pix))
    coord = np.arange(-half_pixels, half_pixels + 1, dtype=float) * target_kpc_pix
    yy, xx = np.meshgrid(coord, coord, indexing="ij")
    return coord, xx, yy


def _resample_physical_image(
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


def _psf_match_to_target(
    image: np.ndarray,
    z_source: float,
    z_target: float,
    source_psf_fwhm_arcsec: float,
    target_psf_fwhm_arcsec: float,
    target_pixel_scale_arcsec: float,
    cosmology: FlatLCDMReference,
) -> tuple[np.ndarray, float, float]:
    source_equiv = source_psf_fwhm_arcsec * (
        _kpc_per_arcsec(cosmology, z_source) / _kpc_per_arcsec(cosmology, z_target)
    )
    if target_psf_fwhm_arcsec <= source_equiv:
        raise ValueError(
            "Target PSF is sharper than the redshifted source PSF; a pure degradation kernel does not exist."
        )
    kernel_fwhm = float(np.sqrt(target_psf_fwhm_arcsec**2 - source_equiv**2))
    kernel_sigma_pix = kernel_fwhm * FWHM_TO_SIGMA / target_pixel_scale_arcsec
    matched = gaussian_filter(
        image,
        sigma=kernel_sigma_pix,
        mode="constant",
        cval=0.0,
        truncate=6.0,
    )
    return matched, source_equiv, kernel_fwhm


def _direct_target_image(
    x_kpc: np.ndarray,
    y_kpc: np.ndarray,
    z_target: float,
    target_pixel_scale_arcsec: float,
    target_psf_fwhm_arcsec: float,
    center_um: float,
    sigma_um: float,
) -> np.ndarray:
    rest_band = _direct_band_average(x_kpc, y_kpc, center_um, sigma_um)
    observed = rest_band / (1.0 + z_target) ** 5
    sigma_pix = target_psf_fwhm_arcsec * FWHM_TO_SIGMA / target_pixel_scale_arcsec
    return gaussian_filter(observed, sigma=sigma_pix, mode="constant", cval=0.0, truncate=6.0)


def _artificial_target_image(
    source_rest_cube_psf: np.ndarray,
    source_coord_kpc: np.ndarray,
    target_x_kpc: np.ndarray,
    target_y_kpc: np.ndarray,
    z_source: float,
    z_target: float,
    source_psf_fwhm_arcsec: float,
    target_psf_fwhm_arcsec: float,
    target_pixel_scale_arcsec: float,
    center_um: float,
    sigma_um: float,
    cosmology: FlatLCDMReference,
) -> tuple[np.ndarray, float, float]:
    source_band = _band_average_from_cube(source_rest_cube_psf, center_um, sigma_um)
    resampled = _resample_physical_image(
        source_band,
        source_coord_kpc,
        target_x_kpc,
        target_y_kpc,
    )
    observed = resampled / (1.0 + z_target) ** 5
    return _psf_match_to_target(
        observed,
        z_source,
        z_target,
        source_psf_fwhm_arcsec,
        target_psf_fwhm_arcsec,
        target_pixel_scale_arcsec,
        cosmology,
    )


def _moments(image: np.ndarray, pixel_scale_arcsec: float) -> tuple[float, float, float]:
    data = np.clip(np.asarray(image, dtype=float), 0.0, None)
    total = float(np.sum(data))
    if total <= 0:
        raise RuntimeError("Non-positive image flux.")
    y, x = np.indices(data.shape, dtype=float)
    cx = float(np.sum(data * x) / total)
    cy = float(np.sum(data * y) / total)
    varx = float(np.sum(data * (x - cx) ** 2) / total)
    vary = float(np.sum(data * (y - cy) ** 2) / total)
    sigma_arcsec = float(np.sqrt(0.5 * (varx + vary)) * pixel_scale_arcsec)
    return cx, cy, sigma_arcsec


def _radial_flux_fractions(image: np.ndarray, radius_kpc: np.ndarray) -> np.ndarray:
    edges = np.array([0.0, 1.5, 3.0, 5.0, 7.5, 10.5, 14.0, 18.0], dtype=float)
    fluxes = []
    data = np.clip(np.asarray(image, dtype=float), 0.0, None)
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (radius_kpc >= lo) & (radius_kpc < hi)
        fluxes.append(float(np.sum(data[mask])))
    values = np.asarray(fluxes, dtype=float)
    if values.sum() <= 0:
        raise RuntimeError("No flux in radial-profile bins.")
    return values / values.sum()


def _color_gradient_mag(blue: np.ndarray, red: np.ndarray, radius_kpc: np.ndarray) -> float:
    inner = radius_kpc < 2.0
    outer = (radius_kpc >= 5.0) & (radius_kpc < 9.0)
    b_in = float(np.mean(blue[inner]))
    r_in = float(np.mean(red[inner]))
    b_out = float(np.mean(blue[outer]))
    r_out = float(np.mean(red[outer]))
    if min(b_in, r_in, b_out, r_out) <= 0:
        raise RuntimeError("Color-gradient apertures contain non-positive mean intensity.")
    color_inner = -2.5 * np.log10(b_in / r_in)
    color_outer = -2.5 * np.log10(b_out / r_out)
    return float(color_outer - color_inner)


def _radiometric_flux_scaling_error(
    rest_band: np.ndarray,
    physical_pixel_kpc: float,
    z_source: float,
    z_target: float,
    cosmology: FlatLCDMReference,
) -> float:
    # Use the same physical pixels at both redshifts.  Pixel angular area is
    # (physical size / kpc-per-arcsec)^2.  This makes the expected matched-rest-
    # band F_lambda ratio explicit and independent of the image resampler.
    omega_s = (physical_pixel_kpc / _kpc_per_arcsec(cosmology, z_source)) ** 2
    omega_t = (physical_pixel_kpc / _kpc_per_arcsec(cosmology, z_target)) ** 2
    flux_s = float(np.sum(rest_band) * omega_s / (1.0 + z_source) ** 5)
    flux_t = float(np.sum(rest_band) * omega_t / (1.0 + z_target) ** 5)

    dl_s = cosmology.luminosity_distance_m(z_source)
    dl_t = cosmology.luminosity_distance_m(z_target)
    expected_ratio = (dl_s**2 * (1.0 + z_source)) / (dl_t**2 * (1.0 + z_target))
    measured_ratio = flux_t / flux_s
    return float(abs(measured_ratio - expected_ratio) / expected_ratio)


def run_ferengi_synthetic_benchmark(
    z_target: float,
    *,
    z_source: float = 0.05,
    source_pixels: int = 241,
    source_pixel_scale_arcsec: float = 0.20,
    target_pixel_scale_arcsec: float = 0.05,
    source_psf_fwhm_arcsec: float = 0.70,
    target_psf_fwhm_arcsec: float = 0.25,
) -> FerengiSyntheticMetrics:
    """Run one observation-only synthetic artificial-redshifting experiment."""
    if z_target <= z_source:
        raise ValueError("This benchmark requires z_target > z_source.")

    cosmology = FlatLCDMReference(H0_km_s_Mpc=70.0, Om0=0.3)
    source_coord, source_observed_cube = _source_observed_cube(
        z_source,
        source_pixels,
        source_pixel_scale_arcsec,
        source_psf_fwhm_arcsec,
        cosmology,
    )
    # Undo only the known source-redshift spectral-density factor to obtain the
    # source-PSF-blurred rest-frame knot planes.  No deconvolution is attempted;
    # the shrunk source PSF is explicitly carried into the later matching step.
    source_rest_cube_psf = source_observed_cube * (1.0 + z_source) ** 5

    target_coord, tx, ty = _target_grid(
        source_coord,
        z_target,
        target_pixel_scale_arcsec,
        cosmology,
    )
    radius_kpc = np.sqrt(tx**2 + ty**2)

    main_center, main_sigma = 0.62, 0.035
    recovered, source_equiv, kernel_fwhm = _artificial_target_image(
        source_rest_cube_psf,
        source_coord,
        tx,
        ty,
        z_source,
        z_target,
        source_psf_fwhm_arcsec,
        target_psf_fwhm_arcsec,
        target_pixel_scale_arcsec,
        main_center,
        main_sigma,
        cosmology,
    )
    truth = _direct_target_image(
        tx,
        ty,
        z_target,
        target_pixel_scale_arcsec,
        target_psf_fwhm_arcsec,
        main_center,
        main_sigma,
    )

    rec_sum = float(np.sum(recovered))
    truth_sum = float(np.sum(truth))
    if rec_sum <= 0 or truth_sum <= 0:
        raise RuntimeError("Non-positive target flux.")
    rec_norm = recovered / rec_sum
    truth_norm = truth / truth_sum
    l1 = float(np.sum(np.abs(rec_norm - truth_norm)))
    flux_err = float(abs(rec_sum - truth_sum) / truth_sum)

    cx_r, cy_r, sigma_r = _moments(recovered, target_pixel_scale_arcsec)
    cx_t, cy_t, sigma_t = _moments(truth, target_pixel_scale_arcsec)
    centroid_err = float(
        np.hypot(cx_r - cx_t, cy_r - cy_t) * target_pixel_scale_arcsec
    )
    sigma_err = float(abs(sigma_r - sigma_t) / sigma_t)

    radial_rec = _radial_flux_fractions(recovered, radius_kpc)
    radial_truth = _radial_flux_fractions(truth, radius_kpc)
    radial_l1 = float(np.sum(np.abs(radial_rec - radial_truth)))

    blue_rec, _, _ = _artificial_target_image(
        source_rest_cube_psf,
        source_coord,
        tx,
        ty,
        z_source,
        z_target,
        source_psf_fwhm_arcsec,
        target_psf_fwhm_arcsec,
        target_pixel_scale_arcsec,
        0.50,
        0.020,
        cosmology,
    )
    red_rec, _, _ = _artificial_target_image(
        source_rest_cube_psf,
        source_coord,
        tx,
        ty,
        z_source,
        z_target,
        source_psf_fwhm_arcsec,
        target_psf_fwhm_arcsec,
        target_pixel_scale_arcsec,
        0.70,
        0.020,
        cosmology,
    )
    blue_truth = _direct_target_image(
        tx,
        ty,
        z_target,
        target_pixel_scale_arcsec,
        target_psf_fwhm_arcsec,
        0.50,
        0.020,
    )
    red_truth = _direct_target_image(
        tx,
        ty,
        z_target,
        target_pixel_scale_arcsec,
        target_psf_fwhm_arcsec,
        0.70,
        0.020,
    )
    grad_rec = _color_gradient_mag(blue_rec, red_rec, radius_kpc)
    grad_truth = _color_gradient_mag(blue_truth, red_truth, radius_kpc)

    rest_band_truth = _direct_band_average(tx, ty, main_center, main_sigma)
    physical_pixel_kpc = target_pixel_scale_arcsec * _kpc_per_arcsec(cosmology, z_target)
    radiometric_err = _radiometric_flux_scaling_error(
        rest_band_truth,
        physical_pixel_kpc,
        z_source,
        z_target,
        cosmology,
    )

    return FerengiSyntheticMetrics(
        z_source=z_source,
        z_target=z_target,
        mode="observation_only",
        source_pixels=source_pixels,
        target_pixels=len(target_coord),
        source_pixel_scale_arcsec=source_pixel_scale_arcsec,
        target_pixel_scale_arcsec=target_pixel_scale_arcsec,
        source_psf_fwhm_arcsec=source_psf_fwhm_arcsec,
        source_psf_equivalent_at_target_arcsec=source_equiv,
        target_psf_fwhm_arcsec=target_psf_fwhm_arcsec,
        added_matching_kernel_fwhm_arcsec=kernel_fwhm,
        radiometric_flux_scaling_relative_error=radiometric_err,
        normalized_l1_image_error=l1,
        total_flux_relative_error=flux_err,
        centroid_error_arcsec=centroid_err,
        second_moment_relative_error=sigma_err,
        radial_flux_profile_l1_error=radial_l1,
        color_gradient_error_mag=float(abs(grad_rec - grad_truth)),
    )


def benchmark_grid() -> list[dict]:
    return [run_ferengi_synthetic_benchmark(z).to_dict() for z in (0.20, 0.50, 1.00)]
