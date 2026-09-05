# Gate D1i — fixed empirical neighbour-support growth diagnostic

Frozen before inspecting any D1i result.

## Motivation

D1h executed successfully, but the fixed >5-sigma core templates did not
produce a general scientific recovery.  Relative to D1g, the bright
intermediate cases improved, while the near-source cases remained strongly
biased and the faint AB=29 cases remained a failure regime.  This points to a
specific unresolved possibility: the component identities may be adequate,
but the high-significance template support may omit lower-surface-brightness
wings that contaminate the target fit.

GALFIT explicitly recommends simultaneous modelling of sufficiently close
neighbours, and Photutils deblending uses multi-threshold structure to separate
overlapping source light.  Before adding free Sérsic shape parameters for every
neighbour, D1i tests the narrower support-truncation hypothesis.

## Frozen construction

1. Input is the exact successful D1d real-mosaic injection artifact.
2. Neighbour component identities are derived only from pre-injection
   `SCI_ORIG` and `ERR`, with the unchanged D1c/D1g/D1h definition
   `(SCI_ORIG - robust_background_median) / ERR > 5`.
3. Connectivity remains 8-connected.  The detection threshold is not lowered
   and no new components are created.
4. For each existing component, empirical support is tested at exactly
   `0`, `2`, and `4` pixels of binary growth.  These values are frozen before
   looking at D1i results.
5. Template values are positive `SCI_ORIG-background` pixels inside the grown
   support, L2-normalized.  They are observed-space templates and therefore are
   **not PSF-convolved again**.
6. Each neighbour template retains only one non-negative free amplitude.
   No neighbour centroid, size, Sérsic index, axis ratio, or PA is fitted.
7. The injected target uses exactly the D1e renderer, STPSF provenance, ERR
   weighting, planar background, linear loss, and target bounds.  No target
   tolerance or bound is relaxed.
8. All low-S/N cases, optimizer failures, target bound hits, and nuisance
   amplitudes remain in the artifact.
9. No additional background, source-shot noise, Tolman dimming, or PSF
   operation is applied.

## Interpretation

A successful workflow means only that the frozen support-growth diagnostic
executed.  If modest support growth improves the near/intermediate bright
recoveries without changing isolated controls, missing neighbour wings are
implicated and a later parametric/deblended neighbour model is justified.
If it does not, increasing empirical support further is not justified; the
next scientific step should instead test explicit neighbour morphology or
deblending.  D1i is a diagnostic using the known pre-injection scene, not a
production method and not literal survey-source reproduction.
