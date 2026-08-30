"""Controlled image-level C2 experiment for Paulino-Afonso et al. (2017).

This is a *measurement-floor* experiment, not a claim to reproduce the paper's
full artificial-redshifting result.  Paulino-Afonso et al. redshift real SDSS
galaxies, transform the source PSF, and insert the degraded galaxies into real
COSMOS/ACS backgrounds before fitting them with GALFIT.  Here we deliberately
start from exact single-Sersic latent truth and use a Gaussian approximation to
the quoted ACS/F814W PSF.  The purpose is diagnostic: determine how much bias is
created by target sampling, PSF convolution and survey-depth noise *when the
fitted model family is exactly correct*.

If this controlled experiment does not reproduce the paper's ~16--19 per cent
median n under-recovery, that is scientifically informative rather than a test
failure: it implies that source complexity, source-PSF preparation, real-sky
structure, fitting freedom/selection, or some combination is required before
we should expect the published bias.

Published target anchors used here
----------------------------------
Paulino-Afonso et al. (2017), Sections 3--5 and Appendix B:
* target redshifts: 0.40, 0.84, 1.47, 2.23;
* COSMOS ACS/F814W pixel scale: 0.03 arcsec/pixel;
* typical F814W PSF FWHM: ~0.09 arcsec;
* F814W point-source depth: AB=27.2 at 5 sigma.

The depth is converted into a white-Gaussian pixel-noise level using the exact
matched-filter variance of the normalized Gaussian PSF.  This makes the depth
normalization reproducible without inventing an instrumental zeropoint.  Real
ACS backgrounds are correlated/non-Gaussian, so this remains a controlled floor
rather than the final C2 reproduction.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.optimize import least_squares
from scipy.special import gammaincinv, gamma

from .paulino_afonso_2017 import TARGET_REDSHIFTS
from .reference import FlatLCDMReference

PIXEL_SCALE_ARCSEC = 0.03
PSF_FWHM_ARCSEC = 0.09
POINT_DEPTH_AB_5SIGMA = 27.2
FWHM_TO_SIGMA = 1.0 / 2.354_820_045_030_9493
ARCSEC_TO_RAD = np.deg2rad(1.0 / 3600.0)
KPC_M = 3.085_677_581_491_367e19

# A compact, pre-declared diagnostic set.  These are not fitted to the paper's
# output.  They span disk-like through concentrated profiles, sizes below the
# paper's ~10-kpc reliable-size regime, and brightnesses around the quoted ACS
# depth.  Changing this grid requires review because it changes the experiment.
TRUTH_CASES = (
    {"case": "disk_bright", "re_kpc": 3.0, "n": 1.0, "q": 0.70, "mag_ab": 23.5},
    {"case": "disk_faint", "re_kpc": 3.0, "n": 1.0, "q": 0.70, "mag_ab": 26.0},
    {"case": "mixed_bright", "re_kpc": 5.0, "n": 2.0, "q": 0.65, "mag_ab": 24.5},
    {"case": "concentrated", "re_kpc": 5.0, "n": 4.0, "q": 0.75, "mag_ab": 24.5},
    {"case": "large_disk", "re_kpc": 9.0, "n": 1.0, "q": 0.60, "mag_ab": 24.5},
)


@dataclass(frozen=True)
class RecoveryRow:
    case: str
    z_target: float
    realization: int
    seed: int
    input_re_kpc: float
    input_n: float
    input_q: float
    input_mag_ab: float
    target_re_arcsec: float
    target_re_pixels: float
    psf_fwhm_pixels: float
    point_source_depth_ab_5sigma: float
    total_flux_depth_units: float
    pixel_noise_sigma_depth_units: float
    fit_success: bool
    fit_status: int
    fit_cost: float
    recovered_re_kpc: float
    recovered_n: float
    recovered_q: float
    recovered_mag_ab: float
    recovered_sky: float
    re_ratio: float
    n_ratio: float
    q_difference: float
    mag_difference: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _kpc_per_arcsec(z: float, cosmology: FlatLCDMReference | None = None) -> float:
    if cosmology is None:
        cosmology = FlatLCDMReference(H0_km_s_Mpc=70.0, Om0=0.3)
    return cosmology.angular_diameter_distance_m(float(z)) * ARCSEC_TO_RAD / KPC_M


def _bn(n: float) -> float:
    """Sersic b_n defined exactly by P(2n,b_n)=1/2."""
    if n <= 0:
        raise ValueError("Sersic n must be positive.")
    return float(gammaincinv(2.0 * n, 0.5))


def _sersic_total_normalization(re_pix: float, n: float, q: float) -> float:
    """Continuous integral for a profile with I_e=1."""
    b = _bn(n)
    return float(2.0 * np.pi * q * re_pix**2 * n * np.exp(b) * gamma(2.0 * n) / b ** (2.0 * n))


def _sersic_image(
    shape: tuple[int, int],
    total_flux: float,
    re_pix: float,
    n: float,
    q: float,
    x0: float,
    y0: float,
    pa_rad: float = 0.37,
) -> np.ndarray:
    if total_flux <= 0 or re_pix <= 0 or n <= 0 or not (0 < q <= 1):
        raise ValueError("Invalid Sersic parameters.")
    y, x = np.indices(shape, dtype=float)
    dx = x - x0
    dy = y - y0
    c = np.cos(pa_rad)
    s = np.sin(pa_rad)
    xp = c * dx + s * dy
    yp = -s * dx + c * dy
    r = np.sqrt(xp**2 + (yp / q) ** 2)
    b = _bn(n)
    ie = total_flux / _sersic_total_normalization(re_pix, n, q)
    return ie * np.exp(-b * ((r / re_pix) ** (1.0 / n) - 1.0))


def _psf_sigma_pix() -> float:
    return PSF_FWHM_ARCSEC * FWHM_TO_SIGMA / PIXEL_SCALE_ARCSEC


def _convolved_model(
    shape: tuple[int, int],
    total_flux: float,
    re_pix: float,
    n: float,
    q: float,
    x0: float,
    y0: float,
    sky: float,
) -> np.ndarray:
    intrinsic = _sersic_image(shape, total_flux, re_pix, n, q, x0, y0)
    return gaussian_filter(intrinsic, _psf_sigma_pix(), mode="constant", cval=0.0, truncate=7.0) + sky


def _normalized_psf_stamp(size: int = 41) -> np.ndarray:
    if size % 2 == 0:
        raise ValueError("PSF stamp size must be odd.")
    image = np.zeros((size, size), dtype=float)
    image[size // 2, size // 2] = 1.0
    psf = gaussian_filter(image, _psf_sigma_pix(), mode="constant", cval=0.0, truncate=7.0)
    psf /= np.sum(psf)
    return psf


def pixel_noise_from_point_depth() -> float:
    """White-pixel sigma when an AB=27.2 point source has matched-filter S/N=5.

    Flux units are defined so that an AB=27.2 source has total flux one.
    For normalized PSF P and independent equal-variance pixels,

        S/N = F * sqrt(sum(P^2)) / sigma_pix.
    """
    psf = _normalized_psf_stamp()
    return float(np.sqrt(np.sum(psf**2)) / 5.0)


def flux_in_depth_units(mag_ab: float) -> float:
    return float(10.0 ** (-0.4 * (float(mag_ab) - POINT_DEPTH_AB_5SIGMA)))


def mag_from_depth_units(flux: float) -> float:
    if flux <= 0:
        return float("nan")
    return float(POINT_DEPTH_AB_5SIGMA - 2.5 * np.log10(flux))


def _fit_single_sersic(
    image: np.ndarray,
    sigma_pix_noise: float,
    initial_re_pix: float,
    initial_n: float,
    initial_q: float,
    initial_flux: float,
) -> tuple[np.ndarray, object]:
    """Fit flux, Re, n, q, centroid and constant sky with the exact render model.

    Log parameters are used for positive quantities.  Bounds are numerical
    safeguards, not scientific acceptance cuts.  They are intentionally wider
    than the truth grid and the returned status is archived for every fit.
    """
    ny, nx = image.shape
    xmid = 0.5 * (nx - 1)
    ymid = 0.5 * (ny - 1)

    # [lnF, lnRe, lnN, logit_q, dx, dy, sky]
    def q_to_u(q: float) -> float:
        qmin, qmax = 0.15, 1.0
        t = (q - qmin) / (qmax - qmin)
        t = np.clip(t, 1e-8, 1 - 1e-8)
        return float(np.log(t / (1 - t)))

    def u_to_q(u: float) -> float:
        qmin, qmax = 0.15, 1.0
        t = 1.0 / (1.0 + np.exp(-u))
        return float(qmin + (qmax - qmin) * t)

    p0 = np.array(
        [
            np.log(max(initial_flux, 1e-12)),
            np.log(max(initial_re_pix, 0.2)),
            np.log(max(initial_n, 0.2)),
            q_to_u(initial_q),
            0.0,
            0.0,
            0.0,
        ],
        dtype=float,
    )

    lower = np.array([np.log(1e-8), np.log(0.15), np.log(0.2), -12.0, -2.0, -2.0, -5*sigma_pix_noise])
    upper = np.array([np.log(1e8), np.log(80.0), np.log(8.0), 12.0, 2.0, 2.0, 5*sigma_pix_noise])

    def decode(p: np.ndarray) -> tuple[float, float, float, float, float, float, float]:
        return (
            float(np.exp(p[0])),
            float(np.exp(p[1])),
            float(np.exp(p[2])),
            u_to_q(float(p[3])),
            xmid + float(p[4]),
            ymid + float(p[5]),
            float(p[6]),
        )

    def residual(p: np.ndarray) -> np.ndarray:
        model = _convolved_model(image.shape, *decode(p))
        return ((model - image) / sigma_pix_noise).ravel()

    result = least_squares(
        residual,
        p0,
        bounds=(lower, upper),
        method="trf",
        x_scale="jac",
        ftol=1e-9,
        xtol=1e-9,
        gtol=1e-9,
        max_nfev=450,
    )
    return np.asarray(decode(result.x), dtype=float), result


def run_recovery_ensemble(
    realizations: int = 12,
    base_seed: int = 2717,
    stamp_size: int = 81,
) -> list[RecoveryRow]:
    """Run the pre-declared truth grid at all four literature target redshifts."""
    if realizations < 1:
        raise ValueError("realizations must be positive")
    if stamp_size % 2 == 0:
        raise ValueError("stamp_size must be odd")

    sigma = pixel_noise_from_point_depth()
    center = 0.5 * (stamp_size - 1)
    rows: list[RecoveryRow] = []

    for iz, z in enumerate(TARGET_REDSHIFTS):
        kpc_arcsec = _kpc_per_arcsec(float(z))
        for icase, truth in enumerate(TRUTH_CASES):
            re_arcsec = float(truth["re_kpc"]) / kpc_arcsec
            re_pix = re_arcsec / PIXEL_SCALE_ARCSEC
            flux = flux_in_depth_units(float(truth["mag_ab"]))
            noiseless = _convolved_model(
                (stamp_size, stamp_size),
                flux,
                re_pix,
                float(truth["n"]),
                float(truth["q"]),
                center,
                center,
                0.0,
            )

            for realization in range(realizations):
                seed = int(base_seed + iz * 100_000 + icase * 1_000 + realization)
                rng = np.random.default_rng(seed)
                image = noiseless + rng.normal(0.0, sigma, size=noiseless.shape)

                # Initial guesses are deterministic perturbations of truth, not
                # truth itself, to exercise optimizer stability without adding
                # a second stochastic variable.
                initial_flux = flux * 0.93
                initial_re = re_pix * 1.08
                initial_n = max(0.25, float(truth["n"]) * 0.90)
                initial_q = min(0.95, max(0.2, float(truth["q"]) + 0.04))
                fit, result = _fit_single_sersic(
                    image, sigma, initial_re, initial_n, initial_q, initial_flux
                )
                recovered_flux, recovered_re_pix, recovered_n, recovered_q, _, _, sky = fit
                recovered_re_kpc = recovered_re_pix * PIXEL_SCALE_ARCSEC * kpc_arcsec

                rows.append(
                    RecoveryRow(
                        case=str(truth["case"]),
                        z_target=float(z),
                        realization=realization,
                        seed=seed,
                        input_re_kpc=float(truth["re_kpc"]),
                        input_n=float(truth["n"]),
                        input_q=float(truth["q"]),
                        input_mag_ab=float(truth["mag_ab"]),
                        target_re_arcsec=re_arcsec,
                        target_re_pixels=re_pix,
                        psf_fwhm_pixels=PSF_FWHM_ARCSEC / PIXEL_SCALE_ARCSEC,
                        point_source_depth_ab_5sigma=POINT_DEPTH_AB_5SIGMA,
                        total_flux_depth_units=flux,
                        pixel_noise_sigma_depth_units=sigma,
                        fit_success=bool(result.success),
                        fit_status=int(result.status),
                        fit_cost=float(result.cost),
                        recovered_re_kpc=float(recovered_re_kpc),
                        recovered_n=float(recovered_n),
                        recovered_q=float(recovered_q),
                        recovered_mag_ab=mag_from_depth_units(float(recovered_flux)),
                        recovered_sky=float(sky),
                        re_ratio=float(recovered_re_kpc / float(truth["re_kpc"])),
                        n_ratio=float(recovered_n / float(truth["n"])),
                        q_difference=float(recovered_q - float(truth["q"])),
                        mag_difference=float(mag_from_depth_units(float(recovered_flux)) - float(truth["mag_ab"])),
                    )
                )
    return rows


def summarize_rows(rows: list[RecoveryRow]) -> list[dict[str, object]]:
    """Summarize median and 16/84-percentile recovery by truth case/redshift."""
    out: list[dict[str, object]] = []
    for z in TARGET_REDSHIFTS:
        for truth in TRUTH_CASES:
            subset = [r for r in rows if r.z_target == float(z) and r.case == truth["case"]]
            if not subset:
                continue
            result: dict[str, object] = {
                "case": str(truth["case"]),
                "z_target": float(z),
                "n_realizations": len(subset),
                "fit_success_fraction": float(np.mean([r.fit_success for r in subset])),
                "input_re_kpc": float(truth["re_kpc"]),
                "input_n": float(truth["n"]),
                "input_q": float(truth["q"]),
                "input_mag_ab": float(truth["mag_ab"]),
                "target_re_pixels": float(subset[0].target_re_pixels),
            }
            for name in ("re_ratio", "n_ratio", "q_difference", "mag_difference"):
                values = np.asarray([getattr(r, name) for r in subset], dtype=float)
                result[f"{name}_p16"] = float(np.percentile(values, 16))
                result[f"{name}_median"] = float(np.median(values))
                result[f"{name}_p84"] = float(np.percentile(values, 84))
            out.append(result)
    return out
