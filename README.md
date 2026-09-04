# Pre-implementation Forward-Modeling Verification Suite

This repository is **not the production astronomy package**. It is the pre-production scientific verification harness used to freeze physical conventions, numerical semantics, cross-code behavior, benchmark evidence, and later acceptance criteria before the public framework is implemented.

## Why this exists

The intended framework will answer questions such as:

> If the same astrophysical source were observed at a different redshift, through a different bandpass, PSF, pixel grid, or survey, what would be observed, what would a real measurement pipeline recover, and what biases or completeness losses would result?

The desired scientific product is therefore not only a synthetic image but a documented transfer function between source/observation truth and recovered measurements. The forward-rendering core is intended to remain science-neutral; spiral structure, bars, mergers, AGN-host decomposition, completeness, and similar science cases belong to measurement/recovery adapters and validation plugins.

## Repository structure

- `verification/` — independent physics/numerical reference implementations and synthetic experiments.
- `crosscode/` — comparisons against maintained astronomy packages such as Astropy, reproject, Photutils, GalSim, STPSF, and the JWST calibration stack.
- `benchmarks/` — frozen protocols, archived benchmark receipts, reviews, and literature-motivated stress tests.
- `scripts/` — reproducible experiment runners and read-only artifact audits.
- `tests/` — regression and physics tests for the verification harness.
- `.github/workflows/` — isolated CI workflows for expensive or specially pinned verification stages.

The lightweight package itself still depends only on Python, NumPy, SciPy, and Matplotlib; benchmark-specific environments are pinned separately so optional scientific software is not silently imported into the core verification environment.

## Current status — 2026-09-04

Gate A (independent numerical physics) is substantially complete. The original Gate B cross-code set is complete, including Astropy/reproject/Photutils/GalSim/STPSF/JWST-pipeline/CRDS/drizzle checks; a new PyAutoGalaxy/PyAutoArray morphology cross-code extension remains before architecture freeze.

Gate C has completed the FERENGI, Paulino-Afonso/DOPTERIAN, Yu et al. (2023), AGN nuclear-fraction, and Zhuang & Shen PSF-mismatch scopes. The Zhuang & Shen wrong-PSF stage is intentionally retained as a **scientific morphology-recovery failure** even though its diagnostic workflow completed successfully; CI success is never treated as scientific success.

The active Gate-C line is Dewsnap-style independent-fitter/PSF-construction validation. C6a, the AstroPhot 0.18.0 signed-PSF installation and coordinate-convention preflight, completed successfully in run `33849387267`. The next controlled step is C6b: reuse a clean matched-PSF, noiseless common scene and compare AstroPhot against the archived Imfit result before introducing PSF-construction mismatch or noise.

Gate D real-survey injection, Gate E numerical acceptance freeze, and Gate F production architecture review have not started. Production framework code must not be introduced before those gates are closed.

See `docs/NEXT_GATES.md` for the current roadmap and `benchmarks/dewsnap_2025/C6A_RESULT.md` for the latest completed gate receipt.

## Important scientific rules already frozen

1. Do not apply duplicated K-correction or Tolman-dimming factors when the forward spectral operator already contains the corresponding redshift physics.
2. Wavelength-dependent PSF belongs inside spectral integration; source-SED dependence must be representable.
3. Flux-per-pixel, surface brightness, calibrated image units, and detector counts are explicit semantics and are never inferred silently.
4. Direct mode may degrade information but may not invent unsupported spatial frequencies.
5. Spectral support is judged by predictive information/uncertainty and prior dominance, not wavelength overlap alone.
6. Source Poisson noise is generated after optical redistribution at the detector-order stage.
7. Real-image injection does not add a second realization of the already-existing sky/background noise.
8. Intrinsic evolution is an explicit operator and is never silently mixed with observational degradation.
9. Optimizer convergence or a successful CI job is not sufficient evidence of physical/morphological recovery.
10. Acceptance thresholds are not widened or invented after observing a difficult benchmark; unresolved failures remain part of the verification record.

Development is pre-release. The `verification-v0.1` branch and draft PR #5 are the scientific verification record before production implementation begins.
