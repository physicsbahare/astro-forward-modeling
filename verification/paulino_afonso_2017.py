"""Paulino-Afonso et al. (2017) Gate-C verification anchors.

This module belongs to the pre-production verification harness.  It does not
implement the future production framework and it does not claim to reproduce
GALFIT on the original survey images.

The purpose of this first C2 sub-gate is twofold:

1. encode the published Table 2 structural-recovery ratios as immutable
   machine-readable reference values; and
2. verify the radiometric equivalence between the distance-based artificial-
   redshifting convention described in Section 3 of Paulino-Afonso et al.
   (2017) and the corresponding Tolman surface-brightness ratio when the same
   physical source and matched rest-frame observable are assumed.

Reference
---------
Paulino-Afonso, Sobral, Buitrago & Afonso (2017), MNRAS 465, 2717,
arXiv:1611.05039, especially Sections 3 and 5.1, Figures 4-5 and Table 2.

The paper adopts H0=70 km/s/Mpc, Omega_m=0.3 and Omega_Lambda=0.7.  Its target
redshift slices are z=0.40, 0.84, 1.47 and 2.23.  The luminosity-evolution law
used for the H-alpha-selected population is log10 L*(z) = 0.45 z + 41.87.

No tolerance in this module is an empirical production acceptance threshold.
The exact radiometric identity is a mathematical consistency check.  The table
values are published literature anchors, not generic correction factors.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .reference import FlatLCDMReference

TARGET_REDSHIFTS = np.array([0.40, 0.84, 1.47, 2.23], dtype=float)

# Table 2 of Paulino-Afonso et al. (2017).  Each pair is
# (median recovered/input effective radius, median recovered/input Sersic n).
PUBLISHED_TABLE2 = {
    "CALIFA": np.array(
        [[0.885, 0.805], [0.918, 0.828], [0.863, 0.829], [0.918, 0.839]],
        dtype=float,
    ),
    "SAMI": np.array(
        [[1.006, 0.869], [1.166, 0.763], [1.096, 0.812], [1.052, 0.789]],
        dtype=float,
    ),
    "MaNGA": np.array(
        [[1.031, 0.856], [1.037, 0.848], [1.039, 0.851], [1.037, 0.832]],
        dtype=float,
    ),
    "NYU-VAGC": np.array(
        [[1.107, 0.729], [1.011, 0.841], [0.989, 0.832], [1.001, 0.887]],
        dtype=float,
    ),
}

PUBLISHED_TABLE2_AVERAGE = np.array(
    [[1.007, 0.815], [1.033, 0.820], [0.997, 0.831], [1.002, 0.837]],
    dtype=float,
)


@dataclass(frozen=True)
class RadiometricEquivalenceRow:
    z_source: float
    z_target: float
    luminosity_distance_flux_ratio: float
    angular_area_ratio: float
    distance_based_surface_brightness_ratio: float
    tolman_surface_brightness_ratio: float
    relative_difference: float
    luminosity_evolution_ratio: float
    distance_based_with_evolution: float
    tolman_with_evolution: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def h_alpha_lstar_log10_erg_s(z: float) -> float:
    """Equation (2) of Paulino-Afonso et al. (2017)."""
    return 0.45 * float(z) + 41.87


def luminosity_evolution_ratio(z_source: float, z_target: float) -> float:
    """Return L*(z_target)/L*(z_source) from the paper's luminosity law.

    Algebraically the intercept 41.87 cancels exactly.  We therefore evaluate
    the ratio as ``10**(0.45 * (z_target-z_source))`` rather than subtracting
    two numbers near 42.  The previous implementation performed that needless
    subtraction and lost about four parts in 10^15 in binary64 arithmetic,
    causing the exact-form regression test to fail.  This change fixes the
    numerical evaluation; the test tolerance is deliberately unchanged.
    """
    return float(10.0 ** (0.45 * (float(z_target) - float(z_source))))


def distance_based_surface_brightness_ratio(
    z_source: float,
    z_target: float,
    cosmology: FlatLCDMReference | None = None,
) -> tuple[float, float, float]:
    """Surface-brightness ratio implied by distance and angular-size scaling.

    For a source with unchanged physical size and luminosity, observed total
    flux scales as D_L^-2.  The apparent angular area scales as D_A^-2.
    Therefore, when moving an image from z_source to z_target,

        SB_t / SB_s = (D_L,s / D_L,t)^2 (D_A,t / D_A,s)^2.

    This is the distance-based version of the artificial-redshifting operation
    described in Section 3 of Paulino-Afonso et al. (2017).
    """
    if cosmology is None:
        cosmology = FlatLCDMReference(H0_km_s_Mpc=70.0, Om0=0.3)
    if z_source <= 0 or z_target <= 0:
        raise ValueError("Both redshifts must be positive for this ratio.")

    dl_s = cosmology.luminosity_distance_m(z_source)
    dl_t = cosmology.luminosity_distance_m(z_target)
    da_s = cosmology.angular_diameter_distance_m(z_source)
    da_t = cosmology.angular_diameter_distance_m(z_target)

    flux_ratio = (dl_s / dl_t) ** 2
    angular_area_ratio = (da_s / da_t) ** 2  # Omega_t / Omega_s
    sb_ratio = flux_ratio / angular_area_ratio
    return float(flux_ratio), float(angular_area_ratio), float(sb_ratio)


def tolman_surface_brightness_ratio(z_source: float, z_target: float) -> float:
    """Matched-rest-frame bolometric/band-integrated Tolman SB ratio."""
    if z_source <= -1 or z_target <= -1:
        raise ValueError("Redshift must be greater than -1.")
    return float(((1.0 + z_source) / (1.0 + z_target)) ** 4)


def radiometric_equivalence_row(
    z_source: float,
    z_target: float,
    cosmology: FlatLCDMReference | None = None,
) -> RadiometricEquivalenceRow:
    flux_ratio, area_ratio, distance_sb = distance_based_surface_brightness_ratio(
        z_source, z_target, cosmology=cosmology
    )
    tolman_sb = tolman_surface_brightness_ratio(z_source, z_target)
    rel = abs(distance_sb - tolman_sb) / abs(tolman_sb)
    evolution = luminosity_evolution_ratio(z_source, z_target)
    return RadiometricEquivalenceRow(
        z_source=float(z_source),
        z_target=float(z_target),
        luminosity_distance_flux_ratio=flux_ratio,
        angular_area_ratio=area_ratio,
        distance_based_surface_brightness_ratio=distance_sb,
        tolman_surface_brightness_ratio=tolman_sb,
        relative_difference=float(rel),
        luminosity_evolution_ratio=float(evolution),
        distance_based_with_evolution=float(distance_sb * evolution),
        tolman_with_evolution=float(tolman_sb * evolution),
    )


def table2_rows() -> list[dict[str, float | str]]:
    """Return the published Table-2 values in tidy row form."""
    rows: list[dict[str, float | str]] = []
    for sample, values in PUBLISHED_TABLE2.items():
        for z, (re_ratio, n_ratio) in zip(TARGET_REDSHIFTS, values, strict=True):
            rows.append(
                {
                    "sample": sample,
                    "z_target": float(z),
                    "recovered_over_input_re": float(re_ratio),
                    "recovered_over_input_n": float(n_ratio),
                }
            )
    for z, (re_ratio, n_ratio) in zip(
        TARGET_REDSHIFTS, PUBLISHED_TABLE2_AVERAGE, strict=True
    ):
        rows.append(
            {
                "sample": "Average",
                "z_target": float(z),
                "recovered_over_input_re": float(re_ratio),
                "recovered_over_input_n": float(n_ratio),
            }
        )
    return rows


def published_trend_summary() -> dict[str, object]:
    """Summarize the quantitative Table-2 trend without inventing thresholds."""
    re_avg = PUBLISHED_TABLE2_AVERAGE[:, 0]
    n_avg = PUBLISHED_TABLE2_AVERAGE[:, 1]
    all_n = np.concatenate([values[:, 1] for values in PUBLISHED_TABLE2.values()])
    all_re = np.concatenate([values[:, 0] for values in PUBLISHED_TABLE2.values()])
    return {
        "target_redshifts": TARGET_REDSHIFTS.tolist(),
        "average_re_ratio": re_avg.tolist(),
        "average_n_ratio": n_avg.tolist(),
        "average_re_fractional_bias": (re_avg - 1.0).tolist(),
        "average_n_fractional_bias": (n_avg - 1.0).tolist(),
        "all_sample_re_ratio_min": float(np.min(all_re)),
        "all_sample_re_ratio_max": float(np.max(all_re)),
        "all_sample_n_ratio_min": float(np.min(all_n)),
        "all_sample_n_ratio_max": float(np.max(all_n)),
        "all_sample_n_ratios_below_unity": bool(np.all(all_n < 1.0)),
    }
