# Scientific Verification Status

## Scope of this snapshot

This snapshot is a **pre-implementation scientific verification harness**, not the production package. Its purpose is to make ambiguous conventions fail visibly before a public astronomy framework is implemented.

## Closed at the independent-reference level

- Cosmological distance duality and angular-size semantics.
- Observer/emitter transformations for `F_nu`, `F_lambda`, `I_nu`, and `I_lambda`.
- Tolman surface-brightness scaling as a consequence of the spectral transformation.
- Photon-count representation consistency.
- Explicit separation of K-correction diagnostics from the forward spectral integral.
- Chromatic-PSF non-commutativity for spatial colour gradients.
- Regularized PSF-matching diagnostics and impossible-resolution detection.
- Flux-conserving pixel-overlap transfer and finite-input-sampling limitations.
- Detector-order source Poisson statistics.
- No-double-background rule for real-image injection.
- Spectral-support diagnostics must measure predictive information, not wavelength-envelope overlap alone.

## Closed cross-code sub-gates

- Astropy cosmological distances and spectral-density unit conversion.
- `reproject` exact/adaptive resampling semantics, including the distinction between surface brightness and flux per pixel.
- Photutils Wiener PSF-matching convention.
- GalSim chromatic Gaussian rendering against an analytic photon-weighted second-moment prediction.
- JWST/NIRCam STPSF semantics using STPSF 2.2.0 with the exact 2.2.0 reference-data archive. Four CI checks pass: software/data pinning, ideal/distorted/detector-output semantics and detector-effect toggling, chromatic PSF broadening, and detector-position field dependence. The data archive is fixed by SHA-256 `bbdfbe7c5aa7ee7fdb60efed13720ba3e0619c976b77aa0d63941dd59a4b6a98`.

## Not yet closed

The following remain release gates:

1. JWST pipeline/CRDS calibrated-unit round trips, explicit PHOTOM/AREA provenance, and drizzle/resampling behavior.
2. Published-method reproduction: FERENGI, DOPTERIAN/Paulino-Afonso, Yu et al. (2023), AGN nuclear-contamination experiments, and Zhuang & Shen PSF-mismatch experiments.
3. Real COSMOS-Web Level-1 injection/recovery using 30-mas mosaics, empirical/survey PSFs, WCS, segmentation, and real background statistics.
4. Comparison of Level-1 mosaic injection with a small Level-2 exposure-injection experiment to quantify source-shot-noise/drizzle-covariance limitations.
5. Numerical acceptance thresholds for wavelength quadrature, PSF matching, resampling, spectral-support errors/warnings, and stochastic ensemble convergence.

Production-framework implementation should begin only after these gates have been reviewed and the remaining numerical policies are justified rather than guessed.
