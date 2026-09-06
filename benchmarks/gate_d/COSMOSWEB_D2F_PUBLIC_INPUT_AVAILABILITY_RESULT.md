# Gate D2f — public availability preflight for survey-processed CRF inputs

Status: **LITERAL CRF INPUTS NOT FOUND IN AUDITED PUBLIC DR1 SURFACES / RELATED ARCHIVE CAL PRODUCTS ARE NOT EQUIVALENT / SOURCE-SHOT REALIZATION STILL BLOCKED**

Date of authoritative public-web audit: 2026-09-06.

This is Phase 1 of `COSMOSWEB_D2F_SURVEY_PROCESSED_INPUT_PROVENANCE_PROTOCOL.md`. No survey pixel data were downloaded or modified.

## Frozen literal contributors

The exact release contributors at the Gate-D anchor remain:

- `jw01727084001_04101_00001_nrcalong_jhat_a3001_crf.fits`
- `jw01727084001_04101_00003_nrcalong_jhat_a3001_crf.fits`
- `jw01727084001_04101_00002_nrcalong_jhat_a3001_crf.fits`
- `jw01727084001_04101_00004_nrcalong_jhat_a3001_crf.fits`

These identities come from the released A1 mosaic `CON`+`HDRTAB`; they are not inferred from filename similarity.

## Authoritative public-release audit

The official COSMOS-Web DR1 NIRCam page (`https://cosmos2025.iap.fr/nircam.html`) publishes, for NIRCam, the final per-filter/per-tile `i2d` mosaics plus extracted `SCI`, `ERR`, and `WHT` files at 30 and 60 mas. Its published product/download tables do not list individual survey-processed `*_crf.fits` or `*_jhat_a3001_crf.fits` inputs.

The COSMOS public release page (`https://cosmos.astro.caltech.edu/page/cosmosweb-dr`) likewise describes DR1 as complete NIRCam/MIRI mosaics and catalog products, with a single `i2d` per filter/tile and separate `SCI`, `ERR`, and `WHT` extensions. It identifies the NIRCam data-reduction lead as Maximilien Franco for release questions.

Exact-name web searches restricted to the authoritative COSMOS/Caltech/STScI surfaces returned no public hit for any of the four frozen `*_jhat_a3001_crf.fits` filenames.

This supports only the narrow conclusion:

`literal_crf_found_in_audited_public_dr1_distribution = false`

It does **not** prove that the files do not exist on team/internal storage or cannot be provided by the data-reduction team.

## Reduction-paper context

Franco et al. (2025), arXiv:2506.03256, explicitly describes survey processing in which JHAT-aligned images are used for outlier rejection, background removal is performed in the `*crf.fits` files immediately before resampling, and overlapping `*crf.fits` images are selected into an ASN for each final tile resampling.

Therefore the D2c `*_jhat_a3001_crf.fits` identities represent a custom survey-processing state that should not be silently collapsed to the public archive Stage-2 products.

## Archive comparison

D2a already established public MAST `_cal` candidate exposure roots near the frozen anchor, including the same underlying exposure numbers. Those products remain useful for archive provenance, but:

`related_mast_cal_is_literal_cosmosweb_crf = false`

No D2f scientific conclusion is allowed to substitute a related `_cal.fits` product for one of the exact D2c `*_jhat_a3001_crf.fits` inputs and call that a literal release replay.

## Why the CRF distinction matters

JWST documentation establishes that calibrated imaging products can contain `SCI`, `ERR`, `DQ`, `VAR_POISSON`, `VAR_RNOISE`, `VAR_FLAT`, optional `AREA`, and ASDF metadata, and that photometric calibration transforms calibrated science to surface-brightness units. JWST outlier detection can update DQ and set flagged locations in SCI/ERR/variance arrays to NaN.

Those generic semantics tell us what to inspect **if the literal CRFs are obtained**; they do not establish that the custom COSMOS-Web CRFs retain an invertible detector/source-count boundary for a new injected source.

## Scientific decision

`source_shot_realization_permitted = false`

Current blockers are now narrower:

1. the four exact survey-processed `*_jhat_a3001_crf.fits` inputs are not exposed in the audited public DR1 product surfaces;
2. their actual extension/header/calibration/count/variance content therefore cannot yet be audited directly;
3. the final-resample kernel is still not explicitly established by D2d/D2e.

The next non-redundant action is to obtain authoritative access information for the four literal CRFs—preferably from the COSMOS-Web NIRCam reduction lead or an official team data location—before any pixel-level D2f audit. If they cannot be made available, the literal source-shot replay remains scientifically non-identifiable and Gate D should preserve that negative result rather than replacing it with an approximate `_cal`-based replay.

## Mutation audit

- science pixels modified: `false`
- ERR modified: `false`
- WHT modified: `false`
- variance planes modified: `false`
- source-shot noise generated: `false`
- background/sky noise added: `false`
- PSF sharpening applied: `false`
- Tolman factor applied: `false`
