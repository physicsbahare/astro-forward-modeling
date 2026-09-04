# Gates Before Production Implementation

Production package coding should not begin until these gates are closed. This roadmap tracks **distinct scientific/numerical failure modes**, not a requirement to reproduce every cited paper line by line. A literature case is mandatory only when it contributes a non-redundant operator, failure mode, external implementation, or survey-reality check that is not already covered by a stronger test.

## Gate A — independent numerical suite

**Status: substantially complete.**

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

These tests freeze physical semantics, not universal application tolerances.

## Gate B — cross-code verification against maintained astronomy packages

**Status: original Gate-B set complete; one morphology extension remains before Gate F.**

- [x] Compare cosmological distances and units against `astropy.cosmology`.
- [x] Compare exact/adaptive reprojection against `reproject`.
- [x] Compare Wiener kernels against maintained Photutils PSF matching.
- [x] Compare chromatic rendering against GalSim on the same analytic scene.
- [x] Compare polychromatic JWST PSFs against STPSF with controlled input spectra.
- [x] Verify NIRCam PHOTOM science/error/variance scaling and inverse round trip against `jwst==3.0.0`.
- [x] Freeze a compatible CRDS context and verify live NIRCam PHOTOM/AREA reference selection with checksummed provenance.
- [x] Quantify JWST drizzle/resampling behavior for a controlled imaging case, including flux, centroid, pixel scale, morphology, variance, and covariance.
- [ ] Add a pinned PyAutoGalaxy/PyAutoArray PSF-convolved morphology cross-code benchmark using identical analytic Sérsic/MGE scenes; compare flux, centroid, profile shape, second moments, and recovered structural parameters. Treat it as an independent reference, not ground truth or a production dependency.

Frozen JWST evidence includes STPSF 2.2.0 plus its exact data archive, `jwst==3.0.0`, `stcal==1.20.0`, and CRDS context `jwst_1584.pmap`. The NIRCam calibration audit established that PHOTOM lookup must respect FILTER + PUPIL + SUBARRAY when a subarray column is present. Controlled drizzle tests also demonstrated that correlated noise is configuration-dependent and must not be collapsed into one universal correction factor.

Detailed historical workflow/debug records remain in the corresponding benchmark reviews and CI-routing documentation rather than defining current gate state here.

## Gate C — literature-motivated scientific stress tests

**Status: five scopes complete; Dewsnap C6 is active.**

- [x] **FERENGI-style artificial redshifting** — synthetic-equivalent reproduction reviewed as **PASS WITH EXPLAINED DIFFERENCE**. This validates the artificial-redshift operator family and prevents duplicated redshift/radiometric factors; see `benchmarks/ferengi_2008/REVIEW.md`.
- [x] **Paulino-Afonso/DOPTERIAN-style degradation** — reviewed as **PASS WITH EXPLAINED DIFFERENCE**. This exposed detector-pixel integration, subpixel phase, and low-information identifiability issues; see `benchmarks/paulino_afonso_2017/REVIEW.md`.
- [x] **Yu et al. (2023) resolvedness/morphology trends** — reviewed as **PASS WITH EXPLAINED DIFFERENCE**. This establishes that morphology metrics can fail before flux does and that realistic asymmetric PSFs alter asymmetry; no universal `R_p/FWHM` cut is adopted; see `benchmarks/yu_2023/REVIEW.md`.
- [x] **AGN nuclear-fraction contamination** — controlled scope complete. Nuclear dominance and low S/N produce real optimizer/identifiability failures that remain observables, not reasons to widen bounds; see `benchmarks/agn_nuclear_fraction/REVIEW.md`.
- [x] **Zhuang & Shen PSF mismatch** — controlled scope complete with an explicit scientific failure. C5r run `33842347328` completed as a diagnostic, but six of 12 starts timed out and every selected wrong-PSF solution hit a bound. Target noise is not added to a condition that already fails noiseless morphology recovery; see `benchmarks/zhuang_shen_2024/REVIEW.md`.
- [ ] **Dewsnap-style independent fitter / PSF-construction validation.**
  - [x] C6a AstroPhot 0.18.0 signed-PSF/runtime/convention preflight — run `33849387267` completed/success; signed samples, unit-sum normalization, public array orientation, and AstroPhot's internal transpose/convolution convention were verified. This is a software/convention pass only, not morphology validation; see `benchmarks/dewsnap_2025/C6A_RESULT.md`.
  - [ ] C6b matched-PSF, noiseless common-scene AstroPhot-versus-Imfit comparison. Reuse the clean C5o `n=1` scene/result so fitter/renderer behavior is isolated before PSF mismatch. Predeclare diagnostics; record all starts, convergence messages, bounds, image products, objectives, runtime, versions, and parameter differences. Do not invent a recovery band after seeing the result.
  - [ ] C6c compare independent PSF constructions only after C6b establishes the common-scene baseline. Fit quality alone is not a morphology-validity criterion.
