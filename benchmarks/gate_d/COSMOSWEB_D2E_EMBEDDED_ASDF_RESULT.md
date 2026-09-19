# Gate D2e — embedded-ASDF provenance audit result

Status: **PARTIAL HISTORICAL RESAMPLING PROVENANCE GAIN / FINAL KERNEL STILL UNKNOWN / SOURCE-SHOT REALIZATION STILL BLOCKED**

This receipt records the read-only local D2e audit of the embedded `ASDF_METADATA` payload in the authoritative COSMOS-Web DR1 F444W 30-mas A1 `i2d` product. It is metadata/provenance evidence only. No science, error, weight, or variance array was modified and no stochastic realization was generated.

## Frozen protocol and implementation

- Protocol: `benchmarks/gate_d/COSMOSWEB_D2E_EMBEDDED_ASDF_PROTOCOL.md`
- Audit script: `scripts/audit_gate_d_cosmosweb_embedded_asdf.py`
- Frozen release product: `mosaic_nircam_f444w_COSMOS-Web_30mas_A1_v1.0_i2d.fits.gz`
- Frozen anchor provenance from D2c: input rows `[45, 46, 70, 77]`, OBS 084 NRCALONG F444W exposures 1–4.
- D2d FITS-level values remain authoritative: `RESWHT=ivm`, `PIXFRAC=1.0`, `PXSCLRT=0.4750281915826499`, `NDRIZ=62`.

D2e read only the one-row `ASDF` extension payload and parsed the embedded YAML metadata without invoking the broader `stdatamodels` FITS-array mapping path.

## Payload identity

- `ASDF_METADATA` payload size: `37723` bytes
- SHA256: `58bd874a47a96aca306dab3a71add5645b7da9e7f6b98e1d15b7929e8438558e`

The payload identity is recorded so later interpretation can be checked against the same immutable metadata bytes without treating a later software default as historical evidence.

## Explicit historical metadata recovered

The embedded release metadata explicitly records:

- `meta.ref_file.drizpars.name = crds://jwst_nircam_drizpars_0001.fits`
- `meta.resample.pixel_scale_ratio = 0.4750281915826499`
- `meta.resample.pixfrac = 1.0`
- `meta.resample.pointings = 62`
- `meta.resample.weight_type = ivm`

These values independently reinforce the release-level D2d evidence for the historical resampling configuration and establish the exact DRIZPARS reference-file identity recorded in the product.

The DRIZPARS reference name is **provenance, not permission to substitute its contents for the runtime configuration**. D2e does not assume that any current/default value in that reference file, or in a modern JWST pipeline, was necessarily the effective historical final-resample value unless the released product explicitly records the parameter or a separate replay audit proves it.

## Final-resample kernel decision

No explicit final-resample kernel value is established by the embedded ASDF metadata under the frozen D2e decision rule.

`final_resample_kernel_established = false`

A software-only candidate-classification defect was identified after the local audit: the helper could count a parent `meta.resample` mapping as a kernel candidate merely because its preview contained a nested `kernel` field. Commit `07e45bb7121404e61da2e1af0d351e93c67e1a2e` restricts candidate classification to an actual `kernel` key in a resample/drizzle context. This does not change any extracted ASDF bytes or explicit metadata values; it formalizes the scientific rule that a parent mapping or generic token is not evidence for the historical final drizzle kernel.

The captured real-product evidence contains no qualifying explicit final-resample kernel value after applying that rule. Therefore D2e does **not** promote `square`, or any other kernel, from JWST defaults, reference-file expectations, or the separate outlier-rejection configuration.

## Source-shot decision

`source_shot_realization_permitted = false`

D2e closes useful operator provenance—weight type, pixfrac, pixel-scale ratio, pointings count, and DRIZPARS reference identity—but it does not close the remaining literal pre-resample calibration/count/variance provenance needed for a defensible exposure-space source-shot realization. The final resampling kernel also remains unestablished from release-recorded explicit metadata.

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

Proceed to D2f: audit the four exact survey-processed pre-resample contributors identified by D2c—`*_jhat_a3001_crf.fits`—for authoritative availability and calibration/count/variance provenance. The first question is not to generate noise, but to establish whether the literal survey-processed files can be obtained and whether their headers/data-model metadata retain enough information to reconstruct the detector/exposure source-count boundary without equating them to archive `_cal.fits` products. Any missing provenance must remain missing rather than being replaced by a default or an approximate output-pixel Poisson model.
