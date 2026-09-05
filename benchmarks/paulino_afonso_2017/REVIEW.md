# Gate C2 — Paulino-Afonso / DOPTERIAN-style degradation benchmark

**Review decision: PASS WITH EXPLAINED DIFFERENCE for the controlled synthetic-equivalent benchmark.**

This decision does **not** claim a literal reproduction of the original CALIFA/SAMI/MaNGA/NYU-VAGC images, COSMOS/ACS backgrounds, GALFIT implementation, or Table-2 correction factors. It closes the controlled verification case because the redshifting operator, radiometry, PSF feasibility, detector sampling, noiseless morphology floor, structural-model mismatch, and target-noise identifiability have now been exercised without loosening scientific bounds or tuning the experiment to the published answer.

Primary reference: Paulino-Afonso, Sobral, Buitrago & Afonso (2017), *The structural and size evolution of star-forming galaxies over the last 11 Gyr*, MNRAS 465, 2717, arXiv:1611.05039.

## Frozen literature anchors

The benchmark remains anchored to Section 3 and Figure 2 (artificial-redshifting sequence), Figures 4–5 (size and Sérsic-index recovery), Table 2 (median recovered/input ratios), and Appendix B (magnitude, axial ratio, and magnitude-dependent structural effects).

Published average Table-2 ratios are:

| target z | `r_e,recovered / r_e,input` | `n_recovered / n_input` |
| ---: | ---: | ---: |
| 0.40 | 1.007 | 0.815 |
| 0.84 | 1.033 | 0.820 |
| 1.47 | 0.997 | 0.831 |
| 2.23 | 1.002 | 0.837 |

These values are literature comparison anchors, not production correction factors and not acceptance tolerances.

The paper's operator sequence is represented as angular rescaling at fixed physical size, luminosity-distance flux scaling plus a separately applied H-alpha luminosity-evolution term, source-to-target PSF transformation, convolution, and insertion into an empty region of the target survey. The harness deliberately does not apply an additional `(1+z)^-4` multiplier after distance and angular-area transformations, because that would double-count the same cosmological surface-brightness effect.

## Numerical history and resolved blockers

The original high-`n` problem was first diagnosed as an optimizer-basin/conditioning issue. A multistart, 3-point-Jacobian trust-region fit demonstrated that exact same-model noiseless Sérsic truth can be recovered essentially at the numerical floor. That removed optimizer failure as the primary blocker.

A later detector-sampling audit exposed a second, more important issue: the historical fitter evaluated a continuous Sérsic profile at detector pixel centres while the transfer/direct-target truth renderers integrated the profile over detector pixels. Compact high-`n` profiles can be catastrophically misrepresented by point-centre sampling when the Sérsic cusp lands on a pixel centre. This was kept as a historical diagnostic rather than silently rewriting previous benchmark output.

The transfer path also contained a sub-pixel phase/centering error caused by asymmetric trimming of a fine grid before block summation. A detector-centred subpixel integration diagnostic removed the phase offset; after the correction the transferred/direct-target centroid difference is numerically negligible and radiometric differences remain at the sub-percent level.

No morphology bound, optimizer tolerance, or acceptance criterion was widened to obtain these results.

## Pixel-integrated structural fitter

A separate 4x detector-pixel-integrated fitter was then introduced solely as a verification comparison. It retains the established physical bounds, multistart semantics, 3-point finite-difference Jacobian, `x_scale='jac'`, and lowest-residual-cost winner rule.

On the complete 20-image noiseless single-Sérsic full-chain set (5 pre-declared profiles x 4 target redshifts), GitHub Actions run `33528679081` completed successfully for all four shards. The aggregate result is:

- 20/20 lowest-cost fits formally successful;
- zero `r_e` or `n` bound hits;
- median `r_e,recovered/r_e,input = 1.000096`;
- median `n_recovered/n_input = 1.002192`;
- maximum absolute `r_e` ratio departure from unity = 0.047203;
- maximum absolute `n` ratio departure from unity = 0.039082;
- maximum centroid error = `2.3e-13` target pixels.

This establishes that the large historical noiseless high-`n` offset was a fitter-rendering/sampling floor, not an astrophysical degradation signal.

The dedicated concentrated-`n=4` pixel-integrated structural-fitter run `33528679456` also completed successfully at all four target redshifts and independently supports the same conclusion.

## Target-noise identifiability result

The next experiment added only the already declared ACS-like white-Gaussian target noise (AB 27.2 at 5 sigma point-source depth), reused the deterministic seeds, and retained the same physical fitting bounds. GitHub Actions run `33528680153` completed successfully for all 12 matrix shards, producing 60 lowest-cost fits (5 cases x 4 redshifts x 3 noise realizations).

