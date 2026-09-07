# Gate D1f — paired-difference numerical recovery control

Frozen before inspecting D1f results.

## Motivation

D1e succeeded as software but did not demonstrate scientific recovery: all 18 optimizations returned finite solutions, while 14/18 hit at least one bound and the strongest failures tracked real-scene contamination/crowding. We therefore need to separate two hypotheses without changing any D1e tolerance, bound, PSF, or acceptance rule:

1. the rendering/fitting operator is itself unable to recover the injected Sérsic model; or
2. the operator is numerically identifiable, but a single Sérsic plus planar background is inadequate in a literal crowded COSMOS-Web scene.

## Control

For each frozen D1d experiment, construct `delta = injected_extension - SCI_ORIG` from the exact same FITS artifact and run the unchanged D1e forced-position fitter on that delta image with the unchanged ERR plane used only as fixed weights.

This subtraction cancels the literal survey scene and its already-realized noise by construction. Therefore D1f is **not** a realistic survey recovery, not a detection test, and not evidence that crowded-scene morphology succeeds. It is only a paired numerical identifiability control on the same pixel grid and PSF realization.

## Frozen rules

- Use the exact D1d artifact from successful run `33949290838`.
- Use the same pinned STPSF 2.2.0 reference data and source PSF configuration as D1d/D1e.
- Keep D1e bounds unchanged: centroid ±2 px, Re 1–20 px, n 0.3–6, q 0.2–1, PA −90..90 deg, positive amplitude.
- Keep linear weighted least squares; no robust loss, clipping, tolerance loosening, or failure filtering.
- Preserve every optimizer failure and bound hit.
- Do not apply Tolman dimming, extra background, extra noise, source-shot noise, or additional PSF convolution.
- A green workflow means only that the control executed successfully. Scientific interpretation requires inspecting recovered parameters and bound hits.

## Decision logic

If D1f cleanly recovers the injected parameters while D1e does not, the next scientific problem is scene modelling/deblending, not renderer tuning. If D1f also fails materially, diagnose numerical precision, renderer/fitter consistency, PSF sampling, and FITS storage effects before touching the real-scene model.
