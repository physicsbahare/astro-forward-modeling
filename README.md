# Passive Disk Artificial-Redshifting / Forward-Modeling Project

This repository contains the validation and forward-modeling work for the **COSMOS-Web passive-disk / passive-spiral project**, with the current science target being:

> If the observed passive-disk population were placed at **z = 3**, how often would its structural morphology still be measurable and still be classified as disk-like after realistic JWST/COSMOS-Web observational degradation?

The repository also keeps the older general forward-modeling verification material that established the numerical and survey-transfer conventions used here. The active science work is now the **GOLD403 passive-disk experiment**.

## Current status - 2026-09-19

The project is **not yet ready for the final 403-object real-background production run**. The renderer/fitter convention problem that affected earlier pilots has now been isolated and fixed, and the next active gate is a 30-object clean identifiability/resolution sweep.

### What is complete

- GOLD403 science sample: **403 passive-disk candidates**.
- Real cutouts and morphology/catalog plumbing are available locally.
- Native Galight recovery was used as an initial validation gate.
- Position-dependent COSMOS-Web PSFEx handling was audited.
- Real-context injection policy was frozen: inject the source into the already noisy mosaic; do **not** add a second sky/background realization.
- E0 and E1J luminosity-evolution scenarios were defined.
- A model-based z=3 pilot was built.
- Context validity checks were added so SCI/ERR shape, finite pixels, positive ERR, center validity, and valid-pixel fraction are enforced before fitting.
- The old custom analytic Sersic renderer was shown to be inconsistent with the Galight/Lenstronomy numerical convention.
- An exact Lenstronomy closed-loop test gives perfect recovery for three representative galaxies.
- A deliberately perturbed-start test also converges for all three representative galaxies.
- Exact B+D tests showed that B/T can become non-identifiable even in noiseless data when components are too compact.
- A native-clean -> z=3-clean comparison separated catalog/model mismatch from genuine redshift/resolution degradation.

### Decisive validation result

The exact single-Sersic Lenstronomy truth -> Galight recovery test recovered all tested parameters essentially exactly for the three diagnostic objects:

- ID 751217: n = 2.2546 -> 2.2546
- ID 322095: n = 1.4136 -> 1.4136
- ID 162363: n = 0.7743 -> 0.7743

With deliberately wrong starting parameters (roughly +30% in Re, +30% in n, delta-q ~ 0.12, and a one-pixel centroid offset), all three still converged back to truth. This establishes that the earlier catastrophic single-Sersic result was **not** caused by Galight itself or by the signed PSF. It came from a mismatch between the homemade renderer and the Lenstronomy/Galight rendering convention.

The production renderer must therefore use the **same Lenstronomy image-model convention as the fitter**.

### B+D identifiability result

The clean B+D experiment exposed a separate problem: a formally excellent fit does not guarantee that bulge/disk parameters are identifiable.

For ID 751217:

- input B/T = 0.268
- native-clean recovered B/T = 0.077
- z=3-clean recovered B/T = 0.092
- native disk Re ~ 1.72 pixels -> z=3 disk Re ~ 0.42 pixels
- native bulge Re ~ 0.33 pixels -> z=3 bulge Re ~ 0.08 pixels
- native B+D -> single n = 1.53
- z=3 B+D -> single n = 8.80
- disk classification changes from True at native-clean to False at z=3-clean

Therefore the z=3 B/T value for such an object must **not** be interpreted as a physical B/T change. The native decomposition is already non-identifiable. B/T needs an explicit identifiability flag in the final catalog.

For the other two representative objects, native-clean and z=3-clean morphology remained stable.

## Active next step

The restart-safe **31-object clean identifiability / resolution sweep** completed 31/31 successful fits. It confirms 751217 as a compact, structurally non-identifiable case and distinguishes an identifiable n-boundary flip (514739) from fit failure. See [the clean-sweep receipt](docs/CLEAN_SWEEP_2026-09-19.md).

