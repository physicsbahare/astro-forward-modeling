# Documentation Index

## Start here

1. [Project README](../README.md) - science goal, current status, validated assumptions, and remaining work.
2. [Passive-disk z=3 method](PASSIVE_DISK_Z3_METHOD.md) - detailed scientific and numerical methodology.
3. [Validation results](VALIDATION_RESULTS_2026-09-19.md) - frozen numerical receipts and diagnostic cases.
4. [Runbook](RUNBOOK.md) - operational instructions for resuming and running the analysis.
5. [Next gates](NEXT_GATES.md) - short checklist of what blocks the full GOLD403 production run.
6. [Controlled recovery diagnostic](CONTROLLED_RECOVERY_2026-09-19.md) - fixed-input PSO repeat gate after the interrupted sweep.
7. [Repository cleanup record](REPOSITORY_CLEANUP_2026-09-19.md) - what was removed from the active tree and what remains preserved in history.

## Active code

- `../scripts/gold403_validation_notebook_cells.py` - current consolidated Galight/Lenstronomy validation helpers.
- `../scripts/gold403_restartable_sweep.py` - atomic per-object checkpoint/resume utility.
- `../scripts/run_gold403_controlled_recovery_diagnostics.py` - controlled PSO-repeat gate without modifying the source notebook.
- `../tests/test_gold403_validation_helpers.py` - static regression test for the consolidated helper.
- `../verification/` - general numerical and survey-transfer verification utilities retained from the framework work.

## Machine-readable validation receipts

- `../data/validation/GOLD403_lenstronomy_closed_loop_receipt.csv`
- `../data/validation/GOLD403_three_object_native_z3_receipt.csv`
- `../data/validation/GOLD403_controlled_z3_recovery_2026-09-19.csv`

## Historical scientific evidence

- `../benchmarks/` - completed verification/stress-test receipts.
- `../crosscode/` - cross-code comparisons.
- `../verification/` and `../tests/` - reusable historical numerical checks.

Historical benchmark material is retained because it supports the scientific conventions of the active project, but it should not be confused with the current GOLD403 production pipeline.

## Current checkpoint

The controlled recovery gate has passed: 751217 is demonstrably structurally non-identifiable at z=3, while 322095 and 162363 are stable controls. The next required science product is the representative restart-safe clean identifiability/resolution sweep:

`clean_native_to_z3_identifiability_sweep_30.csv`

The 403-object real-background run remains intentionally blocked until the clean sweep and corrected real-context pilot are reviewed.
