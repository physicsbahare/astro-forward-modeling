# Frozen mass–redshift analysis protocol (2026-10-12)

Scope: observed COSMOS2025 mass/redshift/SFR, frozen native paired-band morphology
and dual passive labels. No fitting, ML, sample retuning or recovery correction.
The original 39 master cells are preserved; only the new section is executed.

1. Verify cached parent provenance and exact GOLD403 membership. Reconcile all
   one-dimensional aggregate counts with published tables. Reuse original bin
   edges z=[0,.5,1,1.5,2,2.5,3], mass=[9.5,10,10.5,11,11.5,12,13].
2. Report every 2D cell and five binomial estimands (Wilson 95%). Denominator<20
   is sparse; numerator<5 or complement<5 is low-event support, even if Wilson
   intervals remain valid. Never impute unknown morphology as non-disk.
3. Standardize on bins present at all six z intervals: measurable N>=50 AND
   passive measurable N>=20. This denominator-only rule selects mass10–11.
   Fix reference weights to pooled measurable mass counts. Use 4000 stratified
   multinomial draws, four joint passive/disk states per cell, seed20261012.
   The effective standardized disk/passive rate is standardized PD/all divided
   by standardized P/all; averaging D/P with unrelated weights violates the
   decomposition. Report endpoint differences and symmetric additive (Shapley)
   passive/disk contributions with joint bootstrap uncertainty.
4. Simple logistic summaries: PD/all vs continuous z + mass-bin intercepts;
   D/P vs continuous mass + z-bin intercepts; P/all vs z + mass-bin intercepts.
   Restrict to supported cells; report ordinary and tile-cluster intervals,
   nonlinearity/observational-eligibility caveats, Holm adjustment over the three
   directional questions plus matched SFR comparison. No causal interpretation.
5. Sensitivities: deterministic coarse z=[0,1,2,3], mass=[9.5,10.5,11.5,13];
   fixed reference standardization thresholds10/20/50 passive; eligibility/
   magnitude/WHT/photometric-redshift-quality subsets; 100 independent Gaussian
   mass/z perturbations inferred from 68% interval half-widths, labels fixed.
   These perturbations are a bin-migration diagnostic, not posterior propagation
   of correlated SEDs, passive labels or changing morphology-band assignments.
6. Reuse saved M/L limits with receipt verification. Retain mass-boundary and
   F444W<27.5 sensitivity separately; no validated mass-complete claim or weights.
7. SFR: one-to-one optimal nearest matching without replacement, calipers0.1dex
   and0.1z; squared standardized distance, deterministic IDs/ties. Only matched
   disks and measurable passive non-disks (non-disk does not mean pure bulge).
   Report balance, paired mean and median contrast, 4000 pair-bootstrap intervals,
   sign-flip permutation for mean (20000 draws), within-cell medians16–84% and
   floor-sensitive pair exclusion. Posterior endpoints are not censoring flags.
8. Six static PDF/PNG figures, aggregate tables, methods/results report, code/input/
   output SHA256 manifest and notebook section. Publish compact artifacts only.

Interpret after calculations; no bin/rule changes driven by favorable outcomes.
