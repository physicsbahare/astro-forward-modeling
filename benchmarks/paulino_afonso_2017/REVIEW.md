# Gate C2 — Paulino-Afonso / DOPTERIAN-style degradation benchmark

**Status: IN PROGRESS — anchor/radiometric sub-gate implemented; image-level structural reproduction still required.**

Primary reference: Paulino-Afonso, Sobral, Buitrago & Afonso (2017), *The structural and size evolution of star-forming galaxies over the last 11 Gyr*, MNRAS 465, 2717, arXiv:1611.05039.

## Exact literature targets

This benchmark is anchored to:

- Section 3 and Figure 2: artificial-redshifting operator sequence;
- Section 5.1 and Figures 4–5: recovery of effective radius and Sérsic index after degradation;
- Table 2: median recovered/input ratios for `r_e` and `n` at z = 0.40, 0.84, 1.47 and 2.23;
- Appendix B: separation of the imposed luminosity evolution from observational degradation.

The paper adopts `H0 = 70 km s^-1 Mpc^-1`, `Omega_m = 0.3`, `Omega_Lambda = 0.7`.  The high-redshift HST images use a typical F814W PSF FWHM of about 0.09 arcsec and 0.03 arcsec/pixel; the local SDSS g-band images have median PSF FWHM about 1.3 arcsec and 0.396 arcsec/pixel.

## Published operator map

The Section-3 procedure is represented as:

1. angular re-scaling while preserving total flux at the rebinning step and physical galaxy size;
2. flux correction from luminosity distance plus a separate intrinsic luminosity-evolution factor;
3. source-to-target PSF transformation following the FERENGI prescription;
4. convolution and insertion into a blank region of the target survey.

The luminosity evolution used for the H-alpha-selected population follows

`log10 L*(z) = 0.45 z + 41.87`,

and is kept explicitly separate from cosmological dimming in this verification harness.

## Radiometric equivalence sub-gate

`verification/paulino_afonso_2017.py` independently checks that, for unchanged physical size and matched rest-frame observable,

`(D_L,s / D_L,t)^2 / (Omega_t / Omega_s)`

with `Omega_t/Omega_s = (D_A,s/D_A,t)^2` is numerically identical to

`[(1+z_s)/(1+z_t)]^4`.

This demonstrates that the distance-based image-redshifting convention and the Tolman surface-brightness convention are two forms of the same final observable when definitions are matched.  The luminosity-evolution multiplier is applied only after this identity and is never hidden inside the cosmological factor.

The equality tolerance in the test is purely a floating-point consistency tolerance for an exact distance-duality identity; it is not a morphology acceptance threshold.

## Published structural anchors

Table 2 reports average median recovered/input ratios:

| target z | `r_e,recovered / r_e,input` | `n_recovered / n_input` |
| ---: | ---: | ---: |
| 0.40 | 1.007 | 0.815 |
| 0.84 | 1.033 | 0.820 |
| 1.47 | 0.997 | 0.831 |
| 2.23 | 1.002 | 0.837 |

Thus the average effective-radius recovery stays within 3.3% of unity in the published table, while the average Sérsic-index recovery is systematically low by 16.3–18.5%.  Across the four individual local samples in Table 2, every tabulated median Sérsic-index ratio is below unity.  Figures 4–5 further show that effective radii below about 10 kpc are generally recovered within about 10%, whereas Sérsic indices are biased low, with larger degradation for larger input `n`.

These numbers are literature reproduction targets only. They are **not** generic correction factors and are **not** production tolerances.

## Executable and machine-readable outputs

Current executable:

`python scripts/run_paulino_afonso_2017_anchor_benchmark.py`

Current tests:

`pytest -q tests/test_paulino_afonso_2017.py`

Outputs:

- `benchmark_output/paulino_afonso_2017/radiometric_equivalence.csv`
- `benchmark_output/paulino_afonso_2017/published_table2.csv`
- `benchmark_output/paulino_afonso_2017/summary.json`

## What is not yet reproduced

This C2 gate is **not closed**.  The remaining scientific step is an image-level degradation/recovery experiment that includes, as closely as public information permits:

- controlled Sérsic or survey-like truth scenes;
- angular rebinning;
- the paper-matched cosmological dimming and separately controlled luminosity-evolution modes;
- source-to-target PSF transformation;
- Poisson noise plus real-background insertion semantics;
- a 2-D structural fitting backend with explicit PSF treatment;
- recovery of `r_e` and `n` across the four target redshifts;
- comparison of the recovered bias direction and scale with Figures 4–5 and Table 2.

A synthetic-equivalent experiment must not be described as a literal reproduction of the original CALIFA/SAMI/MaNGA/NYU-VAGC image samples.  If the recovered structural bias differs from the published 16–20% Sérsic under-recovery, the discrepancy must be diagnosed through S/N, fitting backend, sky treatment, PSF, sampling, source population and selection before any pass decision is made.

## Current review decision

**IN PROGRESS.**

The radiometric convention is verified and the quantitative literature targets are frozen without changing any existing scientific tolerance.  A final `PASS`, `PASS WITH EXPLAINED DIFFERENCE`, or `FAIL` decision is deferred until the image-level structural-degradation experiment is complete.
