# C5f: frozen centroid diagnostic (2026-09-03)

Before inspecting C5f results, freeze this point-source-only diagnostic. C5e
run 33727185586 (b23d2a21f1d6cb2823b1adb44c04e9a14b55fac7) explicitly
completed/success in both jobs. The reviewed artifact manifest is
`phase_33727185586.json`: 96 direct fits, 192 Gaussian controls, 576 aperture
rows and 964 image arrays were inspected. Module B native signed sums span
0.976862–1.048114; the full/cropped sum difference is at most 0.00000170.
Fixed-position cubic amplitudes differ from Quintic by less than 0.19%.
These facts do not establish physical flux conservation or astrometric accuracy.

## Frozen experiment

Use all 16 phases per module from C5e, unchanged signed data and 201-square
fixed detector crop. Fit Photutils cubic ImagePSF to (1) archived cubic and
(2) archived GalSim Quintic images. Also fit the archived exact Gaussian
controls at optical FWHM 0.09 and 0.165 arcsec, all 16 phases. Gaussian controls
are deliberately repeated in both module jobs. Thus 64 cases/module,
3 starts/case, 128 winners and 384 starts overall.

Free only x/y, bounded to [-1,1] native pixel relative to the geometric
stamp center. Starts are (0,0), (0.5,0.5), (-0.5,-0.5), independent of injected
phase. Profile one nonnegative amplitude with inherited SciPy NNLS; no upper
flux bound. SciPy TRF, two-point Jacobian, linear loss, max_nfev=160,
ftol=xtol=1e-10, gtol=1e-7; full-crop RMS-normalized residual objective.
Winner is smallest finite cost, including unsuccessful optimizer returns.
Retain every start, status, active mask, bound/zero-flux flag, prediction and
residual; compare to fixed-injected-position amplitude/cost. Preserve signed
wings, 2x sampling, original factor-4 padded ImagePSF input and no second pixel
integration or phase-dependent normalization. No host, added noise or PSF repair.

Acceptance is complete finite products/provenance/algebra, not a new empirical
recovery band. Nonconvergence, boundary hits, centroid and flux shifts remain
observables. Inspect start agreement and cost/position tradeoffs before freeing
galaxy shape. A local optimum or cross-interpolator agreement is not truth.

## Software-first decision

Reuse pinned Photutils 3.0.0 ImagePSF (cubic RectBivariateSpline) and SciPy
1.18.1 least_squares/NNLS through a thin adapter; retain C5e dependency pins.
Official ImagePSF and PSFPhotometry documentation checked 2026-09-03:
https://photutils.readthedocs.io/en/stable/api/photutils.psf.ImagePSF.html
https://photutils.readthedocs.io/en/stable/api/photutils.psf.PSFPhotometry.html
Installed SciPy 1.18.1 public signature/docstring was inspected after online
documentation retrieval failed. Both packages use BSD licenses. Installation
of the exact C5e pins succeeded locally. No new optimizer/interpolator is written.
Full PSFPhotometry is deferred because its initial-position-relative bounds and
source-fit pipeline are not this fixed global-ROI/profile-amplitude experiment.
Input normalization and signed-model limitations are inherited, not corrected.

## Infrastructure restoration confirmed

Calibration run 33727866409 at 00971fe32a7de9fb68d412830ea1650c48ce182f
completed/success; its actual logs report 3 tests passed. Artifact 9883823792
ZIP SHA256 b6bb6cc3f477edc595c1f8a4c4fc033f40c5661305e192138ff17cd80d0be914
contains the CRDS jwst_1584.pmap NIRCALONG/F444W selection, PHOTOM row 90 and
AREA metadata. Raw reference FITS are not archived here: their hashes are
CI-reported, not independently redownloaded in this review. Regression run
33727866435 passed both Python jobs (65 passed, 4 skipped each); actionlint
1.7.12 checksum/version validation succeeded. Preserve earlier failed workflow
records; no additional calibration rerun is needed.
