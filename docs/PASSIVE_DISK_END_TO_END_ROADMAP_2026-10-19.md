# Passive Disk / COSMOS-Web — End-to-End Research Roadmap

**Living project handoff and execution plan.** Created 2026-10-19 after the discussion with Priyanka Jalan, Gutu Dereje and Angel Rodriguez. **Main science target: passive DISKS.** The spiral-recovery literature is a methodological guide, not a decision to rename the sample or replace its selection with an arm-visibility classifier.

> **START HERE on every return to the project.** Read the live checkpoint below, inspect the latest linked numerical receipts, perform only the first unchecked task whose dependencies are satisfied, record a dated result, and update this file. Do not infer that a code run, a fitted parameter, or a visual demonstration is a calibrated completeness correction.

## 0. One-minute checkpoint — as of 2026-10-19

**What exists:**
- A frozen, catalog-based **GOLD403 = 403 selected passive-disk candidates** with morphology and visual-calibration information. This is a selected sample, **not** the survey denominator.
- **GOLD91 = 91 catalog objects at 0.75 <= z < 1.00**, a predeclared high-count slice; **90** had supported interpolated models, **73** were input disk-classified, **56** real-context results were measurable, and **45 of the 73** input disks remained both measurable and disk-classified; **28/73** were unmeasurable (27 low-S/N; one quality failure). These numbers are **conditional selected-sample structural recoveries**, **not** detection completeness and **not** 45 recovered spiral arms out of 91.
- A completed but **historical** 403 x 2 E0/E1J = **806-case** real-background fitting campaign: **786 OK / 20 ERROR**. Its single-Sérsic-n values were inferred from B+D truth, so its combined disk classes are **not final science**. Do not publish those classifications or repeat the 806 cases just because a CSV is complete.
- A **corrected 30-object two-branch clean pilot**: 30/30 successful; native pass fraction 1.0 for both branches; median |delta n| ~ 0.000865, median |delta B/T| ~ 0.00876, 0/30 native-clean-to-z3-clean disk-class changes. This is a technical pilot, not population completeness.
- A **real-cutout R3 test**: 8 eligible COSMOS-Web galaxies x 5 target redshifts = 40 requested cells, **39 spectrally supported**, measured source-only plus three real-context placements = **156 OK descriptive metric rows**. These are real galaxy SCI cutouts transferred/injected into actual COSMOS-Web background; **not a final disk recovery/classification curve**.
- A defensible example is **COSMOS2025 ID 83970 (z_source = 0.3299; inherited visual label = clear_spiral)** with rendered panels at z = 1, 1.5, 2, 3 (z = 2.5 can be included in the full R3 ladder). **ID 316667 (z = 0.4921; smooth_disk_S0)** is nearer the z~0.5 source asked for in the meeting; verify passivity, morphology and usable output before presenting it as a *passive* disk.
- The 2026-10-11 continuation reproduced **395/403 supported morphology spectral brackets** (8 unsupported), and performed **24/24 reruns** across eight disputed fits. Two objects change B/T boundary classification across contexts; several fits remain systematically biased. The corrected full-403 scientific production is **on hold** pending fitted-model identifiability / numerical gates. The **1,580 input rendering precision controls** passing do not resolve fitting identifiability.

**Current main bottleneck:** establish a validated and frozen selection/recovery estimator; independently check simulation realism at the target redshift; resolve the structural n/B/T pipeline's remaining gates. **Do not claim a completeness-corrected passive-disk evolution result yet.**

**Next immediate action [OPEN]:** assemble and email 1–3 self-explanatory PNG/PDF image ladders (including the native original) to Priyanka, with clean/source-only and isolated/intermediate/crowded contexts clearly distinguished. Then freeze the z~0.5 -> z~1 matched real-galaxy control protocol **before** inspecting the comparisons.

