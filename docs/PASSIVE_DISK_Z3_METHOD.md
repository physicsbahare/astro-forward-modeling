# Passive Disk z=3 Method and Validation Notes

Last updated: 2026-09-19

This document records the active methodology for the GOLD403 passive-disk artificial-redshifting experiment and the validation lessons that must be preserved in future notebooks/scripts.

## Scientific question

For the observed passive-disk population, ask what would be measured if the same structural systems were observed at z=3 in JWST/COSMOS-Web conditions.

The experiment is an observational transfer-function test. It is not a claim that an individual lower-redshift galaxy is the literal progenitor of a specific z=3 object.

The structural question is:

- what intrinsic model is carried forward,
- how angular size and flux are transformed,
- how the target PSF and detector sampling alter the image,
- what Galight recovers,
- when the recovered morphology ceases to be identifiable,
- and how much additional damage is caused by real mosaic background/crowding.

## GOLD403 sample

The working science sample contains 403 passive-disk candidates.

The current disk-like structural criterion is:

- B/T < 0.5
- single-Sersic n < 2.5

These are classification cuts, not guarantees that every fitted component is individually resolved.

## Four-stage baseline

Every production result should retain four stages:

1. published catalog
2. native clean synthetic model
3. z=3 clean model
4. z=3 real-background injection

This distinction was added after validation showed that catalog single-Sersic and B+D solutions are not always mutually reproducible.

### Published -> native clean

Measures mismatch introduced by representing the catalog object with the chosen synthetic structural model.

This is not redshift degradation.

### Native clean -> z=3 clean

Measures the pure artificial-redshift transfer:

- angular-size change
- target detector sampling
- target PSF
- structural non-identifiability caused by lost resolution

This is the correct baseline for resolution-driven morphology bias.

### z=3 clean -> z=3 real background

Measures additional observational/recovery effects:

- real background structure
- crowding
- neighbors
- segmentation
- local noise
- fit instability in the real context

## Wavelength / morphology mapping

For a target filter at z_target, the corresponding source-frame observed wavelength is

lambda_source = lambda_target * (1 + z_source) / (1 + z_target)

The available source morphology filter is chosen as the nearest valid morphology band to that wavelength.

For F444W at z=3 this can select F115W, F150W, F277W, or F444W depending on source redshift.

The chosen morphology band must be recorded per object.

## Angular-size scaling

For the same physical structure,

theta_target / theta_source = D_A(z_source) / D_A(z_target)

Therefore each catalog Re is scaled by

Re_target = Re_source * D_A(z_source) / D_A(z_target)

Do not assume angular size monotonically shrinks with redshift because D_A turns over.

## Flux scaling

For corresponding rest frequencies, the adopted F_nu transfer is

Fnu_target / Fnu_source =
[(1 + z_target) / (1 + z_source)] *
[D_L(z_source) / D_L(z_target)]^2

Do not multiply an additional Tolman factor on top of a forward spectral/radiometric transformation that already includes the redshift physics.

## Luminosity-evolution scenarios

### E0

No intrinsic luminosity evolution.

Use this as the clean observational-degradation baseline.

### E1J

F444W-only luminosity-evolution sensitivity experiment using eta = 1.02 +/- 0.128.

This is not a per-galaxy evolutionary history and not a complete wavelength-dependent stellar-population model. It is a sensitivity branch.

## Real-mosaic injection policy

A real COSMOS-Web mosaic already contains the observed sky/background/noise realization.

Therefore the main real-context injection should:

- add a deterministic synthetic source to SCI,
- retain the existing background/noise,
- keep the real scene and neighbors,
- not add an independent second sky/background realization,
- not treat i2d VAR_POISSON as a license to generate a second source-Poisson realization.

If a later source-shot approximation is added, label it explicitly as an approximation unless full exposure-level count/variance/resampling provenance has been reconstructed.

## Position-dependent PSF

COSMOS-Web PSFEx is spatially varying.

For NIRCam PSFs:

1. evaluate the PSFEx model at the object/context position;
2. use x_image + 1 and y_image + 1 when passing COSMOS zero-based mosaic coordinates to PSFEx;
3. use GalSim DES_PSFEx;
4. draw with method="no_pixel";
5. preserve signed PSF structure;
6. normalize by signed total flux.

The PSFEx effective PSF already includes pixel response. Applying another detector-pixel response would double count it.

Negative PSF pixels produce a Lenstronomy warning. The warning is expected for these empirical/effective PSFs and was not responsible for the earlier morphology failure.

## Why the custom Sersic renderer was rejected

An early renderer evaluated a homemade elliptical Sersic profile on the image grid, optionally with oversampling, then convolved it with the target PSF.

A noiseless self-recovery test showed a catastrophic example:

- ID 751217 truth n about 2.25
- custom-renderer recovery n about 8.7-8.8

Increasing the custom renderer to 5x oversampling did not solve the problem.

The critical diagnostic was then changed to a closed-loop test in which Lenstronomy generated the truth image using the same numerical model family used by Galight.

## Exact Lenstronomy closed-loop result

Three representative objects were tested:

- ID 751217
- ID 322095
- ID 162363

The exact single-Sersic truth image was created by Lenstronomy ImageModel and then fitted by Galight.

Results:

- 751217: n 2.254607 -> 2.254607
- 322095: n 1.413573 -> 1.413573
- 162363: n 0.774276 -> 0.774276

Median errors in n, Re, and q were effectively zero.

This proves that the Galight/Lenstronomy model convention can recover the exact injected model and that the previous catastrophic bias originated in renderer/fitter inconsistency.

## Perturbed-start convergence result

The same three objects were then initialized deliberately away from truth:

