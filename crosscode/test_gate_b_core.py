"""Executable Gate-B cross-code checks.

These tests compare the independent reference harness against maintained astronomy
packages. They are intentionally separate from the future production package.

Pinned benchmark environment:
- Astropy 8.0.1
- reproject 0.21.0
- Photutils 3.0.0
- GalSim 2.8.4
"""

from __future__ import annotations

import numpy as np


def test_astropy_cosmology_matches_independent_flat_lcdm_reference():
    import astropy.units as u
    from astropy.cosmology import FlatLambdaCDM

    from verification.reference import FlatLCDMReference

    independent = FlatLCDMReference(H0_km_s_Mpc=70.0, Om0=0.3)
    astropy_cosmo = FlatLambdaCDM(H0=70.0 * u.km / u.s / u.Mpc, Om0=0.3, Tcmb0=0.0 * u.K)

    z_grid = np.geomspace(1.0e-5, 20.0, 80)
    dl_ref = np.array([independent.luminosity_distance_m(float(z)) for z in z_grid])
    da_ref = np.array([independent.angular_diameter_distance_m(float(z)) for z in z_grid])
    dl_astropy = astropy_cosmo.luminosity_distance(z_grid).to_value(u.m)
    da_astropy = astropy_cosmo.angular_diameter_distance(z_grid).to_value(u.m)

    dl_rel = np.max(np.abs(dl_ref - dl_astropy) / dl_astropy)
    da_rel = np.max(np.abs(da_ref - da_astropy) / da_astropy)
    duality = np.max(np.abs(dl_astropy / ((1.0 + z_grid) ** 2 * da_astropy) - 1.0))

    assert dl_rel < 5.0e-10
    assert da_rel < 5.0e-10
    assert duality < 5.0e-13


def test_astropy_spectral_density_equivalency_matches_explicit_formula():
    import astropy.constants as const
    import astropy.units as u

    wave = np.geomspace(0.2, 10.0, 40) * u.um
    fnu = np.geomspace(0.01, 100.0, 40) * u.uJy

    flambda_astropy = fnu.to(u.W / u.m**2 / u.m, equivalencies=u.spectral_density(wave))
    flambda_explicit = (fnu.to(u.W / u.m**2 / u.Hz) * const.c / wave.to(u.m) ** 2).to(
        u.W / u.m**2 / u.m
    )
    rel = np.max(np.abs((flambda_astropy - flambda_explicit) / flambda_explicit))
    assert rel < 5.0e-14


def test_photutils_wiener_kernel_matches_reference_convention():
    from photutils.psf_matching import make_wiener_kernel

    from verification.psf import gaussian_psf, kernel_metrics, wiener_matching_kernel

    source = gaussian_psf(101, 2.5)
    target = gaussian_psf(101, 5.0)
    regularization = 1.0e-6

    external = make_wiener_kernel(source, target, regularization=regularization)
    reference = wiener_matching_kernel(source, target, regularization=regularization)

    assert abs(external.sum() - 1.0) < 5.0e-13
    assert abs(reference.sum() - 1.0) < 5.0e-13

    kernel_l1 = float(np.sum(np.abs(external - reference)))
    assert kernel_l1 < 2.0e-8

    d_ext, w_ext, _, _, _ = kernel_metrics(source, target, external)
    d_ref, w_ref, _, _, _ = kernel_metrics(source, target, reference)
    assert abs(d_ext - d_ref) < 2.0e-8
    assert abs(w_ext - w_ref) < 2.0e-8


def _simple_tan_wcs(nx: int, ny: int, pixel_arcsec: float, rotation_deg: float = 0.0):
    from astropy.wcs import WCS

    w = WCS(naxis=2)
    w.wcs.crpix = [(nx + 1) / 2.0, (ny + 1) / 2.0]
    scale = pixel_arcsec / 3600.0
    theta = np.deg2rad(rotation_deg)
    cd = np.array(
        [
            [-scale * np.cos(theta), scale * np.sin(theta)],
            [scale * np.sin(theta), scale * np.cos(theta)],
        ]
    )
    w.wcs.cd = cd
    w.wcs.crval = [150.0, 2.0]
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    return w


def test_reproject_exact_preserves_constant_surface_brightness():
    from reproject import reproject_exact

    source = np.ones((101, 101), dtype=float) * 7.25
    w_in = _simple_tan_wcs(101, 101, pixel_arcsec=0.10, rotation_deg=0.0)
    w_out = _simple_tan_wcs(129, 129, pixel_arcsec=0.078, rotation_deg=17.0)

    out, footprint = reproject_exact((source, w_in), w_out, shape_out=(129, 129))
    valid = footprint > 0.999
    assert np.count_nonzero(valid) > 1000
    max_abs = np.max(np.abs(out[valid] - 7.25))
    assert max_abs < 2.0e-10


