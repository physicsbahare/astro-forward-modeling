#!/usr/bin/env python3
"""Run Passive Spiral P1 and archive machine-readable metrics."""

from __future__ import annotations

import json
import platform
from pathlib import Path

import numpy as np
import scipy

from verification.passive_spiral_redshift import benchmark_grid


def main() -> None:
    rows = benchmark_grid()
    payload = {
        "benchmark": "Passive Spiral P1 spiral-feature survival under controlled artificial redshifting",
        "scope": (
            "Synthetic observation-only spiral-feature diagnostic. This is not a literal "
            "COSMOS-Web reproduction, not a passive-galaxy classifier, and not a production threshold."
        ),
        "references": [
            "Barden, Jahnke & Haussler (2008), FERENGI",
            "Yu et al. (2023), A&A 676 A74",
            "Kuhn et al. (2024), arXiv:2312.12389",
        ],
        "noise_added": False,
        "source_shot_noise_added": False,
        "background_added": False,
        "intrinsic_size_evolution": False,
        "intrinsic_luminosity_evolution": False,
        "psf_sharpening_allowed": False,
        "extra_tolman_factor": False,
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "results": rows,
    }

    out = Path("benchmark_output/passive_spiral_redshift")
    out.mkdir(parents=True, exist_ok=True)
    path = out / "p1_spiral_feature_survival.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
