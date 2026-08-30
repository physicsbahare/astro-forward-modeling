# Pre-implementation Forward-Modeling Verification Suite

This repository snapshot is **not the production astronomy package**. It is an independent scientific verification harness used to freeze equations, numerical semantics, and later acceptance criteria before production implementation begins.

## Why this exists

The intended public framework will eventually answer questions such as:

> If the same astrophysical source were observed at a different redshift, through a different bandpass/PSF/pixel grid/survey, what would be observed, what would a real measurement pipeline recover, and what biases or completeness losses would result?

The core is intended to remain science-neutral: spiral structure, bars, mergers, AGN-host decomposition, photometric completeness, and other tasks belong to measurement/recovery plugins rather than the forward-rendering core.

## Current verification modules

- `verification/reference.py` — independent flat-LCDM and radiometric reference formulas.
- `verification/radiometry.py` — `F_nu/F_lambda`, luminosity distance, photon-count and Tolman consistency checks.
- `verification/psf.py` — analytic Gaussian PSF matching, Wiener reference implementation, `D`/`W_-` diagnostics, impossible-resolution case.
- `verification/resampling.py` — exact overlap transfer versus direct continuous Gaussian pixel integration.
- `verification/chromatic.py` — two-component color-gradient + wavelength-dependent PSF experiment.
- `verification/noise.py` — correct detector-order source Poisson statistics and real-background double-noise check.
- `verification/spectral_support.py` — inverse-problem demonstration that wavelength overlap is not equivalent to spectral information support.

## Run

The current standalone suite needs only Python, NumPy, SciPy, Matplotlib, and pytest.

```bash
python run_verification.py
pytest -q
```

Results are written to `results/` and diagnostic plots to `figures/`.

## Current status

Seven regression/physics tests pass in the present snapshot. The current results establish physical/numerical behavior but **do not yet define universal public-package tolerances**. Those limits will be frozen only after cross-code checks against maintained astronomy libraries and reproduction of literature benchmarks such as FERENGI, Yu et al. (2023), PSF-mismatch AGN simulations, and real survey injection/recovery.

See:

- `docs/MATHEMATICAL_VERIFICATION.md`
- `docs/REFERENCES.md`
- `docs/NEXT_GATES.md`

## Important scientific rules already frozen

1. No duplicated K-correction/dimming factors in the forward model.
2. Wavelength-dependent PSF belongs inside the spectral integration.
3. Flux-per-pixel and surface-brightness semantics are never inferred silently.
4. Direct mode may degrade information but may not invent unsupported spatial frequencies.
5. Spectral support is judged by predictive information/uncertainty, not wavelength overlap alone.
6. Source Poisson noise is generated at the detector-order stage, after optical redistribution.
7. Real-image injection does not add a second realization of the already-existing sky noise.
8. Intrinsic evolution is an explicit operator, never silently mixed with observational degradation.

Development is currently private and pre-release. The `verification-v0.1` branch contains the scientific verification work before production implementation begins.
