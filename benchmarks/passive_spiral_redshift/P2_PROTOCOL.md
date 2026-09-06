# Passive Spiral P2 — real COSMOS-Web context arm-recovery stress test

Status: **PROTOCOL FROZEN BEFORE P2 OUTPUT INSPECTION**

## Purpose

P1 isolated resolution/operator suppression of a known two-armed spiral feature in a noiseless controlled scene. P2 adds the next non-redundant failure mode: **the same known spiral morphology placed into literal COSMOS-Web DR1 F444W mosaic context can acquire biased or unstable arm measurements because of real background structure, crowding, correlated survey residuals, and finite S/N even when the injected source itself is deterministic.**

P2 is a verification-harness diagnostic. It is not a production classifier, not a literal COSMOS-Web source reproduction, and it does not define a universal spiral-detection threshold.

## Scientific motivation frozen before execution

- Kuhn et al. (2024; arXiv:2312.12389) artificially redshift low-redshift galaxies and re-inspect them to quantify observational bias in the inferred JWST spiral fraction. This motivates testing observability rather than treating intrinsic spiral structure as automatically recoverable.
- Recent JWST morphology work continues to quantify non-axisymmetric features and spiral arms at cosmic noon; the relevant failure mode is therefore not simply whether a disk remains visible, but whether arm-specific information survives the observing context.
- Classical quantitative spiral work commonly measures low-order azimuthal/Fourier structure, especially `m=2`, reinforcing the use of an explicitly arm-sensitive diagnostic rather than a global single-Sersic proxy.

P2 deliberately reuses the already frozen P1 two-arm geometry and the already frozen Gate-D real cutout/placement classes. It introduces no new source-selection rule after looking at P2 results.

## Frozen real survey input

Use the exact Gate-D real COSMOS-Web DR1 JWST/NIRCam F444W 30-mas A1 cutout produced by workflow run `33941326833`:

- artifact: `gate-d-cosmosweb-real-cutout`;
- FITS: `cosmosweb_f444w_30mas_A1_ID4204_real_cutout.fits`;
- SHA256: `764d542f2417810c904bce711455b3eb69c70cf388f97348cb857b056b2dd66d`;
- dimensions: `512 x 512` pixels;
- planes: `SCI`, `ERR`, `WHT`;
- SCI unit required: `MJy/sr`;
- pixel scale: `0.03 arcsec/pixel`.

The existing sky/background/noise in SCI is part of the real observing context and must not be regenerated or added again.

## Frozen placement matrix

Reuse the nine positions selected before the original Gate-D injection outcomes, with no relocation after P2 inspection:

### near-source, 2–5 pixels

- `(x,y)=(168,66)`, nearest source-like pixel distance `4.4721` px;
- `(379,254)`, distance `4.1231` px;
- `(143,369)`, distance `3.0` px.

### intermediate, 8–20 pixels

- `(282,225)`, distance `19.9249` px;
- `(365,275)`, distance `17.6918` px;
- `(110,389)`, distance `11.7047` px.

### relatively isolated, >=30 pixels

- `(358,97)`, distance `108.8531` px;
- `(69,195)`, distance `135.1185` px;
- `(268,328)`, distance `54.2310` px.

These classes come from the pre-injection D1c context audit, not from P2 recovery performance.

## Frozen P2 source morphology

Use the P1 **direct-target** spiral and smooth-control renderers at only:

`z_target = 2.0`.

This redshift is frozen before P2 execution because P1 showed its largest resolution-only arm suppression among the predeclared `z=0.5,1,2,3` grid, about 16.4%. Selecting this stress case uses a prior immutable result; it is not a P2-derived threshold.

Retain the P1 scene and observation geometry exactly:

- exponential disk scale length `4.0 kpc`;
- compact Gaussian bulge scale `0.9 kpc`, amplitude `0.5`;
- logarithmic two-arm perturbation, `m=2`;
- pitch angle `22 deg`;
- arm modulation amplitude `0.38`;
- target pixel scale `0.03 arcsec/pixel`;
- declared target Gaussian PSF FWHM `0.145 arcsec`.

The P1 Gaussian target PSF is a controlled surrogate and is **not** claimed to be the literal effective COSMOS-Web F444W PSF. P2 changes the image context, not the frozen P1 morphology/PSF definition.

## Frozen observed-flux stress levels

Normalize the P1 z=2 spiral image to fixed observed total magnitudes:

- AB = `26.0`;
- AB = `29.0`.

These are the same two apparent-flux stress levels used in the original Gate-D matrix. They are not pass/fail cuts.

