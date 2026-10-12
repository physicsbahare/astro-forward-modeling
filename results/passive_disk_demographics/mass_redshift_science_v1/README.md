# Observed passive-disk mass–redshift science

Read `REVIEW_AND_INTERPRETATION.md` first, then `SCIENTIFIC_RESULTS.md` for the
full methods, primary results, sensitivity scope and six figure captions.
`figure5b_same_support_mass_mix_sensitivity` additionally compares marginal and
standardized trends over exactly the same mass support; it isolates mass-mix
adjustment from the coverage change in Figure5.

These are native observed COSMOS2025 results, conditional on the frozen parent
and measurable paired-band morphology. No artificial-redshifting fits, inverse
completeness weights, ML labels or changed passive/disk thresholds are used.
The sample remains403. Observed correlations do not establish quenching pathways.

## Tables

- `mass_redshift_fractions.csv`:36cells, counts, five binomial fractions, pointwise
  Wilson95% intervals, sparse-event flags and detected-catalog missing-label bounds.
  `N_passive` is measurable passive count; `N_passive_eligible` also includes
  unknown morphology. Unknown is never classified as non-disk.
- `mass_standardized_trends.csv` / `reference_mass_weights.csv`: pooled fixed mass
  distribution at10–11; all six redshift bins have>=50measurable and>=20passive.
- `PD_all_broader_common_support_standardized.csv` / broader reference weights:
 9.5–11support requires>=50measurable per cell. It is appropriate to PD/all,
  while its low-mass/high-z passive denominators remain too sparse for precise D/P.
- `same_support_marginal_comparisons.csv`: raw observed marginals on identical
  mass support, so coverage changes are not mistaken for standardization effects.
- `standardized_change_decomposition.csv`: additive symmetric P/all and effective
  D/P contributions; shared joint multinomial bootstrap preserves covariance.
- `statistical_tests.csv`: supported-cell linear-logit slopes and deterministic
  bin/quality/depth sensitivities. Tile-cluster errors use20tiles, not a full cosmic
  variance model. Holm adjustment applies to the four primary questions; secondary
  tests, including common10–11slope and omnibus KS, are explicitly exploratory.
- `matched_SFR_comparison.csv`:403unique within-caliper pairs, location contrasts,
  pair-bootstrap intervals, balance diagnostics, SED-floor sensitivity.
- `matched_distribution_sensitivity.csv`:secondary paired-label-swap KS comparison.
- `SFR_mass_redshift_cell_summaries.csv`:group counts, medians,16–84% scatter,
  median bootstrap intervals and floor/valid-interval counts in original cells.
- `mass_completeness_assessment.csv` and reused M/L diagnostic: consistent mass
  floor, separate detection/measurement/classification limitations, no correction.
- `standardization_sensitivity.csv`, coarse fractions, fixed-label Gaussian
  migration diagnostic: robustness checks, not retuned final selections.

## Reproduction

The permanent entry point is `Codes/Passive_Spiral_MASTER.ipynb`, Step17, executed
in the existing `phd` kernel. Its preceding39cells/results remain unchanged.
`scripts/passive_disk_mass_redshift.py` computes or validates the frozen checkpoint;
`scripts/validate_passive_disk_mass_redshift.py` independently verifies raw boolean
counts and fixed-weight estimates, then produces explicit same-support sensitivities.
Run from the project root with the original relative output-path spelling:

```python
from passive_disk_mass_redshift import run
run(PROJECT, 'Results/Project_Completion_20261011/mass_redshift_science_v1')
```

The checkpoint rejects changed method/input/output hashes. The primary manifest
records code/input hashes, original selection manifest, bin edges, environment,
random seeds, uncertainties and code-base commit. The validation receipt records
supplementary method/output hashes; the notebook receipt verifies preserved cells
and successful execution of the appended section. This section can run in a fresh
kernel; old fits or notebook analyses need not run again.

Local source catalogs, matched-pair identifiers, raw images and previous results
remain local. Only aggregate tables, figures, methods and compact receipts are
published. Failures during initial plotting/report construction are preserved
locally and resolved; they did not alter any original source data or selection.
