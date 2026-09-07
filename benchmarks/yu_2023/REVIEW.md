# Gate C3 — Yu et al. (2023) resolvedness / morphology benchmark

**Status: COMPLETE — PASS WITH EXPLAINED DIFFERENCE.**

Primary reference: Yu, Cheng, Pan, Sun & Li (2023), *Redshifting galaxies from DESI to JWST CEERS: Correction of biases and uncertainties in quantifying morphology*, A&A 676, A74, arXiv:2307.04753.

This gate is a controlled synthetic-equivalent verification record, not a literal DESI-to-CEERS reproduction and not a source of production acceptance cuts.

## Frozen literature anchors

The benchmark freezes the paper's seven resolvedness levels exactly:

`R_p,true/FWHM = 1.98, 3, 4.55, 6.89, 10.45, 15.83, 24`.

It also freezes the paper's relevant definitions:

- `R_p`: local surface brightness equals 20% of the mean surface brightness inside `R_p`;
- curve-of-growth total aperture: `1.5 R_p`;
- `R20`, `R50`, `R80` from that curve of growth;
- `C = 5 log10(R80/R20)`;
- `A` measured inside `1.5 R_p`, with the center chosen by minimizing asymmetry;
- Yu et al. Eq. (28) asymmetry-noise correction with `f1 = 2.25`, `f2 = 2.1`;
- PSF-convolved single-Sérsic fitting with the literature-motivated `0.5 <= n <= 6` range.

The paper's `R_p/FWHM ~ 5` statement is retained only as a literature reference for their corrected asymmetry analysis. It is **not** interpreted as a universal morphology cut.

## Stage 1 — circular-PSF, noiseless resolvedness sweep

GitHub Actions run `33589966103` completed successfully.

Three predeclared synthetic scenes were used: an `n=1` Sérsic disk, an `n=4` concentrated Sérsic profile, and a disk plus a fixed off-center clump. Intrinsic profiles were detector-pixel integrated at 4x before a circular Gaussian PSF was applied. The PSF width was varied so that the seven frozen `R_p,true/FWHM` values were constructed exactly.

The noiseless results reproduce the important qualitative directions in Yu et al. without tuning the scenes to the paper. Poorer resolvedness broadens non-parametric radii and suppresses concentration, with stronger concentration suppression for the intrinsically concentrated scene. For the asymmetric disk+clump, poorer resolvedness suppresses real asymmetry. Correctly PSF-convolved same-model Sérsic fits remain very stable in the two pure-Sérsic scenes, while the one-Sérsic fit to the clumpy scene develops large structural shifts and reaches the declared `n=0.5` lower bound at the poorest resolvedness. That bound hit is retained as a model-mismatch/resolvedness observable; the bound was not widened.

At `R_p,true/FWHM=1.98`, the `n=1` scene has concentration bias about `-0.370`, the `n=4` scene about `-1.34`, and the clumpy scene changes from intrinsic `A ~ 0.324` to measured `A ~ 0.170` (`delta A ~ -0.154`). The symmetric scenes remain at numerical-zero asymmetry because a circular PSF cannot test the positive `A` contribution from JWST PSF asymmetry.

## Stage 2 — controlled target noise x resolvedness

The historical noisy Stage-2 record is preserved. A stale anchor-test/schema mismatch was fixed without changing any scientific definition, and a later numerical-support diagnostic showed that the inherited fixed radial ceiling `0.45 * min(image_shape)` could falsely terminate otherwise supported measurements.

The support-corrected Stage-2 workflow, run `33620940799`, completed successfully for all three declared integrated aperture S/N shards: `10`, `30`, and `100`. The correction changed radial numerical support only: the sampler extends to the center-dependent detector-edge clearance minus a 0.5-pixel interpolation margin. Scenes, noise realizations, seeds, Eq. (28), `f1/f2`, Sérsic bounds, optimizer settings, and winner rules were unchanged.

