from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS


DEFAULT_RA = 149.8671500
DEFAULT_DEC = 2.1294010

HDRTAB_FIELDS = (
    "FILENAME",
    "PROGRAM",
    "OBSERVTN",
    "VISIT",
    "VISITGRP",
    "EXPOSURE",
    "DETECTOR",
    "FILTER",
    "PUPIL",
    "DATE-BEG",
    "DATE-END",
    "OBS_ID",
    "VISIT_ID",
    "NEXPOSUR",
)

PRIMARY_FIELDS = (
    "TELESCOP",
    "INSTRUME",
    "FILTER",
    "PUPIL",
    "PROGRAM",
    "OBSERVTN",
    "VISIT",
    "FILENAME",
    "ASNPOOL",
    "ASNTABLE",
    "CAL_VER",
    "CRDS_VER",
    "CRDS_CTX",
    "S_RESAMP",
    "NEXPOSUR",
    "NDRIZ",
    "PIXFRAC",
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
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def decode_context_indices(values: np.ndarray) -> list[int]:
    """Decode JWST drizzle context planes into zero-indexed input indices."""
    decoded: list[int] = []
    for plane, raw in enumerate(values):
        value = int(np.uint32(raw))
        for bit in range(32):
            if value & (1 << bit):
                decoded.append(32 * plane + bit)
    return decoded


def run(mosaic: Path, out_json: Path, ra: float, dec: float) -> dict[str, Any]:
    if not mosaic.exists():
        raise FileNotFoundError(mosaic)

    with fits.open(mosaic, lazy_load_hdus=True) as hdul:
        names = [hdu.name for hdu in hdul]
        required = {"SCI", "CON", "HDRTAB"}
        missing = sorted(required.difference(names))
        if missing:
            raise RuntimeError(f"Missing required extensions: {missing}")

        sci_hdu = hdul["SCI"]
        con_hdu = hdul["CON"]
        hdrtab_hdu = hdul["HDRTAB"]

        wcs = WCS(sci_hdu.header)
        x, y = wcs.world_to_pixel_values(ra, dec)
        ix = int(np.rint(x))
        iy = int(np.rint(y))

        sci_shape = tuple(int(v) for v in sci_hdu.shape)
        con_shape = tuple(int(v) for v in con_hdu.shape)
        inside = 0 <= ix < sci_shape[1] and 0 <= iy < sci_shape[0]
        if not inside:
            raise RuntimeError("Frozen anchor lies outside SCI image")

        sci_value = _jsonable(sci_hdu.data[iy, ix])
        con_values_raw = con_hdu.data[:, iy, ix]
        decoded = decode_context_indices(con_values_raw)

        hdrtab = hdrtab_hdu.data
        if hdrtab is None:
            raise RuntimeError("HDRTAB has no data")
        n_hdrtab = len(hdrtab)

        invalid = [idx for idx in decoded if idx < 0 or idx >= n_hdrtab]
        if invalid:
            raise RuntimeError(
                f"Decoded context indices outside HDRTAB range 0..{n_hdrtab - 1}: {invalid}"
            )

        colnames = set(hdrtab_hdu.columns.names or [])
        contributors: list[dict[str, Any]] = []
        for idx in decoded:
            row = hdrtab[idx]
            record = {"input_index_zero_based": idx, "hdrtab_row_zero_based": idx}
            for field in HDRTAB_FIELDS:
                record[field] = _jsonable(row[field]) if field in colnames else None
            contributors.append(record)

        primary = {
            field: _jsonable(hdul[0].header.get(field)) for field in PRIMARY_FIELDS
        }

        con_values = []
        for plane, raw in enumerate(con_values_raw):
            unsigned = int(np.uint32(raw))
            con_values.append(
                {
                    "plane": plane,
                    "decimal_uint32": unsigned,
                    "hex_uint32": f"0x{unsigned:08x}",
                    "binary_uint32": f"{unsigned:032b}",
                }
            )

        result = {
            "stage": "Gate D2c local full-mosaic pixel-level provenance audit",
            "claim": "read-only release metadata/WCS/context audit; no stochastic injection",
            "mosaic": {
                "basename": mosaic.name,
                "byte_size": mosaic.stat().st_size,
                "primary_header": primary,
                "extensions": names,
                "extension_presence": {
                    name: name in names
                    for name in (
                        "SCI",
                        "ERR",
                        "CON",
                        "WHT",
                        "VAR_POISSON",
                        "VAR_RNOISE",
                        "VAR_FLAT",
                        "HDRTAB",
                        "ASDF",
                    )
                },
            },
            "anchor": {
                "ra_deg": ra,
                "dec_deg": dec,
                "x_float_zero_based": float(x),
                "y_float_zero_based": float(y),
                "x_nearest_zero_based": ix,
                "y_nearest_zero_based": iy,
                "inside_mosaic": inside,
                "sci_shape": list(sci_shape),
                "con_shape": list(con_shape),
                "sci_value": sci_value,
            },
            "context": {
                "interpretation": "plane p / bit k -> zero-indexed input 32*p+k",
                "values": con_values,
                "decoded_input_indices_zero_based": decoded,
                "n_contributors_at_anchor": len(decoded),
            },
            "hdrtab": {
                "n_rows": n_hdrtab,
                "contributors_at_anchor": contributors,
            },
            "assessment": {
                "pixel_level_release_membership_established": bool(decoded)
                and not invalid
                and all(c.get("FILENAME") for c in contributors),
                "source_shot_realization_permitted": False,
                "remaining_requirements": [
                    "literal survey-processed pre-resample input files available with calibration/count provenance",
                    "exact historical resampling kernel/weighting/operator configuration replayable",
                    "variance/count provenance available for the literal contributing pre-resample inputs",
                ],
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
    out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mosaic", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--ra", type=float, default=DEFAULT_RA)
    parser.add_argument("--dec", type=float, default=DEFAULT_DEC)
    args = parser.parse_args()
    run(args.mosaic, args.out_json, args.ra, args.dec)


if __name__ == "__main__":
    main()
