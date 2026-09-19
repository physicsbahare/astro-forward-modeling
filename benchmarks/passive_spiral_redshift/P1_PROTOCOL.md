# Passive Spiral P1 — spiral-feature survival under controlled artificial redshifting

## Purpose

Test a failure mode that is not isolated by the existing FERENGI, Paulino-Afonso, or Yu benchmarks: **a galaxy can remain globally disk-like while its spiral-arm signal is suppressed by the redshift/PSF/pixel operator and become observationally closer to a smooth disk**.

This is directly relevant to passive-spiral selection, where a low Sérsic index or disk-like bulge fraction is not by itself evidence that spiral structure remains detectable. The experiment is a verification-harness diagnostic only. It is not a production classifier and it does not define a universal spiral-detection threshold.

## Literature motivation frozen before execution

- Barden, Jahnke & Häußler (2008; FERENGI) establish the artificial-redshifting operator family and the need to separate the transfer operator from downstream morphology measurement.
- Yu et al. (2023) show that redshifting/resolvedness can suppress morphology information before total flux is lost and that no single resolvedness cut is universal.
- Kuhn et al. (2024, arXiv:2312.12389) explicitly use artificially redshifted low-redshift galaxies to assess observational bias in JWST spiral fractions.
- Recent JWST work continues to recover spiral structure at `z > 1`, so the relevant question is not whether spirals can ever be seen, but how much a controlled spiral-feature statistic is altered by the observation operator.

The implementation uses SciPy's maintained `RegularGridInterpolator` for explicit grid transfer and `scipy.ndimage.gaussian_filter` for a declared Gaussian convolution. The Gaussian kernel is a controlled PSF surrogate, not a claim about the literal COSMOS-Web effective PSF.

## Frozen scene

Two co-grid analytic scenes are used.

1. **Spiral scene**
   - exponential disk scale length: `4.0 kpc`;
   - compact circular Gaussian bulge scale: `0.9 kpc` with fixed central amplitude `0.5` relative to the disk normalization;
   - two-armed logarithmic perturbation;
   - pitch angle: `22 deg`;
   - arm modulation amplitude: `0.38`;
   - arm modulation is smoothly tapered at the centre and outer edge.
2. **Smooth control**
   - identical exponential disk + bulge radial profile;
   - arm modulation amplitude exactly zero.

There is no intrinsic size evolution, luminosity evolution, clump evolution, dust evolution, or stellar-population evolution.

## Frozen observation geometry

- source redshift: `z_s = 0.10`;
- target redshifts: `z_t = 0.50, 1.00, 2.00, 3.00`;
- source pixel scale: `0.03 arcsec/pixel`;
- source Gaussian PSF FWHM: `0.05 arcsec`;
- target pixel scale: `0.03 arcsec/pixel`;
- target Gaussian PSF FWHM: `0.145 arcsec`;
- physical scene half-extent: `15 kpc`;
- cosmology: the existing independent `FlatLCDMReference(H0=70, Om0=0.3)`.

The target PSF must be broader than the redshifted-equivalent source PSF. If not, the case fails rather than invoking a sharpening/deconvolution kernel.

## Radiometric convention

This P1 scene is a single fixed rest-frame **band-integrated surface-brightness** field. Therefore the observation-only surface-brightness transformation is

`I_target / I_source = ((1 + z_s) / (1 + z_t))^4`.

That factor is applied exactly once. No additional Tolman multiplier, K-correction, luminosity evolution, or source-shot/sky noise is allowed in P1.

This is deliberately separate from the `I_lambda` convention used in the multiband FERENGI benchmark; the two conventions must not be mixed.

## Transfer and direct-target paths

For each target redshift and each scene:

1. render the source scene on the source physical grid;
2. apply source Tolman dimming once;
3. convolve with the source Gaussian PSF;
4. resample the source observation onto the target physical grid;
5. apply only the source-to-target `(1+z)^-4` surface-brightness ratio;
6. degrade from the redshifted-equivalent source PSF to the declared target PSF using a positive Gaussian matching kernel;
7. independently render the same latent physical scene directly on the target grid, apply target Tolman dimming once, and convolve with the target PSF.

The artificial-redshift path is compared with this direct-target control. Agreement is an identifiability/numerical control, not independent cross-code validation.

## Frozen spiral statistic

Measure a matched logarithmic-spiral complex amplitude in the physical annulus `2.5 <= r < 9.0 kpc`:

`A_sp = |sum I exp[-i phi_spiral]| / sum I`,

where `phi_spiral` uses the same frozen `m=2` and `22 deg` pitch geometry as the latent scene.

Record, without thresholding:

- latent/source-free `A_sp`;
- direct-target `A_sp`;
- artificially redshifted `A_sp`;
- smooth-control `A_sp` on both paths;
- arm-retention ratio `A_sp,direct / A_sp,latent`;
- artificial/direct arm-amplitude ratio;
- absolute artificial-minus-direct arm-amplitude difference;
- normalized image L1 difference;
- total-flux relative difference;
- target physical PSF FWHM in kpc;
- redshifted-equivalent source PSF and positive matching-kernel FWHM.

## Interpretation policy

No post-hoc threshold for "spiral detected" is permitted. P1 asks only:

1. whether the artificial-redshift operator reproduces the direct-target spiral statistic without a hidden extra dimming or sharpening step;
2. how much the target observation operator suppresses the known latent spiral feature even in the absence of noise;
3. whether the smooth control develops a spurious matched-arm signal from numerical transfer alone.

A workflow that completes successfully is only software success. The numerical trend is interpreted in a separate immutable result receipt.

## Explicit exclusions

P1 does **not** include target noise, real COSMOS-Web backgrounds, source-shot noise, empirical/STPSF kernels, segmentation, visual classification, ML classification, Sérsic fitting, B/T recovery, or a passive-galaxy SED. Those are separate questions and must not be silently folded into this run.

No historical benchmark result is overwritten.
