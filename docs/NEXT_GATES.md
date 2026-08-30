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

- [ ] Compare cosmological distances and units against `astropy.cosmology`.
- [ ] Compare exact/adaptive reprojection against `reproject`.
- [ ] Compare Wiener kernels against current `photutils.psf_matching.make_wiener_kernel`.
- [ ] Compare chromatic rendering against GalSim on the same analytic scene.
- [ ] Compare polychromatic JWST PSFs against STPSF with controlled input spectra.
- [ ] Confirm JWST calibrated-unit round trips against current `jwst` pipeline/CRDS products.

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
