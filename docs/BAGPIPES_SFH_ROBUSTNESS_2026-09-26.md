# BAGPIPES backward-luminosity / SFH robustness experiment - 2026-09-26

## Purpose

This experiment asked whether the GOLD91 passive-disk subsample can support a physically motivated, object-specific luminosity-evolution factor for moving each observed galaxy backward to z=3.

The intended factor was:

`g_BAG = L_rest(z=3) / L_rest(z_source)`.

measured in the same intrinsic rest-frame band sampled by F444W at z=3. If this factor were robust, it could in principle define an object-specific EBAG artificial-redshifting branch.

The test showed that the backward luminosity factor is strongly SFH-model dependent even when the observed-epoch SED is fitted comparably well. The project therefore does **not** adopt a per-object BAGPIPES luminosity correction for the GOLD91/GOLD403 imaging experiment.

## Starting sample and pilot logic

The narrow population bin was fixed before the BAGPIPES experiment:

- 0.75 <= z < 1.00
- N = 91
- selected from the final GOLD403 catalog by the predeclared redshift-bin rule

The first pilot used three representative objects. One object, 727233, was already poorly fit by the catalog LePHARE solution and was not used for the final SFH-family robustness test.

The robustness test therefore used the two clean pilot objects:

| source_id | z | logM |
|---:|---:|---:|
| 487469 | 0.8674 | 9.60136 |
| 756229 | 0.8781 | 9.85000 |

## Photometric fitting setup that was retained

The final two-object robustness test held the photometric setup fixed and changed only the SFH family.

- COSMOS2025 SE++ model fluxes
- calibrated model-flux uncertainties
- fixed catalog redshift
- HSC g/r/i/z/y
- UltraVISTA Y/J/H/Ks
- JWST/NIRCam F115W/F150W/F277W/F444W
- IRAC ch1/ch2 excluded
- maximum S/N = 20, implemented as a minimum 5% fractional flux uncertainty
- Calzetti dust attenuation
- no nebular component
- broad formed-mass and metallicity priors
- Nautilus nested sampler in the dedicated `bagpipes` Python 3.11 environment

IRAC was removed because it was among the strongest residual contributors in the initial pilot and is not required for the controlled no-IRAC comparison.

### Why the error floor was introduced

With the raw calibrated errors, the initial DPL fits were formally very poor:

- 487469: best reduced chi2 about 10.87
- 756229: best reduced chi2 about 39.59

Applying the S/N cap reduced these to about 3.28 and 2.57. Removing IRAC while retaining the same floor reduced them further to about 2.36 and 2.14. The final SFH-family experiment therefore used this no-IRAC, S/N-capped setup for every model.

The error floor is a likelihood-stability choice, not evidence that the catalog errors are globally wrong by one fixed factor.

## SFH models compared

Three BAGPIPES SFH families were tested:

1. `dblplaw`: double-power-law SFH
2. `delayed`: delayed-tau SFH
3. `continuity`: Leja-style non-parametric continuity SFH

For the continuity model, a bin boundary was placed at the lookback time from each source redshift to z=3. This prevents the z=3 epoch from being hidden inside one very broad ancient-time bin.

The observed photometry, redshift, filter set, S/N floor, dust treatment, and luminosity-factor calculation were otherwise held fixed.

## Observed-epoch fit quality

Exact saved receipt: `data/validation/bagpipes_sfh_robustness_2026-09-26/SFH_model_fit_quality.csv`.

| source_id | SFH | Nband | Npar | chi2_best | reduced chi2 | AIC | BIC | lnZ |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 487469 | continuity | 13 | 9 | 16.5687 | 4.1422 | 34.5687 | 39.6532 | 561.9047 |
| 487469 | dblplaw | 13 | 6 | 16.5567 | 2.3652 | 28.5567 | 31.9464 | 562.8009 |
| 487469 | delayed | 13 | 5 | 17.0043 | 2.1255 | 27.0043 | 29.8291 | 563.6998 |
| 756229 | continuity | 13 | 9 | 15.4011 | 3.8503 | 33.4011 | 38.4857 | 549.2694 |
| 756229 | dblplaw | 13 | 6 | 14.9833 | 2.1405 | 26.9833 | 30.3730 | 549.4024 |
| 756229 | delayed | 13 | 5 | 16.7374 | 2.0922 | 26.7374 | 29.5622 | 550.0440 |

