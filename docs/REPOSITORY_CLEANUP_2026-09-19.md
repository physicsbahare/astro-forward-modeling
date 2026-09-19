# Repository Cleanup - 2026-09-19

The active branch was cleaned while preserving full git history.

## Changes

- Replaced the old generic verification README with the current GOLD403 passive-disk project README.
- Added current methodology, validation results, runbook, and gate/status documentation.
- Added consolidated reusable Lenstronomy/Galight validation code.
- Added an active passive-disk requirements file and optional dependency set.
- Disabled the obsolete custom-Sersic GOLD403 runner so it cannot be used accidentally.
- Added a static regression test for the consolidated validation helper.
- Expanded .gitignore for local FITS/HDF5/NPY/NPZ and GOLD403 products.
- Removed 91 historical one-off GitHub Actions workflow YAML files from the active tree.
- Kept the active passive-spiral workflows plus the general verification workflow.
- Removed obsolete root-level requirements files tied to one-off AGN/Dewsnap/PyAutoGalaxy/JWST benchmark environments.

## What was intentionally not deleted

- `benchmarks/`: scientific receipts and historical evidence remain useful.
- `verification/`: numerical/survey-transfer reference code remains useful.
- `crosscode/`: cross-code verification history remains useful.
- `tests/`: regression history remains useful.
- git history: every removed workflow/configuration remains recoverable.

The cleanup is a working-tree cleanup, not a history rewrite.
