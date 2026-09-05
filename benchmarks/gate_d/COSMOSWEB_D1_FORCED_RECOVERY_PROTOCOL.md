# Gate D1e — forced-position morphology recovery on the real COSMOS-Web injection matrix

Frozen before inspecting recovery results.

## Scope

This is the first morphology-recovery benchmark on the real COSMOS-Web F444W mosaic context. It is deliberately a **forced-position** benchmark, not a blind source-detection/completeness experiment: the fitter is given the injected integer pixel location but may move the centroid within ±2 pixels. All 18 frozen D1d scenes are fit, including the AB=29 cases with nominal independent-pixel S/N < 0.4 and the near-source placements.

## Forward model

The recovery model is a PSF-convolved single Sérsic profile plus a local planar background. The PSF construction and pinned STPSF reference data are identical to D1d. No Tolman factor, extra background, source-shot noise, or PSF sharpening operation is applied. The fitted postage stamp is 65×65 pixels. The pixelwise ERR plane supplies weights; non-finite or non-positive ERR pixels are retained in accounting and excluded from the weighted residual only.

Free parameters are positive total source amplitude, centroid offsets, effective radius, Sérsic n, axis ratio q, position angle, and three planar-background coefficients. Bounds are frozen before the result: centroid ±2 px, Re 1–20 px, n 0.3–6, q 0.2–1, PA −90–90 deg, positive amplitude. Background terms are unbounded. The optimizer is scipy `least_squares` with ordinary weighted residuals and no robust-loss downweighting.

## Interpretation

`optimizer_success` is not scientific success. For every experiment the output records recovered morphology, reduced chi-square proxy, parameter-bound hits, and whether the recovered values are finite. Low-S/N failures, optimizer failures, and bound hits remain in the table and must not be removed from summaries. This benchmark is synthetic-source recovery **in a literal real mosaic context**, but the injected PSF/SED model remains synthetic-equivalent rather than a literal reproduction of every COSMOS-Web source.
