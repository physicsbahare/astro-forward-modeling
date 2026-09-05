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

**Status: complete for the pre-production verification scope.**

- [x] Compare cosmological distances and units against `astropy.cosmology`.
- [x] Compare exact/adaptive reprojection against `reproject`.
- [x] Compare Wiener kernels against maintained Photutils PSF matching.
- [x] Compare chromatic rendering against GalSim on the same analytic scene.
- [x] Compare polychromatic JWST PSFs against STPSF with controlled input spectra.
- [x] Verify NIRCam PHOTOM science/error/variance scaling and inverse round trip against `jwst==3.0.0`.
- [x] Freeze a compatible CRDS context and verify live NIRCam PHOTOM/AREA reference selection with checksummed provenance.
- [x] Quantify JWST drizzle/resampling behavior for a controlled imaging case, including flux, centroid, pixel scale, morphology, variance, and covariance.
- [x] Add a pinned PyAutoGalaxy/PyAutoArray PSF-convolved morphology cross-code benchmark using identical analytic Sérsic scenes; see `benchmarks/pyautogalaxy_2026/B9A_RESULT.md` and `B9B_RESULT.md`. It is an independent reference, not ground truth or a production dependency.

Frozen JWST evidence includes STPSF 2.2.0 plus its exact data archive, `jwst==3.0.0`, `stcal==1.20.0`, and CRDS context `jwst_1584.pmap`. The NIRCam calibration audit established that PHOTOM lookup must respect FILTER + PUPIL + SUBARRAY when a subarray column is present. Controlled drizzle tests also demonstrated that correlated noise is configuration-dependent and must not be collapsed into one universal correction factor.

Detailed historical workflow/debug records remain in the corresponding benchmark reviews and CI-routing documentation rather than defining current gate state here.

## Gate C — literature-motivated scientific stress tests

**Status: core non-redundant scopes complete; Kawase remains a conditional method evaluation, not a blocker.**

- [x] **FERENGI-style artificial redshifting** — synthetic-equivalent reproduction reviewed as **PASS WITH EXPLAINED DIFFERENCE**. This validates the artificial-redshift operator family and prevents duplicated redshift/radiometric factors; see `benchmarks/ferengi_2008/REVIEW.md`.
- [x] **Paulino-Afonso/DOPTERIAN-style degradation** — reviewed as **PASS WITH EXPLAINED DIFFERENCE**. This exposed detector-pixel integration, subpixel phase, and low-information identifiability issues; see `benchmarks/paulino_afonso_2017/REVIEW.md`.
- [x] **Yu et al. (2023) resolvedness/morphology trends** — reviewed as **PASS WITH EXPLAINED DIFFERENCE**. This establishes that morphology metrics can fail before flux does and that realistic asymmetric PSFs alter asymmetry; no universal `R_p/FWHM` cut is adopted; see `benchmarks/yu_2023/REVIEW.md`.
- [x] **AGN nuclear-fraction contamination** — controlled scope complete. Nuclear dominance and low S/N produce real optimizer/identifiability failures that remain observables, not reasons to widen bounds; see `benchmarks/agn_nuclear_fraction/REVIEW.md`.
- [x] **Zhuang & Shen PSF mismatch** — controlled scope complete with an explicit scientific failure. C5r run `33842347328` completed as a diagnostic, but six of 12 starts timed out and every selected wrong-PSF solution hit a bound. Target noise is not added to a condition that already fails noiseless morphology recovery; see `benchmarks/zhuang_shen_2024/REVIEW.md`.
- [x] **Dewsnap-style independent fitter / PSF-construction validation.**
  - [x] C6a AstroPhot 0.18.0 signed-PSF/runtime/convention preflight — see `benchmarks/dewsnap_2025/C6A_RESULT.md`.
  - [x] C6b matched-PSF, noiseless common-scene AstroPhot-versus-Imfit comparison — see `benchmarks/dewsnap_2025/C6B_RESULT.md`.
  - [x] C6c crossed empirical-PSF diagnostic — see `benchmarks/dewsnap_2025/C6C_RESULT.md`. Crossed PSFs destroy clean morphology recovery in both independent fitters, with fitter- and direction-dependent failure topology.
- [ ] **Kawase, Shibuya & Matsuda (2026) method check — conditional implementation target.** First test the genuinely new smooth-host + sparse-point-source / point-source-balance idea on a minimal controlled scene only if it adds a non-redundant diagnostic beyond the current suite.
- [x] **Explicit source-SED / chromatic-PSF mismatch stress test** including a color-gradient source — see `benchmarks/chromatic_psf/C7_RESULT.md`. The frozen color-gradient test produced a normalized image L1 difference of about 0.047 and about a 7% relative change in central concentration while flux and the chosen global second moment remained essentially unchanged.

### Gate-C evidence policy

The papers are **sources of distinct scientific checks, not mini-products that must each be rebuilt in full**. For each source, extract the smallest controlled experiment that tests the unique claim relevant to the future framework. Stop expanding a literature benchmark once its unique failure mode/operator has been isolated and independently audited. Preserve paper-specific numerical reproduction only when an exact number is itself needed to validate a convention or implementation.

## Gate D — real-survey injection

**Status: active. Real COSMOS-Web L1 injection/recovery is established; scene-contamination modelling is the current unresolved diagnostic.**

- [x] Acquire and checksum real COSMOS-Web DR1 JWST/NIRCam F444W 30-mas tile-A1 SCI/ERR/WHT data and create a finite 512x512 real cutout.
- [x] Freeze real-context placement classes from the pre-injection scene and construct 18 L1 injections (9 locations x AB=26/29) while modifying SCI only. ERR/WHT remain unchanged; no extra background noise, source shot noise, or extra Tolman factor is added.
- [x] Verify injected flux conservation and run forced-position morphology recovery on the literal real mosaic context. This is synthetic-source injection into **real survey context**, not literal reproduction of real COSMOS-Web sources; the declared STPSF is not claimed to be the exact effective survey PSF.
- [x] Run the paired-difference identifiability control (`injected - SCI_ORIG`), which recovers the injected target essentially exactly and isolates real-scene contamination/deblending as the dominant failure source.
- [x] Preserve D1g-D1k neighbour masking/template/deblending diagnostics. None provides a coherent global solution. D1k remains 13/18 target-bound-hit fits and does not improve both AB=26 near-source and intermediate regimes; see `benchmarks/gate_d/COSMOSWEB_D1_DEBLENDED_NEIGHBOUR_TEMPLATES_RESULT.md`.
- [ ] **D1l limited simultaneous parametric-neighbour Sérsic diagnostic.** Reuse D1k's frozen deblending, model at most the three nearest children with free PSF-convolved Sérsic nuisance morphology, mask only exact support for remaining children, and keep the target fit/bounds unchanged; see `benchmarks/gate_d/COSMOSWEB_D1_PARAMETRIC_NEIGHBOUR_SERSIC_PROTOCOL.md`.
- [ ] Quantify the L1 source-shot-noise/covariance approximation as a separately declared experiment.
- [ ] Design the L2 exposure-injection adapter and compare L1 versus L2 on a small controlled sample.

Gate D remains more important to production readiness than reproducing additional redundant literature cases, because it tests the actual survey transfer function, crowding/background/WCS/segmentation interactions, and measurement-pipeline recovery.

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
