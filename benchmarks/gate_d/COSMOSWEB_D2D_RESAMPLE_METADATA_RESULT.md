# COSMOS-Web Gate D2d release-recorded resampling metadata audit — result

Status: **PARTIAL RESAMPLING OPERATOR RECOVERED / FINAL KERNEL STILL UNKNOWN / SOURCE-SHOT REALIZATION STILL BLOCKED**

This receipt records the local read-only execution of the frozen D2d protocol against the authoritative COSMOS-Web DR1 F444W 30-mas A1 `i2d` mosaic. No science/variance/weight array was modified and no stochastic realization was generated.

## Frozen protocol and software provenance

- Protocol: `benchmarks/gate_d/COSMOSWEB_D2D_RESAMPLE_METADATA_PROTOCOL.md`
- Local product: `mosaic_nircam_f444w_COSMOS-Web_30mas_A1_v1.0_i2d.fits.gz`
- Frozen D2c contributor rows: `[45, 46, 70, 77]`
- D2d script after the ASDF-HDU compatibility repair: commit `208fe1e1c575dd86962972097bed269a77f7935c`
- Missing-FITS-value normalization repair: commit `22a3c9c31a4b69097332ba9b7f47005954954645`
- Regression test for that repair: commit `59c2de97652097aaa52688bc3b28790688b1b012`
- Verification-suite run `34026670632`: Python 3.11 and 3.12 jobs both completed successfully.

The local audit initially exposed absent `R_DRZPAR`/`R_RESAMP` cells as floating `NaN`. The first summary helper consequently treated the four NaNs as distinct values. This was a software serialization/bookkeeping defect only: the raw HDRTAB rows themselves already showed the fields were absent. The corrected code serializes non-finite FITS placeholders as JSON `null`, refuses non-standard JSON `NaN`, and distinguishes “not recorded for all contributors” from “all contributors share one recorded value”. No scientific threshold, acceptance criterion, or FITS evidence changed.

## Release-recorded final-resample quantities

The authoritative output primary header explicitly records:

- `S_RESAMP = COMPLETE`
- `NDRIZ = 62`
- `RESWHT = ivm`
- `PIXFRAC = 1.0`
- `PXSCLRT = 0.4750281915826499`
- `ASNTABLE = mosaic_nircam_f444w_COSMOS-Web_30mas_A1_v0_8_asn.json`
- `CAL_VER = 1.14.1.dev1+g415de86`
- `CRDS_CTX = jwst_1223.pmap`

Therefore D2d establishes directly from the release product that the final resampling used inverse-variance weighting (`ivm`), `pixfrac=1.0`, the recorded pixel-scale ratio `0.4750281915826499`, and `NDRIZ=62` as the output product's recorded resampling group/pointing count.

These are historical product values, not values copied from current/default JWST settings.

## Contributor-level resample/reference provenance

For the four D2c contributors:

- rows 45, 46, 70 and 77 each identify the same OBS 084 / NRCALONG release inputs established in D2c;
- `S_RESAMP = SKIPPED` on every contributor row;
- `R_DRZPAR` is absent on every contributor row;
- `R_RESAMP` is absent on every contributor row;
- all four retain `CAL_VER = 1.14.1.dev1+g415de86` and `CRDS_CTX = jwst_1223.pmap`.

The absence of `R_DRZPAR`/`R_RESAMP` is evidence that those reference names are not preserved in these blended HDRTAB rows. It is **not** evidence that no drizzle reference file or runtime override was used historically.

The contributor `S_RESAMP=SKIPPED` values are consistent with these rows representing survey-processed pre-final-resample inputs rather than already-resampled final products, but the literal `*_jhat_a3001_crf.fits` files themselves and their calibration/count/variance boundary are still required before any exposure-space stochastic experiment.

## Final kernel status

No explicit `KERNEL`, `RESKERN`, or `DRIZKERN` card was found in the audited final-product FITS header metadata.

`final_resample_kernel_established = false`.

The JWST 1.14.1 software default and the `kernel='square'` configuration documented for COSMOS-Web outlier rejection are **not** promoted to historical final-resample evidence. The final mosaic kernel therefore remains unknown at D2d.

## ASDF status

The product contains an `ASDF` extension represented by Astropy as a one-row `BinTableHDU` with column:

`ASDF_METADATA`

D2d inventories this extension structurally only. The embedded ASDF tree was not parsed in this run, so it remains a legitimate next provenance source for any final-kernel/output-WCS/operator metadata not exposed as FITS cards.

## Scientific consequence

D2d closes three important pieces of the historical final-resample operator that were previously only partially known:

1. `weight_type = ivm`;
2. `pixfrac = 1.0`;
3. `pixel_scale_ratio = 0.4750281915826499`.

It also preserves `NDRIZ=62` and the exact output ASN identity.

However:

`source_shot_realization_permitted = false`.

The remaining blocking requirements are:

1. literal survey-processed `*_jhat_a3001_crf.fits` input files with defensible calibration/count provenance;
2. variance/count provenance for those literal contributing pre-resample inputs;
3. any still-absent historical final-resampling parameters, especially the final drizzle kernel, unless recovered from embedded release metadata or release-authoritative documentation.

## Mutation audit

- science pixels modified: `false`
- ERR modified: `false`
- WHT modified: `false`
- variance planes modified: `false`
- source-shot noise generated: `false`
- background/sky noise added: `false`
- PSF sharpening applied: `false`
- Tolman factor applied: `false`

## Next non-redundant decision

Perform a separate **D2e embedded-ASDF provenance audit** in an isolated, historically compatible metadata environment. JWST 1.14.1 declared `asdf>=3.1,<4` and `stdatamodels>=1.10.1,<1.11`, and `stdatamodels.asdf_in_fits.open` is the maintained interface for reading ASDF embedded in FITS. D2e should inspect metadata only and must not load or modify SCI/ERR/WHT/variance arrays. Search specifically for resample kernel, weight type, pixfrac, pixel-scale ratio, output WCS/shape and ASN metadata. If a parameter is absent from the embedded tree, it remains unknown rather than being filled from a software default.
