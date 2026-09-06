# Gate D2d — release-recorded resampling metadata audit

## Purpose

Use the already-authoritative local COSMOS-Web DR1 F444W 30-mas A1 `i2d` product to determine which historical resampling parameters are **explicitly recorded by the release product** and which remain absent. This is a read-only provenance audit following D2c; it is not a replay and not a stochastic injection.

D2d must not infer an absent historical parameter from a modern/default JWST value.

## Frozen evidence before execution

The JWST 1.14.1 imaging `ResampleStep`/`ResampleData` implementation records several resampling quantities in output data-model metadata:

- `meta.resample.pointings` -> FITS `NDRIZ`;
- `meta.resample.weight_type` -> FITS `RESWHT`;
- `meta.resample.pixfrac` -> FITS `PIXFRAC`;
- `meta.resample.pixel_scale_ratio` -> FITS `PXSCLRT`.

The 1.14.1 implementation uses separate runtime parameters for `kernel`, `fillval`, `weight_type`, `pixfrac`, output WCS/scale and good-bit handling. The output schema does not establish that every runtime parameter, especially the drizzle kernel, is preserved in the final product.

Franco et al. describe COSMOS-Web final tile construction with the JWST Stage-3 Resample routine using overlapping survey-processed `*crf.fits` images in an ASN and a fixed COSMOS tangent point. The paper explicitly reports `pixfrac=1` and `kernel='square'` for the preceding outlier-rejection configuration; D2d must **not** silently transfer that kernel statement to the final mosaic resampling step unless release/product evidence independently supports it.

## Frozen target/product

Use the same D2c product and anchor:

- tile A1;
- F444W;
- 30 mas;
- RA=`149.8671500 deg`, Dec=`2.1294010 deg`;
- D2c pixel contributors `[45, 46, 70, 77]`.

The absolute local path is runtime-only and must not be committed as portable scientific provenance.

## Required audit

Record without loading/modifying science arrays beyond what is required to open metadata:

1. primary-header values for `NDRIZ`, `RESWHT`, `PIXFRAC`, `PXSCLRT`, `S_RESAMP`, `ASNTABLE`, `CAL_VER`, `CRDS_VER`, `CRDS_CTX`, and WCS scale/orientation cards when present;
2. for D2c contributor rows 45, 46, 70 and 77, record `FILENAME`, `R_DRZPAR`, `R_RESAMP`, `CAL_VER`, `CRDS_CTX`, and `S_RESAMP` when present;
3. report whether all four contributors share the same drizzle/resample reference provenance;
4. inventory the ASDF extension structurally if it can be done read-only with installed maintained libraries, but do not require a new heavy dependency merely to make the audit pass;
5. search ASDF/FITS metadata for explicit historical values or names corresponding to `kernel`, `weight_type`, `pixfrac`, pixel-scale ratio, output WCS/shape and association identity;
6. explicitly list parameters that remain absent.

## Decision rules

- A historical parameter is `established` only when it is explicitly recorded by the release product or independently stated for the **final resampling step** by release-authoritative documentation.
- A current/default JWST value is never sufficient by itself.
- A `R_DRZPAR` reference filename is provenance evidence, but it does not prove that no runtime override was supplied.
- The outlier-rejection `kernel='square'` reported by Franco et al. is not automatically the final mosaic resample kernel.
- `source_shot_realization_permitted` remains `false` unless the complete replay requirements, including literal pre-resample calibration/count/variance provenance, are independently closed.

## Mutation audit

D2d must record all of the following as false:

- SCI/ERR/WHT/variance modification;
- source-shot generation;
- added background/sky noise;
- PSF sharpening;
- Tolman application.

A negative/partial result is scientific provenance evidence, not workflow failure.
