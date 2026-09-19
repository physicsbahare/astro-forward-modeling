# Gate C — Literature Reproduction Protocols

Gate C asks a stricter question than ordinary software testing: **when the verification harness is configured to reproduce a published experiment, does it recover the published physical behavior without hiding convention differences?**

The purpose is not to force pixel-for-pixel agreement when source data, PSFs, fitting software, or random realizations differ. Every benchmark must explicitly separate differences caused by source data, cosmology, filters, PSFs, source preparation, measurement definitions, noise, selection, and intrinsic-evolution prescriptions.

No numerical acceptance threshold may be relaxed merely to obtain a pass. A discrepancy must first be traced to a documented methodological or numerical cause.

## Common benchmark record

Every Gate-C benchmark must archive:

1. paper, DOI/arXiv identifier, exact section/figure/table being tested;
2. source sample or synthetic truth definition;
3. cosmology and redshift convention;
4. source and target bandpasses;
5. source preparation, masking, neighbor removal and PSF treatment;
6. all intrinsic-evolution prescriptions, explicitly separated from observation-only effects;
7. target PSF, pixel scale, noise/background and exposure assumptions;
8. measurement software, version and parameter definitions;
9. random seeds and ensemble size;
10. machine-readable truth/recovery table;
11. quantitative comparison to the paper;
12. discrepancy diagnosis and reviewed pass/fail decision.

## C1. FERENGI benchmark

**Primary reference:** Barden, Jahnke & Häußler (2008), *FERENGI: Redshifting Galaxies from SDSS to GEMS, STAGES and COSMOS*, ApJS 175, 105; arXiv:0812.1022.

Reproduce the logical operator sequence on a controlled SDSS-like multiband galaxy or a synthetic equivalent with known truth:

1. multiband registration and source-PSF preparation;
2. spatially resolved spectral interpolation;
3. angular-size transformation;
4. cosmological spectral/surface-brightness transformation;
5. target bandpass integration;
6. source-to-target PSF transformation;
7. target pixel sampling;
8. realistic background/noise insertion.

Compare at minimum total flux, angular size, radial profile, color-gradient behavior, and normalized morphology residuals across target redshifts. Run observation-only and luminosity-evolution configurations separately. The observation-only configuration is the reference calibration mode for this project.

A required diagnostic is to demonstrate that our direct SED-through-bandpass radiometry gives the same observable as the equivalent FERENGI convention when the same assumptions are imposed, without applying a second K-correction or Tolman factor.

## C2. DOPTERIAN / Paulino-Afonso benchmark

**Primary reference:** Paulino-Afonso et al. (2017), MNRAS 465, 2717, plus later DOPTERIAN-based work.

Reproduce the published style of angular rebinning, cosmological dimming, PSF transformation, Poisson noise and real-background insertion. The purpose is to confirm that a modern implementation reproduces the direction and scale of structural degradation without inheriting legacy implementation assumptions blindly.

Record explicitly where the modern radiometric treatment differs from a hard-coded Tolman multiplier and demonstrate equivalence at the final observable level when the definitions are matched.

## C3. Yu et al. (2023) DESI → JWST morphology benchmark

**Primary reference:** Yu et al. (2023), A&A 676, A74, arXiv:2307.04753.

The paper artificially redshifts nearby DESI/DECaLS galaxies into CEERS-like JWST/NIRCam observations. Their experiment provides an especially valuable benchmark because it connects morphology bias to **resolvedness** rather than redshift alone.

### Published configuration anchors

- 1816 nearby galaxies;
- stellar-mass range approximately `9.75 < log10(M*/Msun) < 11.25`;
- target redshifts `0.75 <= z <= 3`;
- cosmology `(Omega_M, Omega_Lambda, h) = (0.27, 0.73, 0.70)`;
- source DECaLS `g/r/z` effective wavelengths approximately 4796/6382/9108 Å;
- target filters selected to maintain approximately rest-frame optical 5000–7000 Å:
  - F115W at z=0.75 and 1.0;
  - F150W at z=1.25, 1.5 and 1.75;
  - F200W at z=2–3;
- CEERS-like output sampling 0.03 arcsec/pixel;
- the published setup used oversampled WebbPSF PSFs for the relevant bands;
- foreground stars/neighbors were cleaned before the redshifting experiment, which must be represented as an explicit source-preparation step rather than silently changing the truth scene.

### Required measurements

Recover, using definitions matched as closely as practical:

- Petrosian-like radius / resolvedness measure;
- half-light radius;
- concentration;
- asymmetry;
- axis ratio where practical;
- Sérsic index when the fitting backend is available.

