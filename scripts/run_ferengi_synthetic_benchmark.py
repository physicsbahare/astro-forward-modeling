#!/usr/bin/env python3
"""Run the deterministic FERENGI-style Gate-C1 baseline and archive metrics.

This runner deliberately contains no production defaults.  It executes the
controlled observation-only synthetic benchmark at three target redshifts and
writes machine-readable provenance/metrics for review.
"""

from __future__ import annotations

import json
import platform
from pathlib import Path

import numpy as np
import scipy

from verification.ferengi_synthetic import benchmark_grid


def main() -> None:
    rows = benchmark_grid()
    payload = {
        "benchmark": "FERENGI-style synthetic observation-only baseline",
        "primary_reference": {
            "paper": "Barden, Jahnke & Haussler (2008), ApJS 175, 105",
            "arxiv": "0812.1022",
        },
        "scope": (
            "Controlled synthetic analogue of the FERENGI operator sequence. "
            "This is not yet a reproduction using the original SDSS/GEMS/STAGES/COSMOS datasets."
        ),
        "mode": "observation_only",
        "intrinsic_luminosity_evolution": False,
        "intrinsic_size_evolution": False,
        "noise_background_insertion": False,
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "results": rows,
    }

    out = Path("benchmark_output/ferengi_2008")
    out.mkdir(parents=True, exist_ok=True)
    path = out / "synthetic_observation_only.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
