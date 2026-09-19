# Passive-disk real-galaxy pilot — preflight result

Status: **REAL INPUT AUDITED / PRIMARY PILOT FIXED / RENDERING NOT YET CLAIMED**

This receipt records the real COSMOS-Web development inputs and the methodological decision that follows from inspecting them. It does **not** supersede P1–P5 or Gate-D, does not claim a production implementation, and does not claim that the full real-galaxy artificial-redshifting chain has already run.

## Scope alignment

The paper-scope decision in `SCOPE_DECISION.md` remains in force. P6 implementation is deferred. The purpose of this pilot is to move directly toward the catalog-aligned morphology-recovery/completeness experiment using a real passive disk as a development control.

## Input selection inherited from the science project

The development objects come from the existing COSMOS-Web passive-disk candidate work rather than from a new selection built for this repository.

- Prior fiducial candidate set: 1139 objects at `z < 3`.
- Visual-calibration sample: 228 objects.
- Primary development source: COSMOS2025 **ID 57977**, tile A2, `z_source = 0.4304`.
- Secondary stress source: COSMOS2025 **ID 39749**, tile A2, `z_source = 0.8814`.

Manual inspection of the COSMOS-Web SED/postage-stamp panels and the extracted A2 cutouts found ID 57977 to be the cleanest clearly elongated/inclined disk in the A2 subset. ID 39749 is structurally disk-dominated in the catalog but its raw cutout is more affected by surrounding/background structure, so it is retained as a later crowding/context stress case rather than the first transfer target.

### Catalog structural context

For ID 57977, the released catalog measurements supplied with the project are consistent with an inclined disk containing a non-negligible bulge rather than a pure exponential disk:

- `B/T` = 0.493, 0.494, 0.459, 0.588 in F115W/F150W/F277W/F444W;
- single-Sérsic `n` = 2.240, 2.433, 2.696, 3.099;
- axis ratio = 0.407, 0.399, 0.354, 0.370;
- `Re` = 0.399, 0.387, 0.349, 0.342 arcsec.

For ID 39749:

- `B/T` = 0.128, 0.181, 0.093, 0.185;
- single-Sérsic `n` = 1.426, 1.313, 1.198, 1.390;
- axis ratio = 0.728, 0.696, 0.691, 0.682;
- `Re` = 0.247, 0.253, 0.219, 0.218 arcsec.

Thus 57977 is the visually cleaner disk pilot, whereas 39749 is the more disk-dominated catalog object but the less isolated image-level control.

## Real A2 cutout provenance

The user extracted 8-arcsec 30-mas SCI cutouts from the literal COSMOS-Web A2 v1.0 mosaics in F115W, F150W, F277W and F444W for both objects. The extraction log records 267x267 finite-pixel cutouts and `BUNIT = MJy/sr` in all four filters.

Uploaded archive SHA-256:

`1830bf67f88c064565b18f8a450c0276117d1dfdf498c640dcc397c38664d1b1`

Individual cutout SHA-256 values:

- `57977_f115w_sci_8arcsec.fits`: `56790f81395ae3ac25ea129008f1f78f47fe8e7b97e3063c667e6451866a1c50`
- `57977_f150w_sci_8arcsec.fits`: `03e00c4546ea6cc237a114a2e0298dba4481b06892d43060f29d6b208b42fba0`
- `57977_f277w_sci_8arcsec.fits`: `b5b40dd5d79ef4a9e884ce91bb5777251782c6a42699fca431cb417ab760cacd`
- `57977_f444w_sci_8arcsec.fits`: `46bfed3affd0ed6a4b64c6140906fdf353321ca61689034c605eb247a5245790`
- `39749_f115w_sci_8arcsec.fits`: `472213b4808b3cdb0fe3396595cc7bb64230fedb309ca2effd5f43c1d6a6e95c`
- `39749_f150w_sci_8arcsec.fits`: `3628819f2b9fca106c275545dd4f04e1a0826ecd944f01aee18ecc8eb1d207ba`
- `39749_f277w_sci_8arcsec.fits`: `1134db2e819272fce4f9443c9684688432b3d29335de4dcce4bed564f145e9e2`
- `39749_f444w_sci_8arcsec.fits`: `ee5f451429eaecf51bea9f73dc3632fc18d90b10ebea5c2705fb433282bc7b40`

The binary cutouts are not committed to this repository. This receipt stores their immutable checksums so later runs cannot silently substitute different inputs.

