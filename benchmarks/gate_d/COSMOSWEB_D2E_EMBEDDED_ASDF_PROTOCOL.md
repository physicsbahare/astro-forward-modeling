# Gate D2e — embedded-ASDF provenance audit

## Purpose

Interrogate the embedded `ASDF_METADATA` payload in the authoritative COSMOS-Web DR1 F444W 30-mas A1 `i2d` product for historical resampling provenance that is not exposed as ordinary FITS cards. D2e is a read-only metadata audit following D2d. It is not a replay, not a stochastic injection, and not a production implementation.

D2e must not infer any absent historical parameter from current/default JWST software behavior.

## Frozen evidence before execution

D2c established exact release membership at the frozen anchor pixel: HDRTAB/input rows `[45, 46, 70, 77]`, corresponding to OBS 084 NRCALONG F444W exposures 1–4.

D2d established directly from the released mosaic:

- `RESWHT = ivm`;
- `PIXFRAC = 1.0`;
- `PXSCLRT = 0.4750281915826499`;
- `NDRIZ = 62`;
- final `S_RESAMP = COMPLETE`;
- no explicit FITS `KERNEL`, `RESKERN`, or `DRIZKERN` card;
- contributor `R_DRZPAR` and `R_RESAMP` are absent in the four relevant HDRTAB rows;
- `source_shot_realization_permitted = false`.

The product contains a one-row `ASDF` binary-table HDU with column `ASDF_METADATA`.

## Historical-software reading rule

JWST 1.14.1 declared `asdf>=3.1,<4`, while `stdatamodels==1.10.1` provides the historical ASDF-in-FITS support code. However, the historical `stdatamodels.fits_support.from_fits_asdf()` path calls `_map_hdulist_to_arrays()`, which dereferences FITS-backed array nodes through `hdulist[pair].data`. That is broader than the metadata-only D2e requirement and can touch SCI/ERR/WHT/variance arrays.

Therefore D2e must **not** use the full `stdatamodels.asdf_in_fits.open()`/`from_fits_asdf()` mapping path on the 8.9-GB product. Instead:

1. open the FITS lazily;
2. read only the `ASDF` extension's `ASDF_METADATA` uint8 payload;
3. parse only the YAML portion with the maintained ASDF `asdf.util.load_yaml` interface (ASDF 3.1.x), which does not map external FITS array blocks;
4. search the resulting basic YAML tree plus the raw YAML text for explicit provenance fields.

This restriction is scientific provenance protection, not a performance shortcut.

## Required audit

Record:

1. ASDF payload byte count and SHA256;
2. ASDF/YAML version header lines when present;
3. top-level YAML keys;
4. explicit matched paths/values for keys or scalar metadata containing:
   - `kernel` / drizzle-kernel equivalents;
   - `resample` / `driz`;
   - `weight_type` / `RESWHT` equivalents;
   - `pixfrac`;
   - `pixel_scale_ratio` / output pixel scale;
   - `output_shape`, `array_shape`, `pixel_shape`;
   - association / ASN identity;
   - resample/drizpars reference names;
5. raw YAML line hits for the same terms, so tag/path interpretation can be independently checked;
6. whether any explicit final-resample kernel is actually present in a resampling/provenance context.

## Decision rules

- D2e may confirm a historical value only if the embedded release metadata explicitly records it.
- A generic `kernel` token is not sufficient unless its path/context identifies the final drizzle/resample operator.
- WCS interpolation kernels, transform kernels, software defaults, or unrelated algorithmic kernels must not be promoted to the final drizzle kernel.
- D2d FITS values remain authoritative even if duplicated in ASDF.
- Absence from the ASDF YAML tree means “not recorded here”, not “historically unused”.
- `source_shot_realization_permitted` remains `false` unless the remaining literal pre-resample calibration/count/variance provenance and all replay-critical operator settings are independently closed.

## Mutation audit

D2e must record all of the following as false:

- SCI modified;
- ERR modified;
- WHT modified;
- variance planes modified;
- source-shot noise generated;
- background/sky noise added;
- PSF sharpening applied;
- Tolman factor applied.

A negative ASDF result is valid provenance evidence and must not be converted into a guessed parameter.