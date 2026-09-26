# Documentation Index

## Start here

1. [Project README](../README.md) - science goal, current status, validated assumptions, and remaining work.
2. [Passive-disk z=3 method](PASSIVE_DISK_Z3_METHOD.md) - detailed scientific and numerical methodology.
3. [Validation results](VALIDATION_RESULTS_2026-09-19.md) - frozen numerical receipts and diagnostic cases.
4. [Runbook](RUNBOOK.md) - operational instructions for resuming and running the analysis.
5. [Next gates](NEXT_GATES.md) - short checklist of what blocks the full GOLD403 production run.
6. [Controlled recovery diagnostic](CONTROLLED_RECOVERY_2026-09-19.md) - fixed-input PSO repeat gate after the interrupted sweep.
7. [Representative clean sweep](CLEAN_SWEEP_2026-09-19.md) - checkpointed 31-object identifiability/resolution result and policy.
8. [Corrected real-background pilot](REAL_BACKGROUND_PILOT_2026-09-19.md) - restart-safe real SCI/ERR E0/E1J gate.
9. [Repository cleanup record](REPOSITORY_CLEANUP_2026-09-19.md) - what was removed from the active tree and what remains preserved in history.
10. [Production receipt recovery](PRODUCTION_RECEIPT_RECOVERY_2026-09-20.md) - structured handling of nonphysical real B+D decompositions.\n11. [BAGPIPES SFH robustness experiment](BAGPIPES_SFH_ROBUSTNESS_2026-09-26.md) - why object-specific backward luminosity evolution is not adopted, and why E1J remains a controlled sensitivity branch.

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
- `../data/validation/GOLD403_clean_sweep_31_2026-09-19.csv`
- `../data/validation/GOLD403_real_background_pilot_2026-09-19.csv`
- `../data/validation/GOLD403_production_nonphysical_bt_receipt_2026-09-20.csv`\n- `../data/validation/bagpipes_sfh_robustness_2026-09-26/SFH_model_fit_quality.csv`\n- `../data/validation/bagpipes_sfh_robustness_2026-09-26/SFH_model_gbag_summary.csv`\n- `../data/validation/bagpipes_sfh_robustness_2026-09-26/SFH_model_robustness_summary.csv`

## Historical scientific evidence

- `../benchmarks/` - completed verification/stress-test receipts.
- `../crosscode/` - cross-code comparisons.
- `../verification/` and `../tests/` - reusable historical numerical checks.

Historical benchmark material is retained because it supports the scientific conventions of the active project, but it should not be confused with the current GOLD403 production pipeline.

## Current checkpoint

The controlled recovery, representative clean-sweep, and corrected real-background pilot gates have passed. 751217 is structurally non-identifiable at z=3; 514739 is an identifiable n-boundary flip; the pilot retains real-context classification degradation as an outcome. The restart-safe four-stage GOLD403 production receipt is active; undefined real B/T is retained as an ERROR/quality state rather than coerced into a morphology class.

`published -> native clean -> z3 clean -> z3 real production receipt`
\n\n## Luminosity-evolution decision - 2026-09-26\n\nA two-object BAGPIPES robustness experiment compared double-power-law, delayed-tau, and non-parametric continuity SFHs under the same accepted photometric setup. The observed SEDs could be fit at comparable raw chi-square, but the inferred z=3 stellar populations and intrinsic luminosity factors changed strongly with SFH family, including posterior solutions with no stellar population yet formed at z=3. The project therefore does not adopt an object-specific EBAG correction from the current broadband data. E0 remains primary; E1J is retained only as a controlled F444W brightening sensitivity test. See `BAGPIPES_SFH_ROBUSTNESS_2026-09-26.md`.\n