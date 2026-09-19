# Gate D1h — simultaneous fixed neighbour-template diagnostic

Frozen before inspecting any D1h result.

## Motivation

D1e showed strong crowding-dependent morphology failures on literal COSMOS-Web background structure. D1f showed the target renderer/fitter is numerically identifiable when the pre-existing scene is algebraically removed. D1g then reused the exact D1c >5-sigma pre-injection source-pixel definition as a fixed mask. Masking changed several catastrophic solutions but did not generally recover the target morphology, so discarding neighbour pixels is not sufficient.

A standard parametric-imaging strategy is to fit sufficiently close neighbours simultaneously while masking more distant objects. GALFIT examples explicitly use simultaneous single-Sersic neighbour components to reduce contamination, and recent JWST structural work similarly fits neighbours whose Kron apertures overlap the primary while masking more distant objects. Photutils segmentation/deblending documentation likewise treats connected/deblended source footprints as the basis for separating overlapping sources.

D1h is a deliberately narrower diagnostic than a full neighbour-Sersic fit: every pre-existing >5-sigma connected component overlapping a 65x65 target patch contributes one fixed observed-space empirical template with a non-negative free amplitude. This tests whether retaining and modelling the high-significance neighbour cores is more informative than simply masking them, while adding far fewer poorly identified shape parameters.

## Frozen construction

1. Input is the exact successful D1d real-mosaic injection artifact.
2. The neighbour map is derived only from `SCI_ORIG` and `ERR`, never from an injected image.
3. Background and source-pixel threshold are unchanged from D1c/D1g: `(SCI_ORIG - robust_background_median) / ERR > 5`.
4. Connectivity is 8-connected; no dilation and no target-specific unmasking are allowed.
5. For every connected component overlapping the 65x65 fit patch, the empirical template is the positive `SCI_ORIG-background` signal inside that component footprint, L2-normalized in observed pixel space.
6. Only one non-negative amplitude per neighbour template is fitted. The empirical neighbour shape is fixed from the pre-injection scene; no neighbour size, Sersic index, axis ratio, PA, or centroid is optimized.
7. The injected target uses exactly the D1e renderer, STPSF provenance, ERR weighting, planar background, target bounds and linear least-squares loss. Target bounds are not relaxed.
8. No pixels are masked in D1h. Low-S/N failures, optimizer failures, target bound hits, and zero-amplitude nuisance components remain explicit outputs.
9. No additional background, source-shot noise, Tolman dimming, or PSF operation is applied.

## Interpretation

A green workflow proves only that this frozen diagnostic executed. It does not prove scientific recovery. Improvement relative to D1e/D1g would support the interpretation that explicit neighbour light modelling is necessary. Failure would imply that the >5-sigma fixed-core templates are insufficient and would motivate a more realistic deblending/component model rather than relaxed target bounds. Because the templates are derived from the known pre-injection scene, D1h is not a production method and is not literal survey-source reproduction.
