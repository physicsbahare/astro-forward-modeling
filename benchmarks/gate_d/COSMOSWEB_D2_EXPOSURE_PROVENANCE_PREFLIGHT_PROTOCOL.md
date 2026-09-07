# Gate D2a — exposure-level archive/provenance feasibility preflight

## Purpose

Determine whether a **literal COSMOS-Web DR1 F444W exposure-level source-shot experiment** can be specified from public provenance at the frozen Gate-D sky position before any stochastic source realization is generated.

This is a provenance/feasibility audit only. It does **not** download science pixels, inject a source, draw Poisson noise, alter SCI/ERR/WHT, fit morphology, change target bounds, or define a recovery tolerance. A negative provenance decision is a scientific result, not a workflow failure.

## Frozen sky point and scope

Use the same reproducible anchor as D1b:

- COSMOS2025 object ID 4204;
- ICRS `(RA, Dec) = (149.8671500, 2.1294010) deg`;
- COSMOS-Web DR1 tile A1;
- JWST/NIRCam F444W;
- program 1727;
- MAST positional query radius: `1 arcsec` around the frozen anchor.

This D2a query audits one fixed point only. It is a minimal feasibility check and does not establish contributor membership for the entire 512 x 512 D1 cutout.

## Software/documentation basis frozen before execution

Use maintained/public interfaces rather than a custom archive scraper:

- `astroquery.mast.Observations` with stable `astroquery==0.4.11` for the live archive query. The maintained API distinguishes MAST `obsid` from mission `obs_id`, and `get_unique_product_list` de-duplicates products by `dataURI`: https://astroquery.readthedocs.io/en/latest/mast/mast_obsquery.html
- JWST `calwebb_image3` combines one or more calibrated `_cal` exposures via a Stage-3 association and produces the resampled `_i2d` product: https://jwst-pipeline.readthedocs.io/en/stable/jwst/pipeline/calwebb_image3.html
- JWST associations explicitly encode product members through `expname`/`exptype`: https://jwst-pipeline.readthedocs.io/en/latest/jwst/associations/asn_from_list.html
- JWST resampling has configuration-dependent `pixfrac`, `kernel`, `weight_type`, output WCS/pixel scale, and propagates variance components; these settings cannot be replaced by one universal covariance factor: https://jwst-pipeline.readthedocs.io/en/latest/jwst/resample/
- COSMOS-Web DR1 states that the NIRCam reduction used JWST pipeline 1.14.0 with CRDS pmap 1223 and publishes final tile mosaics. The full `_i2d` products contain `SCI`, `ERR`, `CON`, `WHT`, `VAR_POISSON`, `VAR_RNOISE`, and `VAR_FLAT`; the lightweight extension products contain only selected planes: https://cosmos2025.iap.fr/nircam.html
- Franco et al. describe additional survey-specific processing, JHAT astrometric calibration, custom background treatment, construction of visit/tile association files, and final resampling of selected `*_crf.fits` inputs. Archive `_cal` candidates are therefore **not automatically identical to the literal pre-resample COSMOS-Web DR1 inputs**: https://arxiv.org/abs/2506.03256

The current maintained JWST pipeline may differ from the historical 1.14.0 reduction. Current defaults must not be substituted for an unrecovered historical COSMOS-Web configuration.

## Live archive query

Query MAST with all of the following:

- `obs_collection = JWST`;
- `proposal_id = 1727`;
- `instrument_name = NIRCAM*`;
- `filters = F444W`;
- `dataproduct_type = image`;
- `dataRights = PUBLIC`;
- the frozen coordinate and 1-arcsec radius.

Retrieve products through `Observations.get_unique_product_list`, then identify public calibrated-exposure candidates only when `productSubGroupDescription == CAL` or the product filename ends in `_cal.fits`.

Record candidate filenames, `dataURI`, MAST identifiers, calibration level, size, and the observation metadata needed to reproduce the query. These are **archive candidates**, not verified COSMOS-Web DR1 contributors.

## Literal-release provenance requirements fixed before execution

D2a may authorize a later stochastic exposure-level protocol only if all of the following are independently established, not inferred from archive proximity:

1. at least one public F444W `_cal` archive candidate is found at the frozen point;
2. the exact COSMOS-Web DR1 Stage-3 association membership for the relevant tile/point is available, so contributing exposure roots can be enumerated;
3. the literal survey-specific pre-resample inputs (`*_crf.fits`, or a reproducible documented transform from public `_cal` inputs to those exact files) are available;
4. actual contributing calibrated files have been inspected for the calibration/count-conversion and variance provenance needed for a source-only perturbation, including `VAR_POISSON`, `VAR_RNOISE`, and `VAR_FLAT` where applicable;
5. the exact historical resampling configuration needed to replay the DR1 30-mas tile is available, including association/output WCS geometry and configuration-dependent drizzle settings/weighting;
6. the replay is tied to the COSMOS-Web 1.14.0 / CRDS-1223 processing provenance rather than silently substituting current pipeline defaults.

Public documentation presently establishes some global release facts (pipeline version, CRDS context, tile geometry, custom processing description) but is **not treated as a machine-readable exact ASN, exact per-exposure processing manifest, or complete resampling configuration**. D2a therefore records those missing evidence classes explicitly.

## Interpretation rule

- Finding MAST `_cal` candidates proves only that plausible public exposure-level archive products exist near the frozen sky point.
- Spatial overlap, matching program/filter, or a matching exposure root is not sufficient to call an exposure a literal DR1 contributor without the release association/provenance chain.
- A current JWST `Image3Pipeline` rerun from archive `_cal` files is a **standard-pipeline reprocessing bracket**, not literal COSMOS-Web reproduction, unless exact survey-specific transformations and historical configuration are recovered.
- If any literal-release provenance requirement remains unresolved, `source_shot_realization_permitted` must be `false`. Do not generate source-shot noise, do not modify the L1 mosaic, and do not infer the missing provenance from final `ERR`/`WHT`.

No criterion in this protocol is a post-hoc morphology acceptance band, and this preflight cannot close Gate D or authorize production implementation.
