# Gate D1n-c — AB=26 background / residual-context audit

Protocol version: `D1n-c-v1` (frozen before execution).

## Purpose

D1m removed all AB=26 target-bound hits by fitting neighbouring Sérsic components on `SCI_ORIG` and freezing them, yet two severe interior morphology/flux failures remained. D1n-c asks whether those failures live in unusually structured real-mosaic backgrounds/residuals or coverage regions.

To avoid a post-hoc "bad-case-only" comparison, **all nine frozen AB=26 positions are audited**. Existing D1m recovery outcomes are attached for comparison; no target is refitted and no new success/failure threshold is defined.

## Frozen design

1. Inputs are the exact D1d injected-scene artifact and exact D1m machine-readable `summary.json`.
2. Use `SCI_ORIG`, ERR and WHT from D1d. No plane is modified.
3. Reconstruct the same D1m pre-injection scene decomposition:
   - exact D1k/D1l frozen detection/deblending;
   - same candidate-neighbour selection;
   - at most three nuisance Sérsic components;
   - same declared STPSF;
   - same nuisance bounds and prefit optimizer (`TRF`, linear loss, `x_scale=jac`, `max_nfev=500`);
   - same exact-support mask for remaining children.
4. Audit **all nine** AB=26 locations. Prefit failures and nuisance-bound hits are retained.
5. For each 65x65 patch record:
   - valid/masked fraction and selected/masked child labels;
   - robust raw-SCI median/MAD;
   - ERR and WHT median, 5th/95th percentiles and coefficient of variation;
   - fitted D1m background plane;
   - residual `SCI_ORIG - frozen_neighbour_scene - fitted_plane`;
   - residual median/MAD and ERR-standardized median/MAD/std;
   - standardized residual correlations at ±1/±2 pixel cardinal lags and one diagonal lag;
   - a declared 3-pixel Gaussian low-frequency residual variance fraction;
   - weighted quadratic residual structure and its variance-explained fraction.
6. Attach the pre-existing D1m AB=26 recovery values: magnitude, Re, n, q, centroid excursion, target-bound hits, reduced-chi-square proxy and nuisance-bound flag.
7. For navigation only, report the two rows with largest absolute D1m Δmag. This ranking does **not** define "catastrophic", exclude any row, or create an acceptance band.
8. Do not refit targets, change target/nuisance bounds, tune segmentation/support, add noise, modify ERR/WHT, apply Tolman dimming, or sharpen any PSF.

## Interpretation

The scientific comparison is descriptive across the full nine-location set. If the severe D1m outcomes coincide with conspicuously larger residual correlation, smooth residual power, quadratic structure, or WHT/ERR heterogeneity, background/scene residual structure becomes a leading explanation. If they do not, the remaining failure is more likely tied to target morphology identifiability, local unmodelled source structure, or PSF/effective-PSF mismatch. Either outcome is retained; no thresholds are loosened to make the recovery look successful.
