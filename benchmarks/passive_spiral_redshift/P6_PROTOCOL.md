# Passive Spiral P6 — segmentation-informed nuisance-template profile-likelihood protocol

Status: **FROZEN BEFORE IMPLEMENTATION OR EXECUTION**

## Scientific question

P3 established that the true injected spiral phase is rarely preferred in the raw COSMOS-Web scene even though paired subtraction recovers it in every frozen case. P4 showed that a fixed pre-injection source mask gives only limited, heterogeneous improvement. P5 showed that a frozen Huber residual loss also gives only limited, heterogeneous improvement and must not be retuned.

P6 tests a genuinely different contamination operator: **explicit nuisance-source modeling on a segmentation support frozen from the pre-injection real scene**, followed by profile-likelihood ranking of the same four spiral phases. The question is whether accounting for structured neighboring-source light with independently frozen nuisance templates improves phase/orientation recovery without subtracting the original image, altering the target model, tuning a threshold after seeing outcomes, or changing the scientific acceptance policy.

This is a verification-harness diagnostic only. It is not a production morphology method and does not define a spiral-detection threshold.

## Method motivation frozen before execution

Maintained astronomy tools treat source overlap as a scene-modeling/deblending problem rather than only as a pixel-rejection problem. SourceXtractor++ supports multi-component model fitting and explicitly describes neighbor contamination as a motivation for robust/model-based fitting. statmorph requires a labeled segmentation map for morphology measurements and supports separate masks/weight maps. scarlet2 is a maintained astronomical scene-modeling package designed to handle overlapping sources. These references motivate testing an explicit nuisance-source basis as a distinct operator family; P6 does not adopt any of them as ground truth or as a production dependency.

P6 intentionally avoids a new nonlinear Sérsic-neighbor fit because Gate-D already contains extensive parametric-neighbor experiments. The smallest non-redundant test is a **linear empirical nuisance-template amplitude fit on frozen pre-injection segmentation support**. This isolates whether phase-structured contamination can be profiled out when the nuisance morphology is supplied independently of the injected target.

## Frozen real input and cases

Reuse exactly the same checksummed COSMOS-Web DR1 NIRCam F444W 30-mas A1 512x512 real cutout and P2-P5 injection matrix:

- real cutout SHA-256: `764d542f2417810c904bce711455b3eb69c70cf388f97348cb857b056b2dd66d`;
- 9 placements: 3 near-source, 3 intermediate, 3 relatively isolated;
- AB magnitudes: 26 and 29;
- total cases: 18;
- injected source: the frozen P3 true-phase (`0 deg`) z=2 spiral template;
- phase bank: exactly `0, 45, 90, 135 deg`, unchanged from P3-P5.

No placement, magnitude, source morphology, phase, or scientific subset may be changed after P6 output is inspected.

## Frozen segmentation source

Construct the nuisance segmentation **once from `SCI_ORIG` before any injection**. The injected target must not participate in segmentation or nuisance-template construction.

Use the same finite SCI/ERR validity convention as P2-P5. Source detection must use the pre-existing D1c frozen source-like threshold already recorded for this exact cutout:

`(SCI_ORIG - 4.1250608e-4) / ERR > 5`

Connected components are defined with 8-connectivity. Do not change the threshold, connectivity, deblend rule, support growth, dilation, or minimum-area rule after inspecting P6 results. If the existing P4/D1c helper already provides the exact frozen connected-component map, reuse it rather than implementing a semantically different detector.

The target injection location is not masked and no injected pixels are removed from the fit.

## Frozen nuisance templates

For each connected pre-injection source component that intersects the P3 fitting patch for a case:

1. take the `SCI_ORIG` values only on that component support within the patch;
2. subtract the frozen global background value `4.1250608e-4` from those supported pixels;
3. set all pixels outside that component support to zero;
4. normalize the resulting template to unit Euclidean norm if the norm is finite and positive;
5. if the norm is zero/non-finite, record and omit that component rather than inventing a replacement.

No smoothing, PSF deconvolution, dilation, interpolation, clipping, positivity enforcement, or morphology refit is allowed. The empirical nuisance template may contain real-source substructure and noise; that is part of this diagnostic and must be stated in the result.

