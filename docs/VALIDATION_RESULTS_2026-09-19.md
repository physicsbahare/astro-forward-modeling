# GOLD403 Validation Results - 2026-09-19

This file is the frozen numerical receipt for the current renderer/fitter validation state.

## 1. Custom-renderer noiseless self-recovery

A custom analytic Sersic renderer was tested with noiseless target-PSF-convolved images.

Representative result:

- ID 751217 recovered single-Sersic n about 8.7-8.8 instead of truth about 2.25.
- 5x oversampling did not materially improve the failure.
- Median errors over three diagnostic objects remained roughly:
  - |delta n| ~ 0.52
  - |delta Re/Re| ~ 0.074
  - |delta q| ~ 0.012
  - |delta B/T| ~ 0.24
  - bulge Re fractional error ~ 0.89

Conclusion: the custom renderer was rejected for production morphology work.

## 2. Exact Lenstronomy single-Sersic closed loop

Truth images were generated with Lenstronomy ImageModel using the same numerical convention used by Galight.

| ID | z_source | Re/pixel | Re/F444W PSF | truth n | fit n | delta n |
|---:|---:|---:|---:|---:|---:|---:|
| 751217 | 0.1009 | 5.586 | 1.156 | 2.254607 | 2.254607 | 0 |
| 322095 | 0.8709 | 3.892 | 0.805 | 1.413573 | 1.413573 | 0 |
| 162363 | 2.9478 | 9.335 | 1.931 | 0.774276 | 0.774276 | 0 |

Median absolute errors:

- delta n = 0
- delta Re/Re = 0
- delta q = 0

Conclusion: the Galight/Lenstronomy convention is internally consistent.

## 3. Perturbed-start convergence

Starting values were deliberately moved away from truth:

- Re x 1.30
- n x 1.30
- q changed by about 0.12
- center offset by about (+1, -1) native pixels
- two PSO repeats

Results:

| ID | truth n | start n | fit n | truth Re | start Re | fit Re | truth q | start q | fit q |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 751217 | 2.2546 | 2.9310 | 2.2529 | 0.1676 | 0.2179 | 0.1675 | 0.2866 | 0.4066 | 0.2865 |
| 322095 | 1.4136 | 1.8376 | 1.4138 | 0.1168 | 0.1518 | 0.1167 | 0.3717 | 0.4917 | 0.3718 |
| 162363 | 0.7743 | 1.0066 | 0.7746 | 0.2800 | 0.3641 | 0.2801 | 0.6377 | 0.7577 | 0.6377 |

Median absolute recovery errors:

- |delta n| = 2.87e-4
- |delta Re/Re| = 2.49e-4
- |delta q| = 7.16e-5

All 3/3 passed the diagnostic convergence criteria.

## 4. Exact B+D truth validation at z=3

The exact truth scene used:

- disk n = 1
- bulge n = 4
- exact integrated injected B/T
- Lenstronomy rendering
- target position-dependent PSF
- no background/noise realization

### ID 751217

- z = 0.1009
- z3 disk Re = 0.418 pixel
- z3 bulge Re = 0.081 pixel
- input B/T = 0.2681
- recovered B/T = 0.0924
- published single n = 2.2546
- clean B+D -> single n = 8.7976
- catalog disk = True
- clean model disk = False

This is the important non-identifiable case.

### ID 322095

- z = 0.8709
- z3 disk Re = 3.587 pixels
- z3 bulge Re = 3.228 pixels
- input B/T = 0.3031
- recovered B/T = 0.3116
- published single n = 1.4136
- clean B+D -> single n = 1.4313
- classification preserved

### ID 162363

- z = 2.9478
- z3 disk Re = 9.947 pixels
- z3 bulge Re = 2.611 pixels
- input B/T = 0.0113
- recovered B/T = 0.0059
- published single n = 0.7743
- clean B+D -> single n = 1.0497
- classification preserved

Three-object diagnostic medians:

- |delta B/T| = 0.00852
- |delta disk Re/Re| = 0.00375
- |delta bulge Re/Re| = 0.2298
- median |clean B+D single n - published n| = 0.2754
- classification agreement = 2/3

Do not use these medians as population science. They hide the severe compact-component failure in 751217.

## 5. Native-clean -> z=3-clean baseline

This comparison separates representation mismatch from actual artificial-redshift degradation.

### ID 751217

Morphology band: F115W

- published n = 2.2546
- native B+D -> single n = 1.5255
- z3 B+D -> single n = 8.7976
- published/input B/T = 0.2681
- native recovered B/T = 0.0771
- z3 recovered B/T = 0.0924
- disk Re pixels: 1.716 -> 0.418
- bulge Re pixels: 0.333 -> 0.081
- classification: catalog True -> native True -> z3 False

Interpretation:

- B/T is already non-identifiable in the native synthetic model.
- the large native-clean n -> z3-clean n jump is genuinely introduced by redshift/resolution degradation.

### ID 322095

Morphology band: F150W

- published n = 1.4136
- native n = 1.4598
- z3 n = 1.4313
- input B/T = 0.3031
- native B/T = 0.3126
- z3 B/T = 0.3116
- disk Re pixels: 3.563 -> 3.587
- bulge Re pixels: 3.207 -> 3.228
- classification remains True

### ID 162363

Morphology band: F444W

- published n = 0.7743
- native n = 1.0499
- z3 n = 1.0497
- input B/T = 0.0113
- native B/T = 0.0084
- z3 B/T = 0.0059
- disk Re pixels: 9.896 -> 9.947
- bulge Re pixels: 2.597 -> 2.611
- classification remains True

Three-object diagnostic median absolute changes:

- |published n - native-model n| = 0.27564
- |native-model n - z3-model n| = 0.02842
- |published B/T - native recovered B/T| = 0.00952
- |native B/T - z3 B/T| = 0.00253

Again, these three-object medians are diagnostic only.

## 6. Real-background pilot before renderer correction

The model-based real-context pilot reached 9/9 successful fits after adding the context-quality filter, but morphology was unstable in some objects.

Those results are now classified as debugging history because they were generated before the renderer/fitter convention was fixed.

They must be rerun with the validated Lenstronomy renderer before scientific use.

## 7. Current acceptance state

Validated:

- exact single-Sersic rendering convention
- perturbed-start optimizer recovery
- signed position-dependent PSF compatibility in the controlled test
- existence of structural non-identifiability independent of background noise
- need for a native-clean baseline
- need for B/T identifiability flags

Not yet validated for production:

- empirical identifiability threshold across representative GOLD403 parameter space
- real-background E0/E1J pilot using the corrected renderer
- 403-object completeness/classification results

## 8. Next frozen checkpoint

The next required receipt is:

`clean_native_to_z3_identifiability_sweep_30.csv`

Do not start the full 403 real-background production run until that sweep has been reviewed.
