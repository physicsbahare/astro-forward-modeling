# Gates Before Production Implementation

Production package coding should not begin until these gates are closed.

## Gate A — independent numerical suite

**Status: substantially complete in this snapshot.**

- [x] Distance-duality and redshift spectral-density checks.
- [x] `F_nu` / `F_lambda` bolometric consistency.
- [x] photon-count representation consistency.
- [x] Tolman surface-brightness scaling.
- [x] analytic Gaussian PSF matching.
- [x] regularized Fourier PSF trade-off experiment.
- [x] impossible sharper-target case.
- [x] exact-overlap flux-conserving transfer.
- [x] finite-input-sampling morphology error.
- [x] chromatic/color-gradient PSF non-commutativity test.
- [x] correct source-shot-noise ordering.
- [x] no-double-background injection check.
- [x] spectral-information-support counterexample.

## Gate B — cross-code verification against maintained astronomy packages

Requires an environment with the relevant packages and reference data.

- [x] Compare cosmological distances and units against `astropy.cosmology`.
- [x] Compare exact/adaptive reprojection against `reproject`.
- [x] Compare Wiener kernels against current `photutils.psf_matching.make_wiener_kernel`.
- [x] Compare chromatic rendering against GalSim on the same analytic scene.
- [x] Compare polychromatic JWST PSFs against STPSF with controlled input spectra.
- [x] Verify NIRCam PHOTOM science/error/variance scaling and inverse round trip against `jwst==3.0.0`.
- [x] Freeze a compatible CRDS context and verify live NIRCam PHOTOM/AREA reference selection with checksummed provenance.
- [ ] Quantify JWST drizzle/resampling behavior (flux, centroid, pixel scale, morphology, variance and covariance).

The STPSF sub-gate is reproducibly frozen to STPSF 2.2.0 plus the exact
STPSF 2.2.0 data archive (SHA-256
`bbdfbe7c5aa7ee7fdb60efed13720ba3e0619c976b77aa0d63941dd59a4b6a98`).
The initial CI suite passes four JWST/NIRCam checks covering data/software
pinning, output-extension semantics and detector-effect toggling, chromatic PSF
size, and detector-position field dependence.

The first pipeline/CRDS calibration run also passes under `jwst==3.0.0` and
`jwst_1584.pmap`.  For the controlled NRCA-long/F444W/FULL case, CRDS selects
`jwst_nircam_photom_0168.fits` and `jwst_nircam_area_0261.fits`; both are
recorded by SHA-256.  The test also exposed and resolved an important reference-
table semantic: the PHOTOM table has subarray-specific rows, so NIRCam imaging
must match FILTER + PUPIL + SUBARRAY when the `subarray` column is present,
rather than taking the first F444W/CLEAR row.

The remaining JWST Gate-B item is drizzle/resampling behavior.  It is kept
separate because a correct PHOTOM conversion does not by itself guarantee
correct pixel-area, covariance, or morphology behavior after drizzling.

## Gate C — literature reproduction

- [ ] FERENGI-style artificial-redshift benchmark.
- [ ] Paulino-Afonso/DOPTERIAN-style degradation benchmark.
- [ ] Yu et al. (2023) resolvedness/morphology trends.
- [ ] AGN nuclear-fraction morphology contamination benchmark.
- [ ] Zhuang & Shen PSF-mismatch AGN-host benchmark.

## Gate D — real-survey injection

- [ ] Generic mosaic injection/recovery test.
- [ ] COSMOS-Web NIRCam L1 test using real 30-mas products, PSF, background, WCS, segmentation, and the chosen measurement pipeline.
- [ ] Quantify the L1 source-shot-noise/covariance approximation.
- [ ] Design the L2 exposure-injection adapter and compare L1 vs L2 on a small controlled sample.

## Gate E — numerical acceptance criteria

Only after Gates B-D:

- [ ] Freeze default wavelength quadrature convergence target.
- [ ] Freeze PSF kernel quality diagnostics and application-level rejection policy.
- [ ] Freeze direct-render/resampling tolerance policy by quantity (flux, centroid, size, morphology), not one universal scalar tolerance.
- [ ] Freeze spectral-support warning/error policy based on posterior predictive uncertainty and prior dominance.
- [ ] Freeze stochastic ensemble convergence criteria.

## Gate F — production architecture review

- [ ] Review plugin interfaces (`InstrumentAdapter`, `PSFProvider`, `SceneReconstructor`, `Renderer`, `InjectionEngine`, `MeasurementAdapter`).
- [ ] Review provenance schema.
- [ ] Review exception/warning taxonomy.
- [ ] Review unit conventions and calibration boundaries.
- [ ] Select public package name only after checking uniqueness and scope.

Only then: **production implementation begins.**
