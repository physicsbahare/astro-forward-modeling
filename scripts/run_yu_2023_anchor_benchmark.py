#!/usr/bin/env python3
"""Write the frozen Yu et al. (2023) resolvedness/morphology anchors.

This is an anchor/provenance step only. It does not implement the paper's
empirical correction functions and does not define production acceptance cuts.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verification.yu_2023 import literature_anchor_record, resolution_row


def main() -> None:
    out = Path("benchmark_output/yu_2023")
    out.mkdir(parents=True, exist_ok=True)

    payload = literature_anchor_record()
    payload["definition_checks"] = [
        resolution_row(10.0, 2.0).to_dict(),
        resolution_row(2.5, 0.5).to_dict(),
    ]
    payload["status"] = (
        "exact literature definitions frozen; controlled PSF-only/noiseless resolvedness "
        "sweep is a separate Stage-1 diagnostic and does not evaluate the paper's correction functions"
    )

    path = out / "anchor.json"
    path.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
