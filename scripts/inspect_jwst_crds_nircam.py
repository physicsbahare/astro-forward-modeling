#!/usr/bin/env python3
"""Select and inspect NIRCam PHOTOM/AREA references under a pinned CRDS context.

The script is a live Gate-B provenance check.  It intentionally downloads only
the two calibration reference types required for this test rather than syncing a
full JWST CRDS cache.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def make_model():
    from stdatamodels.jwst import datamodels

    model = datamodels.ImageModel((8, 8))
    model.meta.instrument.name = "NIRCAM"
    # JWST datamodel/CRDS naming for the module-A long-wave detector. STPSF
    # names the same physical detector NRCA5; that translation is handled only
    # at the instrument-adapter boundary.
    model.meta.instrument.detector = "NRCALONG"
    model.meta.instrument.filter = "F444W"
    model.meta.instrument.pupil = "CLEAR"
    model.meta.exposure.type = "NRC_IMAGE"
    model.meta.subarray.name = "FULL"
    model.meta.subarray.xstart = 1
    model.meta.subarray.ystart = 1
    model.meta.subarray.xsize = 2048
    model.meta.subarray.ysize = 2048
    model.meta.observation.date = "2026-08-01"
    model.meta.observation.time = "00:00:00"
    return model


def _text(value) -> str:
    """Normalize FITS string/bytes values for provenance JSON."""
    if isinstance(value, bytes):
        return value.decode("ascii", errors="replace").strip()
    return str(value).strip()


def main() -> None:
    required = ["CRDS_SERVER_URL", "CRDS_PATH", "CRDS_CONTEXT"]
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise RuntimeError(f"Missing required CRDS environment variables: {missing}")

    import crds
    from jwst.photom.photom import find_row
    from stdatamodels.jwst import datamodels

    context = os.environ["CRDS_CONTEXT"]
    if context != "jwst_1584.pmap":
        raise RuntimeError(f"Unexpected CRDS context: {context}")

    model = make_model()
    parameters = model.get_crds_parameters()
    refs = crds.getreferences(
        parameters,
        reftypes=("photom", "area"),
        context=context,
        observatory="jwst",
    )

    result: dict[str, object] = {
        "context": context,
        "crds_version": getattr(crds, "__version__", "unknown"),
        "selection_parameters": {
            "INSTRUME": parameters.get("INSTRUME"),
            "DETECTOR": parameters.get("DETECTOR"),
            "FILTER": parameters.get("FILTER"),
            "PUPIL": parameters.get("PUPIL"),
            "EXP_TYPE": parameters.get("EXP_TYPE"),
            "SUBARRAY": parameters.get("SUBARRAY"),
            "DATE-OBS": parameters.get("DATE-OBS"),
            "TIME-OBS": parameters.get("TIME-OBS"),
        },
        "references": {},
    }

    for reftype in ("photom", "area"):
        ref = refs.get(reftype)
        if not ref or str(ref).upper() == "N/A":
            raise RuntimeError(f"CRDS returned no {reftype.upper()} reference: {ref!r}")
        path = Path(ref)
        if not path.is_file():
            raise RuntimeError(f"Selected {reftype} reference was not cached: {path}")
        result["references"][reftype] = {
            "basename": path.name,
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        }

    photom_path = Path(refs["photom"])
    with datamodels.NrcImgPhotomModel(photom_path) as photom_ref:
        columns = list(photom_ref.phot_table.columns.names)
        # Match exactly as jwst.photom.DataSet.calc_nircam does in v3.0.0:
        # FILTER + PUPIL, plus SUBARRAY whenever that column exists.  The live
        # reference contains multiple F444W/CLEAR rows because it carries
        # subarray-specific calibrations; selecting the first row would be wrong.
        fields_to_match = {"filter": "F444W", "pupil": "CLEAR"}
        if "subarray" in columns:
            fields_to_match["subarray"] = "FULL"
        row_index = find_row(photom_ref.phot_table, fields_to_match)
        if row_index is None:
            raise RuntimeError(f"No PHOTOM row matched {fields_to_match}")
        row = photom_ref.phot_table[row_index]
        result["photom_table_columns"] = columns
        result["photom_match_fields"] = fields_to_match
        result["photom_selected_row"] = {
            "row_index": int(row_index),
            "filter": _text(row["filter"]),
            "pupil": _text(row["pupil"]),
            "subarray": _text(row["subarray"]) if "subarray" in columns else None,
            "photmjsr": float(row["photmjsr"]),
            "uncertainty": float(row["uncertainty"]),
        }
        if not np.isfinite(result["photom_selected_row"]["photmjsr"]):
            raise RuntimeError("Selected PHOTMJSR is not finite")
        if result["photom_selected_row"]["photmjsr"] <= 0:
            raise RuntimeError("Selected PHOTMJSR is not positive")

    area_path = Path(refs["area"])
    with datamodels.PixelAreaModel(area_path) as area:
        area_sr = float(area.meta.photometry.pixelarea_steradians)
        area_a2 = float(area.meta.photometry.pixelarea_arcsecsq)
        if not np.isfinite(area_sr) or area_sr <= 0:
            raise RuntimeError(f"Invalid PIXAR_SR-equivalent area: {area_sr}")
        if not np.isfinite(area_a2) or area_a2 <= 0:
            raise RuntimeError(f"Invalid PIXAR_A2-equivalent area: {area_a2}")
        result["area_metadata"] = {
            "pixelarea_steradians": area_sr,
            "pixelarea_arcsecsq": area_a2,
            "map_shape": list(area.data.shape),
        }

    model.close()

    out = Path("benchmark_output/jwst_crds_nircam")
    out.mkdir(parents=True, exist_ok=True)
    output_path = out / "crds_jwst_1584_nrcalong_f444w.json"
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
