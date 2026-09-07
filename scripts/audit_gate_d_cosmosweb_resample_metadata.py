from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from astropy.io import fits


DEFAULT_CONTRIBUTORS = (45, 46, 70, 77)

PRIMARY_FIELDS = (
    "FILENAME",
    "ASNTABLE",
    "ASNPOOL",
    "CAL_VER",
    "CRDS_VER",
    "CRDS_CTX",
    "S_RESAMP",
    "NDRIZ",
    "RESWHT",
    "PIXFRAC",
    "PXSCLRT",
    "CRVAL1",
    "CRVAL2",
    "CRPIX1",
    "CRPIX2",
    "CDELT1",
    "CDELT2",
    "PC1_1",
    "PC1_2",
    "PC2_1",
    "PC2_2",
)

HDRTAB_FIELDS = (
    "FILENAME",
    "R_DRZPAR",
    "R_RESAMP",
    "CAL_VER",
    "CRDS_CTX",
    "S_RESAMP",
)


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass
    if isinstance(value, float):
        # FITS binary tables may expose absent floating/string-like metadata as
        # NaN.  Preserve absence as JSON null rather than emitting the
        # non-standard JSON token NaN or treating each NaN as a distinct value.
        if not math.isfinite(value):
            return None
        return value
    if isinstance(value, (str, int, bool)):
        return value
    return str(value)


def _nonempty(values: list[Any]) -> list[Any]:
    out: list[Any] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and value.strip().lower() in {"", "none", "n/a", "nan"}:
            continue
        if value not in out:
            out.append(value)
    return out


