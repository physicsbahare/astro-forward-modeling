#!/usr/bin/env python3
"""
DEPRECATED historical GOLD403 z=3 model-only runner.

Do not use this script for production morphology measurements.

Why it is deprecated
--------------------
The original implementation in this path used a homemade analytic Sersic
renderer followed by a simplified target-PSF treatment. Noiseless validation
showed that this renderer could disagree strongly with the Galight/Lenstronomy
model convention. A representative failure was ID 751217, where a truth
single-Sersic n ~ 2.25 was recovered near n ~ 8.8 under the old rendering path.

The validated direction as of 2026-09-19 is:

    catalog structure
      -> Lenstronomy ImageModel rendering
      -> native-clean validation
      -> z=3-clean validation
      -> real COSMOS-Web context injection
      -> Galight recovery

Use:
    scripts/gold403_validation_notebook_cells.py

and follow:
    docs/RUNBOOK.md
    docs/PASSIVE_DISK_Z3_METHOD.md
    docs/NEXT_GATES.md

The previous implementation remains recoverable from git history.
"""

from __future__ import annotations

import sys


MESSAGE = """
This historical runner is intentionally disabled.

The old custom Sersic renderer failed the validated Lenstronomy/Galight
closed-loop convention test and must not be used for production morphology.

Run the current notebook setup, then:

    %run -i scripts/gold403_validation_notebook_cells.py

Proceed through the clean identifiability sweep before rebuilding the
real-background production runner.

See README.md and docs/RUNBOOK.md.
""".strip()


def main() -> None:
    print(MESSAGE, file=sys.stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    main()