Across the three shards there are 189 predeclared scene/resolvedness/realization rows. The support-corrected morphology succeeded in 188/189 rows. The one retained failure is the asymmetric-clump scene at `S/N=100`, `R_p,true/FWHM=1.98`, realization 2, where the required `1.5 R_p` aperture still exceeds finite image support. It is retained rather than converted to a pass.

Noise behaves as an information-loss term rather than as a reason to alter fitting bounds. The median raw asymmetry noise offsets are approximately `+0.944`, `+0.765`, and `+0.492` for S/N `10`, `30`, and `100`. With Yu et al.'s Eq. (28) parameters they become approximately `+0.841`, `+0.257`, and `+0.091`. Thus the published correction reduces the noise contribution strongly at moderate/high S/N in this synthetic ensemble but does not remove it, and it is not uniformly superior to the Wen & Zheng parameter choice at the extreme S/N=10 diagnostic. No correction factor was retuned after seeing this result.

Parametric recovery also becomes progressively less stable toward lower S/N. The support-corrected shards contain 17 Sérsic-`n` bound hits in total (`10`, `4`, and `3` at S/N `10`, `30`, and `100`) and three `q` upper-bound hits, all at S/N=10. These are retained as identifiability observables.

## Stage 3 — real JWST/NIRCam PSF asymmetry

The first STPSF diagnostic failed before science metrics because the fixed 257-pixel stamp was insufficient for the largest constructed `R_p` and exact `1.5 R_p` measurement aperture. That failed run is preserved. The support correction was precomputed from the largest frozen resolvedness, the measured pinned STPSF FWHM, the exact `1.5 R_p` aperture, full sampled PSF half-width, and interpolation margin; no morphology tolerance or scientific bound was changed.

The corrected `gate-c-yu-2023-stpsf-asymmetry` workflow, run `33627936401`, completed successfully with all 21/21 scene/resolvedness rows and all center minimizations successful. It uses the pinned STPSF 2.2.0 JWST/NIRCam F444W `OVERDIST` PSF at NRCA5 detector position `(1024,1024)` and compares it with the same normalized kernel symmetrized under a 180-degree rotation about its measured flux centroid.

The measured sampled-pixel FWHM is `4.9167` for the original PSF and `4.9292` for the symmetrized control; the normalized kernel 180-degree asymmetry is `0.0763`. For the 14 intrinsically symmetric Sérsic rows, the original-minus-symmetrized PSF contribution to measured asymmetry is positive in **14/14** cases, with median `delta A = +0.00602` and range approximately `+0.000168` to `+0.01279`. This directly reproduces the qualitative sign of Yu et al.'s reported small positive asymmetry bias from PSF asymmetry, without tuning the PSF or scenes to the literature.

For the intrinsically asymmetric clumpy scene, smoothing remains the dominant effect and suppresses the intrinsic asymmetry at poor resolvedness; the odd PSF contribution is much smaller and can change sign. This is consistent with keeping PSF smoothing and PSF asymmetry as separately identifiable effects rather than combining them into one empirical correction.

## Review decision

**PASS WITH EXPLAINED DIFFERENCE.**

The gate passes as a synthetic-equivalent literature verification because it reproduces the central qualitative dependencies needed for the forward-modeling project: poorer resolvedness suppresses `C` and real `A`; same-model noiseless Sérsic parameters can remain robust; structural mismatch and low information produce real fit instability and bound solutions; target noise creates large residual morphology bias that Eq. (28) reduces but does not eliminate; and a realistic asymmetric JWST PSF produces a small positive `A` contribution for intrinsically symmetric galaxies.

The differences from Yu et al. are explicit rather than hidden. These experiments do not reproduce the DESI galaxy population, CEERS depth distribution, full empirical correction functions, or the paper's ensemble mean `delta n`/`delta q` values. The controlled S/N levels are not CEERS depth claims, and one finite-stamp morphology failure remains as an observable. Therefore no quantitative result from this gate is promoted to a universal production threshold.

Operationally, downstream work should retain `R_p/FWHM`, target S/N, fit convergence, parameter-bound hits, and asymmetry-correction validity as diagnostics. It should **not** impose `R_p/FWHM ~ 5` as a generic pass/fail cut.
