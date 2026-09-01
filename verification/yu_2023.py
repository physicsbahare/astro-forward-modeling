"""Yu et al. (2023) Gate-C resolvedness/morphology literature anchors.

This module is part of the pre-production verification harness. It encodes only
published definitions and qualitative trends from Yu et al. (2023); it does not
implement their empirical correction functions and it does not define any
production morphology acceptance threshold.

Reference
---------
Yu, S.-Y., Cheng, C., Pan, Y., Sun, F. & Li, Y. A. (2023), A&A 676, A74,
"Redshifting galaxies from DESI to JWST CEERS: Correction of biases and
uncertainties in quantifying morphology", arXiv:2307.04753.

Published anchors used here
---------------------------
* 1816 nearby DESI galaxies;
* stellar-mass range log10(M*/Msun) = 9.75--11.25;
* artificial target-redshift range 0.75 <= z <= 3;
* morphology quantities Rp, R50, A, C, q and Sersic n;
* resolution level defined as Rp/FWHM;
* non-parametric Rp and R50 are reported as slightly overestimated by PSF
  smoothing;
* model-fit R50, q and n do not show significant bias in the paper's tests;
* asymmetry is mildly overestimated for intrinsically symmetric sources because
  of PSF asymmetry, but underestimated for intrinsically asymmetric sources as
  PSF smoothing dominates at poorer resolution;
* concentration is underestimated, especially for intrinsically concentrated
  galaxies and poorer resolution;
* after the authors' corrections, asymmetry is reported as robust only for
  angularly large galaxies with Rp/FWHM >= 5.

The Rp/FWHM >= 5 value is a literature anchor for that paper's asymmetry
analysis. It must not be promoted to a generic production cut without separate
verification.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

N_NEARBY_GALAXIES = 1816
LOG10_STELLAR_MASS_RANGE = (9.75, 11.25)
TARGET_REDSHIFT_RANGE = (0.75, 3.0)
RESOLUTION_DEFINITION = "R_p / FWHM"
ASYMMETRY_ROBUST_RESOLUTION_ANCHOR = 5.0

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
    petrosian_radius: float
    psf_fwhm: float
    rp_over_fwhm: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def resolution_level(petrosian_radius: float, psf_fwhm: float) -> float:
    """Return the Yu et al. resolvedness quantity R_p/FWHM.

    The two inputs must use the same angular or pixel unit. The ratio is
    dimensionless. No interpretation or pass/fail decision is attached here.
    """
    rp = float(petrosian_radius)
    fwhm = float(psf_fwhm)
    if rp <= 0:
        raise ValueError("petrosian_radius must be positive")
    if fwhm <= 0:
        raise ValueError("psf_fwhm must be positive")
    return rp / fwhm


def resolution_row(petrosian_radius: float, psf_fwhm: float) -> ResolutionLevel:
    """Return a machine-readable resolvedness row."""
    return ResolutionLevel(
        petrosian_radius=float(petrosian_radius),
        psf_fwhm=float(psf_fwhm),
        rp_over_fwhm=resolution_level(petrosian_radius, psf_fwhm),
    )


def literature_anchor_record() -> dict[str, object]:
    """Return immutable literature anchors in machine-readable form."""
    return {
        "reference": "Yu et al. 2023, A&A 676 A74, arXiv:2307.04753",
        "nearby_sample_size": N_NEARBY_GALAXIES,
        "log10_stellar_mass_range": list(LOG10_STELLAR_MASS_RANGE),
        "target_redshift_range": list(TARGET_REDSHIFT_RANGE),
        "resolution_definition": RESOLUTION_DEFINITION,
        "asymmetry_robust_resolution_anchor": ASYMMETRY_ROBUST_RESOLUTION_ANCHOR,
        "qualitative_trends": dict(PUBLISHED_QUALITATIVE_TRENDS),
        "semantics": (
            "Literature anchors only. The correction functions and any production "
            "resolvedness policy require separate reproduction and acceptance review."
        ),
    }