def run(mosaic: Path, out_json: Path, contributor_indices: tuple[int, ...]) -> dict[str, Any]:
    if not mosaic.exists():
        raise FileNotFoundError(mosaic)

    with fits.open(mosaic, lazy_load_hdus=True) as hdul:
        names = [hdu.name for hdu in hdul]
        if "HDRTAB" not in names:
            raise RuntimeError("HDRTAB extension is required")

        primary_header = hdul[0].header
        primary = {field: _jsonable(primary_header.get(field)) for field in PRIMARY_FIELDS}

        # Preserve potentially relevant raw cards without interpreting them as
        # final-resample parameters merely because their names contain a token.
        raw_matching_cards: list[dict[str, Any]] = []
        for key, value in primary_header.items():
            ukey = str(key).upper()
            if any(token in ukey for token in ("RES", "DRIZ", "KERN", "PIXFRAC", "PXSCL", "ASN")):
                raw_matching_cards.append({"key": str(key), "value": _jsonable(value)})

        hdrtab_hdu = hdul["HDRTAB"]
        hdrtab = hdrtab_hdu.data
        if hdrtab is None:
            raise RuntimeError("HDRTAB has no data")
        n_rows = len(hdrtab)
        colnames = set(hdrtab_hdu.columns.names or [])

        contributors: list[dict[str, Any]] = []
        for idx in contributor_indices:
            if idx < 0 or idx >= n_rows:
                raise RuntimeError(f"Contributor index {idx} outside HDRTAB range 0..{n_rows - 1}")
            row = hdrtab[idx]
            record: dict[str, Any] = {"hdrtab_row_zero_based": idx}
            for field in HDRTAB_FIELDS:
                record[field] = _jsonable(row[field]) if field in colnames else None
            contributors.append(record)

        drizpar_values = [row.get("R_DRZPAR") for row in contributors]
        resample_ref_values = [row.get("R_RESAMP") for row in contributors]
        unique_drizpars = _nonempty(drizpar_values)
        unique_resample_refs = _nonempty(resample_ref_values)
        drizpar_recorded_for_all = bool(contributors) and all(
            value is not None for value in drizpar_values
        )
        resample_ref_recorded_for_all = bool(contributors) and all(
            value is not None for value in resample_ref_values
        )

        asdf_inventory: dict[str, Any]
        if "ASDF" in names:
            asdf_hdu = hdul["ASDF"]
            # Astropy represents the JWST ASDF FITS extension as a BinTableHDU.
            # BinTableHDU itself does not expose `.shape`; its table data does.
            # Reading this metadata extension is permitted by the frozen D2d
            # protocol and does not touch SCI/ERR/WHT or variance arrays.
            asdf_data = asdf_hdu.data
            asdf_shape = getattr(asdf_data, "shape", None)
            asdf_inventory = {
                "present": True,
                "hdu_class": type(asdf_hdu).__name__,
                "shape": list(asdf_shape) if asdf_shape is not None else None,
                "columns": list(asdf_hdu.columns.names or []) if hasattr(asdf_hdu, "columns") else [],
                "data_tree_parsed": False,
                "note": (
                    "Structural FITS inventory only; D2d does not install a heavy JWST/ASDF stack "
                    "merely to make provenance pass."
                ),
            }
        else:
            asdf_inventory = {"present": False, "data_tree_parsed": False}

        explicit_kernel_cards = [
            card
            for card in raw_matching_cards
            if card["key"].upper() in {"KERNEL", "RESKERN", "DRIZKERN"}
        ]

        result = {
            "stage": "Gate D2d release-recorded resampling metadata audit",
            "claim": "read-only metadata audit; absent historical parameters remain unknown",
            "mosaic": {
                "basename": mosaic.name,
                "byte_size": mosaic.stat().st_size,
                "extensions": names,
                "primary_header": primary,
                "raw_resample_related_primary_cards": raw_matching_cards,
                "asdf_inventory": asdf_inventory,
            },
            "hdrtab": {
                "n_rows": n_rows,
                "contributor_indices_zero_based": list(contributor_indices),
                "contributors": contributors,
                "unique_R_DRZPAR": unique_drizpars,
                "unique_R_RESAMP": unique_resample_refs,
                "R_DRZPAR_recorded_for_all_contributors": drizpar_recorded_for_all,
                "R_RESAMP_recorded_for_all_contributors": resample_ref_recorded_for_all,
                "all_contributors_share_R_DRZPAR": drizpar_recorded_for_all
                and len(unique_drizpars) == 1,
                "all_contributors_share_R_RESAMP": resample_ref_recorded_for_all
                and len(unique_resample_refs) == 1,
            },
            "assessment": {
                "pixfrac_recorded": primary.get("PIXFRAC") is not None,
                "pixel_scale_ratio_recorded": primary.get("PXSCLRT") is not None,
                "weight_type_recorded": primary.get("RESWHT") is not None,
                "pointing_count_recorded": primary.get("NDRIZ") is not None,
                "explicit_final_resample_kernel_cards": explicit_kernel_cards,
                "final_resample_kernel_established": bool(explicit_kernel_cards),
                "source_shot_realization_permitted": False,
                "remaining_requirements": [
                    "literal survey-processed pre-resample input files with calibration/count provenance",
                    "variance/count provenance for the literal contributing pre-resample inputs",
                    "any historical resampling parameters still absent after this audit, especially the final kernel if not explicitly recorded",
                ],
            },
            "interpretation_guardrails": {
                "current_or_default_jwst_values_used_as_historical_evidence": False,
                "outlier_detection_kernel_transferred_to_final_resample": False,
                "R_DRZPAR_treated_as_proof_of_no_runtime_override": False,
            },
            "mutations": {
                "science_pixels_modified": False,
                "err_modified": False,
                "wht_modified": False,
                "variance_planes_modified": False,
                "source_shot_noise_generated": False,
                "background_noise_added": False,
                "psf_sharpening_applied": False,
                "tolman_factor_applied": False,
            },
        }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mosaic", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument(
        "--contributors",
        type=int,
        nargs="*",
        default=list(DEFAULT_CONTRIBUTORS),
        help="Zero-based HDRTAB contributor indices established by D2c.",
    )
    args = parser.parse_args()
    run(args.mosaic, args.out_json, tuple(args.contributors))


if __name__ == "__main__":
    main()
