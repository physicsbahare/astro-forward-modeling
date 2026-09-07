# COSMOS-Web Gate D2c local full-mosaic pixel-level provenance audit — result

Status: **PIXEL-LEVEL RELEASE MEMBERSHIP ESTABLISHED / SOURCE-SHOT REALIZATION STILL BLOCKED**

This receipt records the read-only local execution of the frozen D2c protocol against the authoritative full COSMOS-Web DR1 F444W 30-mas A1 `i2d` mosaic held on the workstation. It is provenance evidence only; no science array, variance array, or weight map was modified and no stochastic realization was generated.

## Frozen protocol and implementation

- Protocol: `benchmarks/gate_d/COSMOSWEB_D2C_LOCAL_MOSAIC_PIXEL_PROVENANCE_PROTOCOL.md`
- Audit script: `scripts/audit_gate_d_cosmosweb_local_mosaic_pixel_provenance.py`
- Script/protocol branch state before local execution included commit `4331e159f34d27b1f510946d8985b94854535375`.
- Frozen anchor: ICRS RA=`149.8671500 deg`, Dec=`2.1294010 deg`.

The workstation emitted only JSON/provenance metadata. The local absolute filesystem path is intentionally not treated as a portable scientific identifier.

## Product identity and release metadata

Local release product basename:

`mosaic_nircam_f444w_COSMOS-Web_30mas_A1_v1.0_i2d.fits.gz`

Recorded byte size: `9483260670`.

Internal primary-header provenance:

- `FILENAME = mosaic_nircam_f444w_COSMOS-Web_30mas_A1_v0_8_i2d.fits`
- `ASNTABLE = mosaic_nircam_f444w_COSMOS-Web_30mas_A1_v0_8_asn.json`
- `CAL_VER = 1.14.1.dev1+g415de86`
- `CRDS_VER = 11.17.19`
- `CRDS_CTX = jwst_1223.pmap`
- `S_RESAMP = COMPLETE`
- `NDRIZ = 62`
- `NEXPOSUR = 16`
- `PIXFRAC = 1.0`

The full product contains:

`PRIMARY, SCI, ERR, CON, WHT, VAR_POISSON, VAR_RNOISE, VAR_FLAT, HDRTAB, ASDF`.

This confirms that the complete release product is richer than the compact D1 L1 bundle and preserves both drizzle context and propagated variance planes.

## Anchor WCS and context result

The frozen sky coordinate maps to:

- floating-point zero-based pixel: `(x, y) = (2151.46029444984, 4801.968962825729)`;
- nearest zero-based pixel: `(2151, 4802)`;
- SCI shape: `(24910, 19200)`;
- CON shape: `(4, 24910, 19200)`;
- SCI value at the anchor: `4.898284435272217`.

Raw 32-bit drizzle-context values at that pixel were:

| CON plane | decimal | hexadecimal | set-bit implication |
|---:|---:|---:|---|
| 0 | 0 | `0x00000000` | none |
| 1 | 24576 | `0x00006000` | input indices 45, 46 |
| 2 | 8256 | `0x00002040` | input indices 70, 77 |
| 3 | 0 | `0x00000000` | none |

Using the frozen JWST context convention `input_index = 32*plane + bit`, the exact decoded zero-based input indices are:

`[45, 46, 70, 77]`.

All four indices are valid rows in the 104-row `HDRTAB` and each row carries an unambiguous survey-processed release input filename.

## Exact release inputs contributing at the anchor pixel

| HDRTAB/input index | exposure | detector | release input filename |
|---:|---:|---|---|
| 45 | 1 | NRCALONG | `jw01727084001_04101_00001_nrcalong_jhat_a3001_crf.fits` |
| 46 | 3 | NRCALONG | `jw01727084001_04101_00003_nrcalong_jhat_a3001_crf.fits` |
| 70 | 2 | NRCALONG | `jw01727084001_04101_00002_nrcalong_jhat_a3001_crf.fits` |
| 77 | 4 | NRCALONG | `jw01727084001_04101_00004_nrcalong_jhat_a3001_crf.fits` |

All four rows are:

- program `01727`;
- observation `084`;
- visit `001`;
- visit group `04`;
- detector `NRCALONG`;
- filter `F444W`;
- pupil `CLEAR`;
- observation date `2023-04-09`.

Therefore the earlier D2a archive query's eight nearby `_cal` roots were correctly treated only as candidates. At the literal Gate-D anchor pixel the released mosaic itself identifies four contributing survey-processed `NRCALONG` `*_jhat_a3001_crf.fits` inputs, not all eight archive-nearby A/B-long candidates.

## Scientific decision

`pixel_level_release_membership_established = true`.

This closes the **exact release membership at the single frozen anchor pixel**. It does not claim the same contributor set for every pixel in the 512x512 Gate-D cutout or for the whole A1 tile.

`source_shot_realization_permitted = false`.

Three requirements remain before a literal exposure-space source-shot experiment is defensible:

1. the literal survey-processed pre-resample input files must be available and their calibration/count boundary established;
2. the exact historical resampling kernel/weighting/operator configuration must be replayable rather than inferred from defaults;
3. variance/count provenance must be available for the literal contributing pre-resample inputs.

The `*_jhat_a3001_crf.fits` identities are release-level input identities. This receipt does not equate them with public archive `_cal.fits` products and does not infer the custom JHAT processing path.

## Mutation audit

- science pixels modified: `false`
- ERR modified: `false`
- WHT modified: `false`
- variance planes modified: `false`
- source-shot noise generated: `false`
- background noise added: `false`
- PSF sharpening applied: `false`
- Tolman factor applied: `false`

## Next non-redundant decision

Audit the same product for release-recorded resampling metadata that was not yet included in D2c output, especially `RESWHT` and `PXSCLRT`, and inspect `HDRTAB` drizzle-reference provenance plus the ASDF metadata tree without reading or modifying science arrays. Historical values recorded by the product may be accepted as evidence; absent values must remain unknown rather than being filled from current/default JWST settings.
