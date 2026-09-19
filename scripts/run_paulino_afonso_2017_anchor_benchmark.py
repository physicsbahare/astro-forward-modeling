#!/usr/bin/env python3
"""Generate machine-readable anchors for Gate C2 (Paulino-Afonso 2017)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from verification.paulino_afonso_2017 import (
    TARGET_REDSHIFTS,
    published_trend_summary,
    radiometric_equivalence_row,
    table2_rows,
)


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise RuntimeError("No rows to write.")
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    output = Path("benchmark_output/paulino_afonso_2017")
    output.mkdir(parents=True, exist_ok=True)

    source_redshift = 0.03
    radiometric_rows = [
        radiometric_equivalence_row(source_redshift, float(z)).to_dict()
        for z in TARGET_REDSHIFTS
    ]
    _write_csv(output / "radiometric_equivalence.csv", radiometric_rows)
    _write_csv(output / "published_table2.csv", table2_rows())

    report = {
        "reference": (
            "Paulino-Afonso, Sobral, Buitrago & Afonso 2017, "
            "MNRAS 465, 2717, arXiv:1611.05039"
        ),
        "paper_targets": [
            "Section 3 artificial-redshifting operator sequence",
            "Section 5.1 and Figures 4-5 structural-degradation directions",
            "Table 2 median recovered/input r_e and Sersic-n ratios",
            "Appendix B luminosity-evolution convention",
        ],
        "source_redshift_for_radiometric_identity": source_redshift,
        "radiometric_equivalence": radiometric_rows,
        "published_trend_summary": published_trend_summary(),
        "scope": (
            "C2 anchor sub-gate only. This records the published structural "
            "targets and proves distance/Tolman observable equivalence. It does "
            "not yet claim image-level reproduction of the GALFIT degradation."
        ),
    }
    with (output / "summary.json").open("w") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")


if __name__ == "__main__":
    main()
