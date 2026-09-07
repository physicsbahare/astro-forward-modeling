# Passive Spiral P1 — spiral-feature survival result

Status: **SOFTWARE PASS / SCIENTIFIC RESULT: RESOLUTION-ONLY ARM SUPPRESSION MEASURED**

This receipt interprets the frozen P1 protocol only. It does not define a passive-spiral classifier, a universal spiral-detection threshold, or literal COSMOS-Web recovery.

## Workflow provenance

- Workflow: `passive-spiral-p1`
- Run: `34025358730`
- Job: `101465240289`
- Branch head: `a99facba1d116ff74e67d628ae3192e364491077`
- Conclusion: `success`
- Regression tests: `3 passed in 1.22 s`
- Artifact: `9986875575` (`passive-spiral-p1`)
- Artifact ZIP SHA256: `ce179bec060adf4c7cd3a50b1de4e88d5022227f481fc2e288520e6f040f281d`
- Artifact size: `2194 bytes`
- Python: `3.12.14`
- NumPy: `2.5.2`
- SciPy: `1.18.1`

Workflow success is software success only; the numerical trend below is the scientific result.

## Frozen exclusions confirmed by the run

- no added target/background noise;
- no source-shot noise;
- no intrinsic size evolution;
- no intrinsic luminosity evolution;
- no extra Tolman factor;
- no PSF sharpening/deconvolution;
- no segmentation/classification threshold.

The same-renderer artificial/direct comparison is an identifiability/numerical control, not independent cross-code validation.

## Numerical result

The latent matched two-arm logarithmic-spiral amplitude is constant by construction:

`A_sp,latent = 0.18430147916037837`.

| z_target | target PSF FWHM [kpc] | direct A_sp | artificial A_sp | direct/latent retention | suppression vs latent | artificial/direct | normalized L1 | flux rel. diff |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.5 | 0.88511 | 0.1676313 | 0.1675750 | 0.90955 | 9.05% | 0.999664 | 0.000254 | -0.000178 |
| 1.0 | 1.16126 | 0.1565073 | 0.1564548 | 0.84919 | 15.08% | 0.999665 | 0.002682 | -0.002621 |
| 2.0 | 1.21378 | 0.1541393 | 0.1540874 | 0.83634 | 16.37% | 0.999663 | 0.002845 | -0.002783 |
| 3.0 | 1.11698 | 0.1588214 | 0.1587701 | 0.86175 | 13.83% | 0.999677 | 0.000340 | -0.000281 |

The smooth-control matched-arm amplitudes remain at numerical-zero scale (`~10^-17`) on both direct and artificial paths, so the transfer does not manufacture a detectable matched spiral pattern in the axisymmetric control.

## Scientific interpretation

1. **Known spiral structure is measurably suppressed by the observation operator even without noise.** The controlled disk+bulge scene retains the same intrinsic structure by construction, yet its matched arm amplitude loses about 9–16% after target angular resolution is applied.

2. **The strongest suppression occurs at z=2 in this frozen geometry, not monotonically at the highest redshift.** This tracks the physical size of the fixed `0.145 arcsec` target PSF: `0.885, 1.161, 1.214, 1.117 kpc` at z=`0.5,1,2,3`. The z=3 rebound is therefore an angular-diameter-distance/resolution effect in this controlled setup, not intrinsic morphological evolution.

3. **The artificial-redshift path reproduces the direct-target control extremely closely.** The arm-amplitude ratio is about `0.99966–0.99968`, with absolute amplitude differences around `5.1–5.6e-5`. The maximum normalized image L1 difference is `0.002845` and the largest total-flux relative difference in magnitude is `0.002783` (~0.28%). This supports the internal transfer implementation for this analytic scene and convention; it is not an independent external-code validation.

4. **No post-hoc detectability statement is made.** P1 does not establish whether a human, Sérsic/B/T cut, segmentation algorithm, or ML classifier would call any target a spiral. It isolates only the resolution/operator loss of a known matched spiral feature.

5. **P1 is a lower-complexity/noiseless floor, not a survey completeness estimate.** Real backgrounds, correlated noise, crowding, empirical PSFs, segmentation and passive-galaxy SED effects can only be addressed in separately declared experiments.

## Gate consequence

P1 adds a non-redundant Passive-Spiral failure-mode check to Gate C: global disk structure alone is insufficient to guarantee preservation of spiral-arm information under artificial redshifting. The operator implementation passes its same-scene direct-target numerical control while the science statistic itself shows real resolution-driven information loss.

No historical FERENGI, Paulino-Afonso, Yu, or Gate-D result is modified.

## Next non-redundant decision

Do not add another paper-specific artificial-redshifting reproduction merely for coverage. The next useful Passive-Spiral step should test whether the P1 arm-information loss is amplified by **literal real-survey context** (background/crowding/segmentation) using the already frozen Gate-D L1 rules: inject into SCI only, leave ERR/WHT unchanged, add no new sky noise, and keep any source-shot experiment separate. Such an experiment requires its own frozen protocol and must not be interpreted as a production classifier.
