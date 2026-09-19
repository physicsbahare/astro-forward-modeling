import math

import pytest

from verification.agn_nuclear_fraction import (
    AGN_TO_HOST_ANCHORS,
    CONTROLLED_HOST_PA_DEG,
    CONTROLLED_HOST_Q,
    CONTROLLED_HOST_RE_PIX,
    CONTROLLED_HOST_SERSIC_N,
    NUCLEAR_FRACTION_ANCHORS,
    PUBLISHED_AGN_TO_HOST_RANGE,
    PUBLISHED_AXIS_RATIO,
    PUBLISHED_PA_DEG,
    PUBLISHED_RE_PIX_RANGE,
    PUBLISHED_SERSIC_N,
    anchor_record,
    nuclear_fraction_from_agn_to_host,
)


def test_literature_agn_to_host_anchors_are_frozen():
    assert AGN_TO_HOST_ANCHORS == (0.1, 1.0, 10.0)
    assert PUBLISHED_AGN_TO_HOST_RANGE == (0.1, 10.0)


def test_nuclear_fraction_conversion_is_exact():
    expected = (1.0 / 11.0, 0.5, 10.0 / 11.0)
    assert len(NUCLEAR_FRACTION_ANCHORS) == len(expected)
    for got, want in zip(NUCLEAR_FRACTION_ANCHORS, expected):
        assert math.isclose(got, want, rel_tol=0.0, abs_tol=1e-15)
    with pytest.raises(ValueError):
        nuclear_fraction_from_agn_to_host(0.0)


def test_controlled_scene_is_predeclared_subset_of_published_grid():
    assert PUBLISHED_RE_PIX_RANGE[0] <= CONTROLLED_HOST_RE_PIX <= PUBLISHED_RE_PIX_RANGE[1]
    assert all(n in PUBLISHED_SERSIC_N for n in CONTROLLED_HOST_SERSIC_N)
    assert CONTROLLED_HOST_Q in PUBLISHED_AXIS_RATIO
    assert CONTROLLED_HOST_PA_DEG == PUBLISHED_PA_DEG


def test_anchor_record_keeps_effects_separate():
    record = anchor_record()
    stage1 = record["controlled_stage1"]
    assert stage1["noise"] == "none in Stage 1"
    assert "perfect known PSF" in stage1["psf_semantics"]
    assert "PSF mismatch" in stage1["psf_semantics"]
    assert "not acceptance cuts" in record["interpretation_rule"]
