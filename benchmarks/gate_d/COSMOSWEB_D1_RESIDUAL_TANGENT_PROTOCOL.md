# Gate D1n-i — residual / target-tangent alignment diagnostic

## Purpose

D1n-h established that the location-specific pre-injection residual is causally sufficient to drive the two catastrophic AB=26 D1m solutions: `alpha=0` restores near-truth morphology, and increasing the same residual dose smoothly recovers the D1m failures. However, scalar residual power does not separate failures from controls.

D1n-i asks one narrower question:

**Does the ERR-weighted pre-injection residual at the failure locations project more strongly onto the local Sérsic target-model tangent space than the residuals at the controls?**

This is a local linear identifiability diagnostic. It does not refit the target, change the model, or define a new acceptance threshold.

## Methodological basis

For a least-squares objective, the Jacobian contains the derivatives of the residual vector with respect to model parameters and therefore defines the local parameter-sensitive tangent directions used by the optimizer. A first-order projection of a structured model residual onto those directions is the smallest diagnostic that follows from D1n-h without changing the recovery objective. Galaxy model-fitting literature likewise shows that imperfect morphology models can bias fitted structural parameters through the residual between the real image and the fitted model.

## Frozen design

1. Use the exact four D1n-g/D1n-h AB=26 positions: two catastrophic positions and their near-source/isolated controls.
2. Reconstruct the exact D1m pre-injection scene and residual using the same detection/deblending, selected neighbours, frozen nuisance Sérsic parameters, STPSF, ERR image, and exact-support child mask.
3. Evaluate the injected target at the known truth: AB=26, zero centroid offset, `Re=0.18 arcsec` (6 native pixels), `n=1`, `q=0.65`, `PA=30 deg`.
4. Freeze central finite-difference steps before execution:
   - `log_amp_ratio`: `1e-3`
   - `dx`, `dy`: `1e-3` pixel
   - `log_re`: `1e-3`
   - `n`: `1e-3`
   - `q`: `1e-4`
   - `pa`: `1e-2` degree.
   These are derivative-evaluation steps, not optimizer tolerances or recovery criteria.
5. Construct the seven target-source Jacobian columns on the 65x65 patch. Do not include target background terms in this target tangent.
6. Apply the exact D1m valid-pixel mask and ERR weighting.
7. Because the target fit has a free planar background, remove the weighted planar-background subspace from both the residual vector and every target-Jacobian column before measuring target alignment. This prevents a simple sky plane from being counted as morphology-sensitive residual structure.
8. Using the background-residualized target Jacobian:
   - record its singular values, numerical rank and condition number;
   - solve the unregularized first-order least-squares projection with `numpy.linalg.lstsq`;
   - record the fraction of background-residualized weighted residual power lying in the target tangent;
   - record per-parameter cosine alignment;
   - record the predicted first-order parameter shift per unit residual dose.
9. Cross-check the first-order prediction against the observed small-dose response from the immutable D1n-h artifact using `(theta(alpha=0.25)-theta(alpha=0))/0.25`. Report per-parameter predicted and observed derivatives; do not introduce a pass/fail threshold after seeing them.
10. Preserve rank deficiency or extreme condition numbers as scientific results. Do not regularize, drop parameters, widen bounds, change finite-difference steps after seeing results, or substitute a different optimizer.
11. No target recovery fit is performed. No noise, source shot noise, background, Tolman factor or PSF modification is added. SCI/ERR/WHT are not modified.

## Interpretation

- Stronger tangent-space projection at the catastrophic locations, especially with first-order shifts consistent in sign/scale with the D1n-h small-dose response, would explain why residual morphology rather than scalar residual amplitude drives the failures.
- Similar tangent projection at failures and controls would imply that higher-order/nonlinear scene structure, not local first-order identifiability alone, is required.
- A poorly conditioned tangent is itself evidence of local structural non-identifiability and is retained rather than repaired post hoc.

This diagnostic does not authorize production implementation or a new morphology acceptance band.
