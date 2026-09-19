# Gate C1 review — FERENGI (Barden, Jahnke & Häußler 2008)

**Decision: PASS WITH EXPLAINED DIFFERENCE**

This is a scientific review record for the controlled FERENGI-style benchmark in the pre-production verification harness. It is not a production tolerance specification.

## Reference and exact published targets

Primary reference: Barden, Jahnke & Häußler (2008), *FERENGI: Redshifting Galaxies from SDSS to GEMS, STAGES and COSMOS*, ApJS 175, 105, arXiv:0812.1022.

The benchmark is mapped to the following parts of the paper:

- Section 3.1: angular-size transformation and surface-brightness scaling.
- Section 3.2: pixel-wise multiband SED interpolation / bandpass shifting.
- Section 4: target PSF adaptation, source Poisson noise, and insertion into real sky backgrounds.
- Table 2 and Section 6: separation of regridding/PSF effects from bandpass-shift effects and the test that the redshifting operator itself should not introduce an additional systematic trend.
- Figures 6 and 7: transfer-only and full bandpass-shift test logic.

The paper reports that, after subtracting the fitting-only baseline, the regridding/PSF redshifting step introduces no additional systematic trend and hardly increases the scatter (their Figure 6). It also explicitly treats finite-filter effects in the bandpass-shift step rather than applying an extra bolometric dimming term after that step.

## Assumption-to-operator map

| Published FERENGI operation | Verification implementation | Review note |
| --- | --- | --- |
| Registered multiband source images with matched source PSF | Synthetic disk+bulge scene sampled at fixed rest-wavelength knots and convolved with one source PSF | Synthetic truth removes unknown source-registration and SED-fit error while preserving spatial colour gradients. |
| Angular-size change | Physical-kpc source and target grids derived independently from angular-diameter distance | Same physical source is viewed at the target redshift; no intrinsic size evolution. |
| Cosmological surface-brightness transformation | Direct spectral-density transformation in `I_lambda`, with `(1+z)^-5` at corresponding wavelengths | Band-integrated surface brightness recovers Tolman `(1+z)^-4`; no second Tolman factor is applied. |
| Pixel-wise bandpass shift / K-correction | Spatially resolved interpolation between SED knots followed by direct target-band integration | The target observable is generated directly. No second K-correction is applied. |
| Source-to-target PSF adaptation | Gaussian degradation kernel after converting the source PSF to its target-redshift angular equivalent | A sharper-than-source target is rejected rather than deconvolved implicitly. |
| Target pixel grid | Explicit target sampling after angular rescaling | Tested at multiple target redshifts. |
| Source Poisson noise | Independent Poisson draw from the final detector-pixel source expectation | Noise is generated after optical redistribution, preserving detector-order shot-noise statistics. |
| Real target sky insertion | Real-background mode adds the supplied noisy background exactly once | This intentionally avoids re-noising an already noisy background. |

## Executable benchmark and provenance

The executable components are:

- `verification/ferengi_synthetic.py`
- `verification/ferengi_noise_benchmark.py`
- `verification/target_noise.py`
- `tests/test_ferengi_synthetic.py`
- `tests/test_ferengi_noise_benchmark.py`
- `tests/test_target_noise.py`
- `scripts/run_ferengi_synthetic_benchmark.py`
- `scripts/run_ferengi_noise_benchmark.py`
- `.github/workflows/gate-c-ferengi.yml`

Reviewed CI artifact:

- workflow: `gate-c-ferengi`, run 11
- commit: `2b0b7cf9710d15fb5b1f899ef18dcece57c985bb`
- artifact: `gate-c-ferengi-synthetic-baseline`
- artifact SHA-256 digest: `a05cde29d5f5cd52478b4742d82ef2af221e983e312516d3504e005c4aa6d1c9`

The workflow completed the deterministic observation-only tests, deterministic metric generation, target-noise regression tests, target-noise metric generation, and artifact upload successfully.

## Quantitative result

For the deterministic observation-only benchmark at target redshifts `z = 0.2, 0.5, 1.0`:

| Metric | z=0.2 | z=0.5 | z=1.0 |
| --- | ---: | ---: | ---: |
| direct-radiometry scaling relative error | `1.54e-16` | `4.03e-16` | `0.00e+00` |
| normalized L1 image error | `9.03e-4` | `6.81e-4` | `5.36e-4` |
| total-flux relative error | `1.30e-6` | `4.22e-5` | `4.81e-4` |
| second-moment relative error | `2.79e-5` | `8.60e-5` | `2.34e-4` |
| radial-profile L1 error | `8.35e-4` | `5.98e-4` | `5.12e-4` |
| colour-gradient error [mag] | `3.01e-4` | `2.08e-4` | `2.43e-4` |

The target-noise extension used 600 realizations and found:

- source-total mean relative bias: `6.86e-5`;
- total-image mean relative bias: `1.24e-4`;
- total-image variance relative error: `2.91e-2`;
- central source-pixel variance/mean: `0.9977`;
- adjacent source-pixel correlation: `-0.0179`;
- adjacent synthetic-background correlation: `-0.0227`.

These numbers are benchmark measurements, not public-package defaults or frozen acceptance tolerances.

## Comparison with the paper

The controlled experiment recovers the key FERENGI behavior relevant to this framework:

1. the redshifting/regridding/PSF operator does not introduce an appreciable extra systematic distortion when the source scene and SED are known;
2. the bandpass transformation is part of the forward observable, so no additional K-correction or Tolman factor is applied after direct target-band integration;
3. source Poisson noise is attached to the final detector-pixel expectation before insertion into the target background;
4. an already noisy real background is inserted once rather than independently re-noised.

The transfer errors above are much smaller than the structural-measurement scatter quoted by Barden et al. for their noisy GALFIT tests (their Table 3), which is consistent with their conclusion that regridding itself does not create an additional systematic trend. This comparison is used only as a scale check because the present benchmark does not use their original galaxies or GALFIT fitting configuration.

## Explained differences and limitations

This is deliberately a **synthetic-equivalent reproduction**, which is allowed by the project Gate-C protocol, rather than a rerun of the original SDSS → GEMS/STAGES/COSMOS dataset. The following differences are therefore explicit rather than hidden:

- analytic disk+bulge truth replaces the original SDSS galaxies;
- piecewise-linear spatial SED truth replaces `kcorrect` template fitting;
- Gaussian source/target PSFs replace the survey PSFs;
- direct image/profile/moment metrics replace the paper's GALFIT Sérsic-parameter comparison;
- the stochastic extension checks detector statistics separately from the deterministic transfer test;
- the real-background identity rule is stricter than reproducing FERENGI's acknowledged statistical approximation for galaxy+sky noise.

Because these differences isolate the forward operators instead of reproducing the historical survey products pixel-for-pixel, the correct review category is **PASS WITH EXPLAINED DIFFERENCE**, not an unqualified claim of data-level reproduction.

## Tolerance decision

No scientific threshold was relaxed during this review. The existing regression bounds remain explicitly broad sanity checks and are not promoted to production tolerances. Gate E remains responsible for freezing quantity-specific numerical acceptance policies after the remaining literature and real-survey gates are complete.

## Next action

C1 is scientifically closed at the synthetic-equivalent level. The next unclosed Gate-C item is **C2: the Paulino-Afonso / DOPTERIAN-style degradation benchmark**. The Zhuang & Shen public-table work already present on this branch is a useful partial C5 result, but it does not supersede C2 and is not yet a full C5 closure record.