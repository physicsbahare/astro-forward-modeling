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

## Not yet closed

The following require independent maintained astronomy packages and/or survey data and therefore remain release gates:

1. Cross-code comparison against Astropy, reproject, Photutils, GalSim, STPSF, and the JWST pipeline/CRDS.
2. Published-method reproduction: FERENGI, DOPTERIAN/Paulino-Afonso, Yu et al. (2023), AGN nuclear-contamination experiments, and Zhuang & Shen PSF-mismatch experiments.
3. Real COSMOS-Web Level-1 injection/recovery using 30-mas mosaics, empirical/survey PSFs, WCS, segmentation, and real background statistics.
4. Comparison of Level-1 mosaic injection with a small Level-2 exposure-injection experiment to quantify source-shot-noise/drizzle-covariance limitations.
5. Numerical acceptance thresholds for wavelength quadrature, PSF matching, resampling, spectral-support errors/warnings, and stochastic ensemble convergence.

Production-framework implementation should begin only after these gates have been reviewed and the remaining numerical policies are justified rather than guessed.
