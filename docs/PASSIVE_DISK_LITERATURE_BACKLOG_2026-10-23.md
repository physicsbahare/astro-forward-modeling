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

### A9. JWST PRIMER/MINERVA quiescent-galaxy bulge–disk decomposition and inside-out quenching (2026-11-02 listing)
- **Paper:** [Prasal, Wadadekar & Biswas, *The Size-Mass Relation and Inside-Out Quenching of Massive Quiescent Galaxies at 2<z<3 with JWST PRIMER and MINERVA*](https://arxiv.org/abs/2610.40937)
- **Type:** **High-priority direct science and methodology comparison** (multi-band Sérsic/B+D, spatially resolved SFH); not a validated GOLD403 recovery calibration.
- **Takeaway:** For 26 massive quiescent galaxies at z=2–3, the authors fit single-Sérsic and bulge+disk models with pysersic in six NIRCam filters and derive resolved SFHs. They report one-third with light B/T<0.5, a ~22% decrease in measured size from F115W to F444W, and older/faster-quenched central regions than outskirts. Proposed AGN/compaction/dynamical-stabilization mechanisms are interpretations, not directly established causal pathways.
- **Apply:** Compare the *definitions and reliability* of wavelength-dependent B/T, sizes, PSF matching and rest-frame bands against GOLD403's separate n<2.5 and B/T<0.5 branches. Consider a small, frozen matched-control comparison at z=2–3 and test whether radial age/colour gradients could alter apparent disk dominance without changing intrinsic structure. **Do not transfer the reported one-third fraction to GOLD403 or substitute these fits for our injection/recovery calibration.**
- **Limitations:** Small, massive, quiescent sample in UDS rather than COSMOS-Web; B/T is light-based and sensitive to wavelength, model choice, resolution and selection. A resolved SFH gradient is not a direct measurement of an individual galaxy's morphological survival after quenching.
- **Next:** Audit sample selection, PSF construction, pysersic priors/model comparison, B/T errors, filter-dependent fitting and piXedfit assumptions; assess whether released data or a matched pilot can be used after the current identifiability gates.
- **Status:** arXiv title and abstract checked 2026-11-03; first submitted 2026-10-29 and announced 2026-11-02. Full text, code and catalog not yet audited.

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

### B19. OASIS I: spectroscopic validation of photometric quiescence at z>4 (2026-11-02 listing)
- **Paper:** [Looser et al., *OASIS I: Spectroscopy of Mini-Quenched and Lulling Galaxies Constrains the Quiet Side of Bursty Star Formation at z > 4*](https://arxiv.org/abs/2610.41489)
- **Type:** Quiescence-selection **validation methodology** and SFH context, not disk-survival or morphology calibration.
- **Takeaway:** Deep JWST/NIRSpec/PRISM data distinguish mini-quenched from temporarily low-SFR galaxies. Seven of ten photometrically selected suppressed-SFR candidates were actually near/above the star-forming main sequence, showing that photometric SFHs alone can misclassify short-term suppression.
- **Apply:** Motivate explicit purity/contamination checks for the *quiescent parent sample* used in GOLD403, using available spectroscopic cross-checks and SED-posterior sensitivity where feasible. Keep quiescence-selection errors distinct from n/B/T morphological classification and recovery errors.
- **Limitations:** Low-mass z>4 galaxies undergoing bursty star formation, unlike the typical GOLD403 massive cosmic-noon targets; their 7/10 photometric misclassification rate is **not** transferable.
- **Next:** Read the photometric selection, SFH timescales and spectroscopic confirmation definitions; determine whether any analogous quiescence validation can be done for matched COSMOS-Web controls.
- **Status:** arXiv title and abstract checked 2026-11-03; submitted 2026-10-30, announced 2026-11-02. Full methods not audited.

### B20. OASIS III: star-formation variability and observed galaxy size (2026-11-02 listing)
- **Paper:** [Baker et al., *OASIS III: Bursty star formation drives observed galaxy sizes at z≥4*](https://arxiv.org/abs/2610.41491)
- **Type:** **Secondary observational morphology/size-systematics context**, not a direct B/T or passive-disk survival result.
- **Takeaway:** JWST NIRCam+NIRSpec analysis of 51 galaxies at z≥4 finds that more strongly rising star formation correlates with smaller UV/optical half-light radii even after controlling for mass and redshift. The authors interpret this as centrally concentrated starbursts changing the observed light profile.
- **Apply:** In GOLD403 forward-model discussions, distinguish stellar-mass morphology from light-weighted morphology and consider whether central young populations or wavelength-dependent M/L gradients can bias single-Sérsic n, half-light radius and B/T. Use as a motivation for a *conditional* colour-gradient/SED-aware stress test, not as a correction to apply.
- **Limitations:** Mostly low-mass, very-high-redshift galaxies; ForcePho half-light radii and burstiness are not B/T recovery measurements and the reported trend does not demonstrate disk survival.
- **Next:** Examine size measurement bands, PSF treatment, selection and partial-correlation controls; assess whether analogous light-profile effects matter for matched GOLD403 galaxies.
- **Status:** arXiv title and abstract checked 2026-11-03; submitted 2026-10-30, announced 2026-11-02. Full methods not audited.

### B21. Khoram et al. (2026): gas and galaxy environment at cosmic noon
- **Paper:** [Khoram et al., *Developing Environments: Formation and Quenching at Cosmic Noon Traced by the Large-scale Distribution of Gas and Galaxies*](https://arxiv.org/abs/2611.00190).
- **Type / priority:** Priority B, directly relevant COSMOS-Web environmental science; not a B/T recovery method or disk-survival measurement.
- **Abstract-level takeaway:** At 1.7 < z < 3.5 the study combines COSMOS-Web galaxy overdensity and LATIS Ly-alpha neutral-hydrogen tomography with 139 Blue Jay and 57 DAWN JWST spectra. Quiescent-galaxy formation-to-quenching intervals vary with environment; galaxy-rich/gas-poor and galaxy-poor/gas-rich regions differ in AGN/outflow incidence. Galaxy number density alone misses important gas-environment structure.
- **Application to GOLD403:** For a *future* environment/quenching comparison, test footprint and redshift overlap, then compare passive disks against mass- and redshift-matched quiescent spheroids and star-forming disks using both galaxy-density and (where available) gas-environment measures. Explore whether disk-dominated quiescent systems occupy the gas-rich developing regions, only after selection/recovery and B/T reliability are calibrated.
- **Limitations:** The spectroscopic sample is not a morphology-selected passive-disk sample; associations do not establish causal quenching mechanisms or stellar disk survival. LATIS coverage, environment definitions, cross-match quality, completeness and uncertainties need validation. Do not import numerical rates into GOLD403.
- **Next:** Read methods/figures for environment estimator and selection; locate any public COSMOS-Web/LATIS density products and verify overlap before proposing a cross-match.
- **Status:** Title and abstract checked in the 2026-11-03 astro-ph announcement; full paper/data not audited.

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

## Daily scan follow-up (2026-11-03)

- **2026-11-02 announcement:** Prasal et al. (2610.40937) added as Priority A, a direct multi-band JWST bulge/disk and quiescence comparison for z=2–3.
- **2026-11-02 announcement:** Looser et al. OASIS I (2610.41489) and Baker et al. OASIS III (2610.41491) added as Priority B methodological context for photometric quiescence misclassification and light-weighted size biases; both involve much higher-redshift/lower-mass galaxies, and their numerical results must not be transferred.
- **Scope:** Abstract-level checks only. No frozen cuts, pipeline settings, code, or quantitative outputs changed.

## Daily scan follow-up (2026-11-04)

- **New 2026-11-03 listing:** Khoram et al. (2611.00190) added as Priority B COSMOS-Web environment/quenching context. Not a direct morphology-recovery or disk-survival result. No code or frozen selection changes.

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

### B22. JWST stacked faint disk outskirts and observational surface-brightness effects (2026-11-04 listing)
- **Paper:** [Jia et al., *Probing the Faint Outskirts of Star-Forming Galaxies with 1<z<9 Using Stacked Images*](https://arxiv.org/abs/2611.04605)
- **Type / priority:** Priority B, **direct observational-methods comparison** for disk-profile detectability and forward modeling; not passive-galaxy quenching or B/T recovery.
- **Plain-language takeaway:** JWST/NIRCam stacks of 14,812 face-on star-forming disks in CEERS, JADES and PRIMER at 1<z<9 recover faint outer exponential light. The authors account for surface-brightness dimming, angular-size scaling, PSF convolution and residual backgrounds using blank-sky stacks, finding broadly bluer outskirts and outer scale-length trends with mass/redshift.
- **Apply to GOLD403:** Compare their control of dimming, PSF and blank-sky backgrounds with our COSMOS-Web artificial-redshifting/injection-recovery E0 design; assess whether extended disks become undetectable while the central Sérsic/B+D fit remains measurable. Consider a separate *outer-disk detectability* diagnostic, without conflating it with the frozen n<2.5 and B/T<0.5 selection gates.
- **Limitations:** Stacked star-forming face-on disks, not individually recovered quiescent disks; stacking cannot directly calibrate individual-galaxy B/T confusion, disk-survival fraction or GOLD403 completeness.
- **Next:** Read stack normalization, background subtraction, PSF-wing handling, rest-frame band matching and profile error propagation; decide whether a small held-out outer-disk surface-brightness test is warranted.
- **Status:** Title and abstract checked on arXiv 2026-11-05; submitted 2026-11-03; full methods/data not audited.

### B23. COSMOS-Web three-dimensional dark-matter map as future environmental context (2026-11-04 listing)
- **Paper:** [Scognamiglio et al., *3D dark matter map of the JWST COSMOS-Web field using diffusion-based generative priors*](https://arxiv.org/abs/2611.03786)
- **Type / priority:** Priority B, **future COSMOS-Web environment cross-match**; not morphology fitting, quenching classification or disk-survival evidence.
- **Plain-language takeaway:** Weak-lensing imaging in 0.54 deg² of COSMOS-Web is combined with a forward model and simulation-trained diffusion prior to infer probabilistic 3D matter maps in 20 lens planes to z≈2. Simulation/null tests support recovered structures and uncertainty estimates.
- **Apply to GOLD403:** If usable map/posterior products become available, compare mass/redshift-matched passive disks, passive spheroids and star-forming disks against matter overdensity or halo environment within the map's actual z/sky coverage; propagate map uncertainties and match completeness before interpreting any trends.
- **Limitations:** Lensing-derived matter density is model-dependent and not equivalent to individual halo mass or galaxy group membership; the reconstruction stops around z≈2, so not all GOLD403 redshifts are covered. No B/T recovery or disk-quenching causal result.
- **Next:** Check public map/posterior release, masks, redshift kernels and spatial resolution; test GOLD403 coordinate/redshift overlap before proposing an environmental statistic.
- **Status:** Title and abstract checked on arXiv 2026-11-05; submitted 2026-11-02; full methods/data not audited.

### B24. COSMOS-Web AGN hosts: quenching before structural compaction (2026-11-05 listing)
- **Paper:** [Han et al., *AGN Host Galaxies in COSMOS-Web: Linking Structural Evolution and Star Formation Quenching up to z=5*](https://arxiv.org/abs/2611.06443)
- **Type / priority:** Priority B, **direct COSMOS-Web science comparison** on quenching versus structural evolution; not a B/T recovery or artificial-redshifting calibration.
- **Plain-language takeaway:** JWST COSMOS-Web imaging and multiwavelength data for 3,955 AGNs at 0<z<5 are compared with star-forming and quiescent galaxies in rest-optical size–mass space. At z≳2 some massive AGN hosts have suppressed star formation while remaining as extended as star-forming galaxies; lower-z hosts increasingly resemble compact quiescent systems with larger Sérsic indices. This is consistent with, but does not prove, suppression preceding compaction in some objects.
- **Apply to GOLD403:** Use as a same-field comparison and discussion reference for possible decoupling of quenching and morphological transformation. Consider mass/redshift-matched comparisons of GOLD403 passive disks versus AGN hosts and passive spheroids, with consistent rest-frame bands, AGN point-source contamination controls, size/n quality flags and selection functions. Do not equate extended AGN hosts with disk-dominated galaxies.
- **Limitations:** AGN-selected rather than passive-disk-selected sample; size and Sérsic index are not direct B/T or spiral-arm measurements; unresolved AGN light may bias structural fits; observational cross-sectional trends cannot establish evolutionary trajectories or causal AGN quenching.
- **Next:** Inspect structural-fitting and AGN-light decomposition methods, mass/redshift cuts and available catalog/sky overlap; only then assess feasibility of a matched comparison. No production pipeline changes.
- **Status:** arXiv title/abstract verified 2026-11-06 (v1 submitted 2026-11-04); full text, catalog release and structural systematics not audited.

## Daily scan follow-up (2026-11-06)

- **2026-11-05 astro-ph listing:** Han et al. (2611.06443) added as B24, COSMOS-Web AGN/quenching/structure comparison. Not direct disk-survival or observational-bias validation.
- **Scope:** Documentation-only update. No scientific code, frozen cuts, fitting settings or numerical outputs changed.

### B25. Dust retention and quenching mode in lensed quiescent galaxies (2026-11-06 listing)
- **Paper:** [Bodansky et al., *Dust Survival in Lensed Quiescent Galaxies at z>1 Depends on How They Quench*](https://arxiv.org/abs/2611.07237)
- **Type / priority:** Priority B, physical-quenching and dust/SED interpretation; **not** direct passive-disk morphology or observational-recovery methodology.
- **Plain-language takeaway:** ALMA Band 6 continuum observations of eight strongly lensed spectroscopically quiescent galaxies at z~1–2.5, plus five archival systems, show widely varying dust-to-stellar-mass ratios. Rapidly quenched objects are more consistent with strong dust destruction, whereas more slowly quenched systems may retain or replenish dust. Two objects have resolved extended dust.
- **Apply to GOLD403:** Use cautiously in the Discussion to distinguish star-formation shutdown, dust evolution, and structural disk survival. When interpreting quiescent SED selection, consider whether obscured residual star formation could affect classification, but do not derive a dust-based morphology correction.
- **Limitations:** Small, lens-selected sample; single-band dust masses depend on unknown dust temperature (~0.3 dex systematic), and obscured star formation remains possible in the dustiest cases. Extended dust is not evidence for a surviving stellar disk or a calibrated B/T.
- **Next:** Inspect spectroscopic quiescence criteria, dust-temperature assumptions and resolved dust maps before citing physical quenching-mode interpretations; no pipeline change.
- **Status:** arXiv abstract verified 2026-11-07; submitted 2026-11-04, in 2026-11-06 listing; full text/data not audited.

### B26. Morphology-informed SED inference and historical star formation (2026-11-06 listing)
- **Paper:** [Alfonzo et al., *Is Morphology All You Need? Quantifying Imprints of Past Star Formation in the Present-Day Morphologies of Galaxies*](https://arxiv.org/abs/2611.07373)
- **Type / priority:** Priority B, prospective morphology–SFH **method** and future-survey context; not an established COSMOS-Web B/T recovery calibration.
- **Plain-language takeaway:** Katachi-PRIME combines gri image morphology and broadband SED information with implicit-likelihood inference to estimate mass, sSFR, redshift, age, dust attenuation and gas metallicity. The abstract reports improved constraints over photometry alone and that stable quiescent-galaxy morphologies can retain information about star formation over several Gyr.
- **Apply to GOLD403:** Potentially motivate an optional post-validation morphology+SED consistency comparison between passive disks, passive spheroids and star-forming disks; treat inferred SFHs as model-dependent, and first finish the independent E0 injection/recovery and n/B/T identifiability gates. Useful for discussing future survey applications.
- **Limitations:** Optical gri training/priors and model-dependent SFH inference do not transfer automatically to high-z JWST/NIRCam images. Morphological information about past SFH is not proof that a particular stellar disk survived quenching, nor a measurement of B/T classification bias.
- **Next:** Read training labels, simulation/empirical priors, uncertainty calibration, domain shift and quiescent-selection definitions; consider only a small held-out pilot after frozen recovery tests.
- **Status:** arXiv abstract verified 2026-11-07; submitted 2026-11-05, in 2026-11-06 listing; full methods/code not audited.

## Daily scan follow-up (2026-11-07)

- **2026-11-06 arXiv listing:** Bodansky et al. (2611.07237) and Alfonzo et al. (2611.07373) added as B25/B26, respectively. First is dust/quenching context; second is prospective morphology+SED method. Neither establishes stellar-disk survival or B/T recovery completeness.
- **Scope:** Literature documentation only; no frozen selection, code, fitting settings or scientific results changed.


### B27. COSMOS/CANDELS stellar kinematics and slow-rotator evolution (2026-11-11 listing)
- **Paper:** [Muñoz López et al., *Intermediate-redshift slow rotators as the progenitors of the most massive galaxies at z ~ 0*](https://arxiv.org/abs/2611.13225)
- **Type / priority:** Priority B, **kinematic and evolutionary science context**, not direct disk-survival or B/T-recovery evidence.
- **Plain-language takeaway:** VLT/MUSE stellar kinematics and star-formation histories for 218 CANDELS/COSMOS galaxies at 0.1<z<1 identify 17 slow rotators (~8%). The authors explore environmental and redshift trends and links to massive present-day slow rotators; they explicitly cannot establish whether angular-momentum loss coincided with the last star-formation episode.
- **Apply to GOLD403:** In Discussion, distinguish photometric disk dominance (n or light B/T) from kinematic rotation and from quenching chronology. If future resolved kinematics become available, compare matched quiescent disk/spheroid controls; do not infer rotational support from GOLD403 B/T alone.
- **Limitations:** Lower-redshift, flux-limited and kinematically heterogeneous sample, with only 17 slow rotators; no high-z JWST B/T confusion calibration, no measured survival of individual stellar disks.
- **Next:** Check the MUSE kinematic classifications, mass/redshift matching, environmental selection and spin-parameter uncertainties before using any population comparison.
- **Status:** Title and abstract verified in 2026-11-11 arXiv new listings; full paper/data not audited.

### B28. Realistic galaxy morphology in generative forward modeling (2026-11-11 listing)
- **Paper:** [Centofanti et al., *SHINE: Shear inference environment - Generative forward modelling for radio weak gravitational lensing*](https://arxiv.org/abs/2611.14301)
- **Type / priority:** Priority B, **transferable forward-model validation lesson**, not a direct passive-disk, JWST or B/T method.
- **Plain-language takeaway:** A radio-interferometric shear-inference forward model performs well on parametric mock galaxies but shows >10-sigma shear bias on realistic COSMOS morphologies; adding a galaxy-image generative model reduces the reported bias below 2 sigma. This highlights how simplified morphology assumptions can fail under realistic galaxy structure.
- **Apply to GOLD403:** Use as methodological motivation for testing the E0 artificial-redshifting/injection-recovery pipeline with realistic COSMOS-Web morphologies and real backgrounds, in addition to idealized Sérsic/B+D mocks. Compare n and B/T recovery, class-confusion matrices, non-identifiable fits and sensitivity to model mismatch on a frozen held-out sample; do not adopt the radio shear model or alter frozen cuts.
- **Limitations:** Different instrument, Fourier-domain radio visibilities and target statistic (cosmic shear rather than bulge/disk photometry); numerical bias improvements cannot be transferred to JWST or interpreted as disk-survival evidence.
- **Next:** Read mock-vs-real comparison and generative-training validation, then assess whether a simple empirical-morphology held-out test is justified after the existing E0 recovery baseline.
- **Status:** Title and abstract verified in 2026-11-11 arXiv new listings; full text/code not audited.

## Daily scan follow-up (2026-11-12)
- **New 2026-11-11 listing:** Muñoz López et al. (2611.13225) added as kinematic science context; Centofanti et al. (2611.14301) added as a model-mismatch/forward-modeling methodology analogy. Neither is direct evidence of quiescent disk survival or a JWST B/T recovery calibration.
- **Scope:** Documentation only; no scientific code, frozen cuts, fitting settings or pipeline configurations changed.


### B29. Three-dimensional dust attenuation biases Sérsic morphology (2026-11-13 listing)
- **Paper:** [Duarte et al., *3D dust attenuation effects in galaxies: structural biases and induced negative color gradients*](https://arxiv.org/abs/2611.15355)
- **Type / priority:** Priority B, **direct structural-bias methodology**, but not a calibrated JWST B/T recovery study.
- **Plain-language takeaway:** SKIRT radiative-transfer experiments with idealized spherical Sérsic stellar/dust distributions show that internal dust can reshape observed surface-brightness profiles, shift fitted Sérsic indices by up to roughly 25% in the tested models, and create apparent negative color gradients without stellar-population gradients.
- **Apply to GOLD403:** Consider dust as a separate model-mismatch/systematic axis when interpreting single-Sérsic n, B/T and color/SED quiescence classifications. After the frozen E0 baseline, test a small matched set of dust-attenuated and dust-free synthetic images with the same PSF, depth and redshifting; measure changes in n, B/T, identifiability and class-confusion, without changing frozen selection cuts.
- **Limitations:** Simplified spherical, constant-SED models are not realistic inclined bulge+disk galaxies; the quoted 25% is model-specific and not a correction for COSMOS-Web. Dust-driven structure does not establish disk survival after quenching.
- **Next:** Inspect SKIRT geometry, optical-depth/wavelength dependence, fitted-profile procedure and released inputs; determine whether a minimal dust stress test is feasible after existing E0 recovery gates.
- **Status:** Exact title and arXiv abstract verified in 2026-11-13 new listings; full text/code not audited.

### B30. Euclid DR1 Bayesian intrinsic galaxy-shape inference (2026-11-13 listing)
- **Paper:** [Dunn et al., *Euclid: Data Release 1 (DR1) -- Bayesian 3D shape inference of star-forming galaxy populations*](https://arxiv.org/abs/2611.16109)
- **Type / priority:** Priority B, **future-survey population-shape methodology/context**, not direct passive-disk or B/T evidence.
- **Plain-language takeaway:** Hierarchical Bayesian inference on observed Sérsic axis ratios and effective radii estimates intrinsic 3D shape distributions for over 40 million Euclid star-forming galaxies at z<1.2, demonstrating population-level shape constraints and redshift trends.
- **Apply to GOLD403:** Use as a reference for distinguishing projected axis ratio from intrinsic disk shape and for future Euclid/COSMOS-Web population comparisons. After morphology recovery is calibrated, consider whether an inclination/axis-ratio selection-function test or a separate hierarchical shape analysis of passive disks and matched star-forming controls is justified.
- **Limitations:** Star-forming rather than quiescent population, lower redshifts and different imaging/PSF; inferred flattening is not an individual galaxy B/T measurement, proof of rotational support, or disk-survival evidence. No JWST artificial-redshifting calibration.
- **Next:** Read selection, mass/redshift bins, Sérsic measurement uncertainties, projection priors and HMC validation; assess overlap with GOLD403 before any cross-survey interpretation.
- **Status:** Exact title and arXiv abstract verified in 2026-11-13 new listings; full paper/implementation not audited.

## Daily scan follow-up (2026-11-14)
- **New 2026-11-13 listing:** Duarte et al. (2611.15355) added for structural dust bias; Dunn et al. (2611.16109) added as Euclid population-shape methodology/context. Neither proves quiescent stellar-disk survival.
- **Scope:** Documentation only. Frozen cuts, code, and pipeline settings unchanged.

### B31. Dynamical disk–spheroid decomposition in TNG100 (2026-11-16 listing)
- **Paper:** [Cristiani, Navarro & Abadi, *Properties of stellar disks and spheroids in simulated galaxies*](https://arxiv.org/abs/2611.17415)
- **Type / priority:** Priority B, **science context and dynamical decomposition comparison**; not an observational JWST B/T recovery method or direct disk-survival test.
- **Plain-language takeaway:** Dynamically decomposes 3,452 TNG100 galaxies into rotating stellar disks and non-rotating spheroids using stellar orbital angular momentum and energy. At fixed disk mass, disk size, rotation and stellar formation epoch depend on spheroid mass; spheroid properties depend less strongly on the coexisting disk.
- **Apply to GOLD403:** Use in Discussion to distinguish photometric light B/T and Sérsic n from dynamical disk fraction. After E0 identifiability and selection validation, consider a controlled comparison with mock-observed TNG galaxies, checking whether photometric B/T tracks dynamical fractions as a function of mass, size and inclination. Do not infer disk survival or rotation from low observed B/T.
- **Limitations:** Simulation-specific definitions, mass range log(M*/Msun)=10–12, no explicit quiescent-disk survival experiment, and no JWST noise/PSF/selection calibration; dynamical and photometric decompositions are not interchangeable.
- **Next:** Read orbital decomposition and population selection, examine star-formation state and redshift coverage, and assess feasibility of mock-observing a small matched subset after existing E0 gates.
- **Status:** Exact title and abstract independently verified on arXiv 2026-11-17; submitted 2026-11-12 and listed 2026-11-16; full paper/code not audited.

### B32. Euclid DR1 multi-band catalog measurement and morphology quality flags (2026-11-16 listing)
- **Paper:** [Euclid Collaboration (Kümmel et al.), *Euclid Data Release 1 (DR1): The MERge processing*](https://arxiv.org/abs/2611.17832)
- **Type / priority:** Priority B, **future-survey measurement pipeline and quality-control methodology**; not direct passive-disk evidence.
- **Plain-language takeaway:** Describes Euclid DR1 source detection and multiwavelength catalog merging, including PSF-matched aperture, template-fitting and Sérsic photometry, morphology measurements, quality flags, and validation of photometric homogeneity.
- **Apply to GOLD403:** Compare survey-quality/flag and PSF-matching strategies with COSMOS-Web morphology catalog provenance. Inform future Euclid transfer tests and held-out E0 recovery diagnostics for reliable n/B/T, without substituting Euclid Sérsic photometry for validated bulge+disk decomposition.
- **Limitations:** Pipeline/data-release paper, not a quiescent-disk sample, artificial-redshifting experiment, B/T confusion matrix or demonstration of stellar-disk survival. Euclid resolution/depth differs from JWST.
- **Next:** Inspect catalog flag definitions, PSF/template/Sérsic validation and released columns; note any comparable quality diagnostics for a future cross-survey comparison only.
- **Status:** Exact title and abstract independently verified in 2026-11-16 arXiv listing; full technical validation and catalog products not audited.

## Daily scan follow-up (2026-11-17)
- **2026-11-16 listing:** Cristiani et al. (2611.17415) added as dynamical decomposition context; Euclid MERge (2611.17832) added as future-survey catalog/morphology quality methodology. Neither demonstrates quiescent disk survival or calibrates JWST B/T recovery.
- **Scope:** Documentation only; frozen cuts, scientific code and pipeline settings unchanged.

### B33. Conditional generative models for realistic galaxy morphology (2026-11-17 listing)
- **Paper:** [Xu et al., *From Non-parametric Statistics to Images: Generating Galaxy Morphologies*](https://arxiv.org/abs/2611.19211)
- **Type / priority:** Priority B, **transferable image-generation / forward-model validation method**, not direct quiescent-disk science or JWST B/T calibration.
- **Plain-language takeaway:** Flow-VAE generates galaxy images conditioned on CAS, Gini and M20 descriptors, trained on 240,000 DESI Legacy Survey r-band images. Re-measured morphology generally tracks requested descriptors but regresses toward common training morphologies and becomes biased in poorly supported descriptor combinations.
- **Apply to GOLD403:** After the frozen E0/Sérsic+B+D recovery gates, consider an explicitly separate held-out realism test comparing parametric truth images with non-parametric or empirical galaxy images, checking n/B/T recovery, class confusion, failures and coverage. Use this as a model-mismatch stress test, not as ground-truth disk labels or a replacement for the established renderer.
- **Limitations:** Ground-based optical r-band training, not JWST NIRCam; CAS/Gini/M20 do not determine intrinsic B/T, stellar dynamics or quiescence. No passive-disk survival measurement and no calibrated JWST injection recovery.
- **Next:** Inspect image resolution, PSF, training support, conditioning fidelity and released model/code; determine whether a small controlled comparison adds value after current gates.
- **Status:** Exact arXiv title and abstract checked 2026-11-18; full paper/code not audited.

### B34. Orbital survival and quiescence in simulated LEGA-C-like galaxies (2026-11-17 listing)
- **Paper:** [Kumar et al., *Orbital decomposition and evolution of LEGA-C-like galaxies in IllustrisTNG from z = 1 to z = 0*](https://arxiv.org/abs/2611.20884)
- **Type / priority:** Priority B, **directly relevant dynamical-evolution science context**, not an observational JWST B/T recovery method.
- **Plain-language takeaway:** Follows TNG100 galaxies from z=1 to 0, decomposing stellar orbits into cold, warm, hot and counter-rotating populations. Lower-mass galaxies tend to have more rotational support; cold-orbit retention differs by star-formation state at z=1, with star-forming progenitors retaining more cold structure than quiescent ones.
- **Apply to GOLD403:** Discuss the distinction between photometric disk-like structure (n/B/T) and dynamically cold stellar orbits; frame future comparisons with mass/redshift-matched mock-observed TNG galaxies and examine how quiescent selection relates to orbital fractions. The paper can motivate a separate disk-survival interpretation, but its simulated evolutionary result is not evidence that an individual GOLD403 disk survived quenching.
- **Limitations:** Simulated LEGA-C-like selection and z=1-to-0 evolution, not COSMOS-Web high-z JWST forward modeling. Orbital circularity cannot be inferred from light B/T alone; quiescence-related differences may be confounded by mass and assembly history.
- **Next:** Audit sample matching, orbital definitions, merger histories, quiescence cuts and available mock observables; consider only a controlled comparison after E0 recovery/identifiability calibration.
- **Status:** Exact arXiv title and abstract checked 2026-11-18; full text and mock products not audited.

## Daily scan follow-up (2026-11-18)
- **2026-11-17 arXiv listing:** Xu et al. (2611.19211) added as transferable generative-morphology methodology; Kumar et al. (2611.20884) added as simulated orbital-evolution context. Neither calibrates JWST B/T completeness or proves disk survival in GOLD403.
- **Scope:** Documentation only; frozen cuts, science code and pipeline settings unchanged.

### B35. Joint imaging–spectroscopy spatial forward modeling in COSMOS (2026-11-18 listing)
- **Paper:** [Vassilakis, Cranmer & Belokurov, *Spectro-Spatial Survey Fusion*](https://arxiv.org/abs/2611.21798)
- **Type / priority:** Priority B, **future-survey and transferable forward-modeling methodology**, not direct passive-disk science, quenching evidence, or a JWST B/T recovery calibration.
- **Plain-language takeaway:** Fits a continuous spectral surface-brightness field with spatial Gaussian components and learned spectral templates jointly to SDSS images and fiber spectra over an 84-arcmin COSMOS region. It predicts held-out HSC images and DESI spectra, including broad spiral patterns in two examples, without refitting those observations.
- **Apply to GOLD403:** A future methodological reference for jointly modeling wavelength-dependent morphology and multi-survey data. After completing the frozen E0 and two-branch n/B/T identifiability gates, compare its instrument-forward-model and held-out-band validation principles with the existing NIRCam rest-band transfer; consider whether spatially varying SEDs could be tested on a small held-out sample. Do **not** substitute Gaussian components for bulge/disk truth or change the frozen pipeline.
- **Limitations:** Demonstrated on SDSS optical imaging/fiber spectra, not JWST or passive-disk-selected galaxies; reproducing broad spiral features does not establish stellar disk survival, physical B/T, quiescence, or classification completeness. A flexible model may still miss faint structure and has not been calibrated for GOLD403.
- **Next:** Read instrument-response formulation, Gaussian/spectral regularization, train/held-out split, source masking and error analysis; check code/data release and whether a limited JWST-compatible benchmark is realistic.
- **Status:** Exact title and abstract checked in the 2026-11-18 arXiv new-submission listing; full text, implementation and applicability to JWST not audited.

## Daily scan follow-up (2026-11-19)
- **2026-11-18 listing:** Vassilakis et al. (2611.21798) added as a prospective multi-survey spatial/spectral forward-modeling reference, not as disk-survival evidence. Brown-dwarf companion demographics and late-M activity papers were screened but not entered in this passive-disk backlog.
- **Scope:** Documentation only; no change to scientific code, selection cuts or pipeline settings.

### B36. GECKOS edge-on bar geometry from molecular-gas kinematics (2026-11-19 listing)
- **Paper:** [Fraser-McKelvie et al., *The GECKOS Survey: deriving bar properties in edge-on galaxies from molecular gas kinematics*](https://arxiv.org/abs/2611.24770)
- **Type / priority:** Priority B, **targeted inclination/bar-method context**; not a direct passive-disk or JWST B/T recovery method.
- **Plain-language takeaway:** Uses ALMA molecular-gas nuclear-ring velocities and stellar circular-velocity models to infer bar orientation in edge-on galaxies; tests on a toy model and hydrodynamical snapshot and applies to six GECKOS systems with boxy-peanut bulges.
- **Apply to GOLD403:** Motivates treating bar orientation, inclination and boxy-peanut light as possible sources of bulge/disk misclassification. After frozen E0 gates, consider a small separate inclination/bar stress test for n/B/T recovery, using imaging-compatible truth models; do not adopt the gas-kinematic estimator in the photometric pipeline.
- **Limitations:** Requires resolved ALMA CO and nuclear rings, generally unavailable for GOLD403; local edge-on systems are not quiescent high-z disk-survival evidence. The inferred bar angle is not a B/T calibration.
- **Next:** Inspect the six-object selection, nuclear-ring assumption and validation failure modes; decide whether orientation-sensitive mock images would add value to a held-out test.
- **Status:** Exact title and arXiv abstract verified 2026-11-20; full text, data and transfer not audited.

### B37. Bar and boxy-peanut growth as a function of disk and bulge structure (2026-11-19 listing)
- **Paper:** [Durán-Camacho et al., *Bar formation and secular evolution in live Milky Way-like galaxies*](https://arxiv.org/abs/2611.24884)
- **Type / priority:** Priority B, **simulation-based disk-structure science context and potential model-mismatch test**, not a quenching or JWST recovery measurement.
- **Plain-language takeaway:** Fifteen isolated AREPO Milky-Way-like simulations vary stellar mass and initial bulge fraction. Bars grow and slow; boxy-peanut structures form on mass- and structure-dependent timescales, often without a sharp buckling event.
- **Apply to GOLD403:** Motivates caution that bar/boxy-peanut structure can be absorbed into simplistic bulge+disk components and alter apparent light B/T. A future held-out comparison could fit B+D-only versus bar-aware mock images at matched JWST PSF, redshift, S/N and inclination, measuring B/T confusion without changing the frozen cuts.
- **Limitations:** Isolated nearby-galaxy analogues over 3 Gyr, not quiescent COSMOS-Web galaxies; simulated bar formation is not proof of disk survival after quenching, and no JWST B/T error rates are provided.
- **Next:** Examine the model parameter range, projection examples and available simulated images; assess whether a limited bar-mismatch test is justified after E0 validation.
- **Status:** Exact title and arXiv abstract verified 2026-11-20; full simulation products not audited.

### B38. Simulation-to-simulation domain transfer for galaxy environment inference (2026-11-19 listing)
- **Paper:** [Chen et al., *Cross-Dataset Inference of Central-Satellite Classification and Host Halo Masses from Galaxy neighbours with Machine Learning*](https://arxiv.org/abs/2611.24803)
- **Type / priority:** Priority B, **future environment/selection methodology**, not direct morphology, quenching, or disk-survival evidence.
- **Plain-language takeaway:** XGBoost predicts central/satellite class and central halo mass from nearby-galaxy positions and stellar masses in TNG100; tests transfer to EAGLE after stellar-mass-distribution alignment and reports performance degradation and satellite misclassification failure modes.
- **Apply to GOLD403:** Future mass/redshift-matched environmental comparisons of passive disks versus quiescent spheroids could use neighbor-based environmental inference, with explicit survey completeness, photo-z projection and domain-shift checks. Do not transfer simulation purity/completeness numbers to COSMOS-Web or alter frozen sample membership.
- **Limitations:** Simulation-to-simulation validation is not observational calibration; host-halo prediction depends on neighbor detection thresholds, 3D/projection errors and simulation assumptions. No stellar-disk survival or JWST B/T recovery measurement.
- **Next:** Inspect the projected-redshift feature definition, survey-depth sensitivity, domain alignment and available code before considering a COSMOS-Web matched-control pilot.
- **Status:** Exact title and arXiv abstract verified 2026-11-20; full text/code and observational transfer not audited.

## Daily scan follow-up (2026-11-20)
- **2026-11-19 new-submission listing:** Fraser-McKelvie et al. (2611.24770), Durán-Camacho et al. (2611.24884) and Chen et al. (2611.24803) added as targeted bar/orientation and future environmental methods/context, not direct passive-disk survival evidence.
- **Scope:** Documentation only; no change to scientific code, frozen cuts or pipeline settings.