## Registration audit

For each object, F115W/F150W/F277W/F444W have identical cutout WCS keywords (`CRPIX`, `CRVAL`, `CDELT`, `PC`, `CTYPE`) and the same 30-mas pixel grid. Therefore the pilot must **not** apply an additional reprojection or force an artificial centroid registration before the wavelength interpolation step.

A simple central positive-flux second-moment diagnostic gives the following raw-cutout axis-ratio proxies:

- ID 57977: 0.585, 0.574, 0.584, 0.600 across F115W/F150W/F277W/F444W;
- ID 39749: 0.928, 0.921, 0.794, 0.848.

The second object is therefore preserved as a context-contaminated case rather than used to tune the first real transfer implementation.

## Rest-frame-method correction

Two operations that had previously been conflated are now explicitly separated:

1. **FERENGI-style bandpass shifting:** infer the source's spatially varying SED from registered multiband images and render that same source into an actual target observed filter.
2. **Rest-frame 1 micron structural comparison:** use the observed filters that bracket or best represent rest-frame 1 micron to compare structural measurements across redshift.

Vijarnwannaluk et al. (2025, ApJ 994, 265, Section 3.4 and Table 7) use COSMOS-Web F115W/F150W, F150W/F277W, and F277W/F444W pairs to estimate the wavelength dependence of effective radius, and use pivot bands F115W/F150W/F277W/F444W in successive redshift intervals. Their method does **not** require constructing a synthetic rest-frame-1-micron image as a separate survey product. The Sérsic index used in their later analysis is taken from the pivot band.

Accordingly, the present pilot will render into actual COSMOS-Web target filters first. Exact rest-frame structural interpolation is an analysis layer and must be flagged unsupported whenever the needed adjacent-band information is not constrained by the available source spectral support.

## Target mapping for ID 57977

For the development grid `z_target = [1.0, 1.5, 2.0, 2.5, 3.0]`, the literature-motivated pivot-band mapping is:

| z_target | target pivot band | target pivot lambda [um] | source observed lambda needed [um] |
| ---: | --- | ---: | ---: |
| 1.0 | F277W | 2.776 | 1.985 |
| 1.5 | F277W | 2.776 | 1.588 |
| 2.0 | F444W | 4.402 | 2.099 |
| 2.5 | F444W | 4.402 | 1.799 |
| 3.0 | F444W | 4.402 | 1.574 |

All five pivot-band source wavelengths fall between the F150W and F277W pivot wavelengths. Therefore the **minimal pivot-band pilot does not require extrapolation** for any of the five target redshifts.

This does not imply that every adjacent target band needed for an exact rest-frame-1-micron interpolation is supported. That support must be tracked independently.

## Interpolation-representation sensitivity diagnostic

The input mosaics are calibrated as specific intensity in `MJy/sr`, i.e. an `I_nu` representation. As a narrow diagnostic only, F150W was degraded to the published empirical F277W FWHM bracket (0.050 to 0.092 arcsec; this is not claimed to be the exact DR1 mosaic effective PSF), and the required source wavelengths above were interpolated in two representations:

- linear `I_nu` versus wavelength;
- convert to `I_lambda`, interpolate linearly, then convert back to `I_nu`.

For ID 57977 over the five target-redshift wavelengths:

- normalized positive central-image L1 difference: 0.0052 to 0.0288;
- second-moment axis-ratio difference: < 0.0016;
- relative RMS-size difference: < 0.0066.

This shows that the representation choice is a small effect for the **smooth global disk-shape diagnostics** of this particular pilot. It is not evidence that a simple interpolation is universally adequate for spiral-arm contrast or arbitrary color gradients. P1 and the chromatic-PSF tests remain the relevant warning that small-scale morphology can be more sensitive.

## Decision

Proceed to one compact real-galaxy transfer experiment on ID 57977 only, with the protocol frozen separately in `R1_PROTOCOL.md`.

Do not:

- resume P6/P7 contamination fitting;
- build a new source extractor/deblender;
- force inter-band centroids to coincide;
- extrapolate outside source spectral support;
- interpret published filter FWHM values as the exact COSMOS-Web mosaic PSF;
- add target sky noise, source-shot noise, or a second Tolman factor in this transfer-only pilot.

ID 39749 remains frozen as the second-stage realistic-context stress source after the primary transfer path is demonstrated.