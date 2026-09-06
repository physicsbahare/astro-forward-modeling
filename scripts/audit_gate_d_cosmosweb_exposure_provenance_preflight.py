#!/usr/bin/env python3
"""Gate D2a: metadata-only COSMOS-Web exposure provenance feasibility audit.

The live path queries MAST for public JWST/NIRCam F444W calibrated-exposure
candidates at the frozen Gate-D anchor.  It never downloads science pixels and
never authorizes a source-shot realization merely because archive candidates
exist.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


FROZEN_RELEASE_EVIDENCE = {
    "survey": "COSMOS-Web DR1",
    "release_pipeline_version": "1.14.0",
    "release_crds_context": "pmap 1223",
    "release_tile": "A1",
    "release_pixel_scale_mas": 30,
    "published_full_i2d_planes": [
        "SCI",
        "ERR",
        "CON",
        "WHT",
        "VAR_POISSON",
        "VAR_RNOISE",
        "VAR_FLAT",
    ],
    "published_pre_resample_input_class": "survey-processed *_crf.fits",
    "published_custom_processing": [
        "survey-specific detector/image corrections",
        "JHAT astrometric calibration",
        "custom background removal",
        "visit/tile association construction",
    ],
    # These booleans are intentionally conservative.  The cited public release
    # documentation describes the reduction but is not itself an exact machine-
    # readable membership/configuration manifest for the frozen point.
    "exact_release_asn_membership_supplied_to_audit": False,
    "literal_release_pre_resample_inputs_supplied_to_audit": False,
    "actual_contributing_cal_variance_inventory_supplied_to_audit": False,
    "exact_historical_resample_configuration_supplied_to_audit": False,
}

OBS_FIELDS = (
    "obsid",
    "obs_id",
    "obs_collection",
    "instrument_name",
    "filters",
    "proposal_id",
    "calib_level",
    "dataRights",
    "t_min",
    "t_max",
    "s_ra",
    "s_dec",
    "distance",
)
PRODUCT_FIELDS = (
    "obsID",
    "obs_id",
    "productFilename",
    "productSubGroupDescription",
    "productType",
    "calib_level",
    "dataRights",
    "size",
    "dataURI",
    "description",
)


def _json_scalar(value: Any) -> Any:
    """Convert common Astropy/Numpy scalars and masked values safely to JSON."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    try:
        if bool(getattr(value, "mask", False)):
            return None
    except Exception:
        pass
    try:
        item = value.item()
    except Exception:
        item = value
    if item is None or isinstance(item, (str, int, float, bool)):
        return item
    text = str(item)
    return None if text in {"--", "masked", "MaskedConstant"} else text


def _records(table: Any, fields: Iterable[str]) -> list[dict[str, Any]]:
    names = set(getattr(table, "colnames", []))
    keep = [name for name in fields if name in names]
    return [
        {name: _json_scalar(row[name]) for name in keep}
        for row in table
    ]


