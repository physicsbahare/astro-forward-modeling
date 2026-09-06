# COSMOS-Web Gate D2b authoritative release-provenance audit — frozen protocol

Status: **FROZEN BEFORE RESULT RECORD**

Purpose: determine whether public, release-authoritative COSMOS-Web DR1 material closes any of the four provenance gaps frozen by D2a, without downloading or modifying science pixels and without generating stochastic source-shot noise.

## Frozen target

- Gate-D anchor: RA `149.8671500 deg`, Dec `2.1294010 deg`.
- Survey/program: COSMOS-Web, JWST GO 1727.
- Instrument/filter: NIRCam F444W.
- Release product: COSMOS-Web DR1 30-mas mosaic tile containing the anchor.
- D2a candidate exposure roots remain archive candidates only unless release-authoritative membership proves otherwise.

## Authoritative sources to inspect

1. COSMOS-Web DR1 NIRCam release page: `https://cosmos2025.iap.fr/nircam.html`.
2. Franco et al. (2025), *COSMOS-Web: Comprehensive Data Reduction for Wide-Area JWST NIRCam Imaging*, arXiv:2506.03256.
3. STScI JWST pipeline imaging-resample documentation for the semantics of resampling metadata; this is implementation documentation, not evidence of the COSMOS-Web choices unless those choices are present in release-authoritative material.

## Frozen questions

Assess each item independently as `proven`, `not proven`, or `partially proven`:

1. **Exact release association membership** — exact contributing exposure/product set for the F444W A1 release mosaic at the Gate-D position.
2. **Literal pre-resample inputs** — exact files at the boundary actually supplied to final resampling, or a replayable transform from public calibrated products to those files.
3. **Actual contributing variance/count provenance** — variance/count information for the literal contributing inputs sufficient to define detector/exposure-space source-shot perturbations without inference.
4. **Exact historical resampling configuration** — release-specific kernel, pixfrac, weighting, output WCS/scale and any custom association/resampling choices needed to replay the transfer operator.

## Scientific acceptance rule

`source_shot_realization_permitted=true` only if **all four** questions are proven from release-authoritative provenance. Generic JWST defaults, archive proximity, plausible observation geometry, or current pipeline defaults cannot substitute for historical release choices.

A public full `i2d` product containing variance extensions may close an L1-product information gap but does **not by itself** establish exposure membership, pre-resample count provenance, or replayable historical resampling.

## Mutation constraints

This audit must not:

- generate source-shot noise;
- add sky/background noise;
- modify SCI, ERR, or WHT;
- apply an additional Tolman factor;
- use a PSF-sharpening kernel;
- change benchmark tolerances, bounds, convergence requirements, or acceptance criteria.

No production-framework code is permitted.
