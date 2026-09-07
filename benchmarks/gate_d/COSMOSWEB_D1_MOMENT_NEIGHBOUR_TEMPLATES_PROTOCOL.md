# Gate D1j — moment-extrapolated neighbour morphology diagnostic

Frozen before inspecting any D1j result.

## Motivation

D1i completed successfully, but empirical support growth was not monotonic:
target bound hits were 13/18 at 0 pixels, 12/18 at 2 pixels, and 13/18 at
4 pixels.  For bright AB=26 injections the 2-pixel growth improved the
near-source median flux bias, but degraded the intermediate median flux bias,
while isolated controls were unchanged.  Therefore simply extending a hard
empirical footprint farther is not scientifically justified.

Astronomical source-measurement packages commonly use centroid and second
moments to characterize source size, ellipticity, and orientation.  D1j tests
the narrower hypothesis that the high-significance neighbour cores identify the
right components, but their hard-edged empirical shapes fail to represent
smooth low-surface-brightness wings.

## Frozen construction

1. Input is the exact successful D1d real-mosaic injection artifact.
2. Component identities are derived only from pre-injection `SCI_ORIG` and
   `ERR`, using the unchanged D1c/D1g/D1h definition
   `(SCI_ORIG - robust_background_median) / ERR > 5` and 8-connectivity.
3. For each component present in a target patch, centroid and 2x2 covariance
   are measured from positive `SCI_ORIG-background` values in the frozen core.
4. Covariance eigenvalues have a numerical floor of 0.5 pixel sigma so
   one-pixel or nearly singular components remain finite.  This is a numerical
   regularization of a nuisance template, not a target acceptance relaxation.
5. The nuisance morphology is a single elliptical Gaussian with those measured
   moments, truncated only at Mahalanobis radius 6.  Shape and centroid are
   fixed; only one non-negative amplitude per neighbour is fitted.
6. These nuisance templates are constructed directly in observed image space.
   They are **not PSF-convolved again**.
7. The injected target uses exactly the D1e renderer, STPSF provenance, ERR
   weighting, planar background, linear loss, and target bounds.  No target
   tolerance or bound is changed.
8. All AB=29 low-S/N cases, optimizer failures, target bound hits, and nuisance
   amplitudes are retained.
9. No additional background, source-shot noise, Tolman dimming, or target PSF
   operation is applied.

## Interpretation

Workflow success means only that this frozen diagnostic executed.  Improvement
of bright near/intermediate recovery without damage to isolated controls would
support moving next to a genuinely deblended/parametric-neighbour experiment.
Failure to improve would argue that second-moment extrapolation is insufficient
and that actual multi-component deblending or free neighbour morphology is
required.  D1j is not a production deblender and is not literal survey-source
reproduction.
