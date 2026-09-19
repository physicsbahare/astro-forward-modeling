# COSMOS-Web Gate D2b authoritative release-provenance audit — result

Status: **PARTIAL PROVENANCE GAIN / SOURCE-SHOT REALIZATION STILL BLOCKED**

This receipt records a documentation/provenance audit only. It is not a stochastic experiment and does not modify science data.

## Frozen protocol

Protocol commit: `e088588e097169637b5fdbbc8a8cc7f2e226426e`.

## Release-authoritative findings

The COSMOS-Web DR1 NIRCam release page establishes the following for the frozen Gate-D position:

- the anchor lies inside release tile **A1**;
- the NIRCam reduction used STScI JWST pipeline **1.14.0** and CRDS **pmap 1223**;
- all tiles share the declared tangent point `CRVAL1=150.1163213`, `CRVAL2=2.200973097`;
- the frozen product family is available at **30 mas** and **60 mas** pixel scales;
- full release `*_i2d.fits` files are public and contain `SCI`, `ERR`, `CON`, `WHT`, `VAR_POISSON`, `VAR_RNOISE`, and `VAR_FLAT` extensions;
- separately extracted `SCI`, `ERR`, and `WHT` files are convenience products, explaining why the frozen compact L1 bundle used in D1o did not contain the variance extensions;
- the release reduction integrated survey-specific code and astrometric processing beyond an untouched stock-pipeline invocation.

Franco et al. (2025) independently documents that COSMOS-Web combined the official JWST calibration pipeline with custom noise removal, background subtraction, astrometric alignment, visit/tile construction, and final mosaic production over 20 tiles. This confirms that current/default JWST resample settings cannot be assumed to be the historical release operator without release-specific evidence.

STScI imaging-resample documentation shows that resampling choices such as pixfrac, weighting and output-WCS/scale are operator parameters and that resample metadata can be recorded in products. That documentation defines semantics only; it does not prove which historical values COSMOS-Web used.

## Four-question assessment

1. **Exact release association membership:** `not proven`.
   - The release page identifies tile A1 and the public mosaic product, but it does not publish the exact contributing exposure/product membership at the frozen position.
   - The eight D2a `_cal` roots therefore remain archive candidates, not literal release members.

2. **Literal pre-resample inputs:** `not proven`.
   - Public release documentation does not provide the exact selected `*_crf.fits`/equivalent input list or a replayable mapping from public `_cal` products through every custom step to the final resample inputs.

3. **Actual contributing variance/count provenance:** `partially proven`.
   - The full A1 `i2d` product publicly contains propagated `VAR_POISSON`, `VAR_RNOISE`, and `VAR_FLAT` arrays, which closes the earlier statement that the *release itself* lacks such output variance products.
   - It does **not** provide the literal detector/exposure-space count provenance required to generate physically exact source-shot realizations for the actual contributors.

4. **Exact historical resampling configuration:** `not proven`.
   - Pipeline version, CRDS context, final scale and tangent point are known.
   - Release-authoritative evidence inspected here does not establish the complete historical kernel/pixfrac/weighting/custom association and resampling configuration needed for replay.

## Scientific outcome

`source_shot_realization_permitted = false`.

The new information is scientifically useful because it separates two distinct statements:

- **D1o remains correct for the immutable compact L1 cutout**: that bundle contains only SCI/ERR/WHT and cannot identify source-shot covariance.
- **The complete public DR1 i2d product is richer than that cutout**: it includes propagated variance extensions, but this still does not reconstruct the literal exposure-space stochastic history or exact contributor/operator provenance.

No acceptance criterion is relaxed and no post-hoc band is introduced.

## Mutations

- science pixels downloaded: `false`
- source-shot noise generated: `false`
- background noise added: `false`
- SCI modified: `false`
- ERR modified: `false`
- WHT modified: `false`
- Tolman factor applied: `false`
- PSF sharpening applied: `false`

## Next non-redundant scientific decision

Before any source-shot experiment, perform a **header/provenance-only audit of the authoritative A1 F444W 30-mas full i2d product and any release-side association metadata that can be retrieved without downloading science arrays**. Specifically test whether the product exposes historical resample metadata and association identifiers sufficient to close any of questions 1, 2, or 4.

If the full product/header still cannot identify literal contributors and replayable custom resampling, Gate D should remain scientifically blocked at this line rather than infer the missing provenance.
