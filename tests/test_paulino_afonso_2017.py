"""Scientific checks for the first Paulino-Afonso et al. (2017) C2 sub-gate.

These tests deliberately do not invent a pass band for synthetic GALFIT-like
structural recovery.  That image-level reproduction is the next C2 step.  Here
we test exact radiometric identity and the integrity/direction of the published
Table-2 anchors.
"""

from __future__ import annotations

import numpy as np

from verification.paulino_afonso_2017 import (
    PUBLISHED_TABLE2,
    PUBLISHED_TABLE2_AVERAGE,
    TARGET_REDSHIFTS,
    luminosity_evolution_ratio,
    published_trend_summary,
    radiometric_equivalence_row,
)


def test_distance_based_dimming_matches_tolman_at_same_observable() -> None:
    # Local samples in the paper have small but nonzero median redshifts.  Use a
    # representative z=0.03 source and each of the four published target slices.
    # The tolerance is numerical only: Etherington distance duality makes these
    # two formulae mathematically identical under the stated assumptions.
    for z_target in TARGET_REDSHIFTS:
        row = radiometric_equivalence_row(0.03, float(z_target))
        assert row.relative_difference < 5e-12
        assert np.isclose(
            row.distance_based_with_evolution,
            row.tolman_with_evolution,
            rtol=5e-12,
            atol=0.0,
        )


def test_luminosity_evolution_is_separate_from_observational_dimming() -> None:
    # Equation log10 L*(z)=0.45 z + 41.87 implies this exact ratio; keeping it
    # separate prevents intrinsic evolution from being hidden inside a Tolman
    # or distance factor.
    z_source = 0.03
    z_target = 2.23
    expected = 10.0 ** (0.45 * (z_target - z_source))
    assert np.isclose(
        luminosity_evolution_ratio(z_source, z_target),
        expected,
        rtol=2e-15,
        atol=0.0,
    )


def test_published_table2_average_values_are_encoded_exactly() -> None:
    expected = np.array(
        [[1.007, 0.815], [1.033, 0.820], [0.997, 0.831], [1.002, 0.837]],
        dtype=float,
    )
    assert np.array_equal(PUBLISHED_TABLE2_AVERAGE, expected)


def test_published_structural_bias_direction_matches_figures_4_5_and_table2() -> None:
    summary = published_trend_summary()

    # Table 2: every sample/redshift combination has median n recovery below
    # unity.  This is the paper's robust direction-of-bias result.
    assert summary["all_sample_n_ratios_below_unity"] is True

    # The paper's average size ratios remain close to unity and show no
    # monotonic redshift trend.  This checks the literal published numbers,
    # not a framework acceptance tolerance.
    re_avg = PUBLISHED_TABLE2_AVERAGE[:, 0]
    assert np.max(np.abs(re_avg - 1.0)) == np.float64(0.03300000000000003)
    assert not (np.all(np.diff(re_avg) >= 0) or np.all(np.diff(re_avg) <= 0))

    # The average n ratios correspond to a 16.3--18.5% under-recovery.
    n_bias = 1.0 - PUBLISHED_TABLE2_AVERAGE[:, 1]
    assert np.isclose(np.min(n_bias), 0.163, rtol=0.0, atol=1e-15)
    assert np.isclose(np.max(n_bias), 0.185, rtol=0.0, atol=1e-15)


def test_published_table2_has_expected_samples_and_shape() -> None:
    assert set(PUBLISHED_TABLE2) == {"CALIFA", "SAMI", "MaNGA", "NYU-VAGC"}
    for values in PUBLISHED_TABLE2.values():
        assert values.shape == (4, 2)
        assert np.all(np.isfinite(values))
        assert np.all(values > 0)