The key independent variable is

`R_p / FWHM_PSF`

rather than redshift alone.

### Published trend anchors

The benchmark should reproduce the reported directions:

- nonparametric size measures are modestly affected by the PSF;
- symmetric galaxies can acquire a small positive asymmetry bias from PSF structure;
- intrinsically asymmetric sources lose asymmetry as small-scale structure is smoothed;
- concentration is biased low most strongly for highly concentrated and poorly resolved systems;
- asymmetry becomes substantially more trustworthy once the source is resolved at roughly `R_p/FWHM >= 5` in their experiment.

The value `~5` is a **paper-specific empirical anchor**, not a universal package threshold. Our framework-wide warning threshold will only be frozen after Gate E.

## C4. AGN nuclear-contamination benchmark

**Primary references:** Pierce et al. (2010), Gabor et al. (2009), and related controlled AGN-host experiments.

Construct host-only truth scenes and add an unresolved nuclear component over a target-band AGN-fraction grid, for example:

`0, 0.01, 0.03, 0.05, 0.10, 0.20, 0.30, 0.50, 0.70, 0.90`.

Repeat over host size, Sérsic index, axis ratio, S/N and PSF-resolvedness. Measure with and without nuclear subtraction/decomposition.

At minimum recover concentration, asymmetry, Gini/M20 where available, half-light radius, Sérsic index, host flux and AGN fraction. We should recover the established qualitative result that central-light-sensitive morphology becomes increasingly biased as unresolved nuclear contribution grows, while the exact transition depends on the host, PSF and S/N.

A paper-specific onset near the 10–20% nuclear-light regime may be used as a comparison anchor where definitions match, but must not become a generic hard-coded threshold.

## C5. Zhuang & Shen NIRCam PSF-mismatch benchmark

**Primary reference:** Zhuang & Shen (2024), ApJ 962, 139; arXiv:2304.13776.

This benchmark has an unusually strong advantage: the authors publicly provide CEERS PSF products and large tables of mock AGN input/recovery results. Our benchmark must use a **commit-pinned copy or download script** rather than a moving branch.

### Published quantitative anchors

The paper reports NIRCam PSF FWHM spatial variation decreasing strongly with wavelength, with maximum/RMS fractional variation of about 20%/5% in F070W and about 3%/0.6% in F444W.

The public mock-product metadata includes fiducial/broader/narrower PSF FWHMs. Examples include:

- F070W: 64.8 / 66.5 / 62.0 mas;
- F115W: 60.5 / 62.0 / 59.1 mas;
- F150W: 64.7 / 64.7 / 63.3 mas;
- F200W: 75.0 / 76.0 / 74.2 mas;
- F277W: 119 / 120 / 118 mas;
- F356W: 138 / 139 / 137 mas;
- F444W: 160 / 162 / 160 mas.

These numbers are benchmark metadata, not generic JWST PSF constants.

### Required experiment

Generate or select PSF+Sérsic truth systems with a known PSF, then recover them with controlled mismatch families:

- width mismatch;
- core/wing mismatch;
- detector-position mismatch;
- source-SED/chromatic mismatch;
- empirical realization mismatch;
- tied versus free AGN/host centroids.

Sweep host-to-nucleus contrast, host size relative to PSF FWHM, Sérsic index, surface brightness and S/N.

Track biases in host flux, effective radius, Sérsic index, axis ratio, AGN fraction, centroid offset and residual structure.

### Required trend recovery

We must reproduce the published directions that:

- mismatched PSFs generally overestimate host flux, more strongly in AGN-dominated systems;
- a broader adopted PSF tends to produce a less concentrated host;
- a narrower adopted PSF tends to produce a more compact/concentrated host;
- at high S/N, systematic PSF/model mismatch can exceed formal fitting uncertainties;
- fitted AGN-host centroid offsets can be artificial and are strongly surface-brightness dependent.

The paper reports >1-sigma apparent centroid offsets in roughly 80% and >3-sigma offsets in roughly 20–30% of their mocks; near their surface-brightness limit, offsets can reach approximately 80%, 26% and 7% of `R_e` for `R_e = 0.12, 0.48, 1.92 arcsec`, respectively. These are high-value quantitative reproduction targets when using the authors' public mock tables.

## C6. COSMOS-Web AGN-host stress case

**Primary references:**

- Zhuang, Li & Shen (2023), arXiv:2309.03266, for COSMOS-Web PSF construction and AGN-host decomposition;
- Vijarnwannaluk et al. (2025), ApJ 994, 265, DOI 10.3847/1538-4357/ae102a, for large-sample rest-frame morphology/size analysis.

