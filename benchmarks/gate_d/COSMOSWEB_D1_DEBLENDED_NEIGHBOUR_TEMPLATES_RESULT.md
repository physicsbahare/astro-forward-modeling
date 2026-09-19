# Gate D1k result receipt — deblended neighbour templates

**Branch HEAD that launched the diagnostic:** `02349c087f9887fddf5b52644494215aff3a8798`  
**D1k workflow run:** `33968383371` — `completed / success`  
**Verification-suite run:** `33968383448` — `completed / success`  
**Artifact:** `gate-d-cosmosweb-deblended-neighbour-templates` (`9970169818`)  
**Artifact digest:** `sha256:b24cf2fb0243e1509d171186aa1fe16a36a65a092b33ae73e14c31d5184b100c`

Workflow success here means only that the frozen diagnostic executed successfully. It is **not** a morphology-recovery success claim.

## Frozen diagnostic

D1k kept the pre-injection parent detection/support fixed at the D1c/D1g/D1h definition,
`(SCI_ORIG - robust_background_median) / ERR > 5` with 8-connectivity. Photutils 3.0.0
partitioned only those already-detected parent pixels using `n_pixels=3`, `n_levels=32`,
`contrast=0.001`, exponential mode, and 8-connectivity. Each child was represented by a
non-negative-amplitude empirical observed-space template and was not PSF-convolved again.
The target renderer, STPSF, 65x65 patch, ERR weighting, linear loss, and all target bounds
were unchanged.

The real scene contained 43 frozen parent components. Deblending produced 51 children:
4 parents split, and the largest split contained 7 children. Parent support was unchanged.

## Direct result

All 18 target optimizations returned finite solutions and optimizer success, but 13/18
target fits still hit at least one target bound. The split by injected brightness was:

| brightness | target bound hits |
|---|---:|
| AB=26 | 5/9 |
| AB=29 | 8/9 |

AB=29 remains the deliberately low-S/N stress regime; no criterion or bound was relaxed to
rescue it.

For the informative AB=26 rows, medians were:

| placement | bound hits | median Δmag | median Re [arcsec] | median n | median q | median centroid radius [pix] | median neighbour templates |
|---|---:|---:|---:|---:|---:|---:|---:|
| near-source | 3/3 | -1.2598 | 0.3779 | 1.931 | 0.879 | 1.463 | 1 |
| intermediate | 2/3 | -0.4293 | 0.3207 | 0.567 | 0.429 | 2.562 | 4 |
| relatively isolated | 0/3 | -0.0123 | 0.1910 | 1.061 | 0.621 | 0.899 | 0 |

The isolated median remains close to truth, but this should not be over-read: isolated
placement index 1 is a large non-bound-hit failure (`Δmag≈-1.011`, `Re≈0.600"`,
`n≈3.106`, `q≈0.824`). Bound-hit counts therefore do not capture all scientific failures.

## Comparison to the preceding real-scene diagnostics

The same frozen real D1d injection artifact was used throughout. The table below reports
global target-bound-hit counts plus AB=26 median magnitude/size recovery in the two
crowded regimes.

| diagnostic | target bound hits | near Δmag / Re["] | intermediate Δmag / Re["] |
|---|---:|---:|---:|
| D1e forced position | 14/18 | -2.695 / 0.463 | +1.530 / 0.115 |
| D1g fixed neighbour mask | 13/18 | -1.006 / 0.262 | -0.943 / 0.544 |
| D1h simultaneous empirical templates | 13/18 | -1.260 / 0.378 | -0.439 / 0.326 |
| D1i support growth = 2 px | 12/18 | -0.913 / 0.269 | -0.727 / 0.292 |
| D1j moment-Gaussian templates | 13/18 | -0.963 / 0.227 | -0.844 / 0.544 |
| D1k deblended empirical templates | 13/18 | -1.260 / 0.378 | -0.429 / 0.321 |

D1i's 2-pixel row is shown because it had the lowest global bound-hit count, but the full
predeclared support-growth experiment was non-monotonic (0/2/4 pixels gave 13/12/13
bound-hit fits and changed the failure topology by placement class). It is not evidence that
a larger support radius is a general solution.

## Scientific decision

D1k does **not** satisfy the predeclared requirement of coherent improvement in both the
near-source and intermediate AB=26 regimes without damage to controls. It improves the
intermediate median relative to D1j, but the near-source median reverts to the poorer D1h
solution, and the global target-bound-hit count remains 13/18.

Therefore no further segmentation-threshold or support-radius tuning is justified. The next
diagnostic is a limited simultaneous **parametric neighbour morphology** experiment, with
its design frozen before seeing its output. It keeps the target model and target bounds
unchanged and tests whether the missing degree of freedom is neighbour shape rather than
neighbour identity/support.
