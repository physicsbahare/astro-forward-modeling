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

### A7. HSC multi-band B/T posteriors and wavelength-dependent morphology (backfill: 2026-10-29)
- **Paper:** [Sarkar et al., *Complete Multi-Band Structural Characterization for 10 Million Galaxies in the Hyper Suprime-Cam Wide Survey using Deep Learning*](https://arxiv.org/abs/2610.32913)
- **Type:** Direct structural-measurement validation and future-survey methods.
- **Takeaway:** Bayesian deep-learning posteriors for bulge-to-total **light** ratio, effective radius and flux in multiple HSC bands; reported g-band performance deteriorates at z >= 0.5 as the observed band moves toward rest-frame UV. This is not a JWST B/T recovery calibration.
- **Apply:** Design a controlled, wavelength-aware GOLD403 injection/recovery comparison across NIRCam bands, separating true structural changes from PSF/depth/rest-frame wavelength effects. Evaluate bias, coverage and calibrated uncertainties for B/T and n, including class confusion, without adopting HSC performance numbers.
- **Next:** Inspect posterior-calibration tests, truth-label construction, training domain and redshift/band exclusions; assess which diagnostics transfer to JWST.
- **Status:** Title and abstract checked 2026-10-29; full methods and catalog not audited.

### A8. COSMOS-Web size-mass relations separated by sSFR and morphology (revision noticed: 2026-10-30)
- **Paper:** [Tudorache et al., *pop-cosmos: Galaxy size evolution across structural and star-formation classifications in COSMOS-Web*](https://arxiv.org/abs/2606.28489)
- **Type:** **High direct science/analysis relevance**, COSMOS-Web comparison; an October revision of a paper first submitted in June 2026, **not** a new October submission.
- **Takeaway:** Combines pop-cosmos stellar mass/sSFR estimates with COSMOS-Web sizes and structural classifications for 99,369 galaxies. The abstract finds that separating galaxies by quiescence versus by B/T or Sérsic index changes inferred size–mass trends; the quiescent and bulge-dominated populations show different characteristic mass scales. This supports treating quenching and structural transformation as separate observables, not proof of their causal order.
- **Apply:** Compare GOLD403 passive-disk and matched quiescent-spheroid/star-forming-disk controls against published size–mass–redshift relations, **only after** checking sample overlap, bandpass, size definitions, mass completeness and n/B/T selection. In the manuscript, explicitly distinguish sSFR-based quiescence from structural disk classification and account for their different denominators.
- **Limitations:** Population scaling relations do not establish that individual disks survive quenching. Its morphological measurements and selection functions are not interchangeable with GOLD403 forward-model recovery or B/T confusion calibration.
- **Next:** Inspect revised paper's catalog, COSMOS-Web structural input, sSFR posterior/selection, completeness, redshift bins and size estimator; test whether a matched external comparison is possible. The 2026-10-30 arXiv listing marks v2 as accepted in MNRAS, but the cached abstract page still showed v1; verify version metadata before citing the revision.
- **Status:** Title and abstract checked 2026-10-31; original submission 2026-06-26, revised in 2026-10-30 listings. Full text and released data not audited.

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

### B13. FRESCO proto-cluster quiescent fractions at z~4–6 (new: 2026-10-29)
- **Paper:** [Lin et al., *A Large Diversity in the Quiescent Fractions of Massive Galaxies in Proto-clusters at z~4–6 in the FRESCO GOODS fields*](https://arxiv.org/abs/2610.37357)
- **Type:** JWST quiescence-selection and environmental science context, **not** a disk-morphology measurement.
- **Takeaway:** Uses multi-filter JWST/HST SED modeling and color diagnostics to select 12 quiescent candidates in four GOODS proto-clusters; reports strong variation in quiescent fractions between structures and with stellar mass, with small high-mass denominators.
- **Apply:** Inform the passive-disk paper's discussion of mass/environment confounding and the need for explicitly defined quiescent parent denominators. Compare SED/UVJ diagnostics and contamination safeguards, but do **not** transfer the z~4–6 proto-cluster fractions to COSMOS-Web GOLD403 or infer disk survival.
- **Next:** Inspect completeness, candidate probabilities, photo-z and quiescence robustness, field-to-field variance and control samples; check whether any methods apply at the GOLD403 redshifts.
- **Status:** Title/abstract verified 2026-10-29; full text and code/data not audited.

### B14. Void environment versus stellar mass (backfill: 2026-10-29)
- **Paper:** [Zhang, *Radial dependence of galaxy and halo properties in cosmic voids: SDSS DR7 and the ELUCID constrained simulation*](https://arxiv.org/abs/2610.35057)
- **Type:** Environmental-confounding comparison, local-universe context.
- **Takeaway:** Void-centric trends in galaxy color and specific SFR are generally weaker than stellar-mass trends; spiral fraction shows little radial dependence at fixed stellar mass.
- **Apply:** Require stellar-mass and redshift matching, survey completeness checks and environment-definition sensitivity before interpreting passive-disk fractions by filament/group/void location.
- **Next:** Review sample mass limits and environment metrics; avoid extrapolating SDSS z~0 spiral fractions directly to high-z quiescent disks.
- **Status:** Title/abstract checked 2026-10-29; full text not audited.

### B15. AGN outflow in a z=2.6 quiescent galaxy (backfill: 2026-10-29)
- **Paper:** [Bugiani et al., *Recently launched AGN-driven outflow in a lensed quiescent galaxy at Cosmic Noon*](https://arxiv.org/abs/2610.33176)
- **Type:** Physical-quenching context, not a morphology or B/T method.
- **Takeaway:** Spatially resolved JWST/NIRSpec IFU observations reveal a high-velocity ionized wind in a lensed quiescent galaxy, consistent with AGN-driven maintenance of quiescence.
- **Apply:** Cite cautiously when distinguishing mechanisms that maintain suppressed star formation from those that dynamically destroy or preserve disks. This single case does **not** demonstrate disk survival.
- **Next:** Inspect gas/stellar kinematics, outflow energetics, morphology and alternative interpretations before using in Discussion.
- **Status:** Title/abstract checked 2026-10-29; full text not audited.

### B16. Chemical clocks for massive quiescent-galaxy formation (late catch: 2026-10-30)
- **Paper:** [O'Connor et al., *How Quickly Did the Giants Form? Constraining the Formation Timescales of Massive Quiescent Galaxies at Cosmic Noon Using Chemical Evolution Modelling*](https://arxiv.org/abs/2610.34883)
- **Type:** Quenching-timescale / stellar-population interpretation, **not** passive-disk morphology validation.
- **Takeaway:** One-zone chemical evolution modeling of alpha-enhanced massive quiescent galaxies at z~2 supports rapid star-formation episodes of roughly 0.1–0.4 Gyr; chemical abundances provide constraints that SED-derived SFHs alone may miss.
- **Apply:** Use as a cautious comparison when discussing the possible range of formation and quenching timescales for mass-matched passive disks versus spheroids. If chemical or spectroscopic measurements become available, test SFH consistency rather than assigning these model-derived timescales to GOLD403.
- **Limitation:** Massive quiescent sample and simplified chemical evolution models; no disk selection, no measured B/T recovery, and no demonstrated disk-survival mechanism.
- **Next:** Read abundance compilation, priors/yields, selection and SFH-model comparisons; assess whether any matched GOLD403 control has comparable stellar mass and spectroscopy.
- **Status:** arXiv title and abstract verified 2026-10-30; submitted 2026-10-26; full text not audited.

### B17. JWST cosmic-noon morphology and gas-phase metallicity (late catch: 2026-10-30)
- **Paper:** [Hasan et al., *The Role of Star Formation and Morphology in the Mass-Metallicity Relation of Galaxies at Cosmic Noon*](https://arxiv.org/abs/2610.37612)
- **Type:** Evolutionary/morphology science context, **not** quiescent-disk survival or B/T fitting calibration.
- **Takeaway:** JWST/NIRISS slitless spectroscopy of >1,000 galaxies at 1.7<z<3.5 finds that at fixed stellar mass in the lower-mass regime, galaxies with larger sizes, lower SFR surface densities, bulges and/or spiral features tend to be more metal-rich than less structurally developed counterparts.
- **Apply:** Motivate an explicitly conditional discussion of whether structurally mature disks could have different gas-accretion histories before quenching. If overlapping ancillary spectroscopy exists, compare mass/redshift-matched star-forming disks, passive disks and spheroids without equating gas metallicity with stellar metallicity or structural survival.
- **Limitation:** Mainly emission-line, star-forming systems; morphology–metallicity correlation is not evidence that a bulge, spiral structure or metal enrichment causes quenching or preserves a stellar disk.
- **Next:** Inspect morphology definitions, selection limits, mass/SFR matching, metallicity calibration and rest-frame imaging bands before any quantitative comparison.
- **Status:** arXiv title and abstract verified 2026-10-30; submitted 2026-10-27; full text not audited.

### B18. Satellite environmental quenching and morphology in GAMA/DEVILS (new listing: 2026-10-30)
- **Paper:** [Oxland et al., *Environmental Quenching of Satellite Galaxies out to z~0.4 with GAMA and DEVILS*](https://arxiv.org/abs/2610.38836)
- **Type:** Environmental-quenching science and matched-survey methodology; not direct high-z disk-survival evidence.
- **Takeaway:** Compares satellite populations across GAMA and DEVILS with consistent property and environment definitions, using projected phase space as an infall-time proxy. The abstract reports a decline in SFR relative to the star-forming main sequence of about 0.14 dex/Gyr after infall, including similar trends for visually early- and late-type galaxies, with no significant evolution between the two survey redshift ranges.
- **Apply:** For any future GOLD403 environment test, distinguish quenching from structural transformation, define central/satellite status where possible, use consistent mass/redshift-matched controls, and assess whether environment-dependent selection biases mimic morphology trends. The low-z satellite result is a conceptual comparator, **not** a correction or timescale to transfer to COSMOS-Web.
- **Limitations:** z~0.4 or lower, visually classified early/late types rather than JWST B/T-recovered passive disks; projected phase space is a proxy, not a direct infall clock. No demonstration that disks survive quenching at GOLD403 redshifts.
- **Next:** Read group/satellite selection, mass limits, morphology bins, phase-space treatment, and completeness; check which environmental definitions are reproducible with COSMOS-Web ancillary catalogs.
- **Status:** arXiv title and abstract checked 2026-10-31; submitted 2026-10-28, appeared in the 2026-10-30 new listings. Full text and data not audited.

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

### C3. SIRMOS future near-IR spectroscopy across Euclid (new: 2026-10-29)
- **Paper:** [Wirth et al., *The SIRMOS mission concept: a space-based near-IR spectroscopic survey of 100 million galaxies in the Euclid Wide Survey footprint*](https://arxiv.org/abs/2610.35945)
- **Type:** Future-survey prospect / environment context; **mission concept, not observed data**.
- **Takeaway:** Proposes slit spectroscopy of ~100 million galaxies at 1<z<4 over the Euclid footprint, with environment at cosmic noon as a secondary science objective.
- **Apply:** Potential future combination of imaging-derived morphology (Euclid/JWST) with spectroscopic redshifts and environmental mapping to test quiescent-disk demographics and redshift trends. Do not assume SIRMOS will fly or that it will supply resolved morphologies.
- **Next:** Check target selection, spectral sensitivity, quiescence indicators and survey timeline before citing in future-work plans.
- **Status:** Title/abstract checked 2026-10-29; full proposal not audited.

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

## Daily scan follow-up (2026-10-29)

- **New listing:** Lin et al. (2610.37357) added as environmental/quiescence-selection context. The GOODS proto-cluster redshift range and lack of disk classification limit direct GOLD403 transfer.
- **New listing:** Wirth et al. (2610.35945) added as future-survey concept only, not an operational source of data.
- **Backfilled from October 27–28 alerts:** Sarkar et al. (2610.32913) for multi-band B/T methods, Zhang (2610.35057) for mass/environment confounding, and Bugiani et al. (2610.33176) for AGN-maintenance context.
- **Scope:** No scientific pipeline, cuts, production tests or model settings changed. Entries are literature notes, not replicated numerical claims.

## Daily scan follow-up (2026-10-30)

- **Late-caught from October 26–27 submissions:** O'Connor et al. (2610.34883) on chemical constraints for quiescent-galaxy formation timescales, and Hasan et al. (2610.37612) on cosmic-noon morphology and gas metallicity. Both are Priority B science context, not morphology validation or disk-survival evidence.
- **Freshness limitation:** At the time of this check, the accessible arXiv astro-ph listing still showed 2026-10-28 as its newest announcement. Do not represent this as an exhaustive check of 2026-10-29 announcements; recheck that announcement day when accessible.
- **Scope:** Documentation-only addition; no code, selection cuts, pipeline settings, or numerical science outputs changed.

## Daily scan follow-up (2026-10-31)

- **Newly announced paper:** Oxland et al. (2610.38836), submitted 2026-10-28 and listed 2026-10-30, added as Priority B environmental-quenching/morphology context. The low-z satellite result does not measure high-z passive-disk survival.
- **Relevant revision noticed:** Tudorache et al. (2606.28489), first submitted June 2026 and newly revised in the 2026-10-30 listings, added as Priority A COSMOS-Web science comparison. Treat this as a revision, not a new submission; check revised version metadata before manuscript use.
- **Backfill check:** All seven passive-disk references from the October 27–30 alerts were already in this backlog, so none was duplicated.
- **Scope:** No changes to fitting code, scientific outputs, frozen cuts or production settings. No direct new brown-dwarf paper met the present selection threshold.

## Review tracker

| ID | First reading | Full text verified | Data/code checked | Pilot designed | Implemented |
|---|---|---|---|---|---|
| A1 Euclid RQG | pending | no | no | no | no |
| A2 Xu B/T | pending | no | no | no | no |
| A3 Zhang Σ1 | pending | no | no | no | no |
| A4 IMFIT-MW | pending | no | no | no | no |
| A5 JADES clumps | pending | no | no | no | no |
| A6 Bars | pending | no | no | no | no |\n| A7 Sarkar multi-band B/T | abstract checked | no | no | no | no |\n| B13 Lin proto-cluster QGs | abstract checked | no | no | no | no |\n| C3 SIRMOS concept | abstract checked | no | no | no | no |

**Scope note:** Brown-dwarf papers from the same chat (COSMOS-3D, astrometry, UCD atmosphere and completeness) are intentionally excluded from this repository-specific backlog because `astro-forward-modeling` is the passive-disk project. They belong in the brown-dwarf repository.
