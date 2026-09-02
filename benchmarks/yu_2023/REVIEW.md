# Gate C3 — Yu et al. (2023) resolvedness / morphology benchmark

**Status: IN PROGRESS — literature anchors frozen; Stage 1 PSF-only/noiseless sweep completed successfully; Stage 2 controlled target-noise sweep implemented and awaiting CI.**

Primary reference: Yu, Cheng, Pan, Sun & Li (2023), *Redshifting galaxies from DESI to JWST CEERS: Correction of biases and uncertainties in quantifying morphology*, A&A 676, A74, arXiv:2307.04753.

## Why this benchmark is next

The Paulino-Afonso controlled C2 benchmark established that morphology recovery can become non-identifiable once extended-source information is lost, even when the radiometry, PSF transfer and detector sampling are numerically clean. Yu et al. provide a complementary way to parameterize that problem directly through source resolvedness relative to the PSF.

## Frozen literature anchors

The paper uses 1816 nearby DESI galaxies with `9.75 <= log10(M*/Msun) <= 11.25`, artificially places them over `0.75 <= z <= 3` in a CEERS/JWST observing context, and studies Petrosian radius `R_p`, half-light radius `R50`, asymmetry `A`, concentration `C`, axis ratio `q`, and Sérsic index `n`.

The controlled verification freezes the paper's seven resolution levels exactly:

`R_p,true/FWHM = 1.98, 3, 4.55, 6.89, 10.45, 15.83, 24`.

Other frozen definitions are:

- `R_p`: local surface brightness equals 20% of the mean surface brightness inside `R_p`;
- total-light curve of growth: `1.5 R_p`;
- `R20`, `R50`, `R80`: radii from that curve of growth;
- `C = 5 log10(R80/R20)`;
- `A`: measured within `1.5 R_p` with the center chosen by minimizing asymmetry;
- improved asymmetry-noise correction: Yu et al. Eq. (28), with `f1 = 2.25` and `f2 = 2.1`;
- parametric morphology: PSF-convolved single Sérsic, with approximately `0.5 <= n <= 6`.

Published qualitative trends frozen for verification are:

- non-parametric `R_p` and `R50` are slightly overestimated as PSF smoothing increases;
- model-fit `R50`, `q`, and Sérsic `n` are comparatively robust on average;
- for intrinsically symmetric galaxies, PSF asymmetry can cause a small positive asymmetry bias;
- for intrinsically asymmetric galaxies, PSF smoothing suppresses `A`, with stronger underestimation at poorer resolution and larger intrinsic asymmetry;
- concentration `C` is underestimated, especially for higher intrinsic concentration and poorer resolution;
- the reported mean offsets are approximately `delta n = -0.11` and `delta q = -0.005`;
- after the authors' correction procedure, `R_p/FWHM ~ 5` is a useful literature reference for asymmetry robustness.

None of these literature values is a production acceptance threshold. In particular, `R_p/FWHM ~ 5` is **not** a generic morphology cut.

## Anchor stage

Machine-readable definitions live in `verification/yu_2023.py` and are tested by `tests/test_yu_2023.py`. The anchor workflow completed successfully before Stage 1 was interpreted.

The module now also freezes the algebra of Yu et al. Eq. (28). This is the published asymmetry-noise estimator, not the paper's empirical resolvedness-correction functions.

## Stage 1 — PSF-only / noiseless resolvedness sweep

GitHub Actions run `33589966103` completed successfully.

The Stage-1 experiment is controlled synthetic-equivalent verification, not a literal DESI/CEERS reproduction. Three predeclared scenes were used:

1. single Sérsic disk: `n=1`, `Re=16 pix`, `q=0.65`;
2. single Sérsic concentrated profile: `n=4`, `Re=16 pix`, `q=0.80`;
3. disk plus a fixed off-center clump, fitted parametrically by one Sérsic to expose structural-model mismatch.

