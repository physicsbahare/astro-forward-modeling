# Limitations and required science gates

Status: PARTIAL SCIENTIFIC COMPLETION, not final population calibration.

1. **B/T real-context calibration remains open.** All eight disputed cases are
   repeated recovery outcomes; two cross the boundary between contexts. Multiple
   contexts/seeds and representative passive/non-passive morphology populations
   are required to estimate classification probabilities. No bound hit, high S/N
   or low residual alone proves identifiability. Three trials per disputed case
   cannot estimate a population confusion matrix.
2. **Requested and rendered truth must match.** The original builder clips three
   GOLD91 radii. Freeze a representation that can render the intended model
   without hidden clipping, test appropriate fit bounds, retain impossible cases
   explicitly, and establish a matching native-clean interpolated baseline.
   The normalization helper repair is numerically validated but not a license
   to rerun all 403 before these representation gates.
3. **Spectral methodology must be reconciled.** The GOLD91 effective-wavelength
   scalar brightness method differs from frozen full-throughput R3. The integrated
   comparison is validated, but its flux changes must be propagated into
   measurement/classification recovery, with explicit spectral failures and
   negative coefficients. No old result is silently promoted.
4. **Native population completeness is uncalibrated.** The parent catalog exists
   and GOLD403 membership is exactly reproducible. What is missing is a
   depth/footprint-aligned stellar-mass completeness calculation and calibrated
   detection/measurement/classification selection probabilities over the actual
   passive and star-forming denominators. A selected narrow-z sample injected
   only at z=3 cannot supply those corrections. Survey detection comparisons
   are depth-dependent in the [catalog paper](https://arxiv.org/html/2506.03243v1);
   a generic completeness number is not substituted for this sample.
5. **SFR floor and censoring.** Catalog posterior intervals are not direct limits.
   Recover or calibrate an appropriate censoring/model-prior treatment before
   claiming physical passive-SFR medians or precise distances below the main
   sequence. The reported offset tables are conditional SED-model summaries.
6. **Uncertainties beyond counting.** Redshift/mass migrations, fit covariance,
   resampled-noise correlations, field variance, AGN incompleteness and threshold
   selection must be included before intrinsic demographics. Current Wilson and
   bootstrap intervals have explicit conditional scopes. No inverse-probability
   correction is applied outside validated support.

The source-by-source table preserves all 403 objects, eight unsupported
morphology brackets, disputed B/T cases, clipped truth and not-run corrected
states. The historical 806-case ERROR rows remain untouched. Final corrected
403 production is intentionally not launched through these gates. The paper
can currently defend validated numerical methods, the reproducible selected
sample, qualified observed conditional fractions and recovery sensitivity. It
cannot defend intrinsic morphology evolution or a completeness-corrected cosmic
passive-disk fraction.