Aggregate pixel-integrated noisy result:

- 60/60 lowest-cost fits formally report optimizer success;
- 31/60 (51.7%) hit at least one `r_e` or `n` bound;
- `n` lower-bound hits: 25/60;
- `n` upper-bound hits: 1/60;
- `r_e` upper-bound hits: 6/60;
- centroid error >= 2 pixels: 43/60;
- `q <= 0.151`: 12/60; `q >= 0.999`: 15/60;
- overall median `r_e` ratio = 0.92694;
- overall median `n` ratio = 0.20351.

Every noisy image has all eight multistart solutions within 1% of the lowest residual cost; the largest within-image start-to-start cost spread is only about 0.061%. This is a direct signature of a shallow/noise-dominated objective rather than a well-identified morphology solution.

The median known-template extended-source S/N decreases strongly with target redshift:

| target z | median known-template S/N | median `r_e` ratio | median `n` ratio |
| ---: | ---: | ---: | ---: |
| 0.40 | 5.520 | 1.032 | 0.464 |
| 0.84 | 2.026 | 0.694 | 1.490 |
| 1.47 | 1.075 | 0.946 | 0.200 |
| 2.23 | 0.830 | 0.896 | 0.200 |

The noisy pixel-integrated and historical point-sampled fitters produce nearly the same ensemble behaviour: the median absolute row-by-row change is only 0.00242 in `r_e` ratio and 0.00126 in `n` ratio, while both have 31/60 structural-bound cases and 43/60 centroid excursions >=2 pixels. Individual very-low-S/N realizations can jump between radically different structural solutions with residual-cost changes of only order `1e-5` fractionally. Therefore the remaining noisy instability is classified as information/identifiability loss, not as evidence that bounds should be widened.

## Structural-model mismatch

The separate co-centred bulge+disk truth experiment deliberately fits one Sérsic component to a two-component source. Its noiseless and noisy matrix workflows now complete across all redshift shards (`33528679730` and `33528679721`). Boundary solutions and noise-realization dependence are retained as observables. These tests demonstrate that even when the image-transfer operator is numerically clean, a one-Sérsic summary of a composite source can move substantially as PSF, depth, and recoverable surface-brightness structure change.

## Why the controlled noisy medians do not reproduce Table 2

The difference from the published Table-2 scale is expected and is not tuned away. The controlled ensemble is deliberately small, uses synthetic single-Sérsic truth, Gaussian PSF approximations and white Gaussian noise, and retains every low-information fit. In contrast, Paulino-Afonso et al. redshift real local galaxies, insert them into real target-survey backgrounds, use GALFIT with survey PSFs and SExtractor initialisation/masking, and explicitly exclude irregular/complex or low-S/N sources for which meaningful GALFIT structural measurements do not converge. The paper reports that this exclusion affects roughly 8–40% of the analysed samples. It also states that the imposed luminosity evolution is important because it counterbalances cosmological dimming and keeps the artificial sample close in brightness to the observed high-redshift population.

Our highest-redshift controlled cases have median extended-source information below unity even though their point-source-equivalent S/N can look acceptable. They therefore probe a more information-starved regime than the population that contributes clean structural measurements to the paper's reported medians. The controlled result should consequently not be converted into, or compared as if it were, the paper's empirical correction table.

## Review decision

**PASS WITH EXPLAINED DIFFERENCE — controlled synthetic-equivalent reproduction.**

What is verified:

1. the cosmological/radiometric convention and separate luminosity evolution;
2. pure-convolution PSF feasibility for the CALIFA-like path;
3. detector-pixel integration and centering semantics;
4. a clean noiseless structural floor with a pixel-integrated fitter;
5. survival of strong morphology instability only after target noise removes extended-source information;
6. structural-model-mismatch behaviour for composite bulge+disk sources;
7. the qualitative literature lesson that observational degradation can suppress/alter measurable structure and that Sérsic `n` is less stable than total flux or modest sizes.

What is **not** claimed:

- literal reproduction of the original survey images or GALFIT pipeline;
- reproduction of the exact Table-2 numerical correction factors;
- a universal S/N threshold for valid morphology;
- permission to widen bounds or discard inconvenient fits after seeing the answer.

The Table-2 discrepancy is therefore an explained method/sample difference rather than a failed numerical gate. Survey-realistic injection, correlated backgrounds, empirical JWST/HST PSFs and the eventual production measurement pipeline remain separate Gate-D tasks.