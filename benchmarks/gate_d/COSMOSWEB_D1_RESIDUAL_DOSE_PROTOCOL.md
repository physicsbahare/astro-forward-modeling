# Gate D1n-h — frozen pre-injection residual-dose causal audit

## Purpose

D1n-g shows that five very different deterministic starts, including the exact injection-truth oracle, all converge to the same catastrophic D1m morphology at the two failure locations. The remaining question is therefore not primarily optimizer initialization. D1n-h asks:

**How does the unchanged D1m recovery respond as only the already-existing pre-injection scene-model residual is continuously restored from zero to its literal real-mosaic value?**

This is an injection-only causal diagnostic. Intermediate residual doses are synthetic diagnostic scenes, not literal survey reproduction and not a proposed production preprocessing operation.

## Scientific/software context

Maintained SourceXtractor++ documentation explicitly exposes model, residual, background and variance check images because residual structure is a necessary diagnostic of model-fitting measurements; it also notes that model fitting is sensitive to neighbour contamination and requires accurate PSF models. Recent JWST decomposition work likewise finds that substantial structural-parameter changes can occur with little change in fit quality when a simple parametric profile does not uniquely represent the observed scene. D1n-h therefore measures the response to the frozen real residual directly rather than changing segmentation, bounds, PSF or optimizer settings.

## Frozen sample and residual doses

Use the same four AB=26 locations frozen before D1n-g:

1. near-source index 0 `(168,66)`, catastrophic;
2. relatively-isolated index 1 `(69,195)`, catastrophic;
3. near-source index 1 `(379,254)`, control;
4. relatively-isolated index 0 `(358,97)`, control.

For each location use residual-dose factors exactly:

`alpha = [0.0, 0.25, 0.5, 0.75, 1.0]`.

No additional alpha may be added after seeing results.

## Frozen construction

For each location:

1. Recompute the exact D1m pre-injection neighbour fit on `SCI_ORIG`, with the same detection/deblending, selected nuisance children, nuisance bounds, STPSF, ERR weighting, masks and prefit optimizer.
2. On the 65x65 target patch define the frozen pre-injection model
   `M0 = frozen_neighbour_source + fitted_prefit_background_plane`.
3. Define the literal pre-injection residual
   `R = SCI_ORIG - M0`.
4. Recover the exact injected-only difference
   `D = SCI_INJECTED - SCI_ORIG`.
5. Construct only for diagnosis
   `SCI_alpha = M0 + D + alpha * R`.
   - `alpha=0` is a fitted-scene + exact-injection oracle with the real residual removed;
   - `alpha=1` exactly reconstructs the literal injected D1d patch (up to floating-point roundoff);
   - intermediate alpha values are synthetic residual-dose diagnostics and must not be described as survey realizations.
6. ERR is never rescaled or modified. No new sky noise, source shot noise or covariance term is generated. Existing residual/noise structure is only attenuated for alpha<1; it is never added twice.
7. Fit every `SCI_alpha` with the exact D1m target objective and **only the D1m default start**. D1n-g already demonstrated that start choice is not the controlling failure variable.
8. Keep `scipy.optimize.least_squares`, TRF, linear loss, `x_scale="jac"`, default ftol/xtol/gtol and `max_nfev=500`.
9. Keep all target/nuisance bounds, masks, support, STPSF and planar target-fit background unchanged.
10. Preserve every optimizer failure, bound hit, centroid excursion and morphology loss.

## Machine-readable outputs

For every location and alpha record:

- recovered magnitude and delta-mag;
- Re, n, q, PA;
- dx/dy and centroid excursion;
- optimizer status/message, nfev, chi-square and reduced-chi-square proxy;
- target bound hits;
- residual-dose alpha;
- robust and RMS norms of the injected difference and frozen pre-injection residual;
- an exact-reconstruction check at alpha=1.

For each location report raw parameter sequences versus alpha. Do not fit or define a post-hoc transition threshold and do not introduce an acceptance band.

## Interpretation

- If alpha=0 is truth-like and the catastrophic morphology emerges progressively as alpha approaches 1 only in the failure locations, the already-existing scene-model residual is causally sufficient to drive the D1m failure under the frozen objective.
- If catastrophic morphology persists near alpha=0, then the frozen fitted scene/target parameterization itself remains implicated even after removing the pre-injection residual.
- If controls degrade similarly with alpha, the effect is general real-scene contamination rather than specific to the two catastrophic locations.
- If the response is discontinuous, retain that as practical objective non-identifiability; do not tune alpha sampling after the fact.

No residual subtraction or attenuation is authorized for production by this diagnostic. No production framework code is authorized.
