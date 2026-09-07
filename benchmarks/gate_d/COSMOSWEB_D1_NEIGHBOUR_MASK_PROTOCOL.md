# Gate D1g — fixed neighbour/source-pixel mask diagnostic

Frozen before inspecting D1g scientific output.

## Purpose

D1e showed large morphology failures and bound hits when a single Sérsic + planar background model was fit directly to synthetic sources embedded in the literal real COSMOS-Web scene. D1f then recovered the same injected sources essentially exactly after subtracting the pre-injection scene, showing that the renderer/fitter pair is numerically identifiable when scene contamination is removed by construction. D1g therefore tests a narrower question: how much of the D1e failure is removed by excluding source-contaminated pixels identified from the pre-injection scene, while preserving the same injection, PSF, parameter bounds, optimizer, and real ERR weights.

This is a diagnostic control. It is **not** a final survey-recovery method, not blind detection, not simultaneous neighbour modelling, and not literal survey-source reproduction.

## Frozen mask definition

1. Use `SCI_ORIG` and `ERR` from the frozen successful D1d injection artifact.
2. Estimate the background with the exact D1c iterative median/MAD routine.
3. Define scene/source pixels exactly as D1c did: `(SCI_ORIG - background_median) / ERR > 5.0`.
4. Apply **no dilation**, no deblending threshold change, no hand editing, and no target-specific unmasking.
5. The mask is derived only from the pre-injection scene. It cannot use the injected image to decide what to mask.

## Recovery contract

- Reuse the D1e fitter unchanged except for an optional boolean exclusion mask. With no mask, D1e behavior is identical.
- Keep the frozen D1e bounds: centroid ±2 px, `Re=1–20 px`, `n=0.3–6`, `q=0.2–1`, `PA=-90..90 deg`, positive amplitude.
- Keep the same linear weighted least squares, same 65×65 patch, same pinned STPSF construction, and same real ERR plane.
- Pixels masked by the pre-injection scene are excluded from the residual vector. They are never silently restored around the injected target.
- The existing requirement that at least 80% of patch pixels carry valid weights remains unchanged. If masking violates that requirement, the case remains an explicit `insufficient_valid_weight_pixels` failure.
- Preserve optimizer failures, low-S/N failures, bound hits, mask fractions, and finite/non-finite outcomes as observables.

## Physical semantics

No Tolman dimming is applied in D1g, because the frozen injected fluxes already define the observed-frame experiment. No extra background or source-shot noise is added. No PSF-transfer operation is introduced. The target PSF treatment is exactly the same declared STPSF-based synthetic-source PSF used in D1d–D1f; it is not claimed to be literal COSMOS-Web source PSF reproduction.

## Interpretation

A workflow success means only that the diagnostic executed and produced an artifact. Scientific interpretation must compare D1g with D1e and D1f. Improvement under masking would support scene/neighbour contamination as an important driver, but would not establish that masking is the correct production solution. If significant failures remain, the next justified diagnostic is explicit simultaneous neighbour/source modelling or a more survey-faithful deblending experiment, not relaxed bounds or acceptance criteria.
