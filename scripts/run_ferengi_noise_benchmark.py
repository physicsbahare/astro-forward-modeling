#!/usr/bin/env python3
"""Run the controlled FERENGI target-noise/background extension."""

from __future__ import annotations

import json
from pathlib import Path

from verification.ferengi_noise_benchmark import run_ferengi_noise_benchmark


def main() -> None:
    result = run_ferengi_noise_benchmark()
    payload = {
        "benchmark": "FERENGI-style synthetic target-noise extension",
        "scope": (
            "Synthetic source Poisson noise plus one zero-mean Gaussian target-background "
            "realization, applied after redshifting, target PSF convolution and target pixel sampling."
        ),
        "real_survey_background": False,
        "double_background_noise": False,
        "result": result.to_dict(),
    }
    out = Path("benchmark_output/ferengi_2008")
    out.mkdir(parents=True, exist_ok=True)
    path = out / "synthetic_target_noise.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