The corrected real-background E0/E1J pilot has passed 9/9 restart-safe cases using exact Lenstronomy truth, real SCI/ERR/segmentation, and signed position-dependent PSFEx. See [the pilot receipt](docs/REAL_BACKGROUND_PILOT_2026-09-19.md). The active next step is the frozen, restart-safe four-stage GOLD403 production run.

The sweep should span source redshift and predicted z=3 component size and should record:

- published catalog n and B/T
- native-clean B+D -> single-Sersic n
- z=3-clean B+D -> single-Sersic n
- native and z=3 recovered B/T
- native and z=3 disk/bulge Re in pixels
- native B/T identifiability
- z=3 B/T identifiability
- disk-classification flips
- failures/bound hits/convergence information

Only after this sweep is understood should the real-background E0/E1J pilot be rerun using the validated Lenstronomy renderer.

## Final science chain

The current analysis should preserve four distinct stages:

1. **Published catalog**
2. **Native clean synthetic model**
3. **z=3 clean model**
4. **z=3 real-background injection**

This separation is essential.

- Published -> native clean measures **catalog/model representation mismatch**.
- Native clean -> z=3 clean measures **pure redshift/resolution/PSF degradation**.
- z=3 clean -> z=3 real-background measures **background, crowding, segmentation, and fitting degradation**.

Do not compare the published catalog directly to the noisy z=3 result and attribute the entire difference to redshift.

## Science assumptions frozen so far

### Target

- z_target = 3
- primary target morphology band: F444W
- native mosaic pixel scale: 0.03 arcsec/pixel

### Morphology

The source morphology is chosen from the nearest valid NIRCam morphology band to the rest wavelength sampled by the target filter. The production structural experiment uses catalog/Galight structural models rather than trying to preserve spiral arms.

Spiral-arm survival is a separate resolution diagnostic and should not be conflated with structural B/T or single-Sersic completeness.

### Disk classification

Current structural definition:

- B/T < 0.5
- single-Sersic n < 2.5

This classification should be reported together with measurement/identifiability flags.

### Luminosity evolution

- **E0**: no intrinsic luminosity evolution. This is the primary observational-transfer baseline.
- **E1J**: F444W-only controlled brightening sensitivity branch. Production uses
  `g_E1J = [(1 + z_target) / (1 + z_source)]^1.02`.
  For a typical source at z about 0.87 moved to z=3, this is g about 2.17, or about 0.84 mag brighter than E0 after the same cosmological projection.

E1J does not change morphology, angular-size scaling, PSF, context, or recovery settings. It tests whether the real-background structural result is sensitive to intrinsic brightness/SNR.

A 2026-09-26 BAGPIPES robustness test showed that object-specific backward luminosity factors are strongly SFH-model dependent. Double-power-law, delayed-tau, and continuity models can fit the observed SED at similar raw chi-square while implying very different z=3 stellar populations, including no-progenitor solutions. Therefore the project does **not** adopt a per-galaxy EBAG correction from the current broadband data. E1J remains a sensitivity test, not a physical progenitor reconstruction. See [the BAGPIPES receipt](docs/BAGPIPES_SFH_ROBUSTNESS_2026-09-26.md).

### Injection noise policy

For injection into a real COSMOS-Web mosaic:

- inject a deterministic synthetic source into the existing SCI image/context
- keep the already existing real sky/background noise
- do not add another realization of sky/background noise
- do not use i2d VAR_POISSON as a new source-noise realization
- any source-shot-noise approximation must be clearly labeled as an approximation unless the exposure-level provenance is explicitly reconstructed

### PSF policy

COSMOS-Web PSFEx models are position dependent.

The adopted NIRCam evaluation is:

- use GalSim DES_PSFEx
- evaluate at x_image + 1, y_image + 1 because the catalog mosaic coordinates are zero-based while PSFEx uses one-based image coordinates
- draw with method="no_pixel" because the PSFEx effective PSF already includes pixel response
- preserve the signed PSF; do not clip negative wings just to silence Lenstronomy warnings
- normalize by signed total flux

The Lenstronomy negative-PSF warning is expected for these empirical/effective PSFs and is not by itself evidence of a failed fit.

## Repository layout

- `docs/PASSIVE_DISK_Z3_METHOD.md` - detailed methodology and lessons learned.
- `docs/VALIDATION_RESULTS_2026-09-19.md` - numerical validation record.\n- `docs/BAGPIPES_SFH_ROBUSTNESS_2026-09-26.md` - backward-luminosity/SFH robustness test and E1J interpretation.
- `docs/RUNBOOK.md` - operational order for the remaining analysis.
- `docs/NEXT_GATES.md` - short current gate/status list.
- `scripts/gold403_validation_notebook_cells.py` - consolidated reusable validation code for the active notebook environment.
- `scripts/run_gold403_z3_model.py` - historical model-only script; see warning in that file before reuse.
- `verification/` - general numerical/survey-transfer verification utilities.
- `tests/` - regression tests retained where they support current conventions.
- `benchmarks/` - historical verification evidence. These are background evidence, not the active production pipeline.

## Local data

Large COSMOS-Web mosaics, GOLD403 catalog products, HDF5 cutouts, PSF files, and generated science products are intentionally not stored in this public repository.

Current local project roots used in the analysis include:

```
/home/bahareh/Desktop/Projects/Passive_Spiral/Data
/home/bahareh/Desktop/Projects/Data_General/Cosmos_Web
/run/media/bahareh/Seagate Hub/NIRCam_mosaics
```

Important current local products include:

```
passive_disk_GOLD403_with_visual_flags.csv
real_cutouts_GOLD403_for_z3/
forward_z3_GOLD403_v1/
```

Do not hard-code those paths into reusable library code. Keep them in notebook/project configuration.

## Reproducible validation order

Run these in order:

1. Environment and catalog preflight.
2. Position-dependent PSF preflight.
3. Exact Lenstronomy single-Sersic closed-loop.
4. Perturbed-start single-Sersic convergence.
5. Exact B+D clean validation.
6. Native-clean -> z=3-clean baseline.
7. 30-object clean identifiability/resolution sweep.
8. Review empirical failure/identifiability thresholds.
9. Rebuild the z=3 real-background pilot with Lenstronomy rendering.
10. Rerun E0/E1J pilot with valid contexts.
11. Only then run all 403 objects.
12. Produce completeness/classification diagnostics versus mass, redshift, size, B/T, n, S/N, background, and crowding.

## Remaining decisions before the 403 run

- Define the production B/T identifiability flag from the 30-object sweep rather than inventing a threshold from one galaxy.
- Decide whether single-Sersic classification alone remains usable when B+D is non-identifiable.
- Freeze the clean-model baseline used for bias measurements.
- Replace all remaining custom Sersic rendering in the production path with Lenstronomy-consistent rendering.
- Repeat the real-context 9-fit pilot after the renderer replacement.
- Confirm output/provenance columns and failure codes.
- Freeze which E0/E1J products are considered primary versus sensitivity outputs.

## Important warning about old results

Earlier model-only and real-background pilot products generated with the custom analytic Sersic renderer are useful as debugging history, but they must **not** be treated as final production morphology results. The exact Lenstronomy closed-loop experiment demonstrated that the renderer/fitter convention mismatch can create large artificial n and Re biases.

## Branches

The current cleaned project work is being consolidated from `gold403-z3-model-only`. Git history preserves the older experiments even when obsolete workflow/config files are removed from the active tree.

## Citation / scientific-use note

This repository records the numerical methodology and validation state of an active research project. Thresholds and provisional sensitivity prescriptions should not be quoted as final science results until the full GOLD403 production analysis and robustness checks are complete.