A component template is used only if its frozen pre-injection segmentation support intersects the fitting patch. The number of nuisance templates per case must be recorded.

## Frozen phase-profile fit

For each of the four P3 phase templates, fit a single unconstrained weighted linear model to the raw injected patch using the existing diagonal `ERR` weights. The design matrix contains:

1. constant background;
2. x gradient;
3. y gradient;
4. smooth injected-galaxy template coefficient;
5. signed arm-residual coefficient for the tested phase;
6. one signed amplitude for each frozen nuisance template intersecting the patch.

All coefficients are unconstrained (`-inf, +inf`). Do not impose positivity on nuisance amplitudes. Do not mask or clip residuals. Do not use Huber or another robust loss. Do not subtract `SCI_ORIG` from the science patch.

Solve by weighted linear least squares using the same finite positive-ERR validity rule as P3. Record matrix rank, singular values/condition number, number of valid pixels, number of fitted coefficients, and whether the solve is rank deficient or non-finite. Rank deficiency, ill conditioning, or non-finite solutions are scientific/numerical outcomes and must not be hidden by regularization introduced after seeing the result.

## Phase score and ranking

For each phase, the score is the minimized diagonal-ERR weighted residual sum of squares from the full target+nuisance model. Rank the four phases from lowest to highest score. The true phase remains `0 deg`.

Record for each case:

- P3 true-phase rank;
- P6 true-phase rank;
- best P6 phase;
- true-minus-best weighted objective difference;
- fitted signed arm coefficient for the true phase;
- number of nuisance templates;
- design-matrix rank and condition number for every phase;
- rank-deficiency/non-finite flags;
- paired-difference P6 true-phase rank;
- injected flux-closure error.

Aggregate only descriptively:

- rank-1 count out of 18;
- median true-phase rank;
- counts improved / unchanged / worsened relative to P3;
- the same quantities by frozen crowding class and magnitude;
- rank-deficiency/non-finite counts.

No post-hoc success fraction, rank threshold, acceptance band, significance cutoff, nuisance-template pruning rule, or conditioning cutoff may be introduced.

## Paired-difference control

Run the identical phase+nuisance design on `injected - SCI_ORIG`, with the same nuisance columns and `ERR` values, only as an identifiability/numerical control. Because the nuisance scene is algebraically absent in this control, nuisance amplitudes should have no scientific interpretation. Paired-difference recovery is not independent cross-code validation and is not an observable production workflow.

## Guardrails

- Construct injected copies by modifying SCI only; never mutate the frozen input in place.
- Leave ERR and WHT data products unchanged.
- Do not re-add or regenerate existing sky/background noise.
- Do not generate source-shot noise.
- Do not apply any extra Tolman factor.
- Do not apply PSF sharpening/deconvolution.
- Do not change P3 phase bank, target morphology, placement matrix, or magnitudes.
- Do not tune segmentation threshold/support or nuisance-template selection after seeing P6 outcomes.
- Do not regularize, prune, or bound nuisance amplitudes post hoc to improve recovery.
- Preserve AB=29 low-information failures, rank deficiency, non-finite solves, centroid-independent morphology loss, and any other failure as results.
- Preserve P1-P5 historical results unchanged; P6 must receive a separate immutable result receipt after execution.
- Workflow success means reproducible execution only, not scientific success.
- Synthetic-source injection into a real L1 mosaic remains distinct from literal survey reproduction.
- D1o/D2 literal source-shot realization remains forbidden unless exposure-level provenance independently establishes that it is defensible.

## Interpretation rule fixed before execution

P6 is informative whether recovery improves or fails.

- If nuisance profiling coherently improves raw phase recovery without pathological conditioning, record explicit structured-neighbor modeling as a relevant contamination-control mechanism, but do not promote the empirical-template diagnostic to a production default.
- If improvement is heterogeneous, preserve the heterogeneity and do not alter segmentation or nuisance-template construction.
- If solves become rank deficient/ill conditioned or faint cases degrade, preserve those failures rather than introducing regularization or pruning after inspection.
- If P6 does not improve recovery, stop cycling simple contamination controls unless a new experiment addresses a genuinely distinct scientific failure mode.

No production-framework implementation is authorized by P6.
