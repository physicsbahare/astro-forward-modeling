# GOLD403 Passive-Disk Next Gates

Last updated: 2026-09-19

This file is intentionally short. Detailed methodology is in `PASSIVE_DISK_Z3_METHOD.md` and numerical receipts are in `VALIDATION_RESULTS_2026-09-19.md`.

## Gate 0 - renderer/fitter convention

Status: **PASS**

- [x] Reject old custom Sersic renderer after noiseless mismatch.
- [x] Generate truth with Lenstronomy ImageModel.
- [x] Exact single-Sersic closed loop.
- [x] Perturbed-start convergence.
- [x] Keep signed PSFEx PSF and verify warning is not the failure source.

## Gate 1 - clean structural identifiability

Status: **ACTIVE**

- [x] Exact B+D truth -> B+D recovery on three diagnostic objects.
- [x] Same B+D truth -> single-Sersic recovery.
- [x] Native-clean -> z=3-clean baseline on three diagnostic objects.
- [x] Demonstrate a real compact-component failure mode (ID 751217).
- [ ] Run ~30-object clean sweep spanning redshift and predicted z=3 size.
- [ ] Freeze diagnostic/final identifiability fields.
- [ ] Decide whether a hard component-size warning threshold is justified by the sweep.
- [ ] Decide how disk classification is reported when B/T is non-identifiable.

Required output:

`clean_native_to_z3_identifiability_sweep_30.csv`

## Gate 2 - corrected real-background pilot

Status: **BLOCKED ON GATE 1**

Use the validated Lenstronomy renderer.

- [ ] Rebuild the model-injection renderer.
- [ ] Keep context validity checks.
- [ ] Run the small E0/E1J F444W/F277W pilot.
- [ ] Verify flux conservation.
- [ ] Verify no second background/noise realization is added.
- [ ] Record S/N, background, neighbors, crowding, fit radius, bound hits, and failure codes.
- [ ] Compare z3-real results against z3-clean baseline, not directly against the published catalog.

## Gate 3 - production schema freeze

Status: **PENDING**

Before 403 objects, freeze output columns for:

- object ID and source redshift
- source morphology band
- published n, Re, q, B/T
- native-clean recovered n/B/T
- z3-clean recovered n/B/T
- z3-real recovered n/B/T
- disk/bulge Re in native pixels and target pixels
- Re/PSF metrics
- E0/E1J scenario
- empirical S/N
- context/background/crowding metadata
- B/T identifiability flags
- single-Sersic identifiability/convergence flags
- classification at each stage
- failure/bound-hit codes
- provenance and software versions

## Gate 4 - GOLD403 production

Status: **PENDING**

- [ ] Run all 403 objects.
- [ ] Preserve failures; do not silently drop them.
- [ ] Produce completeness/recovery versus:
  - stellar mass
  - source redshift
  - intrinsic/native size
  - predicted z3 size
  - B/T
  - Sersic n
  - S/N
  - background
  - crowding
  - morphology source band
- [ ] Compare E0 and E1J sensitivity.
- [ ] Quantify classification survival.
- [ ] Separate non-identifiability from non-detection.

## Gate 5 - robustness / paper products

Status: **PENDING**

- [ ] Repeat key results under reasonable fit-start perturbations.
- [ ] Check sensitivity to context selection.
- [ ] Check PSF position dependence.
- [ ] Check neighbor treatment.
- [ ] Keep the arm-survival diagnostic separate from parametric structure.
- [ ] Make final figures/tables.
- [ ] Freeze reproducible run configuration and environment.
- [ ] Archive final CSVs and provenance.

## Stop conditions

Do not proceed to the full 403 real-background run if:

- the 30-object sweep reveals an unresolved renderer/fitter inconsistency,
- clean-model classification failures cannot be separated from fit failure,
- real-context flux conservation is broken,
- context ERR validity is not enforced,
- the pipeline reintroduces custom analytic rendering with different numerical conventions,
- B/T is reported without an identifiability state.
