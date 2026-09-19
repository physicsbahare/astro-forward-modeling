# Passive-disk R1 — real COSMOS-Web transfer-only pilot protocol

Status: **FROZEN BEFORE R1 RENDERING**

This protocol defines the first real-galaxy artificial-redshifting transfer experiment after the paper-scope reset. It is intentionally small. It is not a completeness measurement yet, not a production framework, not a spiral classifier, and not a replacement for COSMOS-Web catalog morphology.

The immutable input audit is `REAL_PILOT_PREFLIGHT_RESULT.md`.

## Scientific question

Can the already-verified redshift/radiometry/resampling operator be connected to a **real, visually disk-like COSMOS-Web source** without introducing unsupported spectral extrapolation, PSF sharpening, duplicated dimming, or a new morphology-extraction problem?

R1 is a transfer-only feasibility experiment. It records what the real source becomes at the chosen target redshifts. It does not define a recovery threshold.

## Frozen source

- COSMOS2025 ID: `57977`
- source redshift: `z_source = 0.4304`
- COSMOS-Web tile: `A2`
- source pixel scale: `0.03 arcsec/pixel`
- source SCI unit: `MJy/sr`
- source filters available: F115W, F150W, F277W, F444W
- cutout size: 267x267 pixels (8 arcsec)
- binary input identity: the eight-file archive/cutout checksums recorded in `REAL_PILOT_PREFLIGHT_RESULT.md`

The source is used because it is visually a clear inclined disk in the COSMOS-Web postage stamps and in the literal A2 mosaic cutouts. It is **not** declared a confirmed spiral.

## Frozen target grid and observed filters

Use:

`z_target = [1.0, 1.5, 2.0, 2.5, 3.0]`

The target observed filter follows the rest-frame-1-micron pivot-band logic used by Vijarnwannaluk et al. (2025, Section 3.4/Table 7):

- z=1.0 -> F277W
- z=1.5 -> F277W
- z=2.0 -> F444W
- z=2.5 -> F444W
- z=3.0 -> F444W

Use the STScI V7 pivot wavelengths:

- F150W: 1.501 um
- F277W: 2.776 um
- F444W: 4.402 um

For each target case, the source observed wavelength corresponding to the target pivot wavelength is

`lambda_source = lambda_target * (1 + z_source) / (1 + z_target)`.

The frozen values are:

| z_target | target band | lambda_source [um] |
| ---: | --- | ---: |
| 1.0 | F277W | 1.985395 |
| 1.5 | F277W | 1.588316 |
| 2.0 | F444W | 2.098874 |
| 2.5 | F444W | 1.799035 |
| 3.0 | F444W | 1.574155 |

All lie between F150W and F277W, so R1 uses no spectral extrapolation.

## Source-stamp boundary

R1 must not redshift the entire noisy 8-arcsec sky cutout as if the surrounding real sky and unrelated objects belonged to the galaxy.

Use a deliberately simple development stamp:

1. estimate a scalar local background independently in F150W and F277W from the annulus `2.5 <= r < 3.5 arcsec` around the catalog position;
2. subtract that scalar background from each source image;
3. retain the central circular source region `r <= 1.5 arcsec`;
4. set pixels outside that radius to zero for the transfer-only source stamp.

The 1.5-arcsec radius is fixed before R1 rendering and is about 4.3 times the catalog F277W effective radius of ID 57977. It is a transparent pilot boundary, **not** a new survey segmentation algorithm and not a future production default.

No clipping of negative in-aperture pixels is allowed before rendering. Negative residual pixels are retained.

## Source PSF homogenization

The R1 pivot-band source wavelengths all lie between F150W and F277W. Before interpolating those two images, place them on one declared source-resolution bracket.

For this pilot only, use the published empirical NIRCam FWHM values from the current STScI PSF documentation as a declared bracket:

- F150W empirical FWHM = 0.050 arcsec
- F277W empirical FWHM = 0.092 arcsec

Degrade F150W to the broader F277W bracket with a Gaussian kernel

`FWHM_kernel = sqrt(FWHM_F277W^2 - FWHM_F150W^2)`.

F277W is not sharpened or deconvolved.

This published-FWHM approximation is **not** claimed to be the exact effective COSMOS-Web DR1 mosaic PSF. R1 must label it as a PSF-bracket transfer pilot. A later science-completeness run must either adopt an independently justified mosaic-PSF provider or propagate this PSF uncertainty explicitly.

## Pixel SED interpolation

The SCI mosaics are in `MJy/sr`, so the R1 interpolation is frozen in the native specific-intensity-per-frequency representation.

For a required `lambda_source` between F150W and F277W:

`t = (lambda_source - 1.501) / (2.776 - 1.501)`

and

`I_nu(lambda_source) = (1 - t) I_nu,F150W_matched + t I_nu,F277W`.

No extrapolation is permitted (`t` must remain in [0,1]).