The raw best chi2 values are similar across the three SFH families. Complexity-penalized statistics mildly prefer the simpler models, but the observed-epoch photometry does not constrain the early SFH tightly enough to make the z=3 extrapolation unique.

## Definition of the BAGPIPES luminosity factor

For each posterior draw:

1. reconstruct the fitted source-epoch SFH;
2. truncate the SFH at the cosmic time corresponding to z=3, removing stars that had not formed yet;
3. construct dust-free stellar populations at the source epoch and z=3;
4. use one common rest-frame filter made by shifting the real F444W throughput to its z=3 rest frame;
5. evaluate both populations at redshift=0 in BAGPIPES so luminosity distance and observer-frame K/projection terms do not enter;
6. take the direct intrinsic luminosity ratio.

Thus BAGPIPES was used only to estimate an intrinsic stellar-population factor. The artificial-redshifting production code already handles cosmological distance/redshift projection, so those terms must not be counted again.

A posterior draw with no stars formed by z=3 is recorded as `NO_STELLAR_HISTORY_AT_Z3`. It must not be converted into a fake tiny image and interpreted as a measured luminosity.

## Final SFH-family luminosity results

Exact saved receipt: `data/validation/bagpipes_sfh_robustness_2026-09-26/SFH_model_gbag_summary.csv`.

### ID 487469

| SFH | valid draws | no-z3-progenitor fraction | g16 | g50 | g84 | formed-mass fraction at z3, median |
|---|---:|---:|---:|---:|---:|---:|
| dblplaw | 160/160 | 0.000 | 8.06e-5 | 0.8306 | 1.2483 | 0.2572 |
| delayed | 12/160 | 0.925 | 1.4611 | 3.1725 | 3.9348 | 0.5168, conditional on valid draws |
| continuity | 160/160 | 0.000 | 0.4735 | 0.9179 | 1.6479 | 0.3392 |

The delayed-tau median must **not** be read as an unconditional prediction of g=3.17. In 92.5% of delayed-tau posterior draws, the model says the galaxy had not begun forming stars by z=3. The quoted delayed-tau g distribution is conditional on the 12/160 draws that do contain a z=3 stellar population.

### ID 756229

| SFH | valid draws | no-z3-progenitor fraction | g16 | g50 | g84 | formed-mass fraction at z3, median |
|---|---:|---:|---:|---:|---:|---:|
| dblplaw | 160/160 | 0.000 | 7.93e-10 | 0.08671 | 0.7066 | 0.02910 |
| delayed | 0/160 | 1.000 | undefined | undefined | undefined | undefined |
| continuity | 160/160 | 0.000 | 0.1923 | 0.4550 | 0.8481 | 0.2104 |

For this object the DPL and continuity medians differ by a factor of 5.25 even though their observed-epoch best chi2 values differ by less than 0.5.

## Cross-model robustness result

Exact saved receipt: `data/validation/bagpipes_sfh_robustness_2026-09-26/SFH_model_robustness_summary.csv`.

- 487469: positive model medians span a factor 3.82 (0.582 dex), but this statistic hides the more important fact that delayed-tau has a 92.5% no-progenitor probability.
- 756229: positive model medians span a factor 5.25 (0.720 dex), and delayed-tau has a 100% no-progenitor probability.
- Individual DPL posterior intervals can extend over many orders of magnitude because the broadband data permit extremely small early stellar populations.

Therefore a single per-galaxy backwards luminosity correction is not identifiable from these broadband data without strong dependence on the assumed SFH family/prior.

## Comparison with E1J

The frozen E1J branch is a separate controlled sensitivity prescription:

`g_E1J = [(1 + z_target) / (1 + z_source)]^eta`, with `eta = 1.02` and `z_target = 3`.