def test_reproject_adaptive_distinguishes_surface_brightness_from_flux_per_pixel():
    """Verify the documented unit semantic, not merely numerical interpolation.

    Reproject's default adaptive mode treats pixel values as surface brightness.
    With an output grid having half the pixel scale in each dimension, blindly
    summing such values should increase the numerical sum by roughly four.  The
    explicit ``conserve_flux=True`` mode instead treats values as flux per pixel
    and should retain the integrated source flux to the accuracy expected for
    this well-sampled smooth test source.
    """

    from reproject import reproject_adaptive

    n_in = 101
    n_out = 201
    y, x = np.indices((n_in, n_in), dtype=float)
    c = (n_in - 1) / 2.0
    source = np.exp(-0.5 * (((x - c) / 12.0) ** 2 + ((y - c) / 12.0) ** 2))
    source *= 1000.0 / source.sum()

    w_in = _simple_tan_wcs(n_in, n_in, pixel_arcsec=0.10)
    w_out = _simple_tan_wcs(n_out, n_out, pixel_arcsec=0.05)

    sb_out, sb_footprint = reproject_adaptive(
        (source, w_in),
        w_out,
        shape_out=(n_out, n_out),
        conserve_flux=False,
        kernel="gaussian",
        boundary_mode="ignore",
        bad_value_mode="ignore",
    )
    flux_out, flux_footprint = reproject_adaptive(
        (source, w_in),
        w_out,
        shape_out=(n_out, n_out),
        conserve_flux=True,
        kernel="gaussian",
        boundary_mode="ignore",
        bad_value_mode="ignore",
    )

    sb_sum = float(np.nansum(sb_out[sb_footprint > 0]))
    flux_sum = float(np.nansum(flux_out[flux_footprint > 0]))
    input_sum = float(source.sum())

    # The factor-four behavior is the expected consequence of treating a
    # flux-per-input-pixel array as if it were surface brightness when the
    # linear output pixel scale is halved. This is a safety/semantics check,
    # not a recommended photometric pathway.
    assert 3.95 < sb_sum / input_sum < 4.05

    # For this smooth, well-contained, well-sampled source, adaptive flux mode
    # should preserve integrated flux at substantially better than percent level.
    # This tolerance is benchmark-specific and is NOT a future package-wide
    # science tolerance.
    assert abs(flux_sum / input_sum - 1.0) < 3.0e-3


def test_galsim_chromatic_gaussian_second_moment_matches_photon_weighted_truth():
    import galsim

    pixel_scale = 0.01  # arcsec/pixel
    source_sigma = 0.18  # arcsec
    psf_sigma_ref = 0.055  # arcsec at 2000 nm
    ref_wave_nm = 2000.0
    alpha_flambda = -1.3

    sed = galsim.SED(
        lambda w: (w / ref_wave_nm) ** alpha_flambda,
        wave_type="nm",
        flux_type="flambda",
    )
    source = galsim.Gaussian(sigma=source_sigma) * sed

    psf0 = galsim.Gaussian(sigma=psf_sigma_ref)
    chromatic_psf = galsim.ChromaticObject(psf0).dilate(lambda w: w / ref_wave_nm)
    observed = galsim.Convolve([source, chromatic_psf])

    band = galsim.Bandpass(
        lambda w: np.exp(-0.5 * ((w - 2600.0) / 650.0) ** 4),
        wave_type="nm",
        blue_limit=1200.0,
        red_limit=4000.0,
    )

    integrator = galsim.integ.ContinuousIntegrator(
        rule=galsim.integ.trapzRule,
        N=700,
        use_endpoints=True,
    )
    image = observed.drawImage(
        band,
        nx=301,
        ny=301,
        scale=pixel_scale,
        method="no_pixel",
        integrator=integrator,
    ).array.astype(float)
    image /= image.sum()

    y, x = np.indices(image.shape)
    cx = np.sum(image * x)
    cy = np.sum(image * y)
    measured_sigma_pix = np.sqrt(
        0.5
        * (
            np.sum(image * (x - cx) ** 2)
            + np.sum(image * (y - cy) ** 2)
        )
    )
    measured_sigma_arcsec = measured_sigma_pix * pixel_scale

    wave = np.linspace(1200.0, 4000.0, 20001)
    throughput = np.exp(-0.5 * ((wave - 2600.0) / 650.0) ** 4)
    flambda = (wave / ref_wave_nm) ** alpha_flambda
    photon_weight = flambda * throughput * wave
    mean_psf_sigma2 = np.trapezoid(
        photon_weight * (psf_sigma_ref * wave / ref_wave_nm) ** 2,
        wave,
    ) / np.trapezoid(photon_weight, wave)
    expected_sigma = np.sqrt(source_sigma**2 + mean_psf_sigma2)

    rel = abs(measured_sigma_arcsec - expected_sigma) / expected_sigma
    assert rel < 3.0e-3
