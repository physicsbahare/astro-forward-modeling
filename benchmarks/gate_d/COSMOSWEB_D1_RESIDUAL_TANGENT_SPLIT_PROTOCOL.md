# Gate D1n-j — causal tangent/orthogonal residual split

## Purpose

D1n-h showed that the location-specific pre-injection residual is causally sufficient to drive the two catastrophic AB=26 D1m recoveries. D1n-i then showed that the catastrophic residuals place a larger fraction of their ERR-weighted, background-residualized power in the local seven-parameter Sérsic target tangent than the controls, while the tangent condition number is similar across failures and controls.

D1n-j asks the next minimal causal question:

**Is the tangent-aligned component of the real pre-injection residual itself sufficient to drive the morphology bias, or is the much larger orthogonal residual/nonlinear interaction required?**

This is an injection-only diagnostic decomposition. It is not a production residual correction, denoiser, acceptance cut, or literal reproduction of a different survey observation.

## Frozen design

1. Use the exact four D1n-g/h/i AB=26 positions: two catastrophic cases and their near-source/isolated controls.
2. Reconstruct the exact D1m pre-injection scene, frozen neighbours, planar prefit, exact-support mask, declared STPSF and ERR weighting.
3. Evaluate the seven target Jacobian columns at the known injection truth using the exact D1n-i finite-difference steps.
4. In ERR-weighted valid-pixel space, remove the same three-dimensional planar-background subspace from both the real pre-injection residual and every target-Jacobian column.
5. Solve the same unregularized least-squares projection used by D1n-i. Freeze the decomposition into:
   - `none`: no valid-pixel residual;
   - `tangent_only`: the target-tangent projection;
   - `orthogonal_only`: the background-residualized residual minus the tangent projection;
   - `background_residualized_full`: tangent + orthogonal;
   - `original_full`: the original real residual, including any component parallel to the free planar-background subspace.
6. Convert weighted components back to image units only by multiplying by the frozen ERR values on valid pixels. Masked pixels retain their original injected-patch values because they are excluded from the objective.
7. `original_full` must reproduce the literal D1d injected patch on valid pixels to the inherited numerical reconstruction tolerance. `background_residualized_full` must equal `tangent_only + orthogonal_only` in weighted valid-pixel space to numerical precision.
8. Recover the target for every mode with the exact D1m/D1n-h target model, start, bounds, TRF optimizer, linear loss, `x_scale=jac`, ERR weighting and `max_nfev=500`.
9. Record optimizer success/failure, target bound hits, centroid excursion, magnitude, Re, n, q, PA, chi-square, component weighted power, tangent/orthogonal inner-product checks, and reconstruction identities. Preserve all failures and boundary solutions.
10. No regularization, Jacobian truncation, parameter dropping, altered finite-difference step, altered mask, new noise, source shot noise, Tolman factor, PSF modification/sharpening, background addition, ERR/WHT change, or post-hoc acceptance threshold is allowed.

## Interpretation

- If `tangent_only` reproduces most of the catastrophic bias while `orthogonal_only` remains near truth, the low-power tangent-aligned residual is causally sufficient and D1n-i provides a direct local explanation.
- If `orthogonal_only` is also strongly biased, or only the combined residual becomes catastrophic, higher-order/nonlinear interaction with the nominally orthogonal scene residual is essential.
- Similar behavior in controls would weaken any failure-specific interpretation.
- Differences between `background_residualized_full` and `original_full` quantify whether the residual component parallel to the free planar background matters; it must not be interpreted as evidence to alter the background model post hoc.

No outcome authorizes production framework implementation or a new morphology acceptance band.
