# C5g: bounded nuclear-centroid release in AGN+host scenes

Frozen 2026-09-03, before evaluating any C5g science fit. Verification only.

## Decision and completed prerequisite

C5f run 33734876563, commit 0cc3f757a1746d1801d06b71e09a41f58e130d0c,
and regression 33734876499 explicitly completed/success. The C5f audit covers
128 winners, 384 starts and 1282 arrays. All starts report optimizer success,
without centroid-bound or zero-flux hits. Cross-interpolator radial offsets
reach 0.006804 pixel (A) and 0.009953 pixel (B). Releasing the centroid changes
the B amplitude by up to 0.002647 relative to fixing it. Matched-interpolator
recovery and agreement among three starts are numerical controls, not physical
PSF validity or global optimality. Artifact hashes and case details are in
`centroid_33734876563.json`; this review does not overwrite C5f.

The next question is whether a wrong empirical PSF can be absorbed as a false
nucleus–host offset and a changed host amplitude. Release the nuclear centroid
FIRST, retaining host shape/center. Releasing Re,n,q or the host center at the
same time would confound this comparison. This is a nonlinear AGN+host fit,
but explicitly NOT a free-shape morphology test or an astrometric calibration.

## Frozen data, model, fitting and outputs

Reuse the ACTUAL C5d run 33717899427 at
88f3fb646a0b89e6cb9b8b8ee1aacae377edca56, artifacts 9880481087 (n=1) and
9880386950 (n=4). Verify every file against the committed C5d audit, the commit,
host identity and input/data hashes; copy original truth and template products
into the new artifact. No new truth rendering or noise realization.

Twelve data images: n=1/4, true A/B effective PSF, AGN/host=0.1/1/10, Re=16
native pixels, q=0.6, PA=45 degrees, both intrinsic centers fixed at zero.
Fit each image with A and B: 24 comparisons. Use the archived fine-Quintic
host template at the true shape and its original fixed center. For the point
component, reuse C5e/f Photutils 3.0.0 cubic ImagePSF, oversampling=2,
input=4 times the signed-normalized 401-square PSF plus eight zero rows per edge,
origin at padded center, fill=0, 0.015/0.03 arcsec sample/native scales. The
201-square detector crop is unchanged and independent of the fitted position.
At zero phase verify agreement with the archived native point template; save
the actual maximum image difference and the fixed-fit change versus C5d.
Retain the input normalization and signed wings. No stamp renormalization,
clipping, extra pixel convolution, PSF reconstruction, or sharpening.

The paired baseline fixes the nuclear center at (0,0); the released arm uses
x,y bounds [-1,+1] native pixel relative to the fixed host center. Reuse C5f
starts (0,0), (0.5,0.5), (-0.5,-0.5), TRF two-point Jacobian, linear loss,
max_nfev=160, ftol=xtol=1e-10, gtol=1e-7. Profile BOTH nonnegative amplitudes
using the inherited SciPy NNLS objective, with no upper bound. Minimize
the same full-crop RMS-normalized residual, with no fitted sky or weights.
The winner has lowest finite cost, regardless of optimizer success.

Save 24 fixed baselines and 24 released winners, all 72 nonlinear starts,
data/host/point models, fixed and all-start predictions/residuals, covariance-
relevant template singular values and KKT gradients, zero amplitudes, active
centroid bounds, termination messages, start spreads, signed offsets, amplitude
changes and objective differences. Record exceptions and partial output before
failing the job; do not silently drop a failed start. Preserve true n/q/Re and
parent baselines so a centroid change is never reported as a morphology recovery.

Acceptance: complete finite output, provenance and algebra only. Retain the
inherited 1e-12 array identity check for implementation bookkeeping; it is not
an empirical accuracy tolerance. No new offset/flux recovery band or desired
sign. Low costs or improved amplitudes do not establish physical truth.
Signed empirical models remain unsuitable as Poisson intensity maps.

Workflow: `gate-c-agn-empirical-agn-centroid`, two host jobs, maximum parallel=2,
20 minutes per job on the standard Ubuntu 24.04 runner. Reuse exact phase pins;
host rendering is reused, not recomputed per optimizer evaluation. Follow the
run at its implementation commit; do not duplicate an active experiment.
Next: review apparent offsets, host/nucleus amplitude changes, zero-flux
plateaus and start agreement before selecting free-shape empirical fits.

## Software-first search and reuse decision (2026-09-03)

Reviewed official ImagePSF origin/oversampling/spline documentation:
https://photutils.readthedocs.io/en/stable/api/photutils.psf.ImagePSF.html
and GalSim rendering/resource semantics:
https://galsim-developers.github.io/GalSim/_build/html/gsobject.html
The installed SciPy 1.18.1 NNLS/TRF interfaces and existing tested adapters
are reused; remote SciPy documentation retrieval was unavailable. GalSim,
Photutils and SciPy are BSD licensed, pinned and already installed in CI.

No new interpolation, convolution or optimization algorithm is needed. The
thin adapter combines the reviewed C5d host templates, C5e/f ImagePSF and
existing two-amplitude NNLS. Full PSFPhotometry/Imfit cross-fitting remains
deferred: changing fitter, objective, PSF conventions and host shape together
would not isolate nuclear-centroid release. The independent cross-fitter and
physical PSF construction gates remain open. The GalSim documentation also
warns about large FFTs; frozen host templates avoid repeated rendering here
without reducing support or changing numerical settings. A later free-shape
renderer must receive its own convention/resource validation, not narrower
scientific bounds or weaker accuracy to fit the resource budget.
