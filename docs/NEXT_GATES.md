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

**Status: original Gate-B experiments are complete; one new cross-code morphology extension is pending before production freeze.**

- [x] Compare cosmological distances and units against `astropy.cosmology`.
- [x] Compare exact/adaptive reprojection against `reproject`.
- [x] Compare Wiener kernels against current `photutils.psf_matching.make_wiener_kernel`.
- [x] Compare chromatic rendering against GalSim on the same analytic scene.
- [x] Compare polychromatic JWST PSFs against STPSF with controlled input spectra.
- [x] Verify NIRCam PHOTOM science/error/variance scaling and inverse round trip against `jwst==3.0.0`.
- [x] Freeze a compatible CRDS context and verify live NIRCam PHOTOM/AREA reference selection with checksummed provenance.
- [x] Quantify JWST drizzle/resampling behavior for a controlled imaging case (flux, centroid, pixel scale, morphology, variance and covariance).
- [ ] Add a pinned PyAutoGalaxy/PyAutoArray PSF-convolved morphology cross-code benchmark using identical analytic Sérsic/MGE scenes; compare flux, centroid, profile shape, second moments and recovered structural parameters. Treat this as an independent reference, not ground truth or a production dependency.

The STPSF sub-gate is reproducibly frozen to STPSF 2.2.0 plus the exact
STPSF 2.2.0 data archive (SHA-256
`bbdfbe7c5aa7ee7fdb60efed13720ba3e0619c976b77aa0d63941dd59a4b6a98`).
The CI suite passes four JWST/NIRCam checks covering data/software pinning,
output-extension semantics and detector-effect toggling, chromatic PSF size,
and detector-position field dependence.

The pipeline/CRDS calibration checks pass under `jwst==3.0.0`, `stcal==1.20.0`
and `jwst_1584.pmap`. For the controlled NRCA-long/F444W/FULL case, CRDS
selects `jwst_nircam_photom_0168.fits` and `jwst_nircam_area_0261.fits`; both
are recorded by SHA-256. The test exposed and resolved an important reference-
table semantic: the PHOTOM table has subarray-specific rows, so NIRCam imaging
must match FILTER + PUPIL + SUBARRAY when the `subarray` column is present,
rather than taking the first F444W/CLEAR row.

The controlled drizzle experiment also passes the flux/centroid/size and pixel-
area checks. A separate white-noise experiment shows why covariance must remain
explicit in later survey work. At native 0.063 arcsec sampling the noise remains
effectively uncorrelated, whereas drizzling the same field to 0.0315 arcsec
produces nearest-neighbor correlations of about 0.665. For a 5x5-pixel aperture,
the true variance is about 5.15 times the value one would infer by treating the
*empirical output-pixel variance* as independent. At the same time, the JWST
pipeline's approximate resampled `VAR_RNOISE` plane is conservative in this
specific experiment: summing its diagonal terms over the aperture overpredicts
the measured aperture variance by about 36%. This behavior is consistent with
stcal's documented approximate drizzle error propagation and must not be turned
into a universal covariance correction factor.

The original Gate-B set is closed as a verification record, not as a claim that
one covariance number applies to arbitrary mosaics, kernels, pixfrac values or
survey reductions. The new PyAutoGalaxy/PyAutoArray item is a post-closure
extension motivated by a maintained 2026 implementation and must be completed
before Gate F is frozen. Survey-specific covariance effects remain deferred to
Gate D.

## Gate C — literature reproduction

- [x] FERENGI-style artificial-redshift benchmark — synthetic-equivalent reproduction reviewed as **PASS WITH EXPLAINED DIFFERENCE**; see `benchmarks/ferengi_2008/REVIEW.md`. Existing regression bounds were not loosened and remain non-production sanity checks.
- [x] Paulino-Afonso/DOPTERIAN-style degradation benchmark — controlled synthetic-equivalent reproduction reviewed as **PASS WITH EXPLAINED DIFFERENCE**. The high-`n` numerical blocker was resolved by separating detector-pixel integration from the historical point-sampled fitter, the transfer centering phase was corrected, and the full noiseless pixel-integrated single-Sérsic set recovers truth cleanly. The remaining target-noise pathologies persist at low extended-source information and are classified as identifiability loss rather than a reason to widen bounds. Exact Table-2 correction factors are not claimed; see `benchmarks/paulino_afonso_2017/REVIEW.md`.
- [x] Yu et al. (2023) resolvedness/morphology trends — controlled synthetic-equivalent reproduction reviewed as **PASS WITH EXPLAINED DIFFERENCE**. Circular-PSF smoothing reproduces the expected concentration/asymmetry suppression, the controlled noise stage preserves low-information failures and bound hits, and the pinned STPSF F444W diagnostic recovers the expected small positive asymmetry contribution from a realistic non-180-degree-symmetric PSF. No universal `R_p/FWHM` cut is inferred; see `benchmarks/yu_2023/REVIEW.md`.
- [ ] AGN nuclear-fraction morphology contamination benchmark — Stage-1 run `33642676932` and Stage-2a run `33650581586` succeeded and artifacts were reviewed. Sampling drift decreases but is nonzero; Stage-2b `gate-c-agn-cross-sampling` fits 16x reference images with 4x/8x templates, freeing structural parameters before noise. Independent convergence and full identifiability remain unproven. Noise and PSF mismatch remain separate. See `benchmarks/agn_nuclear_fraction/REVIEW.md`.
- [ ] Zhuang & Shen PSF-mismatch AGN-host benchmark.
- [ ] Dewsnap et al. JWST AGN-host cross-fitter/PSF-construction benchmark: compare at least two PSF constructions and independent fitting implementations on controlled common scenes; do not use fit quality alone as a morphology-validity criterion.
- [ ] Kawase, Shibuya & Matsuda (2026) controlled AGN-host synthetic validation case using smooth-host + sparse-point-source decomposition and the point-source-balance constraint; compare against the standard Sérsic+PSF stress test before considering production use.
- [ ] Explicit source-SED / chromatic-PSF mismatch stress test including a color-gradient source. The PSF must be allowed to depend on the source SED within the bandpass; a single source-independent broadband PSF is not sufficient as the only verified mode.

See `docs/RECENT_DEVELOPMENTS_2026_08.md` for the provenance and motivation of the newly added verification cases.

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
- [ ] Confirm `PSFProvider` supports bandpass-integrated, source-SED-dependent PSFs and records PSF provenance/mismatch assumptions.
- [ ] Review ScopeSim's source -> optical-train -> detector abstraction as a design/cross-validation reference; do not add ScopeSim as a production dependency solely for architectural similarity.
- [ ] Review provenance schema.
- [ ] Review exception/warning taxonomy.
- [ ] Review unit conventions and calibration boundaries.
- [ ] Select public package name only after checking uniqueness and scope.

Only then: **production implementation begins.**
