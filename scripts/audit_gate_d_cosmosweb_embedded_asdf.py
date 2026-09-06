from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
from typing import Any

from astropy.io import fits


SEARCH_TERMS = (
    "kernel",
    "resample",
    "driz",
    "pixfrac",
    "weight",
    "pixel_scale",
    "pixel scale",
    "output_shape",
    "array_shape",
    "pixel_shape",
    "asn",
    "association",
)


def _short(value: Any, limit: int = 240) -> str:
    text = str(value)
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def _yaml_prefix(payload: bytes) -> bytes:
    """Return only the textual ASDF header/YAML document, excluding blocks."""
    marker = b"\n...\n"
    pos = payload.find(marker)
    if pos >= 0:
        return payload[: pos + len(marker)]
    marker = b"\r\n...\r\n"
    pos = payload.find(marker)
    if pos >= 0:
        return payload[: pos + len(marker)]
    return payload


def _matches_term(text: str) -> bool:
    lower = text.lower()
    return any(term in lower for term in SEARCH_TERMS)


def _collect_matches(tree: Any, max_matches: int = 500) -> list[dict[str, str]]:
    matches: list[dict[str, str]] = []

    def walk(node: Any, path: tuple[str, ...]) -> None:
        if len(matches) >= max_matches:
            return
        if isinstance(node, dict):
            for key, value in node.items():
                key_text = str(key)
                new_path = path + (key_text,)
                if _matches_term(key_text):
                    matches.append(
                        {
                            "path": ".".join(new_path),
                            "match_kind": "key",
                            "matched_text": _short(key_text),
                            "value_preview": _short(value),
                        }
                    )
                    if len(matches) >= max_matches:
                        return
                walk(value, new_path)
        elif isinstance(node, (list, tuple)):
            for idx, value in enumerate(node):
                walk(value, path + (f"[{idx}]",))
                if len(matches) >= max_matches:
                    return
        else:
            value_text = str(node)
            if _matches_term(value_text):
                matches.append(
                    {
                        "path": ".".join(path),
                        "match_kind": "value",
                        "matched_text": _short(value_text),
                        "value_preview": _short(value_text),
                    }
                )

    walk(tree, ())
    return matches


def _raw_line_hits(yaml_text: str, max_hits: int = 500) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for lineno, line in enumerate(yaml_text.splitlines(), start=1):
        if _matches_term(line):
            hits.append({"line": lineno, "text": _short(line, 500)})
            if len(hits) >= max_hits:
                break
    return hits


def _final_kernel_candidates(matches: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for match in matches:
        path = match.get("path", "").lower()
        text = (
            match.get("matched_text", "") + " " + match.get("value_preview", "")
        ).lower()
        # A generic kernel token is not enough. Require the same metadata path
        # to identify drizzle/resample context.
        if "kernel" in text and ("resam" in path or "driz" in path):
            out.append(match)
    return out


def _top_level_keys(tree: Any) -> list[str]:
    if isinstance(tree, dict):
        return [str(key) for key in tree.keys()]
    return []


def run(mosaic: Path, out_json: Path) -> dict[str, Any]:
    if not mosaic.exists():
        raise FileNotFoundError(mosaic)

    try:
        import asdf
    except ImportError as exc:
        raise RuntimeError(
            "Gate D2e requires ASDF 3.1.x for metadata-only YAML parsing. "
            "Install an isolated/local metadata dependency with: "
            "python -m pip install 'asdf==3.1.0'"
        ) from exc

    asdf_version = importlib.metadata.version("asdf")
    if not asdf_version.startswith("3.1."):
        raise RuntimeError(
            f"D2e protocol requires ASDF 3.1.x; found {asdf_version}. "
            "Do not substitute a newer parser silently."
        )

    with fits.open(mosaic, lazy_load_hdus=True) as hdul:
        if "ASDF" not in [hdu.name for hdu in hdul]:
            raise RuntimeError("ASDF extension is required")
        asdf_hdu = hdul["ASDF"]
        if not hasattr(asdf_hdu, "columns") or "ASDF_METADATA" not in (
            asdf_hdu.columns.names or []
        ):
            raise RuntimeError("ASDF_METADATA column is required")

        # This is the only HDU data payload intentionally dereferenced in D2e.
        # We do not call stdatamodels.asdf_in_fits.open/from_fits_asdf because
        # the historical mapping path dereferences FITS-backed array nodes.
        payload = asdf_hdu.data["ASDF_METADATA"].tobytes()

    yaml_bytes = _yaml_prefix(payload)
    yaml_text = yaml_bytes.decode("utf-8", errors="replace")

    tree = asdf.util.load_yaml(io.BytesIO(payload), tagged=False)
    matches = _collect_matches(tree)
    raw_hits = _raw_line_hits(yaml_text)
    kernel_candidates = _final_kernel_candidates(matches)

    result = {
        "stage": "Gate D2e embedded-ASDF provenance audit",
        "claim": "read-only ASDF YAML metadata audit; no FITS science-array mapping",
        "software": {
            "asdf_version": asdf_version,
            "parser": "asdf.util.load_yaml(tagged=False)",
            "stdatamodels_from_fits_mapping_used": False,
        },
        "mosaic": {
            "basename": mosaic.name,
            "byte_size": mosaic.stat().st_size,
        },
        "embedded_asdf": {
            "payload_byte_count": len(payload),
            "payload_sha256": hashlib.sha256(payload).hexdigest(),
            "yaml_byte_count": len(yaml_bytes),
            "header_preview": yaml_text.splitlines()[:12],
            "top_level_keys": _top_level_keys(tree),
            "matched_tree_paths": matches,
            "raw_yaml_line_hits": raw_hits,
            "match_limit_reached": len(matches) >= 500 or len(raw_hits) >= 500,
        },
        "assessment": {
            "explicit_final_resample_kernel_candidates": kernel_candidates,
            "final_resample_kernel_established": bool(kernel_candidates),
            "source_shot_realization_permitted": False,
            "remaining_requirements": [
                "literal survey-processed pre-resample input files with calibration/count provenance",
                "variance/count provenance for the literal contributing pre-resample inputs",
                "any replay-critical historical resampling setting still absent after D2e",
            ],
        },
        "interpretation_guardrails": {
            "generic_kernel_token_promoted_to_final_drizzle_kernel": False,
            "current_or_default_jwst_values_used_as_historical_evidence": False,
            "fits_backed_science_arrays_mapped_by_stdatamodels": False,
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
    out_json.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mosaic", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    args = parser.parse_args()
    run(args.mosaic, args.out_json)


if __name__ == "__main__":
    main()
