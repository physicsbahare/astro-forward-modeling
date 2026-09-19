"""Yu et al. (2023) Gate-C resolvedness/morphology literature anchors.

This module belongs to the pre-production verification harness. It freezes
published definitions and literature values needed by the controlled Gate-C
experiments. It implements the published Eq. (28) asymmetry noise-correction
algebra, but it does not implement the paper's empirical resolvedness-correction
functions and it does not define any production morphology acceptance threshold.

Reference
---------
Yu, S.-Y., Cheng, C., Pan, Y., Sun, F. & Li, Y. A. (2023), A&A 676, A74,
"Redshifting galaxies from DESI to JWST CEERS: Correction of biases and
uncertainties in quantifying morphology", arXiv:2307.04753.

Important semantics
-------------------
The seven resolution levels and the ~R_p/FWHM >= 5 asymmetry statement are
literature anchors from that paper. They are not universal pass/fail cuts.
Synthetic-equivalent experiments in this repository are not literal DESI or
CEERS reproductions unless explicitly stated otherwise.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

N_NEARBY_GALAXIES = 1816
LOG10_STELLAR_MASS_RANGE = (9.75, 11.25)
TARGET_REDSHIFT_RANGE = (0.75, 3.0)

RESOLUTION_DEFINITION = "R_p,true / FWHM"
YU_RESOLUTION_LEVELS = (1.98, 3.0, 4.55, 6.89, 10.45, 15.83, 24.0)
ASYMMETRY_ROBUST_RESOLUTION_ANCHOR = 5.0

PETROSIAN_ETA = 0.20
TOTAL_LIGHT_APERTURE_RP = 1.5
CONCENTRATION_COEFFICIENT = 5.0
ASYMMETRY_APERTURE_RP = 1.5
ASYMMETRY_NOISE_F1 = 2.25
ASYMMETRY_NOISE_F2 = 2.10
ASYMMETRY_NOISE_FORMULA = (
    "A = [min sum|I0-I180| - F2 min sum|B0-B180|] / "
    "[sum|I0| - F1 sum|B0|]"
)
SERSIC_N_BOUNDS = (0.5, 6.0)

PUBLISHED_MEAN_DELTA_N = -0.11
PUBLISHED_MEAN_DELTA_Q = -0.005

PUBLISHED_QUALITATIVE_TRENDS = {
    "petrosian_radius_nonparametric": "slightly_overestimated_with_psf_smoothing",
    "half_light_radius_nonparametric": "slightly_overestimated_with_psf_smoothing",
    "half_light_radius_model_fit": "no_significant_bias_reported",
    "axis_ratio_model_fit": "no_significant_bias_reported",
    "sersic_index_model_fit": "no_significant_bias_reported",
    "asymmetry_intrinsically_symmetric": "minor_overestimate_from_psf_asymmetry",
    "asymmetry_intrinsically_asymmetric": "underestimated_more_at_lower_resolution",
    "concentration": "underestimated_more_at_lower_resolution_and_higher_intrinsic_concentration",
}


@dataclass(frozen=True)
class ResolutionLevel:
    petrosian_radius_true: float
    psf_fwhm: float
    rp_true_over_fwhm: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def resolution_level(petrosian_radius_true: float, psf_fwhm: float) -> float:
    """Return the Yu et al. resolvedness quantity R_p,true/FWHM.

    Both inputs must use the same angular or pixel unit. The ratio is
    dimensionless and carries no pass/fail interpretation here.
    """
    rp = float(petrosian_radius_true)
    fwhm = float(psf_fwhm)
    if rp <= 0:
        raise ValueError("petrosian_radius_true must be positive")
    if fwhm <= 0:
        raise ValueError("psf_fwhm must be positive")
    return rp / fwhm


def resolution_row(petrosian_radius_true: float, psf_fwhm: float) -> ResolutionLevel:
    """Return one machine-readable resolvedness row."""
    return ResolutionLevel(
        petrosian_radius_true=float(petrosian_radius_true),
        psf_fwhm=float(psf_fwhm),
        rp_true_over_fwhm=resolution_level(petrosian_radius_true, psf_fwhm),
    )


def asymmetry_noise_corrected_from_terms(
    galaxy_residual_min: float,
    background_residual_min: float,
    galaxy_abs_flux_sum: float,
    background_abs_flux_sum: float,
    F1: float,
    F2: float,
) -> float:
    """Evaluate the algebraic form of Yu et al. (2023) Eq. (28).

    F1 and F2 are the *fractions* defined by their Eqs. (29)-(30), not the
    lowercase threshold multipliers f1 and f2. The result is not clipped:
    a negative corrected asymmetry or a non-positive corrected denominator is
    a diagnostic outcome rather than a reason to modify the published formula.
    """
    terms = (
        float(galaxy_residual_min),
        float(background_residual_min),
        float(galaxy_abs_flux_sum),
        float(background_abs_flux_sum),
        float(F1),
        float(F2),
    )
    if not all(math.isfinite(v) for v in terms):
        raise ValueError("Eq. (28) terms must be finite")
    gres, bres, gflux, bflux, frac1, frac2 = terms
    if gres < 0 or bres < 0 or gflux < 0 or bflux < 0:
        raise ValueError("Eq. (28) absolute-sum terms must be non-negative")
    if not (0.0 <= frac1 <= 1.0 and 0.0 <= frac2 <= 1.0):
        raise ValueError("Eq. (29)-(30) fractions must lie in [0, 1]")
    denominator = gflux - frac1 * bflux
    if denominator <= 0:
        raise ValueError("Eq. (28) corrected denominator is non-positive")
    return (gres - frac2 * bres) / denominator


def literature_anchor_record() -> dict[str, object]:
    """Return the frozen Yu et al. literature anchors in machine-readable form."""
    return {
        "reference": "Yu et al. 2023, A&A 676 A74, arXiv:2307.04753",
        "nearby_sample_size": N_NEARBY_GALAXIES,
        "log10_stellar_mass_range": list(LOG10_STELLAR_MASS_RANGE),
        "target_redshift_range": list(TARGET_REDSHIFT_RANGE),
        "resolution_definition": RESOLUTION_DEFINITION,
        "resolution_levels": list(YU_RESOLUTION_LEVELS),
        "petrosian_definition": {
            "eta": PETROSIAN_ETA,
            "statement": "local surface brightness equals 20% of mean surface brightness inside Rp",
        },
        "curve_of_growth_total_aperture_rp": TOTAL_LIGHT_APERTURE_RP,
        "curve_of_growth_radii": ["R20", "R50", "R80"],
        "concentration_definition": "C = 5 log10(R80/R20)",
        "asymmetry_aperture_rp": ASYMMETRY_APERTURE_RP,
        "asymmetry_center": "chosen by minimizing asymmetry",
        "asymmetry_noise_correction": {
            "equation": ASYMMETRY_NOISE_FORMULA,
            "F1_definition": "N(I0 < f1 sigma_bkg) / Nall",
            "F2_definition": "N(|I0-I180| < f2 sigma_bkg) / Nall",
            "f1": ASYMMETRY_NOISE_F1,
            "f2": ASYMMETRY_NOISE_F2,
        },
        "single_sersic_fit": {
            "code_in_paper": "IMFIT",
            "psf_convolved": True,
            "n_bounds": list(SERSIC_N_BOUNDS),
        },
        "published_mean_delta_n": PUBLISHED_MEAN_DELTA_N,
        "published_mean_delta_q": PUBLISHED_MEAN_DELTA_Q,
        "asymmetry_robust_resolution_anchor": ASYMMETRY_ROBUST_RESOLUTION_ANCHOR,
        "qualitative_trends": dict(PUBLISHED_QUALITATIVE_TRENDS),
        "semantics": (
            "Literature anchors only. The empirical resolvedness-correction functions and any "
            "production resolvedness policy require separate reproduction and acceptance review. "
            "R_p/FWHM about 5 is not a universal morphology cut."
        ),
    }
