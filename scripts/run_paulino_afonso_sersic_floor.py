#!/usr/bin/env python3
"""Run the controlled Paulino-Afonso single-Sersic measurement-floor experiment."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from verification.paulino_afonso_sersic_floor import run_recovery_ensemble, summarize_rows


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise RuntimeError("No benchmark rows were generated.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    out = Path("benchmark_output/paulino_afonso_2017/sersic_floor")
    out.mkdir(parents=True, exist_ok=True)

    recovery = run_recovery_ensemble(realizations=8, base_seed=2717, stamp_size=81)
    recovery_rows = [row.to_dict() for row in recovery]
    summary_rows = summarize_rows(recovery)

    _write_csv(out / "recovery_rows.csv", recovery_rows)
    _write_csv(out / "summary.csv", summary_rows)

    payload = {
        "experiment": "single-Sersic target-measurement floor",
        "scientific_status": "diagnostic only; not full C2 reproduction",
        "interpretation_rule": (
            "Do not tune the truth grid, noise, or acceptance thresholds to force agreement with Table 2. "
            "Use discrepancies to identify missing source complexity, source-PSF transformation, real-background structure, fitting freedom, or selection."
        ),
        "n_recovery_rows": len(recovery_rows),
        "n_summary_rows": len(summary_rows),
        "summary": summary_rows,
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