Convert AB total flux to Jy and then to the required sum in `MJy/sr` pixels using the actual `PIXAR_SR` from the real SCI header.

Because P2 fixes the **observed apparent AB flux** after selecting the P1 morphology, no additional Tolman factor is applied during the real-mosaic injection. Applying another cosmological dimming factor here would double count the normalization convention.

## Injection semantics

For every one of the 9 placements x 2 magnitudes = 18 P2 scenes:

1. build the unit-total P1 z=2 spiral target template;
2. scale it to the requested observed AB flux using the real mosaic `PIXAR_SR`;
3. add it to a copy of real `SCI` only;
4. leave `ERR` unchanged;
5. leave `WHT` unchanged;
6. do not add or regenerate sky/background noise;
7. do not generate source-shot noise;
8. do not apply an extra Tolman factor;
9. do not invoke PSF sharpening/deconvolution.

The source remains deterministic because Gate D2 has not established enough literal exposure-level calibration/count/variance provenance to authorize survey-faithful source-shot noise.

## Frozen arm-recovery diagnostic

P1's clipped matched-arm amplitude is not directly suitable for an additive real background because clipping can mix source and unrelated positive scene structure. P2 therefore uses an explicitly linear, signed template diagnostic.

Construct on the identical z=2 target grid:

- unit-total spiral template `S`;
- unit-total smooth disk+bulge control `D`;
- arm-residual template `A = S - D`, whose total flux is numerically zero.

At each requested AB flux, scale `D` and `A` by the same requested total source normalization. The injected source is exactly:

`source = 1 * D + 1 * A`.

For the local patch around each frozen placement, fit a diagonal-ERR weighted linear model with basis columns:

1. constant background;
2. x-gradient;
3. y-gradient;
4. scaled smooth template `D`;
5. scaled arm-residual template `A`.

Fit the model independently to:

- the original real SCI patch;
- the injected real SCI patch;
- the paired difference `(injected - original)`.

No coefficient bounds, positivity constraints, clipping, or post-hoc rejection are allowed. Negative, large, unstable, or low-S/N arm coefficients are scientific observables and must be preserved.

For each fit record at minimum:

- smooth coefficient;
- arm coefficient;
- arm/smooth ratio when finite;
- weighted design rank;
- condition number;
- weighted residual norm;
- original-background arm-equivalent coefficient;
- injected arm coefficient bias relative to truth `1`;
- injected smooth coefficient bias relative to truth `1`;
- paired-difference coefficients;
- algebraic closure between `(injected fit - original fit)` and paired-difference fit.

The diagonal-ERR weighting is a declared measurement diagnostic only. It does not assert independent mosaic noise or remove drizzle covariance.

## Interpretation rules

P2 asks:

1. how strongly real COSMOS-Web background/crowding biases the recovered known arm coefficient at AB=26 and AB=29;
2. whether the bias topology differs across the three predeclared crowding classes;
3. how much arm-like contamination is already present in the background-only patch;
4. whether the paired-difference oracle recovers the deterministic source coefficients, separating numerical/template identifiability from real-context contamination.

The paired-difference path is a same-renderer numerical/identifiability control, **not** independent cross-code validation.

No universal `arm coefficient > X` detection rule will be invented from these 18 points. P2 results are descriptive failure-mode measurements, not a classifier calibration.

## Software/numerical invariants allowed in tests

Tests may enforce only implementation identities known before real-data execution, including:

- unit-total spiral and smooth templates;
- zero-total arm residual to numerical precision;
- no mutation of input SCI by the injection helper;
- exact synthetic linear recovery of coefficients `[smooth=1, arm=1]` on a zero-background constructed scene within floating-point precision;
- preservation of negative synthetic arm coefficients rather than clipping.

These are numerical sanity checks, not scientific acceptance bands for the real COSMOS-Web results.

## Required outputs

Archive:

- machine-readable JSON for all 18 cases;
- aggregate descriptive summaries by predeclared crowding class and magnitude;
- a figure showing raw injected arm coefficients relative to the known truth `1`, without converting the plot into a pass/fail threshold;
- software provenance;
- an immutable result receipt written only after the workflow output is inspected.

## Explicit exclusions

P2 does **not** include:

- literal survey exposure-space source-shot noise;
- regenerated sky/background noise;
- modification of ERR or WHT;
- empirical source evolution;
- passive-galaxy SED/K-correction;
- segmentation/deblending optimization;
- visual or ML spiral classification;
- a universal detection threshold;
- a claim that the P1 Gaussian PSF is the literal COSMOS-Web effective PSF.

Any of those requires a separately frozen experiment.
