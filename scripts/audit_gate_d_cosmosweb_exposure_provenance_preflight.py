from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable


OBS_FIELDS = (
    "obsid",
    "obs_id",
    "obs_collection",
    "proposal_id",
    "instrument_name",
    "filters",
    "dataproduct_type",
    "dataRights",
    "calib_level",
    "target_name",
    "s_ra",
    "s_dec",
    "t_min",
    "t_max",
)

PRODUCT_FIELDS = (
    "obsID",
    "obs_id",
    "productFilename",
    "dataURI",
    "productSubGroupDescription",
    "productType",
    "calib_level",
    "size",
    "dataRights",
    "description",
)

FROZEN_RELEASE_EVIDENCE: dict[str, Any] = {
    "cosmos_web_dr1_pipeline_version": "1.14.0",
    "cosmos_web_dr1_crds_pmap": "1223",
    "cosmos_web_dr1_final_pixel_scale_mas": 30.0,
    "cosmos_web_dr1_documented_full_i2d_extensions": [
        "SCI",
        "ERR",
        "CON",
        "WHT",
        "VAR_POISSON",
        "VAR_RNOISE",
        "VAR_FLAT",
    ],
    "survey_specific_processing_documented": True,
    "survey_specific_steps": [
        "JHAT astrometric calibration",
        "custom background treatment",
        "visit/tile association construction",
        "final resampling of selected *_crf.fits inputs",
    ],
    "exact_release_asn_membership_supplied_to_audit": False,
    "literal_release_pre_resample_inputs_supplied_to_audit": False,
    "actual_contributing_cal_variance_inventory_supplied_to_audit": False,
    "exact_historical_resample_configuration_supplied_to_audit": False,
}


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    try:
        if getattr(value, "mask", False) is True:
            return None
    except Exception:
        pass
    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _records(table: Any, fields: Iterable[str]) -> list[dict[str, Any]]:
    names = set(getattr(table, "colnames", []))
    rows: list[dict[str, Any]] = []
    for row in table:
        rows.append({field: _jsonable(row[field]) if field in names else None for field in fields})
    return rows


def canonical_exposure_root(filename: str | None) -> str | None:
    if not filename:
        return None
    name = Path(str(filename)).name
    for suffix in (
        "_cal.fits",
        "_crf.fits",
        "_jhat.fits",
        "_rate.fits",
        "_rateints.fits",
    ):
        if name.lower().endswith(suffix):
            return name[: -len(suffix)]
    match = re.match(r"^(jw\d{11}_\d{5}_\d{5}_[a-z0-9]+)", name.lower())
    return match.group(1) if match else None


def is_cal_candidate(row: dict[str, Any]) -> bool:
    filename = str(row.get("productFilename") or "")
    subgroup = str(row.get("productSubGroupDescription") or "")
    rights = str(row.get("dataRights") or "")
    product_type = str(row.get("productType") or "")
    return (
        rights.upper() == "PUBLIC"
        and product_type.upper() == "SCIENCE"
        and (subgroup.upper() == "CAL" or filename.lower().endswith("_cal.fits"))
    )


def select_cal_candidates(product_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in product_records:
        if not is_cal_candidate(row):
            continue
        key = str(row.get("dataURI") or row.get("productFilename") or "")
        if key in seen:
            continue
        seen.add(key)
        enriched = dict(row)
        enriched["exposure_root"] = canonical_exposure_root(row.get("productFilename"))
        selected.append(enriched)
    return selected


def assess_literal_release_provenance(
    candidates: list[dict[str, Any]],
    release_evidence: dict[str, Any],
) -> dict[str, Any]:
    requirements = {
        "archive_cal_candidates_found": bool(candidates),
        "exact_release_asn_membership_available": bool(
            release_evidence.get("exact_release_asn_membership_supplied_to_audit")
        ),
        "literal_release_pre_resample_inputs_available": bool(
            release_evidence.get("literal_release_pre_resample_inputs_supplied_to_audit")
        ),
        "actual_contributing_cal_variance_inventory_available": bool(
            release_evidence.get("actual_contributing_cal_variance_inventory_supplied_to_audit")
        ),
        "exact_historical_resample_configuration_available": bool(
            release_evidence.get("exact_historical_resample_configuration_supplied_to_audit")
        ),
        "historical_pipeline_and_crds_provenance_declared": bool(
            release_evidence.get("cosmos_web_dr1_pipeline_version")
            and release_evidence.get("cosmos_web_dr1_crds_pmap")
        ),
    }
    missing = [name for name, available in requirements.items() if not available]
    return {
        "requirements": requirements,
        "missing_requirements": missing,
        "archive_cal_candidates_alone_establish_literal_release_membership": False,
        "source_shot_realization_permitted": not missing,
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
    # astroquery 0.4.11 is intentionally frozen for this audit. Its
    # Observations.get_unique_product_list API does not expose batch_size;
    # later development versions do. Use the version-compatible public API
    # without changing the scientific query or product-selection criteria.
    products = Observations.get_unique_product_list(observations)
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
