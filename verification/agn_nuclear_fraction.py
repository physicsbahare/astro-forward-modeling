"""Frozen anchors for the controlled AGN nuclear-fraction morphology gate.

This is verification-only metadata and algebra.  It does not implement a
production decomposition framework and it does not define a morphology
acceptance threshold.
"""
from __future__ import annotations

from dataclasses import dataclass

REFERENCE = {
    "authors": "Zhuang & Shen",
    "year": 2024,
    "journal": "ApJ 962, 139",
    "arxiv": "2304.13776",
    "title": "Characterization of JWST NIRCam PSFs and Implications for AGN+Host Image Decomposition",
}

# Published mock-image grid used by Zhuang & Shen.  These are literature
# anchors, not production requirements.
PUBLISHED_AGN_TO_HOST_RANGE = (0.1, 10.0)
PUBLISHED_AGN_TO_HOST_STEP_DEX = 0.2
PUBLISHED_RE_PIX_RANGE = (4.0, 64.0)
PUBLISHED_RE_STEP_DEX = 0.3
PUBLISHED_SERSIC_N = (0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0)
PUBLISHED_AXIS_RATIO = (0.3, 0.6, 0.9)
PUBLISHED_PA_DEG = 45.0
PUBLISHED_MAGNITUDE_RANGE = (16.5, 30.0)
PUBLISHED_MAGNITUDE_STEP = 0.5

# The paper repeatedly displays AGN-to-host ratios 0.1, 1 and 10.  Freeze those
# three values for the first controlled nuclear-fraction diagnostic.  The
# remaining scene choices are deliberately selected from the published grid
# before any benchmark result is observed.
AGN_TO_HOST_ANCHORS = (0.1, 1.0, 10.0)
CONTROLLED_HOST_RE_PIX = 16.0
CONTROLLED_HOST_SERSIC_N = (1.0, 4.0)
CONTROLLED_HOST_Q = 0.6
CONTROLLED_HOST_PA_DEG = 45.0


def nuclear_fraction_from_agn_to_host(ratio: float) -> float:
    """Return F_AGN / (F_AGN + F_host) for a positive AGN/host flux ratio."""
    r = float(ratio)
    if not r > 0.0:
        raise ValueError("AGN-to-host ratio must be positive")
    return r / (1.0 + r)


NUCLEAR_FRACTION_ANCHORS = tuple(
    nuclear_fraction_from_agn_to_host(r) for r in AGN_TO_HOST_ANCHORS
)


@dataclass(frozen=True)
class ControlledHostScene:
    n: float
    re_pix: float = CONTROLLED_HOST_RE_PIX
    q: float = CONTROLLED_HOST_Q
    pa_deg: float = CONTROLLED_HOST_PA_DEG


CONTROLLED_HOST_SCENES = tuple(ControlledHostScene(n=n) for n in CONTROLLED_HOST_SERSIC_N)


def anchor_record() -> dict[str, object]:
    """Machine-readable Stage-0 record for the next Gate-C experiment."""
    return {
        "reference": dict(REFERENCE),
        "published_mock_grid": {
            "agn_to_host_range": list(PUBLISHED_AGN_TO_HOST_RANGE),
            "agn_to_host_step_dex": PUBLISHED_AGN_TO_HOST_STEP_DEX,
            "agn_magnitude_range": list(PUBLISHED_MAGNITUDE_RANGE),
            "agn_magnitude_step_mag": PUBLISHED_MAGNITUDE_STEP,
            "host_re_pix_range": list(PUBLISHED_RE_PIX_RANGE),
            "host_re_step_dex": PUBLISHED_RE_STEP_DEX,
            "host_sersic_n": list(PUBLISHED_SERSIC_N),
            "host_axis_ratio": list(PUBLISHED_AXIS_RATIO),
            "host_pa_deg": PUBLISHED_PA_DEG,
        },
        "controlled_stage1": {
            "agn_to_host_anchors": list(AGN_TO_HOST_ANCHORS),
            "nuclear_fraction_anchors": list(NUCLEAR_FRACTION_ANCHORS),
            "host_re_pix": CONTROLLED_HOST_RE_PIX,
            "host_sersic_n": list(CONTROLLED_HOST_SERSIC_N),
            "host_q": CONTROLLED_HOST_Q,
            "host_pa_deg": CONTROLLED_HOST_PA_DEG,
            "noise": "none in Stage 1",
            "psf_semantics": "perfect known PSF in Stage 1; PSF mismatch is a later separate gate",
            "comparison": (
                "measure the same AGN+host image with a host-only single-Sersic model and "
                "with an explicit Sersic+PSF decomposition"
            ),
            "outputs": [
                "host flux",
                "nuclear flux",
                "host Re",
                "host Sersic n",
                "host q",
                "fit convergence",
                "parameter-bound hits",
            ],
        },
        "interpretation_rule": (
            "The 0.1, 1 and 10 AGN/host ratios are literature anchors, not acceptance cuts. "
            "Stage 1 isolates nuclear-fraction contamination with a perfect PSF. Noise and "
            "PSF mismatch must remain separate later diagnostics."
        ),
    }
