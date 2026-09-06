#!/usr/bin/env python3
"""Audit whether a frozen Gate-D artifact identifies exact source-shot noise.

This script is intentionally non-stochastic.  It inventories the literal FITS
representation and asks whether the information needed to draw source Poisson
noise *before* the survey resampling operator is available.  It never modifies
SCI/ERR/WHT and never constructs a covariance correction factor.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from astropy.io import fits


VARIANCE_PLANES = ("VAR_POISSON", "VAR_RNOISE", "VAR_FLAT")
HEADER_FIELDS = (
    "BUNIT",
    "PIXAR_SR",
    "PIXAR_A2",
    "PHOTMJSR",
    "EXPTIME",
    "EFFEXPTM",
    "DURATION",
    "NCOMBINE",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _jsonable_header_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def inventory_fits(path: Path) -> dict[str, Any]:
    """Inventory image planes and selected calibration metadata without writes."""
    hdus: list[dict[str, Any]] = []
    sci_header: dict[str, Any] = {}

    with fits.open(path, mode="readonly", memmap=False) as hdul:
        for index, hdu in enumerate(hdul):
            extname = str(hdu.header.get("EXTNAME", "PRIMARY" if index == 0 else "")).strip()
            data = getattr(hdu, "data", None)
            shape = list(data.shape) if data is not None else None
            hdus.append(
                {
                    "index": index,
                    "extname": extname,
                    "shape": shape,
                    "is_image": bool(data is not None and getattr(data, "ndim", 0) >= 2),
                }
            )
            if extname.upper() == "SCI":
                sci_header = {
                    key: _jsonable_header_value(hdu.header.get(key))
                    for key in HEADER_FIELDS
                    if key in hdu.header
                }

    extnames = [entry["extname"].upper() for entry in hdus if entry["extname"]]
    image_extnames = [
        entry["extname"].upper()
        for entry in hdus
        if entry["is_image"] and entry["extname"]
    ]
    variance_presence = {name: name in extnames for name in VARIANCE_PLANES}

    return {
        "path": path.name,
        "sha256": sha256(path),
        "hdus": hdus,
        "extnames": extnames,
        "image_extnames": image_extnames,
        "sci_header_fields": sci_header,
        "variance_planes": variance_presence,
    }


def assess_exact_identifiability(
    inventory: dict[str, Any],
    *,
    representation: str,
    per_exposure_resampling_replay_available: bool = False,
) -> dict[str, Any]:
    """Apply the frozen D1o representational sufficiency rules.

    A final mosaic is not promoted to detector/exposure level merely because it
    carries EXPTIME/PHOTMJSR-like scalar keywords.  Those values can be useful
    for approximations, but cannot recreate the independent Poisson draws from
    each contributing exposure or the exact drizzle mapping.
    """
    if representation not in {"drizzled_mosaic", "exposure_level"}:
        raise ValueError("representation must be drizzled_mosaic or exposure_level")

    exposure_level_representation = representation == "exposure_level"
    variance = inventory["variance_planes"]
    all_variance_planes_present = all(bool(variance[name]) for name in VARIANCE_PLANES)

    missing: list[str] = []
    if not exposure_level_representation:
        missing.append(
            "exposure/detector-level source expectation before mosaic resampling"
        )
    if not per_exposure_resampling_replay_available:
        missing.append(
            "per-exposure contribution/weight/WCS information sufficient to replay the mosaic resampling operator"
        )
    if not all_variance_planes_present:
        absent = [name for name in VARIANCE_PLANES if not variance[name]]
        missing.append(
            "separate calibrated variance provenance in this compact artifact: "
            + ", ".join(absent)
        )

    exact = len(missing) == 0
    return {
        "representation": representation,
        "exposure_level_representation": exposure_level_representation,
        "per_exposure_resampling_replay_available": bool(
            per_exposure_resampling_replay_available
        ),
        "all_variance_planes_present": all_variance_planes_present,
        "exact_l1_source_shot_and_covariance_identifiable": exact,
        "missing_requirements": missing,
        "independent_output_pixel_poisson_is_exact_truth": False,
        "independent_output_pixel_poisson_status": (
            "not executed; if later used, it must be labeled an L1 approximation"
        ),
        "recommended_physical_stage": (
            "existing representation is sufficient for a separately frozen exposure-level protocol"
            if exact
            else "L2/exposure-level injection before final resampling"
        ),
    }


def run(
    fits_path: Path,
    out_path: Path,
    *,
    representation: str = "drizzled_mosaic",
    expected_sha256: str | None = None,
) -> dict[str, Any]:
    inventory = inventory_fits(fits_path)
    if expected_sha256 is not None and inventory["sha256"] != expected_sha256:
        raise ValueError(
            f"FITS checksum mismatch: {inventory['sha256']} != {expected_sha256}"
        )

    # The frozen compact Gate-D artifact has no separately supplied exposure
    # association/resampling replay product.  Keep this boolean explicit rather
    # than inferring replayability from a scalar header keyword.
    assessment = assess_exact_identifiability(
        inventory,
        representation=representation,
        per_exposure_resampling_replay_available=False,
    )

    summary = {
        "stage": "Gate D1o source-shot-noise/covariance identifiability preflight",
        "claim": "representational audit only; no stochastic injection or morphology recovery",
        "input": inventory,
        "assessment": assessment,
        "mutations": {
            "input_fits_modified": False,
            "sci_modified": False,
            "err_modified": False,
            "wht_modified": False,
            "source_shot_noise_added": False,
            "background_noise_added": False,
            "covariance_correction_applied": False,
            "tolman_factor_applied": False,
            "psf_sharpening_applied": False,
        },
        "scientific_outcome": (
            "exact_source_shot_identifiable"
            if assessment["exact_l1_source_shot_and_covariance_identifiable"]
            else "exact_source_shot_not_identifiable_from_frozen_l1_bundle"
        ),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fits", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--representation",
        choices=("drizzled_mosaic", "exposure_level"),
        default="drizzled_mosaic",
    )
    parser.add_argument("--expected-sha256")
    args = parser.parse_args()
    run(
        args.fits,
        args.out,
        representation=args.representation,
        expected_sha256=args.expected_sha256,
    )


if __name__ == "__main__":
    main()
