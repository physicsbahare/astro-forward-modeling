# Literature backlog — passive disks and forward modeling (2026-10-23)

**Audit (2026-10-23):** Core references were rechecked against arXiv titles and abstracts where available; three missing/placeholder links and the 2022 foundational link were replaced with canonical arXiv IDs. Six peripheral entries were moved below the active list. **Full-paper replication/code validation is not claimed.** The earlier version remains available in Git history. The deterministic stand-alone toy script and numerical report were committed on [the separate experiment branch](https://github.com/physicsbahare/astro-forward-modeling/tree/experiment/toy-bt-identifiability-20261023/isolated_experiments/2026-10-23_toy_bt_identifiability).

**Purpose:** Curated, actionable reading list from the October 2026 arXiv discussions. This is a *research backlog*, not a claim that every paper has been fully audited. Every entry has a link, a plain-language takeaway, a project-specific application, and a proposed follow-up. **Check the actual full text, tables, code/data releases and sample definitions before citing quantitative results.** Prior chat summaries are provisional except where independently verified below.

**Project scope:** COSMOS-Web GOLD403 passive-disk candidates; distinguish the **single-Sérsic n < 2.5 branch** from the **B+D B/T < 0.5 branch**, with identifiability/quality flags. Primary forward model E0, real COSMOS-Web backgrounds, PSFEx and source redshifting to z=3. Current blockers are reliable fitted B/T, calibrated selection/recovery and confusion matrices. See [active roadmap](PASSIVE_DISK_END_TO_END_ROADMAP_2026-10-19.md). This literature backlog does **not** authorize production runs or change frozen cuts.

## Priority A — read closely / direct analysis value

### A1. Euclid Q1: recently quenched galaxies — quenching timescale and disk survival
- **Paper:** [Mao et al., *Exploring the complexity of quenching processes across time, environment, and mass through recently quenched galaxies*](https://arxiv.org/abs/2610.08999)
- **Type:** Core science / introduction / comparison.
- **Takeaway:** Euclid classifies fast- versus slow-recently-quenched populations; the abstract reports disk-like morphologies for fast-quenching systems and greater concentration for slow-quenching systems. Morphology alone does not measure quenching timescale.
- **Apply:** Compare GOLD403 disk-dominated versus bulge-dominated quiescent controls in mass, redshift, size, Sérsic n and B/T. If credible SFHs exist, test quenching-time association; do **not** infer it from n alone.
- **Next:** Read selection, UVJ evolutionary-track definitions, morphology measurement and matched-control methods. Evaluate whether the Euclid population and COSMOS-Web sample are comparable.
- **Status:** Abstract independently checked 2026-10-23.

### A2. Environmental morphology and quenching at z=0.1–0.5
- **Paper:** [Xu et al., *The Structural Anatomy of Galaxies: Environmental Dependence of Morphological and Quenching Evolution*](https://arxiv.org/abs/2610.29971)
- **Type:** Science + recovery methodology.
- **Takeaway (prior discussion; needs full-text verification):** Quenching may extend to larger cluster radii than structural transformation; simulated faint galaxies show B/T recovery degradation.
- **Apply:** Replicate a **magnitude/size/SNR/context-dependent B/T bias and scatter calibration** with JWST-specific simulations, using both disk and non-disk truth. Separate measurability, class retention, and contamination; compare environment only after mass/redshift matching.
- **Next:** Inspect Appendix A, input parameter distributions, model mismatch, Figure 7 and treatment of catastrophic/non-identifiable fits.
- **Status:** To verify in full text.

### A3. COSMOS-Web central density, quenching and halo environment
- **Paper:** [Zhang et al., *Connecting galaxy structure, quenching, and halo environments during cosmic noon*](https://arxiv.org/abs/2610.25446)
- **Type:** Direct COSMOS-Web science / introduction.
- **Takeaway (prior discussion):** Central stellar surface density Σ1 correlates strongly with quenching in massive z~1–3 galaxies. Extended low-Σ1 quenched systems are not automatically disk-dominated.
- **Apply:** Build mass- and redshift-matched passive disk / passive spheroid / star-forming disk controls. Compute Σ1 **only after validating Sérsic mass-profile assumptions and M/L gradients**; test whether passive disks are low-Σ1 exceptions.
- **Next:** Check exact Σ1 estimator, mass completeness, environmental definitions and whether released catalogs overlap GOLD403.
- **Status:** To verify in full text.

### A4. IMFIT-MW multiwavelength decomposition
- **Paper:** [Chugunov, *IMFIT-MW: Multiwavelength Photometric Decomposition with IMFIT*](https://arxiv.org/abs/2610.10231)
- **Type:** Potential fitting-method upgrade.
- **Takeaway (prior discussion):** Joint fits across bands can constrain shared or smoothly wavelength-varying structural parameters.
- **Apply:** On a **small frozen held-out set**, compare Galight single-band branches to multi-band fitting, preserving PSF/filter provenance and truth definitions. Compare bias, coverage, catastrophic fit rate and n/B/T classification; do not silently replace the current fitter.
- **Next:** Examine [the publicly released IMFIT-MW code](https://github.com/IVChugunov/IMFIT-MW), PSF handling, parameterization, uncertainty calibration and fair held-out test design.
- **Status:** To verify in full text.

### A5. JADES clump-detection recovery
- **Paper:** [Puskás et al., *The clumpy fraction of galaxies at z=1–9 with JADES*](https://arxiv.org/abs/2610.28515)
- **Type:** Injection/recovery method.
- **Takeaway (prior discussion):** Apparent small-scale-feature fractions depend on wavelength, depth, mass and recovery completeness.
- **Apply:** Adapt injection/recovery **methodology** to optional visual spiral/bar/clump survival, **not** the primary structural passive-disk completeness denominator. Measure detection of features as a separate estimand.
- **Next:** Read truth labels, source-injection design and how completeness is separated from intrinsic evolution.
- **Status:** To verify in full text.

### A6. Local bars and multi-component decompositions
- **Paper:** [Cavalcante-Coelho et al., *Stellar Mass Census of S⁴G Local Bars*](https://arxiv.org/abs/2610.22188)
- **Type:** B/T systematic / introduction. **Bibliography:** arXiv:2610.22188 verified by matching title and abstract.
- **Takeaway (prior discussion):** Bar light can be confused with bulge light in simplified bulge+disk fitting.
- **Apply:** Controlled bulge+disk versus bulge+disk+bar fits on obvious barred examples, both native and transferred, to test B/T bias. Keep separate from current validated two-branch gate.
- **Next:** Verify bibliographic record, code, multi-band GALFITM assumptions and whether mass versus light B/T is used.
- **Status:** Title/arXiv abstract checked; full-text methodological transfer remains to audit.

## Priority B — targeted science, validation and contextual comparisons

### B1. Hidden spiral structure in Virgo early-type dwarfs
- [Gracia et al., *The optical colors of hidden spiral-like features in nine Virgo early-type dwarfs*](https://arxiv.org/abs/2610.20819)
- **Use:** Motivation for a *secondary* residual/arm-visibility experiment. A faint spiral feature may disappear while global n/B/T remains measurable. Different mass/environment from GOLD403; do not transfer numerical fractions.

### B2. DAWN JWST spectroscopically informed galaxy properties
- [Gottumukkala et al., *The DAWN JWST Archive: A spectroscopically-informed population study of the physical properties of galaxies at z>2*](https://arxiv.org/abs/2610.15901)
- **Use:** Validate quiescence versus dusty star formation and inspect availability of SFHs/spectroscopic constraints. Check cross-field and cross-catalog overlap before planning joins.

### B3. Cosmic-web environment in COSMOS
- [Taamoli et al., *The Role of the Cosmic Web in Galaxy Evolution Across 0.4 < z < 4*](https://arxiv.org/abs/2610.07710)
- **Use:** Environment-based introduction and possible cluster/filament/field comparisons; match stellar mass and redshift and control completeness. Cosmic-web classifications must be verified before matching.

### B4. Radio AGN in COSMOS-Web groups
- [Ubertosi et al., *Prevalence of radio Active Galactic Nuclei in galaxy groups since z=3.5 in the COSMOS-Web field*](https://arxiv.org/abs/2610.10719)
- **Use:** Potential COSMOS-Web group and radio cross-match to test association between AGN incidence and passive-disk morphology; radio association is **not** causal proof of AGN quenching.

### B5. COSMOS-Web DR1 cosmic filament catalog (new: 2026-10-24)
- **Paper:** [Hao et al., *A cosmic filament catalog for COSMOS-Web Data Release 1 across 0.5 < z < 3.5*](https://arxiv.org/abs/2610.31168)
- **Type:** Environmental catalog / prospective COSMOS-Web cross-match; not direct evidence for passive-disk survival.
- **Takeaway (provisional; verify against full paper):** A COSMOS-Web cosmic-filament catalog and associated environmental information offer a way to examine large-scale structure alongside galaxy morphology and quiescence.
- **Apply:** Check the released footprint, redshift coverage, catalog access, filament-distance definitions and uncertainties against GOLD403. If compatible, compare passive-disk fractions and n/B/T distributions as a function of filament proximity using mass- and redshift-matched quiescent spheroid and star-forming disk controls. Account for photometric-redshift uncertainty, survey selection and environment-dependent completeness.
- **Next:** Verify catalog release, projection effects, filament-membership probabilities and usable sky overlap before any join or quantitative claim. This is a *future science extension*, not a change to the frozen morphology pipeline.
- **Status:** Identified from 2026-10-23 arXiv alert; full text and data release not independently audited.

### B6. Dormant z>3 galaxies and cold gas
- [Xiao et al., *Sleeping or Dead? Probing the Quenching Mechanism of JWST Dormant Galaxies at z > 3 with ALMA*](https://arxiv.org/abs/2610.19926)
- **Use:** Gas depletion versus suppression discussion; investigate morphology for overlap if possible. Not a direct disk-survival measurement.

### B7. Post-starburst radio AGN
- [D'Onofrio et al., *SQuIGGLE: Radio AGN Found Predominantly in Young, Gas-rich Post-starburst Galaxies at z ~ 0.7*](https://arxiv.org/abs/2610.19146)
- **Use:** AGN timing and quenching literature; avoid equating AGN presence with disk preservation.

## Peripheral references — kept for traceability, NOT active GOLD403 tests

These items are real papers but **too indirect** for the present passive-disk recovery experiments. Keep for optional discussion, future cross-matches, or narrow technical comparison only. They must not drive the core Methods or be represented as evidence for passive-disk survival or the current JWST pipeline.

### B5. LOFAR COSMOS radio imaging
- [Vardoulaki et al., *Cosmic Evolution Survey: LOFAR 144 MHz imaging of the COSMOS field*](https://arxiv.org/abs/2610.18648)
- **Use:** Additional radio counterpart/AGN diagnostics; positional cross-match with chance-association estimates and sensitivity limits. Radio nondetections do not rule out AGN.

### B8. Bar-driven central evolution of NGC 6946
- [Álvarez-Córdoba et al., *The bar-driven central complex of NGC 6946*](https://arxiv.org/abs/2610.22483)
- **Use:** Internal secular inflow and *central* suppression as a possible pathway; not proof of whole-galaxy quiescence. Could motivate bar flags.

### B9. HI eXtreme galaxies / gas stabilization
- [Capa et al., *The H IX Galaxy Survey IV: What Does the Molecular Gas Reveal in HI eXtreme Galaxies?*](https://arxiv.org/abs/2610.28970)
- **Use:** Context for inefficient star formation in gas-rich disks, not an example of confirmed passive disks. Compare gas removal vs stabilization hypotheses.

### B10. Simulation star-formation histories
- [Savelli et al., *Untangling Similarities and Differences in Star Formation Histories Across Cosmological Simulations*](https://arxiv.org/abs/2610.17359)
- **Use:** Quenching-timescale diversity as theoretical context; test disk morphology separately rather than assuming SFH implies structure.

### B11. Shape inference from FIREboxHR
- [Geng et al., *Inferring the shapes of low-mass galaxies at z>6 from FIREboxHR: Where are the disks?*](https://arxiv.org/abs/2610.26969)
- **Use:** 2D apparent axis ratio is not equivalent to intrinsic 3D disk shape. Numerical results from very high-z low-mass simulations are not directly transferable.

### B12. Undersampled PSF reconstruction
- [Nie et al., *RPCA: a Resolved PSF reconstruction method for undersampled images*](https://arxiv.org/abs/2610.19909)
- **Use:** Possible PSF systematic check, **not** a replacement for audited position-dependent COSMOS-Web PSFEx without JWST validation.

## Priority C — future surveys / introduction only

### C1. ALMA2040 cold gas in quiescent galaxies
- [Zanella et al., *Probing Cold Gas and Dust in Quiescent Galaxies Across Cosmic Time*](https://arxiv.org/abs/2610.21513)
- **Use:** Future CO/[CI]/[CII] observations to separate gas removal from inefficient star formation. White paper; not a new measurement.

### C2. ALMA2040 disk assembly
- [Kaasinen et al., *Resolving the Assembly of Disk Galaxies from the Epoch of Reionisation to Cosmic Noon*](https://arxiv.org/abs/2610.21441)
- **Use:** Future resolved kinematic checks of photometrically identified disks. White paper, not a direct test of passive disks.

## Additional directly relevant foundational literature (not from the October alerts)
- [Euclid Q1, *Quenching precedes bulge formation in dense environments but follows it in the field*](https://arxiv.org/abs/2511.02964): **Very high introduction priority**: explicitly compares quiescent disky and star-forming bulge-dominated populations, and the sequence of quenching versus morphological transformation across environment. Abstract independently checked 2026-10-23.
- [Bluck et al., *The quenching of galaxies, bulges, and disks since cosmic noon*](https://arxiv.org/abs/2201.07814): bulge mass, B/T and quenching context; distinguish predictive correlations from causation. Abstract checked 2026-10-23.
- [Margalef-Bentabol et al. (2022), *Observations of the Initial Formation and Evolution of Spiral Galaxies at 1<z<3 in CANDELS*](https://arxiv.org/abs/2201.06334): existing supervisor-requested artificial-redshifting reference; follow roadmap's exact paper identification and Figs 8–11. **Do not adopt its population spiral-fraction power law as the COSMOS-Web recovery law.**

## Concrete execution queue (isolated toy completed; real science gates remain open)

1. **Literature audit:** Title/abstract bibliographic audit performed 2026-10-23; full-method verification, data/code release details, and precise figure/equation checks still pending. No arXiv claim is presented as a replicated result.
2. **Finish existing recovery gates first:** B/T identifiability and fit-quality, real-z matched controls, n/B/T two-branch validity; do not treat historical 806 outputs as final.
3. **Bias calibration inspired by Xu + IMFIT-MW:** Frozen test grid in magnitude, input n/B/T, size/PSF, S/N, neighbor context and band; compare recovered bias, scatter, coverage, failure, and both directions of classification confusion. Include negative controls and avoid tuning on evaluation set.
4. **Secondary feature visibility inspired by Puskás + Virgo:** Optional real-image spiral/bar residual survival with visual truth labels. Never use spiral-arm recovery as a surrogate for passive-disk recovery.
5. **Science comparisons inspired by Euclid + Zhang (with Hao filament catalog as a conditional environmental extension):** Build mass/redshift-matched controls; test passive-disk fractions versus environment and Σ1 only after observational calibration and parent denominator are valid.
6. **Physical interpretation:** Use DAWN/ALMA/radio references to motivate quenching mechanisms; only attempt cross-matches after checking coverage and selection functions.
7. **Manuscript plan:** Introduction = passive disks as quenching/morphology timing probes → observational morphology biases → why COSMOS-Web forward modeling is needed. Methods = frozen two-branch transfer and validated recovery/confusion. Results = conditional recovery and calibrated demographics if gates pass. Discussion = quenching/environment/Σ1/AGN/gas and future surveys, with causal limitations.

## Relevance-audit decision log (2026-10-23; updated 2026-10-24)

- **Core analysis:** A1 Mao/Euclid, A2 Xu, A3 Zhang, A4 Chugunov/IMFIT-MW, A5 Puskás/JADES, A6 Cavalcante-Coelho/S4G bars. These concern quenching/morphology, quantitative fitting, or completeness directly.
- **Core introduction/foundation:** Euclid Gentile (2511.02964), Bluck (2201.07814), Margalef-Bentabol (2201.06334), plus B3 Taamoli and B5 Hao for environment and B1 Gracia for hidden arms. Important distinctions: disc-like vs visible spiral; light B/T vs mass B/T; selection versus measurement completeness.
- **Secondary context:** B2 DAWN, B4 COSMOS-Web radio groups, B6 dormant gas, B7 post-starburst AGN and C1/C2 ALMA2040. Useful only where a paper paragraph specifically calls for that context, not automatic citations.
- **Parked/peripheral:** B5 LOFAR source catalog (radio catalog selection), B8 NGC6946 (one active barred galaxy), B9 HI eXtreme (not quenched), B10 simulated SFHs (no morphologies), B11 FIREboxHR (low-mass z>6 not our sample), B12 RPCA (CSST PSF, not JWST PSFEx); do not include in immediate science/method plan.
- **Accuracy:** The Xu abstract supports environmental trends; B/T simulation quantitative scatter requires full-text inspection. Zhang's Σ1 predictive association cannot be treated as causal. IMFIT-MW reports a working code release but we have not executed it. No manuscript citation is promoted solely from this log.

- **2026-10-24 addition:** Hao et al. (2610.31168) is provisionally placed in Priority B for possible COSMOS-Web filament-environment cross-matching; catalog availability, matching and full-text details remain unverified. No pipeline changes or scientific claims are implied.

## Review tracker

| ID | First reading | Full text verified | Data/code checked | Pilot designed | Implemented |
|---|---|---|---|---|---|
| A1 Euclid RQG | pending | no | no | no | no |
| A2 Xu B/T | pending | no | no | no | no |
| A3 Zhang Σ1 | pending | no | no | no | no |
| A4 IMFIT-MW | pending | no | no | no | no |
| A5 JADES clumps | pending | no | no | no | no |
| A6 Bars | pending | no | no | no | no |

**Scope note:** Brown-dwarf papers from the same chat (COSMOS-3D, astrometry, UCD atmosphere and completeness) are intentionally excluded from this repository-specific backlog because `astro-forward-modeling` is the passive-disk project. They belong in the brown-dwarf repository.
