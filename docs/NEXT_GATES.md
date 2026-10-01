# GOLD403 Passive-Disk Next Gates

Last updated: 2026-10-01

This file is intentionally short. Detailed methodology is in `PASSIVE_DISK_Z3_METHOD.md` and numerical receipts are in `VALIDATION_RESULTS_2026-09-19.md`.

## Gate 0 - renderer/fitter convention

Status: **PASS**

- [x] Reject old custom Sersic renderer after noiseless mismatch.
- [x] Generate truth with Lenstronomy ImageModel.
- [x] Exact single-Sersic closed loop.
- [x] Perturbed-start convergence.
- [x] Keep signed PSFEx PSF and verify warning is not the failure source.

## Gate 1 - clean structural identifiability

Status: **PASS (representative-sweep scope)**

- [x] Exact B+D truth -> B+D recovery on three diagnostic objects.
- [x] Same B+D truth -> single-Sersic recovery.
- [x] Native-clean -> z=3-clean baseline on three diagnostic objects.
- [x] Demonstrate a real compact-component failure mode (ID 751217).
- [x] Controlled fixed-input PSO repeats: 751217 is multimodal/non-identifiable; 322095 and 162363 are stable controls.
- [x] Run restart-safe 31-object clean sweep spanning redshift and predicted z=3 size (31/31 OK).
- [x] Freeze diagnostic identifiability fields and classification-quality states.
- [x] Establish that a general hard component-size cut is **not** justified by this sample; retain continuous resolution warnings and a 751217-reference robustness regime.
- [x] Define classification reporting: `B/T_NONIDENTIFIABLE`, `IDENTIFIABLE_RESOLUTION_FLIP`, or `IDENTIFIABLE_STABLE_CLASS`.

Required output:

`clean_native_to_z3_identifiability_sweep_30.csv`


## Gate 1b - corrected structural representation

Status: **PASS**

The 2026-10-01 audit showed that fitting a single-Sersic model to a B+D truth image is not a valid closed-loop test of the catalog single-Sersic n.

The corrected method therefore uses:

- single-Sersic truth -> single-Sersic recovery for n;
- B+D truth -> B+D recovery for B/T.

Corrective pilot:

- [x] 15 previously representation-unstable objects.
- [x] 15 matched stable controls.
- [x] 30/30 successful.
- [x] native n pass fraction = 1.000.
- [x] native B/T pass fraction = 1.000.
- [x] joint native pass fraction = 1.000.
- [x] 0/30 corrected native -> z=3-clean class flips.

Receipt: `CORRECTED_TWO_BRANCH_PILOT_2026-10-01.md`.

## Gate 2 - corrected real-background pilot

Status: **PASS**

Use the validated Lenstronomy renderer.

- [x] Rebuild the model-injection renderer with exact Lenstronomy B+D truth.
- [x] Keep context validity checks.
- [x] Run the small E0/E1J F444W/F277W pilot (9/9 OK).
- [x] Verify flux conservation and no second background/noise realization.
- [x] Record S/N, background, neighbors, crowding, fit radius, bound hits, and failure codes.
- [x] Compare z3-real results against z3-clean baseline, not directly against the published catalog.

## Gate 3 - production schema freeze

Status: **PASS**

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

## Gate 4 - corrected population production

Status: **ACTIVE: GOLD91 first**

The historical 403 x 2 E0/E1J run is complete project history, but it used one exact B+D truth image for both the B/T fit and the single-Sersic fit. Therefore:

- historical B/T products may be reusable after a strict provenance/configuration match;
- historical single-Sersic n values are not the final n-transfer measurement;
- combined disk classifications that used those n values must be recomputed.

Current next run:

- [ ] Run corrected two-branch native-clean -> z=3-clean on GOLD91, 0.75 <= z < 1.00, N=91.
- [ ] Keep original-selection -> mapped-band changes separate from redshift-induced changes.
- [ ] Review branch validity, n/B/T boundary cases, and native -> z=3 clean flips.
- [ ] Run corrected GOLD91 real-background **E0** primary branch.
- [ ] Reuse historical B/T real-background products only if provenance/configuration identity is demonstrated.
- [ ] Add E1J only if an explicit brightness/S/N sensitivity comparison is needed.
- [ ] Scale the validated corrected chain to GOLD403.

For the clean GOLD91 gate, no per-galaxy luminosity evolution is required.

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

Do not proceed to the corrected full 403 real-background run if:

- the GOLD91 two-branch clean run reveals a new unresolved representation/fitter inconsistency,
- single-Sersic n is again measured from B+D truth and treated as the catalog-n transfer,
- clean-model classification failures cannot be separated from fit failure,
- real-context flux conservation is broken,
- context ERR validity is not enforced,
- the pipeline reintroduces custom analytic rendering with different numerical conventions,
- B/T is reported without an identifiability state.
