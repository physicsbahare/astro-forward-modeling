#!/usr/bin/env python3
"""Run the corrected Paulino-Afonso single-Sersic measurement-floor experiment."""

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

    # Three deterministic noise realizations per source/redshift are sufficient
    # for this diagnostic floor. This is not an ensemble-convergence claim; Gate
    # E will freeze stochastic convergence criteria only after Gates B-D.
    recovery = run_recovery_ensemble(realizations=3, base_seed=2717)
    recovery_rows = [row.to_dict() for row in recovery]
    summary_rows = summarize_rows(recovery)

    _write_csv(out / "recovery_rows.csv", recovery_rows)
    _write_csv(out / "summary.csv", summary_rows)

    payload = {
        "experiment": "single-Sersic target-measurement floor, corrected footprint and flux mapping",
        "scientific_status": "diagnostic only; not full C2 reproduction",
        "interpretation_rule": (
            "Do not tune truth cases, fitting bounds, noise, footprint, or acceptance thresholds to force agreement with Table 2. "
            "Boundary hits, non-convergence, and discrepancies are diagnostic observables."
        ),
        "known_missing_physics": [
            "real local source morphology and substructure",
            "source-image PSF and source noise followed by source-to-target PSF transformation",
            "real correlated/non-Gaussian COSMOS ACS background",
            "GALFIT-specific implementation and selection effects",
        ],
        "n_recovery_rows": len(recovery_rows),
        "n_summary_rows": len(summary_rows),
        "summary": summary_rows,
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
