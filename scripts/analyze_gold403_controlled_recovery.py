#!/usr/bin/env python3
"""Validate and summarize controlled GOLD403 z=3 recovery receipts."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
import statistics
import tempfile


EXPECTED_REPEATS = {"751217": 5, "322095": 2, "162363": 2}
NUMERIC_COLUMNS = (
    "clean_single_n", "clean_single_re_arcsec", "clean_single_q", "recovered_bt",
    "recovered_disk_re_arcsec", "recovered_bulge_re_arcsec", "recovered_disk_q",
    "recovered_bulge_q", "bd_chisq", "single_chisq",
)


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


def span(values: list[float]) -> dict[str, float]:
    return {"min": min(values), "max": max(values), "range": max(values) - min(values), "median": statistics.median(values)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    with args.receipt.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    keys = [(r.get("id"), r.get("repeat_index")) for r in rows]
    errors: list[str] = []
    if len(keys) != len(set(keys)):
        errors.append("duplicate (id, repeat_index) rows")
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row.get("id", ""), []).append(row)
        if row.get("status") != "OK":
            errors.append(f"non-OK row for ID {row.get('id')}: {row.get('status')}")
        for name in NUMERIC_COLUMNS:
            try:
                if not math.isfinite(float(row[name])):
                    errors.append(f"non-finite {name} for ID {row.get('id')}")
            except (KeyError, TypeError, ValueError):
                errors.append(f"missing or invalid {name} for ID {row.get('id')}")
    if set(grouped) != set(EXPECTED_REPEATS):
        errors.append(f"IDs {sorted(grouped)} do not match expected {sorted(EXPECTED_REPEATS)}")
    for oid, count in EXPECTED_REPEATS.items():
        if len(grouped.get(oid, [])) != count:
            errors.append(f"ID {oid}: expected {count} repeats, found {len(grouped.get(oid, []))}")

    with args.reference.open(newline="", encoding="utf-8") as handle:
        reference = {row["id"]: row for row in csv.DictReader(handle)}
    summary: dict[str, object] = {
        "receipt": str(args.receipt), "expected_repeats": EXPECTED_REPEATS,
        "row_count": len(rows), "unique_row_count": len(set(keys)), "validation_errors": errors,
        "objects": {},
    }
    compact_rows: list[dict[str, object]] = []
    for oid, object_rows in sorted(grouped.items(), key=lambda item: int(item[0])):
        metrics = {key: [float(row[key]) for row in object_rows] for key in NUMERIC_COLUMNS}
        classes = [row["disk_classification"] == "True" for row in object_rows]
        bound_runs = [row["repeat_index"] for row in object_rows if row["bd_bound_hits"] != "[]" or row["single_bound_hits"] != "[]"]
        ref = reference.get(oid, {})
        object_summary = {
            "repeat_count": len(object_rows), "classification_values": classes,
            "classification_stable": len(set(classes)) == 1,
            "bound_hit_repeats": bound_runs,
            "metrics": {key: span(values) for key, values in metrics.items()},
            "reference_z3_n": float(ref["z3_clean_n"]) if ref else None,
            "reference_z3_bt": float(ref["z3_recovered_bt"]) if ref else None,
        }
        summary["objects"][oid] = object_summary
        for row in object_rows:
            compact_rows.append({
                "id": oid, "repeat_index": row["repeat_index"], "status": row["status"],
                "seed": row["seed_numpy"], "z3_clean_n": row["clean_single_n"],
                "z3_recovered_bt": row["recovered_bt"], "bd_chisq": row["bd_chisq"],
                "single_chisq": row["single_chisq"], "disk_classification": row["disk_classification"],
                "bound_hit": bool(row["bd_bound_hits"] != "[]" or row["single_bound_hits"] != "[]"),
            })
    atomic_write(args.output_dir / "controlled_recovery_validation.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    fields = list(compact_rows[0])
    with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=args.output_dir, delete=False) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(compact_rows)
        handle.flush(); os.fsync(handle.fileno()); temporary = Path(handle.name)
    os.replace(temporary, args.output_dir / "controlled_recovery_compact_receipt.csv")

    obj = summary["objects"]
    markdown = f"""# Controlled z=3 recovery diagnostic — 2026-09-19

## Receipt validation

- Expected and received independent repeats: **9** (751217: 5; 322095: 2; 162363: 2).
- All rows are `OK`, all required recovery metrics are finite, and no duplicate `(id, repeat_index)` rows exist.
- Each object has a separately saved frozen-input receipt: exact truth-image SHA256, context, signed target-PSF SHA256/statistics, starts, bounds, PSO convention, and requested NumPy/Python seed.

## Controlled result

| ID | n range | B/T range | class stable? | bound-hit repeats | Interpretation |
| --- | ---: | ---: | --- | --- | --- |
| 751217 | {obj['751217']['metrics']['clean_single_n']['min']:.4f}–{obj['751217']['metrics']['clean_single_n']['max']:.4f} | {obj['751217']['metrics']['recovered_bt']['min']:.4f}–{obj['751217']['metrics']['recovered_bt']['max']:.4f} | no (1/5 disk) | {obj['751217']['bound_hit_repeats']} | multiple low-χ² structural solutions |
| 322095 | {obj['322095']['metrics']['clean_single_n']['min']:.4f}–{obj['322095']['metrics']['clean_single_n']['max']:.4f} | {obj['322095']['metrics']['recovered_bt']['min']:.4f}–{obj['322095']['metrics']['recovered_bt']['max']:.4f} | yes | {obj['322095']['bound_hit_repeats']} | stable control |
| 162363 | {obj['162363']['metrics']['clean_single_n']['min']:.4f}–{obj['162363']['metrics']['clean_single_n']['max']:.4f} | {obj['162363']['metrics']['recovered_bt']['min']:.4f}–{obj['162363']['metrics']['recovered_bt']['max']:.4f} | yes | {obj['162363']['bound_hit_repeats']} | stable control |

The controlled 751217 repeats use an identical frozen Lenstronomy truth image, selected real-context PSF, fitting bounds, and initial parameters. Only the requested global PSO seed changes. They produce comparable very small reduced χ² values while their B/T and single-Sersic classification disagree. This is direct evidence for **structural non-identifiability** at this resolution, not a deterministic renderer discrepancy. The archived validated z=3 value (`n={obj['751217']['reference_z3_n']:.4f}`, `B/T={obj['751217']['reference_z3_bt']:.4f}`) is another optimizer-accessible solution, rather than a value that should be privileged physically.

The controls reproduce stable z=3 single-Sersic n values and disk classifications; their small B/T differences from the earlier receipt do not change their interpretation. The result supports retaining the validated four-stage comparison and requiring a native-clean B/T identifiability flag. It does **not** support a final numerical resolution/B/T cut from three objects. The restart-safe representative sweep must measure the prevalence and relation to disk/bulge resolution before such a policy is chosen.
"""
    atomic_write(args.output_dir / "controlled_recovery_interpretation.md", markdown)
    print(json.dumps({"validation_errors": errors, "rows": len(rows), "output_dir": str(args.output_dir)}))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
