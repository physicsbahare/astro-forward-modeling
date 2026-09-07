# Gate D1n-e — published COSMOS-Web empirical-PSF bracket protocol

## Purpose

D1n-d returned zero Gaia DR3 sources in the frozen 512x512 Gate-D cutout, so the 14 D1n-b compact detections cannot be independently promoted to stars or used as a calibrated empirical PSF. The next non-redundant question is therefore: **how different are published, survey-specific COSMOS-Web F444W PSF models from the single ideal STPSF used in D1d–D1m at the sky location relevant to the Gate-D cutout?**

This is a PSF-shape comparison only. It does not yet rerun morphology recovery and it does not adopt any published PSF as automatic ground truth.

## Literature / data basis

Zhuang, Li & Shen (2024, ApJ 962, 93; arXiv:2309.03266) constructed public NIRCam PSF models for COSMOS-Web observations and reported both temporal and spatial variation. For F444W they report a median PSF FWHM of about 158 mas, temporal fractional variation about 0.8%, and spatial variation about 1.5%; they recommend considering the released global/broad/narrow empirical PSF models rather than a simple deterministic spatial interpolation. Their reduced images and PSF products are public at `https://ariel.astro.illinois.edu/cosmos_web/`.

The published pointing table lists `OBS_084` at approximately RA=149.864751 deg, Dec=2.147570 deg, the closest listed pointing center to the current Gate-D cutout center near RA=149.86715 deg, Dec=2.12939 deg. This identifies OBS_084 as the first survey-specific PSF bracket to inspect; it is not a claim that one observation alone reproduces the final DR1 mosaic effective PSF.

## Frozen inputs

Public source files:

- `https://ariel.astro.illinois.edu/cosmos_web/nircam/psf/OBS_084_F444W_global_PSF.fits`
- `https://ariel.astro.illinois.edu/cosmos_web/nircam/psf/OBS_084_F444W_broad_PSF.fits`
- `https://ariel.astro.illinois.edu/cosmos_web/nircam/psf/OBS_084_F444W_narrow_PSF.fits`

The workflow must record byte size and SHA256 of every downloaded source before analysis. If a source changes or becomes unavailable, that is a provenance/infrastructure event and must not be substituted silently.

The comparator is the exact declared Gate-D STPSF convention already frozen by D1d–D1m: F444W, NRCA5, detector position (1024,1024), the same three-point spectral weighting, STPSF 2.2.0 and the same reference-data archive. No new STPSF tuning is allowed.

## Frozen analysis

1. Read each published PSF as supplied; record FITS shape, pixel scale metadata where present, finite/signed-sum diagnostics, negative-pixel fraction, and normalization provenance.
2. Do not clip negative values unless the publication explicitly defines them as invalid; preserve signed values in provenance/diagnostics. For comparison-only normalized profiles, use the documented positive or signed normalization consistently and record which convention is used.
3. Place all PSFs on a common **comparison grid only**. Resampling may use flux-conserving interpolation/downsampling as required by the supplied pixel scales. No deconvolution, Wiener matching, or sharpening kernel is allowed.
4. Compare `global`, `broad`, and `narrow` models separately to the declared STPSF using:
   - FWHM or equivalent radial-width estimate when well-defined;
   - EE50 and EE80 radii;
   - positive-support second moments and axis ratio;
   - normalized L1 image difference on common support;
   - normalized cross-correlation;
   - centroid offset before any optional centering diagnostic.
5. Also compare the three published PSFs with one another so their internal survey-specific bracket is explicit.
6. Preserve all three models. Do not select the one that happens to improve a morphology fit because no morphology rerun occurs in D1n-e.
7. Do not define a post-hoc numerical acceptance threshold. Workflow success means only that provenance and metrics were produced correctly.
8. Do not modify SCI/ERR/WHT, inject a source, add sky/source noise, apply Tolman dimming, alter segmentation, change target/nuisance bounds, change optimizer convergence settings, or run production code.

## Decision rule for the following experiment

- If the published COSMOS-Web PSF bracket is nearly indistinguishable from the declared STPSF at morphology-relevant scales, PSF mismatch becomes a weaker explanation for the remaining D1m catastrophic interior failures, and the next experiment should move to target-model/scene identifiability rather than another PSF rescue.
- If one or more published survey PSFs differ materially in width/core/encircled-energy or image structure, the next experiment may rerun only a **minimal predeclared subset**: the two known AB=26 catastrophic D1m rows plus matched control rows, preserving D1m scene, bounds, objective, convergence requirements, and failure reporting. The published models must be treated as an external empirical bracket, not as literal DR1 mosaic truth.

This protocol intentionally distinguishes published COSMOS-Web observation-level PSFs from the final DR1 mosaic effective PSF and from synthetic STPSF.