Intrinsic profiles are detector-pixel integrated at 4x. A circular Gaussian PSF is then varied to construct the seven `R_p,true/FWHM` values exactly. The circular PSF isolates smoothing; it deliberately does not attempt to reproduce JWST PSF asymmetry.

### Stage-1 scientific result

The PSF-only results reproduce the important *directions* expected from Yu et al. without tuning the scenes to the literature.

For the `n=1` disk, moving from `R_p,true/FWHM=24` to `1.98` changes the concentration bias from about `-0.006` to `-0.370`, while the same-model PSF-convolved Sérsic fit remains essentially unchanged (`delta n ~ -4.5e-5`, `delta q ~ +5.3e-5` at the poorest resolution).

For the `n=4` scene, concentration suppression is much stronger: the bias reaches about `-1.34` at `R_p,true/FWHM=1.98`. The same-model Sérsic fit is still numerically stable there (`delta n ~ -2.9e-4`, `delta q ~ +0.0015`) and has no structural bound hit.

For the intrinsically asymmetric disk+clump scene, asymmetry falls from approximately `0.324` intrinsically to `0.170` at `R_p,true/FWHM=1.98`, giving `delta A ~ -0.154`. Its one-Sérsic structural fit also changes strongly at poor resolution and reaches the declared lower Sérsic bound `n=0.5` in the poorest-resolution case. That bound hit is retained as a model-mismatch/resolvedness observable; the bound is not widened.

The two symmetric scenes keep `A` at numerical zero because the Stage-1 PSF is circular. Therefore Stage 1 cannot test the paper's small positive symmetric-galaxy `A` bias caused by PSF asymmetry.

These outcomes support the intended separation:

- PSF smoothing alone broadens non-parametric radii and suppresses concentration;
- PSF smoothing suppresses real asymmetric structure at poor resolvedness;
- correctly PSF-convolved same-model Sérsic `n` and `q` can remain very stable in noiseless data;
- structural mismatch can still produce large parametric changes and a bound solution.

No numerical acceptance band is inferred from these results.

## Stage 2 — controlled target noise x resolvedness

The next experiment adds noise **without changing the Stage-1 record**.

Noise is declared through integrated source S/N inside the PSF-only `1.5 R_p` aperture:

`S/N = 10, 30, 100`

with three deterministic realizations per scene and resolvedness value. These are controlled diagnostic levels, not CEERS depth claims and not acceptance thresholds.

For every noisy realization, the comparison reference is the PSF-only image at the same constructed `R_p,true/FWHM`. This makes the reported deltas specifically noise-induced rather than a mixture of PSF and noise effects.

The Stage-2 implementation measures:

- noisy `R_p`, `R20`, `R50`, `R80`, and `C`;
- raw minimized-center asymmetry;
- Eq. (28) asymmetry using Wen & Zheng (2016) values `f1=1`, `f2=sqrt(2)`;
- Eq. (28) asymmetry using Yu et al.'s published `f1=2.25`, `f2=2.1`;
- PSF-convolved single-Sérsic `Re`, `n`, and `q`;
- non-convergence, invalid noise-correction denominators, and all parameter-bound hits.

For the non-parametric Stage-2 diagnostic, ellipse `q` and PA are held to their PSF-only values so that target noise is not mixed with a separate noisy-moment shape estimator; the asymmetry center is still minimized independently in every noisy realization. Parametric `q` remains free.

Because a background-subtracted noisy curve of growth need not be monotonic, Stage 2 uses the first upward crossing of each required light fraction. The historical Stage-1 noiseless implementation is preserved unchanged.

No failure is converted into a pass, no parameter bounds are widened, and the published `f1/f2` values are not retuned on this synthetic ensemble.

## Review decision

**IN PROGRESS.** Stage 1 is an explicit successful CI result and has a physically consistent interpretation. A final PASS/PASS-WITH-EXPLAINED-DIFFERENCE/FAIL decision remains deferred until the controlled noise interaction and remaining PSF-asymmetry limitation are assessed.
