# Gate D1o — L1 source-shot-noise / covariance identifiability preflight

## Purpose

Determine whether the **existing frozen COSMOS-Web L1 mosaic bundle** contains enough information to generate a physically exact source-shot-noise realization for an injected source, including the covariance induced by the survey resampling operator.

This is a representational audit only. It does **not** add noise, alter SCI/ERR/WHT, fit morphology, change any D1m/D1n criterion, or define an acceptance tolerance. A negative result is a scientific result, not an infrastructure failure.

## Why this preflight is required before a stochastic D1 experiment

The maintained JWST calibration pipeline tracks Poisson, read-noise and flat-field variance terms through calibrated exposures and propagates diagonal variance products through later stages, while resampling can create covariance that is not represented by a full covariance matrix in the final product. Therefore a source-shot realization that is intended to be physically faithful belongs naturally before the final mosaic resampling operation.

The existing verification primitive in `verification/target_noise.py` already freezes the correct ordering for a controlled detector-level experiment: render the expected source, apply target PSF/pixel sampling, convert the expected source to detector electrons, draw source Poisson noise per detector pixel, and add an existing real background exactly once. It must not be silently reinterpreted as independent Poisson draws on final drizzled mosaic pixels.

## Frozen artifact and current L1 semantics

Audit the same immutable real COSMOS-Web bundle used by Gate D1:

- upstream run: `33941326833`;
- artifact: `gate-d-cosmosweb-real-cutout`;
- FITS SHA-256: `764d542f2417810c904bce711455b3eb69c70cf388f97348cb857b056b2dd66d`;
- survey/filter: COSMOS-Web DR1, JWST/NIRCam F444W;
- sampling: 30 mas/pixel;
- representation: final survey mosaic cutout;
- expected science bundle: `SCI`, `ERR`, and `WHT` image planes.

The current D1 injection operator adds the noiseless synthetic source to **SCI only** in MJy/sr. `ERR` and `WHT` remain unchanged; no additional sky/background realization, source-shot noise, Tolman factor, or PSF sharpening is applied.

## Exact-identifiability requirements

For this preflight, an *exact physically faithful source-shot realization through the mosaic* requires all of the following to be available for the injected source path:

1. an exposure/detector-level representation at which expected source counts/electrons are defined before mosaic resampling;
2. the calibration information needed to map the source expectation into that detector-count convention for each contributing exposure;
3. the per-exposure mapping/coverage/weights needed to propagate those independent Poisson realizations through the actual resampling operator;
4. enough variance provenance to distinguish the relevant source-Poisson term from other uncertainty terms rather than treating the final `ERR` plane as a reversible detector-count model.

A final `SCI/ERR/WHT` coadd does not become sufficient merely because a scalar exposure-time, photometric conversion, or weight keyword is present. Such scalars may support an **approximation**, but they do not reconstruct the missing per-exposure stochastic realization and resampling map.

## Executable audit

The D1o script must inventory the actual FITS extensions and selected calibration/provenance header fields and record, without mutating the input:

- image extension names and shapes;
- `SCI` surface-brightness unit and pixel-area metadata when present;
- presence/absence of `VAR_POISSON`, `VAR_RNOISE`, and `VAR_FLAT` image planes;
- presence/absence of exposure-level detector planes;
- presence/absence of a per-exposure contribution/resampling description sufficient to replay the mosaic operator;
- the explicit representation class (`drizzled_mosaic`).

It must then report the exact-identifiability decision and the complete list of missing requirements. It must also state separately that an independent per-output-pixel Poisson experiment, if ever run, would be an explicitly labeled L1 approximation rather than a truth reference.

## Interpretation rule fixed before execution

- If all exact-identifiability requirements are present, a separately frozen stochastic protocol may be designed without changing the current D1 recovery criteria.
- If any requirement is absent, do **not** invent gain/exposure conversions, infer a universal covariance correction, or add independent Poisson noise to mosaic pixels and call it physical truth. Record the limitation and move the physically faithful experiment to the L2 exposure-injection gate. A separate approximation bracket may be considered later only if its assumptions are explicit and useful.

This preflight cannot close Gate D and cannot authorize production implementation.
