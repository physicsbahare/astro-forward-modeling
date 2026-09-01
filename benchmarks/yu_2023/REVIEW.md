# Gate C3 — Yu et al. (2023) resolvedness / morphology benchmark

**Status: IN PROGRESS — literature anchors frozen; controlled resolvedness experiment not yet run.**

Primary reference: Yu, Cheng, Pan, Sun & Li (2023), *Redshifting galaxies from DESI to JWST CEERS: Correction of biases and uncertainties in quantifying morphology*, A&A 676, A74, arXiv:2307.04753.

## Why this benchmark is next

The Paulino-Afonso controlled C2 benchmark established that morphology recovery can become non-identifiable once extended-source information is lost, even when the radiometry, PSF transfer and detector sampling are numerically clean. Yu et al. provide a complementary way to parameterize that problem directly through the source's resolvedness relative to the PSF.

## Frozen literature anchors

The paper uses 1816 nearby DESI galaxies with `9.75 <= log10(M*/Msun) <= 11.25`, artificially places them over `0.75 <= z <= 3` in a CEERS/JWST observing context, and studies Petrosian radius `R_p`, half-light radius `R50`, asymmetry `A`, concentration `C`, axis ratio `q`, and Sérsic index `n`.

The central resolution variable is

`resolution level = R_p / FWHM`,

where `R_p` and the PSF FWHM must be expressed in the same unit.

Published qualitative trends frozen for verification are:

- non-parametric `R_p` and `R50` are slightly overestimated as PSF smoothing increases;
- model-fit `R50`, `q`, and Sérsic `n` do not show significant bias in the authors' experiments;
- for intrinsically symmetric galaxies, PSF asymmetry can cause a small positive asymmetry bias;
- for intrinsically asymmetric galaxies, PSF smoothing suppresses `A`, with stronger underestimation at poorer resolution and larger intrinsic asymmetry;
- concentration `C` is underestimated, especially for higher intrinsic concentration and poorer resolution;
- after the authors' correction procedure, asymmetry is described as robust only for angularly large galaxies with approximately `R_p/FWHM >= 5`.

The `R_p/FWHM >= 5` statement is a **literature anchor for asymmetry in this paper**, not a generic morphology cut and not a production acceptance threshold.

## Implemented anchor stage

Machine-readable definitions live in `verification/yu_2023.py` and are tested by `tests/test_yu_2023.py`. The script

`python scripts/run_yu_2023_anchor_benchmark.py`

writes `benchmark_output/yu_2023/anchor.json` containing the frozen source/reference metadata, qualitative bias directions and exact `R_p/FWHM` definition checks.

No empirical correction function from the paper has yet been implemented.

## Next controlled experiment

The next sub-gate will vary **resolvedness itself**, not redshift as a proxy, on a common synthetic scene family. It should keep total source structure fixed while changing PSF width and/or apparent scale so that `R_p/FWHM` is known by construction. At minimum it must measure:

1. a Petrosian-like radius and non-parametric half-light radius;
2. concentration and rotational asymmetry with an explicit background/noise correction convention;
3. a PSF-convolved Sérsic fit returning `R50`, `q`, and `n`;
4. the sign and scale of bias as a continuous function of `R_p/FWHM`.

The experiment must separate PSF smoothing from target noise before combining them. It must not tune a resolvedness threshold to force agreement with the paper, and it must not treat `R_p/FWHM = 5` as a universal pass/fail criterion.

## Review decision

**IN PROGRESS.** The literature anchors are frozen. A PASS/PASS-WITH-EXPLAINED-DIFFERENCE/FAIL decision is deferred until the controlled resolvedness sweep is run and compared with the published bias directions.