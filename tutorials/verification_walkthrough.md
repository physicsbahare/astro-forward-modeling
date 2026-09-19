# Verification Walkthrough

This tutorial explains how to inspect and reproduce the **pre-implementation** scientific checks. It is not a tutorial for the eventual public forward-modeling package.

## 1. Create a clean environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-verification.txt
```

## 2. Run the independent physics/regression tests

```bash
pytest -q tests/test_verification.py
```

These tests check cosmological spectral-density identities, Tolman dimming, analytic Gaussian PSF matching, exact-overlap flux conservation, chromatic-PSF non-equivalence, detector-order source Poisson noise, the no-double-background rule, and a spectral-information-support counterexample.

The thresholds here are **verification-harness regression thresholds**. They are not automatically the future public package's science-quality thresholds.

## 3. Generate convergence tables and diagnostic figures

```bash
python run_verification.py
```

This writes machine-readable results under `results/` and diagnostic plots under `figures/`.

The most important principle is to inspect multiple quantities. For example, an operation can conserve total flux almost perfectly while still altering morphology substantially.

## 4. Inspect the mathematical conventions

Read:

```text
docs/MATHEMATICAL_VERIFICATION.md
```

The key frozen choices include:

- canonical spatial-spectral source representation;
- explicit `F_nu/F_lambda/I_nu/I_lambda` conventions;
- no separate multiplicative forward K-correction;
- wavelength-dependent PSF inside the band integration;
- no silent super-resolution;
- source Poisson noise after optical redistribution;
- no second sky-noise realization during injection into a real noisy image.

## 5. Run the first external cross-code benchmark

Create a separate environment because this benchmark intentionally pins astronomy-package versions:

```bash
python -m venv .venv-crosscode
source .venv-crosscode/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-verification.txt
python -m pip install -r requirements-crosscode-core.txt
pytest -q crosscode/test_gate_b_core.py
```

This currently compares the independent reference harness with:

- Astropy cosmological distances and spectral-density equivalencies;
- `reproject_exact` on a controlled WCS/surface-brightness case;
- Photutils Wiener PSF matching on analytic Gaussian truth;
- GalSim chromatic rendering on an analytic source+PSF problem.

A failing cross-code test is **not automatically a package bug**. It may reveal a unit convention, API convention, normalization, integration rule, or numerical tolerance that needs to be understood. The scientific rule is: do not loosen a test merely to make CI green; explain the discrepancy first.

## 6. JWST-specific checks

Read:

```text
docs/JWST_VALIDATION_PROTOCOL.md
```

The JWST acceptance tests will pin both the STPSF software version **and the matching versioned STPSF reference-data bundle**, and will pin the JWST pipeline plus CRDS context. This is necessary because PSF and calibration reference products evolve independently of our repository.

## 7. Literature reproduction

Read:

```text
docs/LITERATURE_BENCHMARK_PROTOCOLS.md
```

The minimum benchmark set before production defaults are frozen is:

1. FERENGI;
2. DOPTERIAN / Paulino-Afonso;
3. Yu et al. (2023) DESI→JWST morphology degradation;
4. AGN nuclear-contamination experiments;
5. Zhuang & Shen JWST PSF-mismatch behavior;
6. COSMOS-Web AGN-host architecture stress test.

## 8. Real survey validation

The first survey-realistic application is planned for COSMOS-Web NIRCam. The objective is not just to create visually plausible images. Synthetic sources must be inserted into the real measurement environment and then passed through the same detection/deblending/morphology or AGN-recovery pipeline used for real objects.

## 9. When can production coding start?

Read `docs/NEXT_GATES.md`.

Production framework implementation starts only after the cross-code, literature, survey-validation, numerical-threshold, and architecture-review gates are closed or explicitly justified. This separation is intentional: the verification harness should remain useful as an independent scientific reference even after the production package exists.
