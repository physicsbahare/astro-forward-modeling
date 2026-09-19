from __future__ import annotations

from scripts.audit_gate_d_cosmosweb_exposure_provenance_preflight import (
    FROZEN_RELEASE_EVIDENCE,
    assess_literal_release_provenance,
    canonical_exposure_root,
    is_cal_candidate,
    select_cal_candidates,
)


def test_canonical_exposure_root_matches_processing_suffixes():
    root = "jw01727001001_02101_00001_nrcalong"
    assert canonical_exposure_root(root + "_cal.fits") == root
    assert canonical_exposure_root(root + "_crf.fits") == root
    assert canonical_exposure_root(root + "_jhat.fits") == root


def test_cal_candidate_filter_is_explicit_and_preserves_failures():
    public_cal = {
        "productFilename": "jw_example_cal.fits",
        "productSubGroupDescription": "CAL",
        "productType": "SCIENCE",
        "dataRights": "PUBLIC",
        "dataURI": "mast:JWST/product/jw_example_cal.fits",
    }
    private_cal = {**public_cal, "dataRights": "EXCLUSIVE"}
    preview = {**public_cal, "productType": "PREVIEW", "productFilename": "x.jpg"}
    assert is_cal_candidate(public_cal)
    assert not is_cal_candidate(private_cal)
    assert not is_cal_candidate(preview)


def test_candidate_only_evidence_does_not_authorize_literal_source_shot():
    rows = [
        {
            "productFilename": "jw_a_cal.fits",
            "productSubGroupDescription": "CAL",
            "productType": "SCIENCE",
            "dataRights": "PUBLIC",
            "dataURI": "mast:JWST/product/jw_a_cal.fits",
        }
    ]
    candidates = select_cal_candidates(rows)
    assessment = assess_literal_release_provenance(candidates, FROZEN_RELEASE_EVIDENCE)
    assert len(candidates) == 1
    assert assessment["requirements"]["archive_cal_candidates_found"]
    assert not assessment["source_shot_realization_permitted"]
    assert not assessment["archive_cal_candidates_alone_establish_literal_release_membership"]
    assert "exact_release_asn_membership_available" in assessment["missing_requirements"]
    assert "exact_historical_resample_configuration_available" in assessment["missing_requirements"]


def test_synthetic_complete_provenance_logic_requires_every_frozen_requirement():
    evidence = dict(FROZEN_RELEASE_EVIDENCE)
    evidence.update(
        {
            "exact_release_asn_membership_supplied_to_audit": True,
            "literal_release_pre_resample_inputs_supplied_to_audit": True,
            "actual_contributing_cal_variance_inventory_supplied_to_audit": True,
            "exact_historical_resample_configuration_supplied_to_audit": True,
        }
    )
    candidate = {
        "productFilename": "jw_a_cal.fits",
        "productSubGroupDescription": "CAL",
        "productType": "SCIENCE",
        "dataRights": "PUBLIC",
    }
    assessment = assess_literal_release_provenance([candidate], evidence)
    assert assessment["source_shot_realization_permitted"]
    assert assessment["missing_requirements"] == []


def test_candidate_deduplication_uses_data_uri():
    row = {
        "productFilename": "jw_a_cal.fits",
        "productSubGroupDescription": "CAL",
        "productType": "SCIENCE",
        "dataRights": "PUBLIC",
        "dataURI": "mast:JWST/product/jw_a_cal.fits",
    }
    selected = select_cal_candidates([row, dict(row)])
    assert len(selected) == 1
