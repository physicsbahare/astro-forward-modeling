# Gate D2g — authoritative CRF access request packet

Status: **REQUEST PACKET PREPARED / NOT YET SENT / SOURCE-SHOT REALIZATION STILL BLOCKED**

Date prepared: 2026-09-06.

## Purpose

D2f established that the four literal COSMOS-Web survey-processed pre-resample contributors identified by the released A1 mosaic are not exposed on the audited public DR1 surfaces. D2g prepares the smallest authoritative access request needed to decide whether a literal exposure-space source-shot replay can ever be made scientifically defensible.

This packet is preparation only. It does not claim that any email has been sent, that the files have been shared, or that source-shot realization is permitted.

## Frozen scientific target

COSMOS-Web DR1 NIRCam F444W, 30 mas, tile A1, Gate-D anchor RA=149.8671500 deg, Dec=2.1294010 deg.

The released A1 `CON`+`HDRTAB` provenance identifies exactly these four survey-processed contributors at the anchor pixel:

1. `jw01727084001_04101_00001_nrcalong_jhat_a3001_crf.fits`
2. `jw01727084001_04101_00002_nrcalong_jhat_a3001_crf.fits`
3. `jw01727084001_04101_00003_nrcalong_jhat_a3001_crf.fits`
4. `jw01727084001_04101_00004_nrcalong_jhat_a3001_crf.fits`

They are OBS 084, NRCALONG, F444W, exposures 1–4. They must not be replaced by related public MAST `_cal.fits` products and still be called a literal COSMOS-Web replay.

## Current provenance already recovered

The released final mosaic records:

- JWST calibration software `1.14.1.dev1+g415de86`;
- CRDS context `jwst_1223.pmap`;
- final association identity `mosaic_nircam_f444w_COSMOS-Web_30mas_A1_v0_8_asn.json`;
- `weight_type = ivm`;
- `pixfrac = 1.0`;
- `pixel_scale_ratio = 0.4750281915826499`;
- `NDRIZ = 62`;
- DRIZPARS reference `crds://jwst_nircam_drizpars_0001.fits`.

The final-resample kernel is not explicitly established by the released FITS/embedded-ASDF metadata audited so far.

## Authoritative contact

The official COSMOS public release page identifies Maximilien Franco as the NIRCam data-reduction lead for DR1 questions and gives the contact address:

`maximilien.franco at cea dot fr`

Official source: `https://cosmos.astro.caltech.edu/page/cosmosweb-dr`

## Minimal information request

The request should ask only for the four frozen contributors, or for enough authoritative metadata to determine whether they can be scientifically replayed. Specifically request:

- whether the four exact `*_jhat_a3001_crf.fits` files can be shared or accessed from an official/team location;
- if full files cannot be shared, whether their primary/SCI/ERR/DQ/VAR_POISSON/VAR_RNOISE/VAR_FLAT/AREA/ASDF header+extension inventory can be provided;
- whether the CRF `SCI` values retain a reversible calibration path to source-electron/count expectation suitable for adding a new source Poisson realization without double counting existing variance;
- the effective final tile-resampling kernel used for the DR1 A1 F444W 30-mas mosaic, if it is known from the historical reduction configuration;
- optionally, the exact historical ASN/resample command/configuration corresponding to `mosaic_nircam_f444w_COSMOS-Web_30mas_A1_v0_8_asn.json` if available.

No broad request for the whole COSMOS-Web reduction tree or survey should be made.

## Sendable email draft

Subject: COSMOS-Web DR1 NIRCam provenance question for four A1 F444W CRF inputs

Dear Dr. Franco,

I am working on a validation study using the public COSMOS-Web DR1 NIRCam mosaics. From the released A1 F444W 30-mas `CON` and `HDRTAB` metadata, I traced one test position to four specific survey-processed inputs:

- `jw01727084001_04101_00001_nrcalong_jhat_a3001_crf.fits`
- `jw01727084001_04101_00002_nrcalong_jhat_a3001_crf.fits`
- `jw01727084001_04101_00003_nrcalong_jhat_a3001_crf.fits`
- `jw01727084001_04101_00004_nrcalong_jhat_a3001_crf.fits`

I am trying to determine whether an exposure-level injection/noise validation can be reproduced without substituting the public MAST `_cal.fits` products for these survey-processed CRFs.

Would it be possible to access these four exact CRF files, or alternatively to obtain their header/extension inventory and the historical final-resampling configuration used for the A1 F444W 30-mas mosaic? In particular, I am trying to establish the pre-resample variance/count provenance and the effective final drizzle kernel.

I only need these four contributors for this provenance check, not the full survey reduction products.

Thank you very much for any guidance.

Best regards,
Bahareh Soleimanpour Salmasi

## Decision rule after a reply

- If the exact CRFs become available, return to D2f Phase 2 and perform a metadata-only structure/calibration/variance audit before any science-array manipulation.
- If only related `_cal` files are available, preserve them as non-equivalent archival controls; do not relabel them as the literal release inputs.
- If the exact CRFs cannot be shared and no reversible calibration/variance boundary can be established, record literal source-shot replay as scientifically non-identifiable for this release path.
- If the historical final-resample kernel is supplied authoritatively, freeze it separately with provenance; do not infer it from a current/default JWST setting.

`source_shot_realization_permitted = false`

## Mutation audit

- science pixels modified: `false`
- ERR modified: `false`
- WHT modified: `false`
- variance planes modified: `false`
- source-shot noise generated: `false`
- background/sky noise added: `false`
- PSF sharpening applied: `false`
- Tolman factor applied: `false`