- [ ] **Kawase, Shibuya & Matsuda (2026) method check — conditional implementation target.** First test the genuinely new smooth-host + sparse-point-source / point-source-balance idea on a minimal controlled scene. It becomes a required production-design input only if it adds recovery robustness or a useful failure diagnostic beyond the Sérsic+PSF stress suite; exact paper reproduction is not required.
- [ ] **Explicit source-SED / chromatic-PSF mismatch stress test** including a color-gradient source. This is a required operator-level test because the final `PSFProvider` must support bandpass-integrated, source-SED-dependent PSFs; a single source-independent broadband PSF cannot be the only verified mode.

### Gate-C evidence policy

The papers are **sources of distinct scientific checks, not eight mini-products that must each be rebuilt in full**. For each source, extract the smallest controlled experiment that tests the unique claim relevant to the future framework. Stop expanding a literature benchmark once its unique failure mode/operator has been isolated and independently audited. Preserve paper-specific numerical reproduction only when an exact number is itself needed to validate a convention or implementation.

## Gate D — real-survey injection

**Status: not started; mandatory before production acceptance.**

- [ ] Generic mosaic injection/recovery test.
- [ ] COSMOS-Web NIRCam L1 test using real 30-mas products, empirical/declared PSF, background, WCS, segmentation, and the chosen measurement pipeline.
- [ ] Quantify the L1 source-shot-noise/covariance approximation.
- [ ] Design the L2 exposure-injection adapter and compare L1 versus L2 on a small controlled sample.

Gate D is more important to production readiness than reproducing additional redundant literature cases, because it tests the actual survey transfer function, crowding/background/WCS/segmentation interactions, and measurement-pipeline recovery.

## Gate E — numerical acceptance criteria

**Only after Gates B-D.**

- [ ] Freeze default wavelength quadrature convergence target.
- [ ] Freeze PSF kernel quality diagnostics and application-level rejection policy.
- [ ] Freeze direct-render/resampling tolerance policy by quantity (flux, centroid, size, morphology), not one universal scalar tolerance.
- [ ] Freeze spectral-support warning/error policy based on posterior predictive uncertainty and prior dominance.
- [ ] Freeze stochastic ensemble convergence criteria.

No acceptance band may be loosened merely because a benchmark failed. Scientific non-recovery, bound hits, centroid excursions, optimizer path dependence, or low-S/N failure may themselves be the result.

## Gate F — production architecture review

- [ ] Review plugin interfaces (`InstrumentAdapter`, `PSFProvider`, `SceneReconstructor`, `Renderer`, `InjectionEngine`, `MeasurementAdapter`).
- [ ] Confirm `PSFProvider` supports bandpass-integrated, source-SED-dependent PSFs and records PSF provenance/mismatch assumptions.
- [ ] Review ScopeSim's source -> optical-train -> detector abstraction as a design/cross-validation reference; do not add ScopeSim as a production dependency solely for architectural similarity.
- [ ] Review provenance schema.
- [ ] Review exception/warning taxonomy.
- [ ] Review unit conventions and calibration boundaries.
- [ ] Select a public package name only after checking uniqueness and scope.

Only then: **production implementation begins.**