This is not intended as a literal reproduction of the entire AGN sample. It is an architecture stress test ensuring that a single experiment supports:

- unresolved nuclear emission;
- extended host components;
- wavelength-dependent host morphology;
- spatial/temporal PSF variation;
- host-only morphology after nuclear decomposition;
- model-comparison / measurement adapters;
- uncertainty propagation across PSF realizations.

The COSMOS-Web PSF literature specifically motivates treating PSF position and epoch as first-class metadata rather than one static PSF per filter.

## C7. Salvador et al. (2024) cosmological surface-brightness degradation / confusion benchmark

**Primary reference:** Salvador et al. (2024), A&A 684, A166, DOI 10.1051/0004-6361/202347522.

This DOPTERIAN-based study is valuable because it tests **classification transfer**, not only changes in scalar morphology statistics.

### Required experiment

Build a reference set with spheroid, early-type disk, late-type disk and irregular truth labels. Artificially degrade the same objects through the paper's redshift-bin logic while recording both object-level confusion and population fractions.

The paper reports that a large majority of individual galaxies (85.16% in their experiment) change visual morphological class at some point as cosmological surface-brightness degradation increases. The principal confusion channels are physically interpretable:

1. disks/irregulars become more bulge dominated as low-surface-brightness structure disappears;
2. late-type disks can become irregular when only disconnected bright structures remain.

Published reference counts rise strongly toward spheroids and fall strongly for late-type disks across their redshift bins; for example the reference-sample counts progress from 55 spheroids / 89 late-type disks near z~0.3 to 143 spheroids / 1 late-type disk near z~2.75.

These raw counts are **not universal expected fractions** and must never be used as a generic correction. They are benchmark targets only when reproducing the source sample and classification procedure.

### Required output

- full confusion matrix as a function of redshift and observing state;
- per-class completeness and contamination;
- population-fraction distortion;
- object-level trajectories through class space;
- comparison of visual/classifier results with Gini/M20/asymmetry where available.

This benchmark directly validates the proposed categorical `TransferFunction` abstraction.

## C8. Liang et al. (2024) bar-resolution / recoverability benchmark

**Primary reference:** Liang et al. (2024), A&A 688, A158, DOI 10.1051/0004-6361/202348539.

This benchmark is important because it tests a morphological feature whose recoverability has a sharply resolution-dependent transition and an undersampling dependence.

### Published anchors

The study finds:

- bar position angle is comparatively robust to resolution;
- bar ellipticity is biased low as resolution worsens;
- bar size is nearly unbiased on average while intrinsic bar size is above roughly `2 x FWHM`;
- detection effectiveness remains near 100% above about `a_bar,true/FWHM ~ 2` for adequately sampled PSFs and then drops quickly;
- the 50% bar-detection effectiveness points reported for their 0.03 arcsec/pixel CEERS-like simulations are approximately:
  - F115W: 2.47 FWHM;
  - F150W: 1.71 FWHM;
  - F200W: 1.65 FWHM.

The F115W degradation occurs at larger `a_bar/FWHM` because the F115W PSF is undersampled at 0.03 arcsec/pixel (about 1.2 pixels/FWHM in their setup), showing that `feature_size/FWHM` alone is insufficient when detector/mosaic sampling is poor.

### Required output

- bar-detection effectiveness versus `a_bar/FWHM`;
- recovered bar length bias/scatter;
- recovered ellipticity bias/scatter;
- position-angle bias/scatter;
- explicit dependence on pixels/FWHM and S/N.

This benchmark is a direct test of whether the framework exposes both **optical resolution and sampling** as separate information limits.

## Benchmark data policy

Where public benchmark data can be legally redistributed, prefer stable download scripts plus checksums and upstream citation over committing large third-party files. For external Git repositories, record repository, exact commit SHA, file paths and license. Where redistribution is restricted, store retrieval instructions and exact identifiers. Synthetic analogues should be retained in this repository because their truth is exactly known.

## Gate-C closure criterion

For **every** benchmark:

1. exact paper/method section recorded;
2. exact assumptions mapped to framework operators;
3. executable reproduction script/notebook;
4. machine-readable outputs;
5. quantitative comparison against the published trend or table;
6. discrepancy discussion;
7. review decision marked `PASS`, `PASS WITH EXPLAINED DIFFERENCE`, or `FAIL`;
8. no production default is derived from the benchmark until its result has been reviewed.
