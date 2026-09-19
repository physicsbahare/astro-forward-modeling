#!/usr/bin/env python3
"""Launch the frozen restart-safe GOLD403 F444W E0/E1J production receipt.

The validated real-background runner supplies all fitting behavior.  This thin
entry point freezes the 403-object selection and the two allowed F444W
scenarios, then delegates atomic checkpointing and forced-case reruns to it.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import run_gold403_real_background_pilot as production


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--notebook", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--force-source-id", action="append", type=int, default=[])
    parser.add_argument("--limit-sources", type=int, help="validated smoke subset; production omits this")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=14400)
    args = parser.parse_args()
    with args.catalog.open(newline="", encoding="utf-8") as f:
        ids = [int(row["id"]) for row in csv.DictReader(f)]
    if len(ids) != 403 or len(set(ids)) != 403:
        raise RuntimeError(f"expected 403 unique GOLD403 IDs; found {len(ids)} rows / {len(set(ids))} unique")
    run_ids = ids if args.limit_sources is None else ids[:int(args.limit_sources)]
    if not run_ids: raise RuntimeError("--limit-sources must select at least one source")
    # F444W is the frozen primary structural target. E1J is F444W-only.
    production.CASES[:] = [(oid, "F444W", "E0") for oid in run_ids] + [(oid, "F444W", "E1J") for oid in run_ids]
    forced = set(args.force_source_id)
    force_cases = [str(ix + 1) for ix, (oid, _, _) in enumerate(production.CASES) if oid in forced]
    argv = [sys.argv[0], "--notebook", str(args.notebook), "--output-dir", str(args.output_dir),
            "--timeout-seconds", str(args.timeout_seconds)]
    if args.prepare_only: argv.append("--prepare-only")
    for case_id in force_cases: argv.extend(["--force-case", case_id])
    old_argv = sys.argv
    try:
        sys.argv = argv
        return production.main()
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    raise SystemExit(main())
