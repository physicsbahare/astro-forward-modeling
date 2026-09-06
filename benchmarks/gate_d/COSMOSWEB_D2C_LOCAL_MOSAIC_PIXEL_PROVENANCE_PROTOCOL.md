# Gate D2c — local full-mosaic pixel-level provenance audit

## Purpose

Determine the exact COSMOS-Web DR1 input-image membership at the frozen Gate-D sky anchor from the release product itself, using only immutable metadata/WCS/context information from the locally held full F444W 30-mas A1 `i2d` mosaic.

This is a provenance audit only. It must not modify SCI/ERR/WHT/variance arrays, generate source-shot noise, add background noise, sharpen a PSF, apply an extra Tolman factor, or infer missing historical resampling parameters.

## Frozen target and product

Use the same Gate-D anchor as D1/D2a:

- ICRS RA = `149.8671500 deg`
- ICRS Dec = `2.1294010 deg`
- COSMOS-Web DR1 tile A1
- JWST/NIRCam F444W
- 30 mas mosaic product

The local product path is runtime-local evidence and must not be committed as a portable scientific identifier. Record instead the basename, byte size, internal FITS `FILENAME`, `ASNTABLE`, calibration version, CRDS context, extension inventory, and relevant resampling header cards.

## Frozen interpretation

JWST `resample` context semantics are used without modification:

- `CON` is interpreted as an unsigned 32-bit bit field;
- plane `p`, bit `k` corresponds to input index `32*p + k` (zero-indexed);
- only set bits at the frozen anchor pixel are treated as contributing inputs;
- those input indices are mapped to the same-index rows of `HDRTAB`, which stores metadata for the input images combined into the resampled product;
- the resulting filenames are release-level `*_crf.fits`/survey-processed input identities, not a claim that raw `_cal.fits` archive products are identical to those release inputs.

The audit must report the raw `CON` plane values and decoded indices so the mapping remains independently checkable.

## Required evidence

The audit must record:

1. celestial WCS conversion of the frozen anchor to floating-point and nearest integer mosaic pixel coordinates;
2. SCI and CON array shapes and the finite SCI value at the anchor;
3. all CON plane values at the anchor in decimal and hexadecimal form;
4. decoded zero-indexed input indices;
5. corresponding HDRTAB row metadata, at minimum `FILENAME`, `PROGRAM`, `OBSERVTN`, `VISIT`, `VISITGRP`, `EXPOSURE`, `DETECTOR`, `FILTER`, `PUPIL`, `DATE-BEG`, and `DATE-END` when present;
6. primary-header provenance including `ASNTABLE`, `CAL_VER`, `CRDS_CTX`, `NDRIZ`, `PIXFRAC`, `NEXPOSUR`, and `S_RESAMP` when present;
7. the full extension-name inventory, including whether `CON`, `VAR_POISSON`, `VAR_RNOISE`, `VAR_FLAT`, `HDRTAB`, and `ASDF` are present.

## Scientific decision rule

This audit may close the **pixel-level release membership** part of D2 provenance only if:

- the anchor is inside the mosaic;
- nonzero CON bits decode to valid HDRTAB rows;
- the referenced rows contain unambiguous release input filenames;
- the mapping is internally consistent and recorded without inference beyond the documented JWST context convention.

It does **not** by itself establish a replayable detector/exposure-space source-shot experiment. In particular, exact historical resampling kernel/weighting details, the calibration/count boundary for the survey-specific `*_jhat_*_crf.fits` inputs, and variance/count provenance of those literal pre-resample files remain separate requirements unless independently demonstrated.

## Mutation audit

The implementation must be read-only with respect to the FITS product and repository science data. The JSON result is metadata/provenance evidence only.