This is the minimal pivot-wavelength approximation for R1. It is **not** promoted to a universal throughput-integrated SED renderer. The preflight representation sensitivity is recorded separately, and a later throughput-aware check is required only if it materially affects the paper-level morphology result.

## Redshift radiometry

The interpolated source plane represents observed `I_nu` at the source redshift at the corresponding source wavelength. For the same emitted surface-brightness distribution observed at `z_target`, apply only the specific-intensity transformation

`I_nu,target = I_nu,source * [(1 + z_source)/(1 + z_target)]^3`.

Do **not** apply any additional `(1+z)^-4` Tolman factor or a second K-correction. The spectral-density transformation already contains the relevant redshift factor for `I_nu` at corresponding emitted/observed frequencies.

No intrinsic luminosity evolution is applied in R1.

## Angular rescaling and sampling

Use the repository `FlatLCDMReference(H0=70 km/s/Mpc, Om0=0.3)` convention already employed by the verification harness.

The angular-size scale factor is

`scale_theta = D_A(z_source) / D_A(z_target)`.

Resample the source stamp onto the target physical view while keeping the target COSMOS-Web output grid at `0.03 arcsec/pixel`.

The resampler must conserve the surface-brightness field semantics; it must not introduce a separate flux-normalization factor on top of the `I_nu` redshift transformation.

## Target PSF bracket

Use the current published empirical STScI FWHM values as the declared R1 target bracket:

- target F277W: 0.092 arcsec
- target F444W: 0.145 arcsec

The source common PSF is 0.092 arcsec at `z_source`. Its angular equivalent after moving the same physical blur to the target redshift is

`FWHM_source_equiv = 0.092 * D_A(z_source) / D_A(z_target)`.

A pure degradation kernel is allowed only when

`FWHM_target > FWHM_source_equiv`.

Then

`FWHM_kernel = sqrt(FWHM_target^2 - FWHM_source_equiv^2)`.

If this inequality fails, preserve the case as `PSF_SHARPENING_REQUIRED_UNSUPPORTED`; do not invent a sharpening kernel.

## Noise and survey context

R1 adds **no new stochastic noise** and performs no real-background injection. This is deliberate: R1 isolates the real-source transfer operator before completeness/recovery is measured in survey context.

Therefore in R1:

- no new sky/background realization;
- no source-shot-noise realization;
- no ERR/WHT modification;
- no SCI injection into another mosaic;
- no detection/deblending rescue;
- no morphology pass/fail threshold.

The later completeness stage may inject the rendered source into real survey context, but must obey the existing Gate-D rule that the already-noisy real background is not re-noised and that L1 injection modifies SCI only.

## Frozen diagnostics

For the source stamp and each of the five target renders, record without post-hoc acceptance bands:

- target redshift and target band;
- required source wavelength and interpolation weight `t`;
- angular-size scale factor;
- source-equivalent PSF FWHM and added target matching-kernel FWHM;
- finite/non-finite pixel count;
- summed signed stamp intensity and summed positive stamp intensity;
- centroid relative to the geometric stamp center;
- second-moment axis-ratio proxy;
- second-moment RMS angular size;
- concentration proxy using fixed enclosed radii if numerically defined;
- any unsupported spectral/PSF state.

The R1 result is descriptive. A case is not discarded because its morphology degrades.

## Rest-frame 1 micron analysis boundary

Do not construct a synthetic rest-frame-1-micron image and treat it as a literal COSMOS-Web observation.

For the **original** ID 57977 source, the catalog F115W/F150W sizes bracket observed `1*(1+z_source)=1.4304 um`; a log-linear size-gradient interpolation gives approximately `Re_1um = 0.389 arcsec`. This is a structural reference only.

For target renders, exact rest-frame-1-micron structural interpolation is performed only when the required adjacent target-band renderings are supported by the source spectral information. Otherwise record the pivot-band morphology and set the exact-rest-frame quantity to unsupported. No extrapolation is allowed merely to populate a table.

## References used to freeze R1

- Barden, Jahnke & Haussler (2008), FERENGI — pixel-by-pixel multiband SED/bandpass-shift logic and artificial-redshifting operator ordering.
- Vijarnwannaluk et al. (2025), ApJ 994, 265, Section 3.4 and Table 7 — COSMOS-Web rest-frame-1-micron size/pivot-band treatment.
- STScI JWST User Documentation, NIRCam Filters, V7 throughput characteristics (updated 2025) — pivot wavelengths and passband definitions.
- STScI JWST User Documentation, NIRCam Point Spread Functions — published empirical FWHM values used only as the R1 PSF bracket.

## Stop rule

After R1 is rendered and audited, do not branch into further transfer refinements automatically. The next decision is only:

1. if R1 is internally coherent, add ID 39749 as the pre-frozen context stress source and then move to survey-context completeness/recovery; or
2. if R1 exposes a new paper-critical spectral/PSF/operator failure, isolate that one failure with the smallest justified diagnostic.

Do not resume P6/P7 contamination fitting.