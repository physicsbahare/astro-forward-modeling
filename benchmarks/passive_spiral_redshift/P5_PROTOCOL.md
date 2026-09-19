# Passive Spiral P5 — robust-loss contamination-control protocol

Status: **FROZEN BEFORE EXECUTION**

## Scientific question

P3 showed that the true injected spiral phase is not generally preferred in the raw real-mosaic scene, while the paired-difference identifiability control recovers it. P4 showed that masking the pre-existing >5-sigma source-like pixels improves only a heterogeneous subset of cases and is not a general recovery.

P5 tests a distinct contamination operator: **robust residual weighting rather than source masking or pre-injection scene subtraction**. The question is whether limiting the influence of large standardized residuals can improve phase/orientation recovery in the same 18 frozen real-context cases without changing the phase grid, target renderer, injection semantics, or scientific acceptance policy.

This is a verification-harness diagnostic only. It is not a production morphology method and does not define a spiral-detection threshold.

## Method motivation frozen before execution

SciPy's maintained `scipy.optimize.least_squares` supports robust loss functions explicitly to reduce the influence of outlier residuals. P5 uses the built-in Huber loss with a fixed transition scale in standardized-residual units. This is deliberately different from P4's hard source mask: every finite pixel remains in the fit and the loss continuously limits the influence of large residuals.

The Huber transition is frozen at `f_scale = 1.0` after dividing residuals by the existing COSMOS-Web `ERR` plane. Thus the transition is one supplied error unit; it is not tuned against the P3/P4 outcomes. No alternative robust loss, clipping level, mask, dilation, or phase grid may be tried after inspecting P5 results.

Relevant maintained-method reference: SciPy `least_squares`, robust loss support (`loss='huber'`, `f_scale`).

## Frozen real input and cases

Reuse exactly the same checksummed COSMOS-Web DR1 NIRCam F444W 30-mas A1 512x512 real cutout and injection matrix used by P2-P4:

- real cutout SHA-256: `764d542f2417810c904bce711455b3eb69c70cf388f97348cb857b056b2dd66d`;
- 9 placements: 3 near-source, 3 intermediate, 3 relatively isolated;
- AB magnitudes: 26 and 29;
- total cases: 18;
- injected scene: the frozen P3 true-phase (`0 deg`) z=2 spiral template;
- phase bank: exactly `0, 45, 90, 135 deg` in model phase, unchanged from P3.

No placement, magnitude, template, orientation, support, or phase is selected after seeing P5 output.

## Frozen robust fit

For each phase template, fit the same five-component model used by P3:

1. constant background;
2. x gradient;
3. y gradient;
4. smooth galaxy template coefficient;
5. signed arm-residual coefficient.

For every finite pixel with positive finite `ERR`, define the standardized residual

`r_i = (model_i - data_i) / ERR_i`.

Minimize SciPy's Huber least-squares objective using:

- `scipy.optimize.least_squares`;
- `loss='huber'`;
- `f_scale=1.0`;
- no parameter bounds (`-inf, +inf` for every coefficient);
- analytic constant design matrix / Jacobian where practical;
- no clipping, source mask, dilation, segmentation exclusion, or manual pixel rejection;
- deterministic initial coefficients from the ordinary weighted linear least-squares solution for the same phase, used only as a numerical starting point.

The ordinary weighted-linear starting solution is not an acceptance criterion and is not substituted for a failed robust fit. Optimizer status, iteration count, finite/non-finite solution state, and objective value must be recorded.

## Phase score and ranking

For each phase, record the minimized Huber objective returned by the frozen robust fit. Rank the four phases from lowest to highest robust objective. The true phase remains `0 deg`.

Record for each case:

- P3 ordinary-linear true-phase rank;
- P5 Huber true-phase rank;
- best P5 phase;
- true-minus-best robust objective difference;
- fitted signed arm coefficient for the true phase;
- optimizer status/success and evaluation count for every phase;
- paired-difference Huber true-phase rank;
- injected flux-closure error.

Aggregate only descriptively:

- rank-1 count out of 18;
- median true-phase rank;
- counts improved / unchanged / worsened relative to P3;
- the same quantities by frozen crowding class and magnitude.

No post-hoc rank threshold, success fraction, acceptance band, or significance cutoff may be introduced.

## Paired-difference control

Run the identical robust phase bank on `injected - SCI_ORIG` using the same `ERR` values. This remains a same-renderer identifiability/numerical control only. It is not independent cross-code validation and does not represent an observable production workflow.

## Guardrails

- Modify SCI only when constructing the synthetic injected copy; never mutate the frozen input in place.
- Leave ERR and WHT data products unchanged.
- Do not add or regenerate the existing sky/background noise.
- Do not generate source-shot noise.
- Do not apply any extra Tolman factor.
- Do not apply a PSF sharpening/deconvolution kernel.
- Do not change the P3 phase bank or source morphology.
- Do not mask, clip, dilate, or retune pixels in response to P4 or P5 outcomes.
- Preserve AB=29 low-information failures and any optimizer failures as scientific/numerical results.
- Preserve P1-P4 results unchanged; P5 receives a separate immutable result receipt.
- Workflow success means reproducible execution only, not scientific success.
- Synthetic-source injection into a real L1 mosaic remains distinct from literal exposure-space survey reproduction.
- D1o/D2 literal source-shot realization remains forbidden unless exposure-level provenance independently establishes that it is defensible.

## Interpretation rule fixed before execution

P5 is informative whether it improves recovery or not.

- If robust loss improves rank recovery coherently across frozen regimes, record that reduced residual influence is a relevant contamination-control mechanism, without promoting it to a production default.
- If improvement is heterogeneous, preserve that heterogeneity and do not tune `f_scale` or switch robust losses.
- If it does not improve recovery, record robust-loss failure and move to a genuinely different operator/failure mode rather than modifying Huber settings.

No production-framework implementation is authorized by P5.
