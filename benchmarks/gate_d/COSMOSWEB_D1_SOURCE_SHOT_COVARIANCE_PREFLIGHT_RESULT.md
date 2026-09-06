# COSMOS-Web Gate D1o — L1 source-shot-noise / covariance identifiability result

## Immutable execution receipt

- source branch HEAD at execution: `4c0ec4d5caea6d22589f321ca2815b48c33b2d79`
- workflow: `gate-d-cosmosweb-source-shot-covariance-preflight`
- workflow run: `34017575982`
- workflow status/conclusion: `completed / success`
- artifact: `gate-d-cosmosweb-source-shot-covariance-preflight`
- artifact id: `9984396144`
- artifact digest: `sha256:37533c9d04ded3ddc97881c2916babf6273763d9b644d3fa5c19bb77bfbef0b6`
- audited real-cutout SHA-256: `764d542f2417810c904bce711455b3eb69c70cf388f97348cb857b056b2dd66d`

Workflow success means that the frozen representational audit executed successfully. It does **not** mean that physically exact L1 source-shot noise is available.

## Machine-readable artifact result

The actual `summary.json` reports:

- representation: `drizzled_mosaic`;
- image planes: `SCI`, `ERR`, `WHT`, each `512 x 512`;
- `SCI` unit: `MJy/sr`;
- `PIXAR_SR = 2.11539874851881e-14`;
- `PIXAR_A2 = 0.0009`;
- `PHOTMJSR = 0.3709999918937683`;
- `VAR_POISSON`: absent;
- `VAR_RNOISE`: absent;
- `VAR_FLAT`: absent;
- exposure-level representation: absent;
- per-exposure resampling replay information: absent from the frozen compact artifact;
- source-shot noise added by this audit: **no**;
- background noise added: **no**;
- covariance correction applied: **no**;
- SCI/ERR/WHT modified: **no**.

The scientific outcome is:

`exact_source_shot_not_identifiable_from_frozen_l1_bundle`

The missing requirements recorded by the artifact are:

1. exposure/detector-level source expectation before mosaic resampling;
2. per-exposure contribution/weight/WCS information sufficient to replay the mosaic resampling operator;
3. separate calibrated variance provenance (`VAR_POISSON`, `VAR_RNOISE`, `VAR_FLAT`) in this compact artifact.

## Scientific interpretation

The existing L1 real-survey injection remains valid for its declared deterministic purpose: a noiseless synthetic source is inserted into an already noisy real survey mosaic while modifying SCI only and leaving ERR/WHT unchanged. The D1o result does not retroactively change that experiment.

However, the frozen L1 `SCI/ERR/WHT` cutout is **not sufficient to define a unique physically exact source-Poisson realization and its resampling-induced covariance**. `BUNIT`, `PIXAR_SR`, `PHOTMJSR`, or any other scalar photometric keyword cannot by themselves reconstruct the independent stochastic realization in each contributing exposure and the exact mapping of those realizations into the final mosaic.

Therefore an independent Poisson draw on final 30-mas mosaic pixels must not be described as ground truth. If such an experiment is later useful, it must be a separately declared L1 approximation bracket with explicit assumptions. No gain, effective exposure, or universal covariance scalar is invented here.

The physically faithful source-shot experiment should move to **L2/exposure-level injection before final resampling**, where the injected source expectation can be expressed in the detector/calibrated-exposure convention and carried through the maintained JWST resampling operator.

## Gate decision

D1o closes the L1 *identifiability preflight*, not the source-shot-noise science question and not Gate D. The next non-redundant Gate-D task is a minimal L2 exposure-injection adapter/provenance preflight on a small controlled subset. It must first establish exact exposure provenance, units/calibration boundary, WCS/pixel convention, and resampling settings before any stochastic source-shot comparison is attempted.
