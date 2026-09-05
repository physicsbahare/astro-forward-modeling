#!/usr/bin/env python3
"""Write the frozen Stage-0 AGN nuclear-fraction benchmark record."""
from __future__ import annotations

import json
from pathlib import Path

from verification.agn_nuclear_fraction import anchor_record


def main() -> None:
    out = Path("benchmark_output/agn_nuclear_fraction")
    out.mkdir(parents=True, exist_ok=True)
    payload = anchor_record()
    (out / "anchor.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