def canonical_exposure_root(filename: str | None) -> str:
    """Return an exposure root while preserving detector/exposure identity."""
    if not filename:
        return ""
    name = Path(str(filename)).name.lower()
    if name.endswith(".fits"):
        name = name[:-5]
    for suffix in ("_cal", "_crf", "_jhat", "_rate", "_rateints", "_uncal"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def is_cal_candidate(record: Mapping[str, Any]) -> bool:
    subgroup = str(record.get("productSubGroupDescription") or "").upper()
    filename = str(record.get("productFilename") or "").lower()
    product_type = str(record.get("productType") or "").upper()
    rights = str(record.get("dataRights") or "").upper()
    if product_type and product_type != "SCIENCE":
        return False
    if rights and rights != "PUBLIC":
        return False
    return subgroup == "CAL" or filename.endswith("_cal.fits")


def select_cal_candidates(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for record in records:
        if not is_cal_candidate(record):
            continue
        out = dict(record)
        out["exposure_root"] = canonical_exposure_root(out.get("productFilename"))
        key = str(out.get("dataURI") or out.get("productFilename") or out["exposure_root"])
        selected[key] = out
    return sorted(
        selected.values(),
        key=lambda row: (str(row.get("productFilename") or ""), str(row.get("dataURI") or "")),
    )


def assess_literal_release_provenance(
    cal_candidates: Iterable[Mapping[str, Any]],
    release_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    candidates = list(cal_candidates)
    requirements = {
        "archive_cal_candidates_found": len(candidates) > 0,
        "exact_release_asn_membership_available": bool(
            release_evidence.get("exact_release_asn_membership_supplied_to_audit")
        ),
        "literal_release_pre_resample_inputs_available": bool(
            release_evidence.get("literal_release_pre_resample_inputs_supplied_to_audit")
        ),
        "actual_contributing_cal_variance_inventory_verified": bool(
            release_evidence.get("actual_contributing_cal_variance_inventory_supplied_to_audit")
        ),
        "exact_historical_resample_configuration_available": bool(
            release_evidence.get("exact_historical_resample_configuration_supplied_to_audit")
        ),
        "historical_release_pipeline_and_crds_identified": bool(
            release_evidence.get("release_pipeline_version")
            and release_evidence.get("release_crds_context")
        ),
    }
    permitted = all(requirements.values())
    missing = [name for name, ok in requirements.items() if not ok]
    return {
        "requirements": requirements,
        "missing_requirements": missing,
        "source_shot_realization_permitted": permitted,
        "archive_cal_candidates_alone_establish_literal_release_membership": False,
        "current_default_image3_is_literal_release_replay": False,
        "standard_pipeline_reprocessing_status": (
            "possible future approximation/control only; not literal DR1 reproduction"
        ),
    }


def query_mast(
    *,
    ra: float,
    dec: float,
    radius_arcsec: float,
    proposal_id: str,
    filt: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    """Query MAST through maintained astroquery interfaces; no files are downloaded."""
    import astroquery
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    from astroquery.mast import Observations

    coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
    observations = Observations.query_criteria(
        coordinates=coord,
        radius=radius_arcsec * u.arcsec,
        obs_collection="JWST",
        proposal_id=str(proposal_id),
        instrument_name="NIRCAM*",
        filters=str(filt),
        dataproduct_type="image",
        dataRights="PUBLIC",
    )
    obs_records = _records(observations, OBS_FIELDS)
    if len(observations) == 0:
        return obs_records, [], str(astroquery.__version__)
    products = Observations.get_unique_product_list(observations, batch_size=100)
    return obs_records, _records(products, PRODUCT_FIELDS), str(astroquery.__version__)


def run(
    out_dir: Path,
    *,
    ra: float,
    dec: float,
    radius_arcsec: float,
    proposal_id: str,
    filt: str,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    obs_records, product_records, astroquery_version = query_mast(
        ra=ra,
        dec=dec,
        radius_arcsec=radius_arcsec,
        proposal_id=proposal_id,
        filt=filt,
    )
    candidates = select_cal_candidates(product_records)
    assessment = assess_literal_release_provenance(candidates, FROZEN_RELEASE_EVIDENCE)

    (out_dir / "observations.json").write_text(
        json.dumps(obs_records, indent=2, sort_keys=True) + "\n"
    )
    (out_dir / "products.json").write_text(
        json.dumps(product_records, indent=2, sort_keys=True) + "\n"
    )
    (out_dir / "cal_candidates.json").write_text(
        json.dumps(candidates, indent=2, sort_keys=True) + "\n"
    )

    outcome = (
        "literal_release_source_shot_provenance_sufficient"
        if assessment["source_shot_realization_permitted"]
        else (
            "archive_cal_candidates_found_but_literal_release_provenance_incomplete"
            if candidates
            else "no_public_archive_cal_candidates_found_at_frozen_point"
        )
    )
    summary = {
        "stage": "Gate D2a exposure-level archive/provenance feasibility preflight",
        "claim": "metadata/provenance audit only; no science pixels or stochastic injection",
        "query": {
            "ra_deg": ra,
            "dec_deg": dec,
            "radius_arcsec": radius_arcsec,
            "obs_collection": "JWST",
            "proposal_id": str(proposal_id),
            "instrument_name": "NIRCAM*",
            "filter": str(filt),
            "dataproduct_type": "image",
            "data_rights": "PUBLIC",
            "astroquery_version": astroquery_version,
        },
        "counts": {
            "observation_rows": len(obs_records),
            "unique_product_rows": len(product_records),
            "cal_candidate_rows": len(candidates),
            "distinct_cal_exposure_roots": len(
                {row["exposure_root"] for row in candidates if row.get("exposure_root")}
            ),
        },
        "cal_candidate_exposure_roots": sorted(
            {row["exposure_root"] for row in candidates if row.get("exposure_root")}
        ),
        "release_evidence": FROZEN_RELEASE_EVIDENCE,
        "assessment": assessment,
        "mutations": {
            "science_pixels_downloaded": False,
            "source_shot_noise_generated": False,
            "background_noise_added": False,
            "sci_modified": False,
            "err_modified": False,
            "wht_modified": False,
            "tolman_factor_applied": False,
            "psf_sharpening_applied": False,
        },
        "scientific_outcome": outcome,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--ra", type=float, default=149.8671500)
    parser.add_argument("--dec", type=float, default=2.1294010)
    parser.add_argument("--radius-arcsec", type=float, default=1.0)
    parser.add_argument("--proposal-id", default="1727")
    parser.add_argument("--filter", default="F444W")
    args = parser.parse_args()
    if args.radius_arcsec <= 0:
        raise ValueError("radius_arcsec must be positive")
    run(
        args.out_dir,
        ra=args.ra,
        dec=args.dec,
        radius_arcsec=args.radius_arcsec,
        proposal_id=args.proposal_id,
        filt=args.filter,
    )


if __name__ == "__main__":
    main()