- Re about 30% high
- n about 30% high
- q offset by about 0.12
- centroid displaced by about one native pixel

All three converged back to the correct solution.

Median absolute errors were approximately:

- |delta n| = 2.9e-4
- |delta Re/Re| = 2.5e-4
- |delta q| = 7.2e-5

This is a much stronger optimizer test than the exact-start closed loop.

## B+D identifiability

An exact Lenstronomy B+D truth image was then fitted with:

- B+D
- single Sersic

The B+D truth used disk n=1 and bulge n=4 with exact injected integrated B/T.

### ID 322095

Stable:

- input B/T 0.3031
- recovered B/T 0.3116
- published single n 1.4136
- clean B+D -> single n 1.4313
- disk classification preserved

### ID 162363

Mostly stable:

- input B/T 0.0113
- recovered B/T 0.0059
- published single n 0.7743
- clean B+D -> single n 1.0497
- disk classification preserved

### ID 751217

Strongly non-identifiable:

- input B/T 0.2681
- recovered z=3-clean B/T 0.0924
- z=3 disk Re about 0.42 pixel
- z=3 bulge Re about 0.08 pixel
- published single n 2.2546
- clean z=3 B+D -> single n 8.7976
- disk classification flips

The fit residual can still be tiny. Therefore low residual or optimizer convergence is not proof of component identifiability.

## Native-clean vs z=3-clean comparison

A native clean baseline was created using the same chosen morphology model before redshifting.

### ID 751217

- morphology source band: F115W
- published n: 2.2546
- native B+D -> single n: 1.5255
- z=3 B+D -> single n: 8.7976
- published/input B/T: 0.2681
- native recovered B/T: 0.0771
- z=3 recovered B/T: 0.0924
- disk Re pixels: 1.716 -> 0.418
- bulge Re pixels: 0.333 -> 0.081
- classification: catalog True, native True, z3 False

Interpretation:

- B/T is already non-identifiable at native-clean resolution, so its z=3 B/T should not be interpreted as a physical change.
- the very large native-clean n -> z=3-clean n change is genuinely introduced by the redshift/resolution step.

### ID 322095

- morphology source band: F150W
- published n: 1.4136
- native clean n: 1.4598
- z=3 clean n: 1.4313
- input B/T: 0.3031
- native recovered B/T: 0.3126
- z=3 recovered B/T: 0.3116
- classification remains disk-like

### ID 162363

- morphology source band: F444W
- published n: 0.7743
- native clean n: 1.0499
- z=3 clean n: 1.0497
- input B/T: 0.0113
- native recovered B/T: 0.0084
- z=3 recovered B/T: 0.0059
- classification remains disk-like

Across only these three diagnostic objects, the median native-clean -> z=3-clean n change is small because one severe outlier and two stable cases are being mixed. Do not use this three-object median as a science conclusion.

## Required B/T identifiability flag

The final catalog should contain explicit fields such as:

- bt_native_abs_error
- bt_z3_abs_error
- bt_native_identifiable
- bt_z3_identifiable
- native_disk_re_pix
- native_bulge_re_pix
- z3_disk_re_pix
- z3_bulge_re_pix

The numerical threshold for "identifiable" must be frozen only after the representative clean sweep. A temporary diagnostic tolerance of |delta B/T| <= 0.10 is acceptable for debugging, but should not automatically become the final science cut.

## Context validity

The real-context selector should reject contexts unless, for both target bands used in the fit:

- SCI and ERR shapes match,
- required arrays are finite over the fit region,
- ERR > 0,
- valid fraction is sufficiently high,
- the central target location is valid.

A 0.95 valid-pixel fraction was used successfully in the pilot to eliminate "No valid ERR pixels" failures.

## Neighbor treatment

Current Galight pilot strategy:

- model the nearest segmented neighbors explicitly,
- mask remaining contaminants,
- keep neighbor handling fixed when comparing E0 and E1J for the same context where possible.

Real-context neighbor/crowding bias is a separate layer from clean-model identifiability and should not be mixed into the renderer validation.

## Native Galight validation gate

A small native validation showed reasonable but non-zero offsets between published/catalog structural values and the local fitting pipeline.

This was useful as a pipeline gate, but it does not supersede the exact synthetic closed-loop tests.

The key lesson is that published single-Sersic, B+D, SE++, and Galight products are not interchangeable representations of exactly the same mathematical object.

## Spiral arms

The structural model experiment does not preserve spiral arms.

A separate P1 controlled test found approximately 9-16% suppression in matched spiral-arm amplitude over z about 0.5-3 under controlled degradation, with a smooth control remaining at numerical zero.

Treat spiral-feature survival and parametric structural recoverability as separate diagnostics.

## Production interpretation rules

1. Never call a parameter "recovered" solely because the optimizer converged.
2. Do not interpret B/T changes if the native clean decomposition already fails identifiability.
3. Measure redshift-induced bias relative to the native clean synthetic baseline.
4. Keep E0 and E1J separate.
5. Record component sizes in pixels and relative to PSF scale.
6. Preserve failures, bound hits, and non-identifiable cases as results.
7. Do not silently drop catastrophic objects.
8. Do not clip signed empirical PSFs merely to satisfy a warning.
9. Do not reintroduce the custom homemade Sersic renderer into the production morphology path.
10. Do not launch the full 403 real-background run until the clean sweep and new pilot pass.

## Immediate next experiment

Run a representative clean sweep of about 30 objects spanning source redshift and predicted z=3 component size.

Use the validated Lenstronomy renderer and the native-clean -> z=3-clean chain.

After reviewing the sweep:

- freeze identifiability/failure flags,
- rebuild the real-background pilot,
- run the E0/E1J pilot,
- then scale to GOLD403.
