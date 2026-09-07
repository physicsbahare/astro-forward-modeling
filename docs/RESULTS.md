# Verification Results Snapshot

This file records the current numerical results of the independent pre-implementation suite. It is a snapshot, not a set of universal production tolerances.

## Radiometry

At `z=2.0` with `30001` spectral samples:

- Distance-duality relative error: `0.000e+00`
- Bolometric consistency from `F_nu`: `1.294e-16`
- Bolometric consistency from `F_lambda`: `1.354e-09`
- `F_nu`/`F_lambda` bolometric representation disagreement: `1.354e-09`
- Photon-rate representation disagreement: `1.621e-12`
- Tolman-integral relative error: `0.000e+00`

The `F_lambda` path is intentionally numerically independent and is currently limited by trapezoidal quadrature at the ~1e-9 level on the finest grid. This is acceptable for the verification harness but is not yet a public-package tolerance.

## Analytic Gaussian PSF matching

For `sigma_source=2.5` px and `sigma_target=5.0` px:

- L1 PSF reconstruction error `D`: `7.916e-16`
- Negative-kernel weight `W_-`: `0.000e+00`
- Kernel normalization error: `0.000e+00`
- Relative second-moment error: `1.599e-15`
- White-noise variance factor after this smoothing kernel: `0.004244`
- Sharper-target impossible case detected: `True`

## Chromatic PSF experiment

At `1025` wavelength samples:

- Blue/extended component effective PSF sigma: `2.1081` px
- Red/compact component effective PSF sigma: `2.5245` px
- Global effective PSF sigma: `2.3568` px
- One-global-PSF versus wavelength-resolved normalized L1 image difference: `3.1017%`
- Integrated-flux relative difference: `2.660e-16`
- Relative second-moment difference: `1.678e-16`

The intentionally matched second moment is essentially identical while the normalized image still differs by ~3.1%. This demonstrates why a low-order size metric cannot by itself validate chromatic morphology.

## Noise-ordering experiment

Using `30000` realizations and `5000` expected source electrons:

- Correct detector-order center variance/mean: `0.9809`
- Correct adjacent-pixel correlation: `-0.0074`
- Incorrect pre-PSF center variance/mean: `0.0330`
- Incorrect pre-PSF adjacent-pixel correlation: `1.000000`
- Variance ratio after incorrectly adding a second equal-noise sky realization: `1.9957`

This validates the ordering rule: source shot noise belongs after optical redistribution, and a real noisy background must not be independently re-noised during mosaic injection.

## Spectral-support counterexample

- Simple wavelength coverage fraction: `1.0000`
- Weighted response-matrix condition number: `47.48`
- Target posterior fractional uncertainty: `14.62%`
- Target fractional bias for this fixed noisy realization: `-22.91%`
- Diagnostic prior fraction in target direction: `46.38%`

The target is fully inside the wavelength envelope of the input filters yet remains weakly constrained. Therefore the eventual framework must base spectral safety on predictive information and uncertainty, not only wavelength overlap.

## Test status

The standalone regression suite has previously passed **7/7 tests** in the local verification snapshot. GitHub CI is now the authoritative repeatability check for the repository branch. Cross-code Gate-B tests are tracked separately and are expected to expose convention/API differences that must be resolved rather than hidden.

The next scientific gates are cross-code verification against Astropy/reproject/Photutils/GalSim/STPSF, literature reproduction, and real-survey injection; see `NEXT_GATES.md`.