**Source of truth for the current numerical state:** [Recovery results (2026-10-11)](https://github.com/physicsbahare/astro-forward-modeling/blob/research/gold403-gates-20261011/docs/RECOVERY_RESULTS_2026-10-11.md), [remaining numerical gates](https://github.com/physicsbahare/astro-forward-modeling/blob/research/gold403-gates-20261011/docs/GOLD403_GATE_RESOLUTION_PROTOCOL_2026-10-11.md), [recovery gate inventory](https://github.com/physicsbahare/astro-forward-modeling/blob/research/recovery-20261011/docs/RECOVERY_GATES_2026-10-11.md), [R3 result](https://github.com/physicsbahare/astro-forward-modeling/blob/jades-realimage-batch/benchmarks/passive_spiral_redshift/R3_RESULT.md). Historical README and RUNBOOK are older than these receipts; **do not promote an older "next run" instruction above an explicitly unresolved newer gate.**

---

## 1. Scientific question, scope and non-goals

**Primary question:** To what extent are observed passive-disk demographics in COSMOS-Web/COSMOS2025 biased by finite resolution, surface-brightness dimming, wavelength-dependent morphology, PSF and sampling, survey depth, background, neighbors, and structural fitting/selection failure? How much of the apparent redshift trend can be interpreted after correcting **validated** observational selection effects?

**Primary population:** passive/quiescent, structurally disk-like galaxies under the *existing* frozen COSMOS2025 science sample cuts. Use the project's actually adopted passive criteria and **both** structural branches: single-Sérsic **n < 2.5** and physical **B/T < 0.5**, conditional on measurement and identifiability quality. The visual labels **clear_spiral**, **smooth_disk_S0**, etc., remain a **secondary, explicitly distinct** morphology layer.

**Distinct estimands (never combine by changing denominators):**
1. **Observability/detection** of galaxies under the released survey selection and depth.
2. **Measurability** of n/B/T given detection and quality rules.
3. **Disk-class retention** when the *same input galaxy* is transferred to a target redshift and passes the frozen n/B/T rule.
4. **Disk/non-disk confusion (purity as well as recovery)**, requiring negative controls.
5. **Optional spiral-arm visibility** within the subset with secure arm labels (an auxiliary test, **not** the passive-disk definition).
6. **Observed passive-disk fractions** with specified parent denominators, and later **selection-corrected fractions only within calibrated support**.

**Not our main paper:** an independent census of all high-z spiral patterns, a reproduction of the JADES AGN subtraction pipeline, a new general-purpose extractor/deblender, a literal JWST exposure simulator, or a physical track of one specific galaxy's real progenitor. Coordinate scope with collaborators and earlier parallel spiral work before drafting overlapping claims.

**Default physics: E0 observational transfer.** Hold the intrinsic physical galaxy image, size and luminosity fixed; change observing redshift, wavelength mapping, angular size, specific intensity, PSF, pixel sampling and survey context. Gutu's JADES method optionally includes intrinsic size/luminosity evolution; this answers a different question. Retain E1J and any intrinsic-size evolution **only as separately labeled sensitivity experiments**, not mixed into the E0 completeness denominator.

---

## 2. Priyanka discussion of 2026-10-19 — action log and decisions

Meeting summary is a working note, **not** proof of paper results; review wording against recordings/collaborators if there is disagreement. Participants discussed:

| Meeting item | Working interpretation / action | Status |
| --- | --- | --- |
| Show clear low-z to high-z examples, not notebook code | Prepare original + z = 1, 1.5, 2, 2.5, 3, label filters, angular scale, display stretch, original vs injected background. Email examples as PNG/PDF. | OPEN |
| Validate against real target-z controls | For one z~0.5 input, compare the simulated z~1 observation to ~10–15 **real** z~1 analogs matched in mass and rest-frame luminosity; expand across more inputs before population conclusions. | OPEN |
| Primary analysis isolates observational effects | Leave intrinsic size/luminosity unchanged for E0. Put empirically motivated evolution in secondary tests and have Priyanka review its motivation. | Agreed working baseline |
| Examine single-band vs multi-band K correction | Test both on identical sources/redshifts/PSFs and compare *classification stability*, not just integrated flux. Do not assume either is superior without a held-out/matched diagnostic. | OPEN |
| Avoid equating a good structural fit with spiral visibility | Resolve the appropriate paper-facing passive-disk selection; label genuinely resolved spirals separately. Treat morphology reliability beyond z~2.5 as an **empirical question**, not a universal cutoff. | OPEN |
| Recovery as a function of redshift and conditions | First measure a validated recovery/confusion surface; choose fitted dependence on z (or 1+z) only if data justify it. | OPEN |
| Priyanka's example literature and code | Read Margalef-Bentabol et al. 2022, especially Figs. 8–11. Priyanka indicated she would share code; await actual files before claiming direct comparison. | PENDING |
| Communicate visualization results | Share labeled examples and a brief methods/limitations note, no expectation that collaborators open Jupyter notebooks. | OPEN |

**Corrections to possible meeting-summary shorthand:**
- The 45 GOLD91 result is **45/73 input disks meeting a measurement + disk-class criterion**, not “45/91 spirals with visible arms.”
- The slope **(1+z)^(-1.1)** in Margalef-Bentabol et al. (2022) describes a fitted *corrected population spiral-fraction trend*; **not** a ready-made COSMOS-Web recovery law.
- That paper's artificial-redshifting implementation **does include** a brightness adjustment for stellar-population evolution in addition to cosmological transfer. Its validation/reclassification *workflow* is relevant even though its physics assumptions are **not identical** to our E0 baseline.
- The meeting note's “n and B/T only reliable for z<2.5” is **not a universal physical or survey-specific proof**. Test resolution, size/PSF, S/N, fitting quality and degeneracy instead of a hard z threshold.
- A snapshot at z=3 by itself **cannot** determine a redshift-dependent correction for an evolving population.

---

## 3. Frozen invariants / safety rules (apply to every step)

### 3.1 Physics, units and spectral support
- State exactly whether source images are **observed real SCI cutouts**, **clean parametric structural models**, or **residual/AGN-subtracted images**. These are different experiments; do not silently mix truth definitions.
- For corresponding *rest-frame emitted frequency*, wavelength mapping is: **lambda_source_obs = lambda_target_obs * (1+z_source)/(1+z_target)**.
- Correct **specific-intensity** transfer on matching rest frequency: **I_nu,target / I_nu,source = [(1+z_source)/(1+z_target)]^3**. In the structural integrated-flux convention, **F_nu,target / F_nu,source = [(1+z_target)/(1+z_source)] * [D_L(z_source)/D_L(z_target)]^2**. Use one consistent representation with correct pixel-solid-angle accounting; **do not apply an extra Tolman factor**.
- Angular-size scaling for unchanged physical structure: **theta_target / theta_source = D_A(z_source)/D_A(z_target)**. Do not assume monotonic shrinkage beyond the angular-diameter-distance maximum.
- Respect exact survey **BUNIT**, pixel area, calibrated flux units, WCS, source/target PSF support, filter-throughput metadata and 0.03 arcsec/pixel mosaic conventions where applicable. No unadvertised flux renormalization.
- Multi-band R3 uses **PSF-homogenized F115W, F150W, F277W** and a quadratic per-pixel F_nu model integrated over target NIRCam transmission. Reject **unsupported** target passbands instead of quietly extrapolating; save condition numbers, signed/negative coefficients and predictions. A brightness-only scalar shortcut and curved-throughput synthesis **are not equivalent by assumption**.
- Compare single-band nearest-rest-wavelength and multi-band throughput outputs with identical source and target conditions; include spatial differences and recovered n/B/T where supported.

### 3.2 PSF, noise, injection and provenance
- Never sharpen or deconvolve an existing observed source PSF unless a separately validated technique and error model are explicitly adopted; transfer is degradation-only.
- For COSMOS-Web PSFEx, preserve **spatial variation** and signed wings, use documented catalog zero-based to PSFEx one-based (+1,+1) coordinates, render GalSim effective PSF with **no_pixel**, and do not double-apply pixel response.
- Inject deterministic source signal into an **already noisy real SCI**. Do **not** add a second realization of background/sky noise. Keep original SCI, ERR/WHT and segmentation products read-only; keep an injected output as a separate derived product. The default experiment leaves existing ERR/WHT unchanged but must separately flag missing **injected-source shot variance** / imperfect resampled-pixel covariance handling.
- Do not manufacture Poisson noise from MJy/sr or treat drizzled i2d VAR_POISSON as an exposure-level simulator without proven count/exposure/resampling provenance.
- Keep target-background placement and source-neighbor context **frozen before** inspecting image outcomes. Preserve isolated/intermediate/near-source cases including poor outcomes and failed placements.
- Identify misalignment, clipped source radii, nonphysical component flux, low S/N, non-convergence, parameter bounds, missing/undefined B/T and spectral failures explicitly. **Unknown does not mean non-disk.**

### 3.3 Correct structural comparison
- The **n branch** must be single-Sérsic truth -> single-Sérsic native/target fit.
- The **B/T branch** must be n=1 disk + n=4 bulge truth -> same B+D native/target fit.
- Do **not** compare single-Sérsic n fitted to B+D truth directly to the catalog's independent single-Sérsic n. The historical 806-case campaign violated this equivalence for its published-style n.
- Maintain: catalog selection -> rest-band/morphology mapping -> native-clean -> target-clean -> target-real. Report the effect of each transition separately.
- Check total analytic component-flux convention versus finite-stamp normalization; avoid model-radius clipping and insufficient adaptive supersampling. A successful optimizer return/low chi-square does not establish B/T identifiability.
- A statistical surface based on true input disk positives **alone** gives retention/sensitivity, not purity. Need non-disk controls and a measurable detection/quality model to correct observed fractions.

### 3.4 Sampling and inference
- Do not omit faint/crowded/failed/unsupported injections from attempted-case denominators without separately reporting the exclusion reason. Distinguish *outside supported physics domain* from *failed observational detection/classification*.
- Respect survey selection, segmentation, PSF, noise-depth footprints, redshift/mass distributions, field/tile correlations and provenance; use independent positions/realizations with recorded seeds.
- Control overfitting: predeclare source and control selection, labels, thresholds, matching tolerances, model comparisons, and primary outcomes **before seeing target-z recovery**.
- Predefine uncertainty estimates (source-level and tile/context clustered bootstrap or hierarchical estimates, plus binomial intervals where appropriate); avoid treating multiple placements of one galaxy as independent galaxies.
- Report coverage/support and model-failure rate with correction weights. Do not extrapolate corrections beyond measured mass, luminosity, redshift, size, S/N and crowding support.

---

## 4. Roadmap: sequential tasks with completion gates

Use **[x]** only for items established by linked receipts. Everything else below is **[ ]** until a new frozen, inspected receipt exists. Adjacent phases can be performed in parallel **only** if neither depends scientifically on unresolved results.

### Phase 0 — Reproducibility, estimand and data map [DO FIRST]

- [ ] **0.1 Verify actual live working tree / branch / notebook.** Record current git SHA, notebook hash, local output roots, package versions and input manifest. Latest research evidence may be on **research/gold403-gates-20261011** rather than default main. Do not assume a notebook is runnable or outputs exist merely because a report says it ran previously.
- [ ] **0.2 Freeze science goal and analysis population.** Write one paragraph defining passive disk vs visually confirmed spiral; freeze selection columns, quiescence definition, current n/B/T cuts, redshift/mass range, parent denominator(s), sample exclusions, and outcome variables. If collaborators request changes, give them a separate version instead of silently changing GOLD403.
- [ ] **0.3 Create an experiment manifest** for all further runs (source_id, original z, target z, original band(s), effective rest wavelength, data-unit/PSF/WCS checks, truth family, target tile/background coordinates, RNG seed, method branch, git SHA, file hash, failure code). Keep local private/large data out of the public repository.
- [ ] **0.4 Freeze explicit primary analysis as E0**. Register E1J and possible size evolution as secondary sensitivity, never as corrections combined with primary E0 by default.

**Deliverable / gate:** committed scope/manifest schema, reproducible environment & data availability report, agreed paper-facing primary observable. No science batch until this gate passes.

### Phase 1 — Priyanka-ready image examples [FIRST EXTERNAL DELIVERABLE]

- [ ] **1.1 Build figure(s) from saved real R3 outputs**: one clear spiral (**ID 83970, z=0.3299**) and at least one contrasting smooth/faint disk. Show **native original** plus simulated z = 1, 1.5, 2, 2.5, 3, including target-band labels. Never substitute an illustrative model for the true original without labeling it.
- [ ] **1.2 Include transfer-only and real COSMOS-Web** injected scenes (isolated, intermediate, near-source) with **matched field of view, angular rulers, orientation, display-stretch policy and noise/sky indications**. A user-friendly color map/asinh stretch may help; **display choices are not quantitative measurements**. Save original quantitative arrays; no visually tuned contrast to alter classification.
- [ ] **1.3 Verify provenance and headers** for native and every target panel, include one-line method caption, target filters, wavelength support, source type, luminosity-evolution setting E0, what does/does not represent real imaging.
- [ ] **1.4 Email only PNG/PDF (and optional one-page summary)** to Priyanka; invite feedback on whether apparent structure/noise looks physically plausible. Log feedback and retain original versions.

**Deliverables:** PNG/PDF ladder, per-panel provenance CSV, email date and any collaborator feedback. **Gate:** figure accurately represents already computed science arrays; native-source image actually comes from the same ID.

### Phase 2 — Literature and independent-method comparison

- [ ] **2.1 Read Margalef-Bentabol et al. (2022)** methodology and Figures **8 (image ladder), 9 (simulated vs real surface brightness), 10 (spiral recovery curve), 11 (corrected observed fraction)**. Extract the *logic*, not its classification cuts, population fit or HST-specific numbers. Document paper's use of stellar-population brightness evolution rather than asserting it is E0.
- [ ] **2.2 Check FERENGI (Barden 2008), Yu et al. (2023), van der Wel et al. (2014)** against our implementation: observed source PSF, single-vs-multi-band K correction, target filter response, cosmological surface brightness, size/luminosity evolution and support ranges.
- [ ] **2.3 When received, obtain Priyanka's actual code and Gutu's method/code**, record code versions/licensing, required inputs and algorithmic differences. Do not assume notebook input compatibility. JADES results from Gutu are **method-development evidence, not COSMOS-Web population data**.
- [ ] **2.4 Run a small apples-to-apples head-to-head**: same original pixel source(s), cosmology, source/target filters, PSF, pixel scale, E0 only, and frozen target scene. Compare image-level integrated flux, flux radial profile, angular size, q/concentration, and fitted n/B/T when valid; separate single-band and multi-band spectral branches.
- [ ] **2.5 Report disagreements without tuning them away**. Investigate causes (PSF, WCS, transfer factor, fixed physical size, throughput, noise, stamp normalization, labels), and decide whether a simpler single-band approximation meets a predeclared morphology/classification tolerance.

**Deliverables:** literature-method comparison table; reproducible head-to-head comparison with per-case source/target arrays and diagnostic plot; decision log with assumptions. **Gate:** the chosen E0 operator has been verified in matched conditions and its spectral/PSF limits documented.

### Phase 3 — Priyanka's real z~1 control experiment [TOP PRIORITY SCIENTIFIC VALIDATION]

- [ ] **3.1 Freeze source and comparison design BEFORE looking at outcomes.** Start with a well-resolved genuine z~0.5 example (candidate **316667 at z=0.4921**, or another prespecified eligible object). Verify its photometry, passive status, visual morphology, image quality and that its z=1 simulation is valid. Consider additional sources for generality.
- [ ] **3.2 Select ~10–15 real z~1 COSMOS-Web galaxies** from a reproducible parent catalog, matching **stellar mass and rest-frame luminosity** (and ideally broad morphological/quiescence class, color and size/selection support). Define z window, mass/L tolerances, reference filter, depth/field restrictions and treatment of missing measurements BEFORE selection. Use **rest-frame luminosity**, not apparent magnitude from two different z as if it were intrinsic.
- [ ] **3.3 Ensure comparability:** same target observed band/rest-wavelength intent, calibration, pixel scale, PSF response, FOV, background treatment and observational depth. Simulated galaxies and observed controls must be subject to the same detection/measurement policies; match or stratify local depth.
- [ ] **3.4 Figure akin to paper Figure 9:** side-by-side matched galaxy images *and distributions* of surface brightness (define mean/peak/profile and aperture), measured S/N, total magnitude, apparent radius, q, concentration and quality/failure indicators. Do not conclude correctness by eyeballing matching thumbnails only.
- [ ] **3.5 Perform reproducible diagnostics**: rank/distribution comparisons, uncertainty and scatter, identify mismatches in faint outskirts/PSF/sky, and quantify source-selection dependence. **Different galaxies need not have identical arms or structure**; agreement is a *population-level plausibility check*, not a true-pixel reconstruction.
- [ ] **3.6 Optional repeat** at z~1.5 or z~2, and for another source-parameter range after first comparison; no post-hoc controls chosen to make simulated distributions pass.

**Deliverables:** frozen matched-control IDs and selection script, pairwise matched catalog, image figure, surface-brightness & structural distributions, comparison-report PDF/MD. **Gate:** explicit acceptance/limitations of simulation realism (or documented reasons to revise the operator) approved before completeness claims.

### Phase 4 — Resolve GOLD403/GOLD91 numerical/structural blockers [IN PARALLEL WITH PHASE 3]

- [x] **4.0 Archive/diagnose old errors.** The custom renderer failed noiseless truth recovery; exact Lenstronomy/Galight closed loop and perturbed-start controls fixed the convention. Historical 806 receipts are complete (786 OK/20 ERROR), but **not** a corrected science classification.
- [x] **4.1 Correct conceptual branch mismatch in a pilot:** independent single-Sérsic n and B+D B/T native/target chains; 30/30 clean validation reported.
- [ ] **4.2 Resolve *all* remaining corrected-production numerical gates**, not merely input rendering: analytic total-flux B/T vs finite-stamp normalization, clipped truth radii (3 flagged cases), adaptive supersampling convergence, recovered component shape/size/flux validity, persistent alternate-fit solutions, fixed/perturbed-start tests and B/T identifiability. Preserve failures and use predeclared tolerance.
- [ ] **4.3 Build matching native-clean baseline for interpolated GOLD91/GOLD403 sources** using the same exact morphology-band mapping, truth and fitting family, PSF conventions and clean settings as the redshifted target; do not attribute native model representation mismatch to redshift.
- [ ] **4.4 Reconcile effective-wavelength scalar flux with R3 full-throughput quadratic transfer**, including 90-source integrated-flux discrepancy (median curved/scalar factor ~1.049; range of individual cases ~0.922–1.216) and propagation to S/N, fit validity and disk classification.
- [ ] **4.5 Preserve spectral-support failures and ambiguous B/T**, including 8 unsupported GOLD403 morphology brackets, 8 disputed GOLD91 recoveries with 24 repeat fits and two context-sensitive boundary crossings. Explicitly distinguish low S/N, optimizer instability, model mismatch and non-identifiable components.
- [ ] **4.6 Approve a blind quality/identifiability policy** on representative pilots using both correct positive and negative morphological controls; ensure not solely reoptimizing cases whose class initially flips.
- [ ] **4.7 Freeze regression tests, environment, hashes and all case-level failure codes**; only then permit corrected full-sample fitting. Where scientific quality cannot be established, record the domain as uncalibrated rather than inventing probabilities.

**Deliverables:** versioned validated numerical-policy file, corrected pilot receipts and acceptance memo, explicit STOP/GO for 403-scale fitting. **Hard STOP:** no final corrected GOLD403 classification run while the real-context B/T-identifiability gate is unresolved.

### Phase 5 — Freeze passive-disk labels, controls, target bins and actual classifier

- [ ] **5.1 Lock the published/candidate and parent-sample selection independently of injection outputs.** Use the existing passive criteria plus catalog n<2.5, B/T<0.5 where both valid; freeze all quality/S/N, photometric/AGN, mass and redshift rules with provenance. Record the exact denominator definitions (all galaxies, passive galaxies, disks).
- [ ] **5.2 Keep distinct labels:** passive vs star-forming; disk vs non-disk; visually clear spiral vs smooth disk/S0 vs uncertain. Do not label 403 as visually confirmed spirals.
- [ ] **5.3 Define the measurement/recovery path at the *target* z** matching what will be used on actual COSMOS-Web catalog data: source detection, segmentation/deblending treatment, wavelength/band choice, Galight/Lenstronomy or released catalogs, goodness/identifiability and final disk cut. Never use direct truth knowledge for blind target classification.
- [ ] **5.4 Select controlled positive AND negative samples:** confidently measured passive disks, passive non-disks, star-forming disks and any reasonable failure/contamination controls. Predeclare bin coverage in z, mass, luminosity, angular size/PSF, depth and crowding; split development vs held-out evaluation sources.
- [ ] **5.5 Decide auxiliary visual-spiral task (optional):** if studied, write a separate visually labeled input set, blinded human-rating protocol, confidence/uncertain labels and inter-rater agreement. It is not interchangeable with B/T and n-based disk recovery.

**Deliverables:** frozen catalog/selection JSON, labeled source/control manifest and independent classification protocol. **Gate:** every target has a reproducible true input class and same operational target classifier/quality cuts; negatives and uncertain examples have not been discarded.

### Phase 6 — Multi-z forward simulation and pilot recovery (not just z=3)

- [ ] **6.1 Predeclare target grid** (development example: z = 1, 1.5, 2, 2.5, 3; only z_target > z_source) with target passbands and observed-rest-wavelength comparison policy, spectral-bracketing failures and support limits.
- [ ] **6.2 Reuse the real-source R3 branch for visual/morphology transfer** and the exact two-family structural branch for n/B/T validation; these are two separate truth models, not evidence that a Sérsic image contains observed spiral arms.
- [ ] **6.3 Inject into reproducibly sampled real COSMOS-Web backgrounds** spanning isolated, intermediate and near-source/crowded conditions and actual depth/tile strata. Multiple placements per input. Honor original SCI/ERR/WHT/noise, segmentation, PSF and pixel covariance caveats; no double sky noise.
- [ ] **6.4 For each case, record** source and target z, target band, source/target PSFs, wavelength-support status, native/target-clean/target-real measured n/B/T, q, radius, concentration, flux/SNR, crowding, neighbor fits, convergence/bounds, class labels, fails and weights. Report target detection separately from fit/selection success.
- [ ] **6.5 Freeze the small pilot** (e.g. 10–30 quality-controlled input disks plus matched non-disks) for visual audit, repeated contexts and independent human/classifier checks before expanding; do not choose only bright success examples.
- [ ] **6.6 Compare both single-band and curved-throughput methods on held-out pilot objects** and, separately, E0 versus optional E1J as a brightness sensitivity. Report if morphological decisions change and their uncertainties; do not silently tune SED or PSF.
- [ ] **6.7 Only if phases 3–5 and pilot pass:** compute multi-z cases for representative GOLD403 and negative parent controls, with object/context clustered uncertainty. Run z=3 corrected full batch only after Phase 4 passes; keep work restart-safe, traceable and reproducible.

**Deliverables:** real-image ladder grid, machine-readable all-attempts table, target-z fits and failure receipts, pilot presentation figures, GO/NO-GO review. **Gate:** complete detection/measurement/classification accounting and supported repeatability across relevant z and source conditions.

### Phase 7 — Recovery matrix, completeness/purity and uncertainties

- [ ] **7.1 Separate stage probabilities**, e.g. P(detected | intrinsic class, X), P(measurable | detected, X), P(labelled disk | measurable, intrinsic class, X); X includes z, observed/rest-frame brightness, stellar mass, resolvedness, PSF/depth and crowding. Clearly distinguish source class and *measured* class.
- [ ] **7.2 Calculate a confusion/recovery matrix with negative controls:** true disk -> measured disk / non-disk / not measurable; true non-disk -> measured disk / non-disk / not measurable. Report false positives, contamination and ambiguous outputs, not only disk survival.
- [ ] **7.3 Publish redshift-dependent recovery first as binned results** with sample counts and uncertainties, compared against surface brightness, luminosity and size strata. Fit a simple C(z) or (1+z) exponent **only after** assessing mass/SNR/size/depth/crowding covariates and goodness-of-fit. Do not reuse Margalef-Bentabol's corrected-fraction exponent -1.1 as the transfer law.
- [ ] **7.4 Quantify uncertainty/support:** source-level confidence/bootstrap, background/tile clusters, finite-N classification uncertainty, fit alternative modes, photo-z/mass migration, correlated mosaic noise, unmatched spectral cases, SED method and E1J sensitivity. Reserve held-out objects for final coverage validation.
- [ ] **7.5 Audit completeness vs purity:** identify where correction weights become huge/undefined; set predeclared valid support domain and report out-of-support observed estimates separately. Use forward-model likelihood/confusion correction where simple inverse weights would be unstable.
- [ ] **7.6 Stress-test** alternate but predeclared n/B/T thresholds, low-S/N policies, selection parent, single/multi-band, visual subset, sky-depth and context; keep negative outcomes.

**Deliverables:** recovery/confusion matrix by z and covariates, statistical coverage report, Fig-10-style structural-disk recovery plot with defensible denominator, explicit note that spiral-arm recovery is a different curve. **Gate:** independent/held-out validation meets predefined stability criteria or final manuscript remains explicitly observational/uncorrected.

### Phase 8 — Observed versus corrected passive-disk demographics

- [ ] **8.1 Recover parent sample & field selection functions.** Current observed measurable parent from 2026-10-11 has **36,905 eligible galaxies**, **25,642 with usable paired-band morphology**, **11,263 morphology-unknown**. Those unknowns are **not** automatically non-disks.
- [ ] **8.2 Keep observed conditional statistics separate:** among 25,642 morphology-measurable galaxies, GOLD403/25,642 ~ **1.572%** (passive disk among all measurable); 403/4,047 ~ **9.958%** (disk among measured passive); 403/15,171 ~ **2.656%** (passive among measured disks). These have different denominators and are **not** survey-wide completeness-corrected intrinsic fractions.
- [ ] **8.3 Validate detection completeness aligned with WHT/depth footprint and mass/redshift selection**, including parent star-forming/passive comparison, mass-to-light limit versus detection probability and correlated missing morphology. Simple 95th-percentile M/L completeness is **not** 95% detection completeness.
- [ ] **8.4 Combine validated positive/negative confusion and detection/morphology support** with observed bins in z/mass, including photo-z/mass migration, field/tile variance, AGN/exclusion uncertainties and prior sensitivity. Never infer corrected population counts solely from **45/73**.
- [ ] **8.5 Propagate full uncertainty** into measured *conditional* and corrected results. Keep original passive selection (NUVrJ/main-sequence/SFR) and note SED SFR-floor / censoring limitations; do not claim precise intrinsic SFRs below model-prior floors.
- [ ] **8.6 Present uncorrected and corrected trends side by side**, within coverage, with qualitative physical interpretation clearly distinguished from observational effects. If recovery calibration does not pass, publish only supported observed statistics plus validated bias bounds/sensitivity, not an invented evolution claim.

**Deliverables:** Table 1 sample selection/denominators, observed-fraction plots, validated corrected curves where supported, systematic/uncertainty table and transparent unsupported-domain summary. **Gate:** inferential conclusions agree with the calibration's validated support and selection estimand.

### Phase 9 — Paper figures, manuscript, coauthor review and publication

- [ ] **9.1 Agree exact novel paper scope/title and collaborators**; explicitly avoid unjustified overlap with prior parallel spiral identification projects. Record roles and collaboration feedback; do not imply Priyanka's methodological suggestions automatically authorize overlapping census claims.
- [ ] **9.2 Freeze figures**: (F1) data/selection flowchart & redshift-mass coverage; (F2) low-z original -> multi-z E0 galaxy ladder with real background; (F3) simulated-versus-real matched controls (paper Fig-9 analogy); (F4) clean/native/real n/B/T examples and identifiability/failure classes; (F5) disk classification confusion/recovery versus z, size/brightness/depth/context (paper Fig-10 analogy); (F6) observed vs supported corrected passive-disk redshift/mass trends (paper Fig-11 *logic*, not its spiral classifier); (F7 optional) wavelength & intrinsic-evolution sensitivity. Include native source, target band, PSF/scale, display stretch and S/N on image figures.
- [ ] **9.3 Freeze tables**: sample & parent counts / selection, source properties and target grid, recovery cases/failures/confusion matrix, numerical validation, systematic budget, observed/corrected fractions and source/output provenance.
- [ ] **9.4 Draft scientific sections in order:** Introduction (passive disks and bias problem, distinction from spirals); Data & sample (COSMOS-Web/COSMOS2025 selection); Method (E0 and controlled alternatives, real-pixel and parametric branches, PSF, noise, fitting); Validation (numerical, matched real z, cross-code); Results (recovery first, corrected demographics if justified); Discussion (identifiability, quenching, model limitations); Conclusion; Appendices (failures, conversion equations, robustness, code/data availability).
- [ ] **9.5 Check every plotted number against one immutable results table.** Report failed cases, 403 vs 91 vs 73 denominators, conditional vs corrected claims, no false spiral-arm labels, proper uncertainty levels, sample support and literature comparison without transporting published empirical fit coefficients as our own.
- [ ] **9.6 Internal review and authorship:** circulate draft with Priyanka/Gutu/Angel/other collaborators as relevant; request code/method critique, document resolved scientific comments, decide which related JADES comparisons are appendix vs separate project.
- [ ] **9.7 Reproducibility release:** pin git commit/DOI if appropriate; publish only non-sensitive configs, tests and compact machine-readable result tables, captions and manifest; document how authorized users with licensed/raw survey data regenerate private figures and science products. Do not upload huge cutouts or embargoed catalogs by default.
- [ ] **9.8 Pre-submission signoff:** coauthor consent, figure rights, selection/recovery gate pass report, citations, journal formatting, supplementary material, manuscript consistency, arXiv/submission approvals and response-to-referee plan.

**Deliverables:** complete internally reviewed paper, figure/table provenance, reproducibility bundle and submission-ready manuscript. **Final gate:** conclusions do not exceed demonstrated recovery/selection calibration.

---

## 5. Practical ordering and blocking-dependency map

1. **NOW:** Phase 0 baseline + Phase 1 examples -> email Priyanka.
2. **FIRST SCIENCE CHECK:** freeze and perform Phase 3 matched z~0.5 -> z~1 real-control test, while doing Phase 2 method/paper review.
3. **IN PARALLEL:** Phase 4 close *fitted* B/T/SED/native truth gates. Numerical tests that pass input rendering are not enough.
4. **BEFORE CLASSIFICATION CURVE:** Phase 5 freeze actual passive-disk classifier and parent/negative samples.
5. **NEXT:** Phase 6 small blind multiple-z real-background pilot; then independently validated larger run.
6. **THEN:** Phase 7 confusion/completeness with error/support; Phase 8 properly selected observed-versus-corrected science.
7. **FINALLY:** Phase 9 draft, review, reproducibility, submission.

### Stop/continue decision rules

| Situation | Required behavior |
| --- | --- |
| Example images ready but control comparison not done | Share images with “illustrative real-data forward test” caption, **not** validated completeness. |
| Matched-control distributions disagree | Diagnose selection/PSF/depth/filter/pixel/noise, do not fit correction to hide mismatch. |
| Scalar vs full-throughput methods alter classification | Freeze comparison and carry method uncertainty or restrict spectral domain. |
| B/T non-identifiable or numeric render tolerance failed | Flag unknown, postpone affected classifications/full production; prefer supported subsample with limitations. |
| Recovery too sparse in faint/high-z/crowded cells | Report supported domain and failure bounds, not arbitrary extrapolated weights. |
| Only positives injected | Report retention only; **cannot** claim purity-corrected fraction. |
| No agreed parent selection/denominator | Observed selected-sample pilot only, not cosmic frequency evolution. |
| Need to choose between passive disk and spiral arm | Keep passive-disk results primary; visualize/label spiral arms as optional auxiliary science, independently. |

---

## 6. Minimal output structure for every new work session

Use this pattern locally, with compact **nonprivate** checkpoint summaries committed to docs or the roadmap:

- **Task ID, date, branch + commit SHA, input hashes**, source catalog revision, software environment.
- **Protocol frozen at commit**, explicit estimand, source IDs, target z and band, truth family, E0/E1J branch, seed, contexts, quality/stop rules.
- **Attempted, supported, successful, failed/unknown** counts. No denominators silently changed.
- **Per-case table** with status/error reason, truth and recovered quantities, uncertainties, context/depth/SNR, quality/identifiability and classification.
- **Key diagnostic figure(s)** with independent controls, numerical closure and astrophysical interpretation; explicitly say what they **do not** establish.
- **Gate decision = PASS / FAIL / CONDITIONAL / BLOCKED**, with frozen decision criterion and link to receipts.
- **Next single executable step**, exact prerequisite files, and expected deliverable.

### Copy this checkpoint at the top of this roadmap after each milestone

**Date:** 2026-10-19  
**Last completed trustworthy gate:** R3 real-source image/scene proof-of-concept; 2026-10-11 catalog and numerics checkpoint only partial; corrected full GOLD403 blocked.  
**Current task:** Phase 1 PNG/PDF image ladders for Priyanka; begin Phase 3 predeclared matched real-z control design.  
**Blocking scientific issues:** missing matched-control validation, final classification/denominators, B/T fitted identifiability, morphology-band/spectral transfer reconciliation, detection/morphology recovery matrix.  
**Next deliverable:** example figures + matched z~1 control selection protocol.  
**Don't do:** publish 45/91 spiral claims, treat 806 historical as final, apply paper's (1+z)^(-1.1) as our completeness or launch corrected 403 production before gates.

---

## 7. Reference shelf (stable canonical links)

**Priyanka's meeting reference / methodological template**
- [Margalef-Bentabol, B. et al. (2022), *Observations of the initial formation and evolution of spiral galaxies at 1 < z < 3 in the CANDELS fields*, MNRAS 511, 1502–1517, DOI:10.1093/mnras/stac080](https://doi.org/10.1093/mnras/stac080). Read §§4 artificial redshifting and Figs. 8–11; the paper studies **visual spiral reclassification**, includes **population-brightness evolution**, and fits a corrected spiral population trend. Adapt its experimental design, **not** its spiral labels/coefficients to our passive disks.
- [Barden, Jahnke & Häußler (2008), *FERENGI: Redshifting Galaxies from SDSS to GEMS, STAGES, and COSMOS*, ApJS 175, 105–115, DOI:10.1086/524039](https://doi.org/10.1086/524039). Foundational observed-image redshifting, PSF/wavelength handling and source preservation.
- [Yu, S.-Y. et al. (2023), *Redshifting galaxies from DESI to JWST CEERS: Correction of biases and uncertainties in quantifying morphology*, A&A 676, A74, DOI:10.1051/0004-6361/202346140](https://doi.org/10.1051/0004-6361/202346140). Multi-band/pixel-SED, morphology biases, observational transfer choices.
- [van der Wel et al. (2014), *3D-HST+CANDELS: The Evolution of the Galaxy Size-Mass Distribution since z = 3*, ApJ 788, 28, DOI:10.1088/0004-637X/788/1/28](https://doi.org/10.1088/0004-637X/788/1/28). Observed **population** evolution at fixed mass, with early/late definitions linked to star formation; **not** a unique time history of a passive disk. Relations calibrated over 0 < z < 3.
- [COSMOS2025 catalog documentation](https://cosmos2025.iap.fr/catalog.html). Released survey columns, selection, provenance and native catalog context.

**Project-specific evidence / do not supersede**
- [2026-10-11 full recovery report](https://github.com/physicsbahare/astro-forward-modeling/blob/research/gold403-gates-20261011/docs/RECOVERY_RESULTS_2026-10-11.md)
- [2026-10-11 GOLD403 blockers](https://github.com/physicsbahare/astro-forward-modeling/blob/research/gold403-gates-20261011/docs/GOLD403_GATE_RESOLUTION_PROTOCOL_2026-10-11.md)
- [2026-10-11 recovery gate summary](https://github.com/physicsbahare/astro-forward-modeling/blob/research/recovery-20261011/docs/RECOVERY_GATES_2026-10-11.md)
- [2026-10-01 two-branch pilot](https://github.com/physicsbahare/astro-forward-modeling/blob/jades-realimage-batch/docs/CORRECTED_TWO_BRANCH_PILOT_2026-10-01.md)
- [Passive disk structural conventions](https://github.com/physicsbahare/astro-forward-modeling/blob/jades-realimage-batch/docs/PASSIVE_DISK_Z3_METHOD.md)
- [R3 real COSMOS-Web multi-object pilot](https://github.com/physicsbahare/astro-forward-modeling/blob/jades-realimage-batch/benchmarks/passive_spiral_redshift/R3_RESULT.md)
- [R3 spectral-method amendment](https://github.com/physicsbahare/astro-forward-modeling/blob/jades-realimage-batch/benchmarks/passive_spiral_redshift/R3_SED_METHOD_AMENDMENT.md)
- [Passive Spiral scope decision](https://github.com/physicsbahare/astro-forward-modeling/blob/jades-realimage-batch/benchmarks/passive_spiral_redshift/SCOPE_DECISION.md)
- [GOLD403 selected z-distribution and GOLD91 definition](https://github.com/physicsbahare/astro-forward-modeling/blob/jades-realimage-batch/docs/GOLD403_FINAL_REDSHIFT_DISTRIBUTION_2026-09-21.md)

**Meeting provenance:** Gemini notes titled *Artificial redshifting meeting*, 2026-10-19, shared by user in discussion. This public roadmap summarizes **scientific actions**, not participants' addresses or the private meeting transcript. Reconfirm uncertain interpreted commitments (e.g. code delivery and whether to adopt a specific single-band rule) directly with participants.

---

## 8. Definition of done for the WHOLE PROJECT

The project is truly finished only when: **(a)** a reproducible input passive-disk + parent selection and comparison/control samples are frozen; **(b)** an E0 artificial-redshifting operator passes numerical, independent-code and target-real-galaxy checks; **(c)** native structural truth, PSF/SED and real-context fitting identifiability are validated or limitations explicitly bounded; **(d)** a multi-redshift detection/measurement/classification confusion & recovery surface with uncertainty and valid support exists; **(e)** observed and only defensibly corrected passive-disk demographics are compared with literature; **(f)** every number/figure and exception is traceable to immutable outputs; and **(g)** coauthors approve and the manuscript/reproducibility package is ready to submit. If (b)–(d) cannot be met, limit the paper to validated observed results and a clearly labeled simulation/recovery-bias study instead of overstating population corrections.

**End-of-session habit:** update the one-minute checkpoint, tick only completed gates, link the receipt/commit, and write the next task in a form that could be followed without this chat.
