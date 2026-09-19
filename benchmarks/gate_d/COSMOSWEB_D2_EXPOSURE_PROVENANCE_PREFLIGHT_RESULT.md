# COSMOS-Web Gate D2a exposure-provenance preflight — result

Status: **SCIENTIFIC PREFLIGHT BLOCKED / SOFTWARE EXECUTION PASS**

This receipt is immutable evidence for the frozen Gate D2a protocol. It records what was actually established by the successful GitHub Actions run and must not be interpreted as permission to synthesize source-shot noise.

## Frozen execution

- Workflow: `gate-d-cosmosweb-exposure-provenance-preflight`
- Run: `34019270052`
- Job: `101448836383`
- Branch commit: `bc6a2598f33b2a4a24074a73ebc8c09f03858d3a`
- Artifact: `9984963008` (`gate-d-cosmosweb-exposure-provenance-preflight`)
- Artifact SHA256 reported by `actions/upload-artifact`: `ba6c697f892a7715b046926b9ae217370d4adbe69fb4e4565013d1d1e4b4ac05`
- Runtime audit dependency: `astroquery==0.4.11`
- Unit tests: `5 passed`

The run completed successfully as software. That is not the scientific acceptance condition.

## Frozen archive query

The metadata-only query used the Gate-D anchor and did not download science pixels:

- RA = `149.8671500 deg`
- Dec = `2.1294010 deg`
- radius = `1.0 arcsec`
- JWST proposal = `1727`
- instrument = `NIRCAM*`
- filter = `F444W`
- data rights = `PUBLIC`

MAST returned one observation row and 126 unique product rows. Eight `_cal` candidate rows, corresponding to eight distinct exposure roots, were identified:

1. `jw01727084001_04101_00001_nrcalong`
2. `jw01727084001_04101_00001_nrcblong`
3. `jw01727084001_04101_00002_nrcalong`
4. `jw01727084001_04101_00002_nrcblong`
5. `jw01727084001_04101_00003_nrcalong`
6. `jw01727084001_04101_00003_nrcblong`
7. `jw01727084001_04101_00004_nrcalong`
8. `jw01727084001_04101_00004_nrcblong`

These are **archive candidates only**. Their presence near the anchor does not establish that they are the exact inputs used in the released COSMOS-Web DR1 mosaic.

## Scientific assessment

`source_shot_realization_permitted = false`.

The audit found archive `_cal` candidates, and the historical COSMOS-Web release provenance declares pipeline `1.14.0`, CRDS pmap `1223`, a 30-mas final scale, and survey-specific processing. However, four frozen requirements were not demonstrated by the available evidence:

- exact COSMOS-Web release association membership;
- literal release pre-resample inputs (or an exact, replayable transform to the selected `*_crf.fits` inputs);
- variance/count provenance for the actual contributing calibrated exposures;
- exact historical resampling/drizzle configuration used for the release product.

Therefore the scientific outcome is:

`archive_cal_candidates_found_but_literal_release_provenance_incomplete`

Finding plausible `_cal` products is insufficient to propagate a literal source-shot perturbation into the final mosaic without inventing unverified membership, calibration, or covariance assumptions.

## Mutation audit

This preflight was metadata/provenance-only. It performed none of the following:

- science-pixel download;
- SCI modification;
- ERR/WHT modification;
- source-shot-noise generation;
- background-noise addition;
- PSF sharpening;
- Tolman-factor application.

## Consequence for Gate D

Do **not** synthesize independent-pixel Poisson noise directly on the final mosaic, infer a literal source-shot component from final `ERR`, re-add existing sky/background noise, or modify `ERR/WHT`.

The next non-redundant step is a release-membership/resampling-provenance audit: locate authoritative COSMOS-Web association/reduction provenance for the exact tile/region and determine whether the selected contributing exposure set plus the release resampling operator can be reproduced without inference. Only if that audit closes the four missing requirements may a detector/exposure-space source-shot realization be designed.
