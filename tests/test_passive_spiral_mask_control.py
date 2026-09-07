import numpy as np

from verification.passive_spiral_mask_control import (
    P4_D1C_BACKGROUND_MJYSR,
    P4_D1C_SOURCE_SIGMA,
    evaluate_p4_case,
    frozen_d1c_source_mask,
)


def test_frozen_d1c_mask_definition():
    err = np.ones((3, 3), dtype=float)
    sci = np.full((3, 3), P4_D1C_BACKGROUND_MJYSR, dtype=float)
    sci[1, 1] += 6.0
    mask = frozen_d1c_source_mask(sci, err)
    assert P4_D1C_SOURCE_SIGMA == 5.0
    assert mask.sum() == 1
    assert mask[1, 1]


def test_mask_construction_does_not_mutate_inputs():
    sci = np.arange(25, dtype=float).reshape(5, 5)
    err = np.ones_like(sci)
    sci0 = sci.copy(); err0 = err.copy()
    frozen_d1c_source_mask(sci, err)
    assert np.array_equal(sci, sci0)
    assert np.array_equal(err, err0)


def test_no_mask_matches_unmasked_phase_rank_and_paired_recovers():
    n = 401
    sci = np.full((n, n), P4_D1C_BACKGROUND_MJYSR, dtype=float)
    err = np.ones_like(sci)
    mask = frozen_d1c_source_mask(sci, err)
    row = evaluate_p4_case(
        sci, err, mask, x=n//2, y=n//2, ab_mag=26.0,
        pixar_sr=2.11539874851881e-14, crowding_class='test',
        placement_index=0, distance_to_source_pixel=999.0,
    )
    assert row.masked_fraction == 0.0
    assert row.masked_true_phase_rank == row.unmasked_true_phase_rank == 1
    assert row.masked_paired_true_phase_rank == 1
    assert row.relative_flux_error < 1e-12


def test_mask_is_pre_injection_only():
    n = 401
    sci = np.full((n, n), P4_D1C_BACKGROUND_MJYSR, dtype=float)
    err = np.ones_like(sci)
    pre = frozen_d1c_source_mask(sci, err)
    assert not np.any(pre)
    # A bright value added later would be detected if recomputed, which is exactly
    # why P4 freezes the mask before injection.
    later = sci.copy(); later[n//2, n//2] += 10.0
    assert frozen_d1c_source_mask(later, err)[n//2, n//2]
    assert not pre[n//2, n//2]