For the two BAGPIPES robustness objects:

- 487469: g_E1J = 2.1749, Delta m = -0.8436 mag
- 756229: g_E1J = 2.1623, Delta m = -0.8373 mag

E1J is applied only as an F444W luminosity-amplitude sensitivity branch. It does not change the structural model, angular-size scaling, PSF, context, masks, or recovery method.

E1J is **not** a BAGPIPES posterior, not a per-galaxy progenitor history, and not a full wavelength-dependent stellar-population model.

## Why retain E1J after the BAGPIPES test?

E0 is the primary experiment and sets intrinsic luminosity evolution to unity. It answers the clean transfer-function question: what happens to the same structural system when it is moved to z=3 and observed with the target PSF, sampling, background, crowding, and recovery pipeline?

However, real high-redshift stellar populations may be intrinsically brighter than a no-evolution copy. If only E0 is reported, a morphology failure in the real-background stage can be sensitive to the assumed source brightness as well as to resolution/background effects.

E1J therefore acts as a controlled brightness perturbation. Comparing E1J with E0 tests whether conclusions change when the same z=3 structural model is made about 0.84 mag brighter for a typical z~0.87 source.

Interpretation:

- E0 vs native-clean/z3-clean isolates structural/redshift/resolution effects.
- E1J vs E0 in the same real context tests sensitivity to intrinsic brightness/S/N.
- If E0 and E1J give similar morphology/classification outcomes, the conclusion is robust to this brightening assumption.
- If E1J recovers disks substantially better than E0, part of the E0 loss is detectability/S/N dependent rather than purely structural resolution loss.

E1J is not required to make the E0 baseline valid. It is retained because luminosity evolution is uncertain and the sensitivity of the final morphology conclusion to that uncertainty should be quantified transparently.

The failed robustness of object-specific BAGPIPES backwards evolution makes this controlled sensitivity framing more defensible than assigning each galaxy one apparently physical EBAG scalar.

## Frozen project decision from this experiment

1. **E0 remains the primary artificial-redshifting branch.**
2. **E1J remains a population-level / controlled F444W brightening sensitivity branch.**
3. Do **not** call E1J an individual evolutionary history.
4. Do **not** launch a 91-object BAGPIPES/EBAG imaging branch from the current broadband data.
5. Do **not** use DPL, delayed-tau, or continuity medians as unique physical corrections for individual galaxies.
6. Preserve no-z3-progenitor posterior states as model outcomes, not as zero-flux measurements.
7. Revisit object-specific backward evolution only if substantially stronger SFH constraints become available, for example spectroscopy or a deliberately justified stronger prior model.
8. The BAGPIPES test does not invalidate E0 or the already validated morphology renderer/recovery chain. It addresses a different question: whether intrinsic luminosity evolution can be inferred object by object.

## Files preserved with this receipt

The repository preserves both the compact decision-driving summaries and the detailed reproducibility products:

- `data/validation/bagpipes_sfh_robustness_2026-09-26/SFH_model_fit_quality.csv`
- `data/validation/bagpipes_sfh_robustness_2026-09-26/SFH_model_gbag_draws.csv`
- `data/validation/bagpipes_sfh_robustness_2026-09-26/SFH_model_gbag_summary.csv`
- `data/validation/bagpipes_sfh_robustness_2026-09-26/SFH_model_robustness_summary.csv`
- `tutorials/GOLD91_BAGPIPES_SFH_model_robustness_2gal.ipynb`

The per-draw table is retained so the conditional delayed-tau results and no-progenitor states can be re-audited rather than reconstructed from summary statistics alone.

## Relationship to the production experiment

The causal chain remains:

`published -> native-clean -> z3-clean -> z3-real-background`

The BAGPIPES experiment does not alter that chain.

For production interpretation:

- use native-clean -> z3-clean for pure redshift/resolution bias;
- use z3-clean -> z3-real for additional background/crowding/recovery degradation;
- compare E0 and E1J only as luminosity-sensitivity branches;
- never reinterpret E1J as a validated stellar-population reconstruction.
