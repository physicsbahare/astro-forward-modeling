# Gate D2f — survey-processed pre-resample input provenance protocol

## Purpose

Determine whether the **literal COSMOS-Web survey-processed pre-resample inputs** that contribute at the frozen Gate-D anchor can be obtained and whether they retain enough calibration/count/variance provenance to support a scientifically defensible exposure-space source-shot experiment.

D2f is a provenance audit. It is **not** permission to generate source-shot noise, reconstruct missing detector counts, substitute archive `_cal.fits` products for the release inputs, or rerun the survey reduction approximately.

## Frozen contributor set

D2c decoded the authoritative A1 F444W 30-mas release mosaic `CON`+`HDRTAB` at the frozen anchor to exactly four survey-processed inputs:

1. `jw01727084001_04101_00001_nrcalong_jhat_a3001_crf.fits`
2. `jw01727084001_04101_00003_nrcalong_jhat_a3001_crf.fits`
3. `jw01727084001_04101_00002_nrcalong_jhat_a3001_crf.fits`
4. `jw01727084001_04101_00004_nrcalong_jhat_a3001_crf.fits`

These names are release-level evidence. They must not be silently replaced by MAST `_cal.fits` files with related exposure roots.

## Authoritative context before execution

The public COSMOS-Web DR1 NIRCam download page exposes final `i2d` mosaics and extracted `SCI`, `ERR`, and `WHT` extensions. It does not advertise the individual survey-processed `*_jhat_a3001_crf.fits` inputs in its published download table.

Franco et al. (2025), *COSMOS-Web: Comprehensive Data Reduction for Wide-Area JWST NIRCam Imaging*, states that the survey performs custom astrometric alignment with JHAT, performs background removal in the `*crf.fits` files immediately before resampling, and constructs each final tile by selecting overlapping `*crf.fits` images into an ASN for the Stage-3 resample step. Therefore the literal release inputs are scientifically distinct from an unmodified public archive `_cal.fits` product.

JWST pipeline documentation establishes that calibrated imaging products normally contain `SCI`, `ERR`, `DQ`, `VAR_POISSON`, `VAR_RNOISE`, `VAR_FLAT`, optional `AREA`, and ASDF metadata; calibrated `SCI` is in surface-brightness units after `photom`. Outlier detection modifies DQ and can propagate flagged pixels to `SCI`, `ERR`, and variance arrays. These generic data-model facts define fields worth auditing, but they do **not** prove what the COSMOS-Web custom `crf` files contain.

Authoritative references for this protocol:

- COSMOS-Web DR1 NIRCam release: `https://cosmos2025.iap.fr/nircam.html`
- COSMOS public release page: `https://cosmos.astro.caltech.edu/page/cosmosweb-dr`
- Franco et al. 2025: `https://arxiv.org/abs/2506.03256`
- JWST science-product documentation: `https://jwst-pipeline.readthedocs.io/en/3.0.0/jwst/data_products/science_products.html`
- JWST photom documentation: `https://jwst-pipeline.readthedocs.io/en/stable/jwst/photom/main.html`

## Phase 1 — authoritative availability audit

For each exact contributor filename, search only authoritative/public release or archive locations first.

Record separately:

- exact public URL, if any;
- whether the URL is a literal survey-processed `*_jhat_a3001_crf.fits` product;
- whether access requires private/team storage or author contact;
- checksum and byte size if a file is obtained;
- whether only a related MAST `_cal.fits` exposure is public.

A filename search failure is not proof that the file never exists. The allowed conclusion is narrower: **not found in the audited authoritative public distribution**.

Do not bulk-download the whole survey. Only the four frozen contributors are relevant to this decision.

## Phase 2 — metadata-only structure audit, only if literal CRF files are available

Before reading science pixels, inspect FITS headers and extension structure for each literal CRF. Record:

### Identity and reduction lineage

- `FILENAME`, `DATAMODL`, program/observation/visit/exposure/detector/filter/pupil;
- `CAL_VER`, `CRDS_VER`, `CRDS_CTX`;
- JHAT/custom-processing identifiers if explicitly recorded;
- step-status metadata for `photom`, background/sky matching, outlier detection, and resampling;
- any parent/input filename or association lineage.

### Science/calibration boundary

- `BUNIT` / science units;
- `PHOTMJSR`, `PHOTUJA2`, pixel-area metadata;
- exposure timing metadata (`EFFEXPTM`, `EXPTIME`, group/integration metadata where present);
- gain/read-noise reference provenance where explicitly recorded;
- whether the product is still a calibrated rate/surface-brightness representation rather than detector counts/electrons.

### Variance and DQ inventory

Record presence, shape, units, and metadata for:

- `SCI`
- `ERR`
- `DQ`
- `VAR_POISSON`
- `VAR_RNOISE`
- `VAR_FLAT`
- `AREA`
- embedded `ASDF`

Do not infer a missing variance component from `ERR` alone unless the historical pipeline semantics make that decomposition explicit and reversible.

## Phase 3 — source-shot identifiability decision

A literal source-shot realization may be considered only if all of the following are established for the actual survey-processed contributors:

1. **Literal-input identity:** the files are the exact D2c `*_jhat_a3001_crf.fits` contributors, not merely exposure-root matches.
2. **Signal boundary:** the relationship between the CRF `SCI` representation and detector/source counts is explicit enough to convert an injected source expectation to the correct stochastic domain without an ad-hoc gain/exposure assumption.
3. **Variance boundary:** the existing variance arrays and their calibration transformations are explicit enough to add the injected source's Poisson contribution without double-counting the pre-existing scene/background variance.
4. **DQ/outlier semantics:** the location of outlier/background operations relative to the injected-source stochastic realization is understood well enough that a replay does not silently bypass a relevant nonlinear step.
5. **Resampling replay:** the historical final resampling operator is sufficiently specified. D2d/D2e currently establish `weight_type=ivm`, `pixfrac=1.0`, `pixel_scale_ratio=0.4750281915826499`, pointings/`NDRIZ=62`, and `crds://jwst_nircam_drizpars_0001.fits`, but **not an explicit final-resample kernel**.

If any item remains unresolved:

`source_shot_realization_permitted = false`

No threshold is to be relaxed to force this gate closed.

## Explicit non-equivalences

D2f must preserve all of these distinctions:

- related MAST `_cal.fits` != literal COSMOS-Web `*_jhat_a3001_crf.fits`;
- final-mosaic `VAR_POISSON` != recoverable detector-level realization history;
- a CRDS DRIZPARS filename != proof of every effective runtime resample parameter;
- an outlier-rejection `kernel='square'` setting in the reduction paper != proof of the final tile-resampling kernel;
- a calibrated surface-brightness value != source electron count without an established reversible calibration boundary;
- independent output-pixel Poisson noise != literal exposure-space source-shot covariance.

## Mutation/stochastic guardrails

D2f is read-only until a later, separately frozen protocol explicitly authorizes otherwise. Record all as false:

- SCI modified;
- ERR modified;
- WHT modified;
- variance arrays modified;
- source-shot noise generated;
- background/sky noise added;
- PSF sharpening applied;
- Tolman factor applied.

## Stop rule

If the exact four CRF files are not available from the audited public release/archive paths, stop the pixel-level phase and record the access/provenance blocker. Do not substitute `_cal.fits` products and call the result a literal COSMOS-Web replay.

If the CRF files are available but the detector/source-count boundary remains non-reversible, stop and preserve that as the scientific result. A negative identifiability result is a valid Gate-D result.
