# Passive Spiral P3 — raw-scene spiral phase/orientation null test

Status: **PROTOCOL FROZEN BEFORE EXECUTION**

## Purpose

P2 established that a raw signed arm-template coefficient can be dominated by unrelated real COSMOS-Web scene structure even when the injected spiral is numerically recoverable in paired difference. P3 asks a narrower, non-redundant question: **without using the pre-injection original scene, does the raw injected image preferentially support the known injected spiral orientation over rotated-arm null templates?**

This is a verification diagnostic, not a production classifier and not a universal spiral-detection criterion.

## Frozen input and scene

P3 reuses, unchanged:

- the checksummed COSMOS-Web DR1 NIRCam F444W 30-mas A1 Gate-D cutout;
- the nine pre-injection-selected Gate-D placements (three near-source, three intermediate, three relatively isolated);
- observed-flux stress levels AB=26 and AB=29;
- the deterministic P1 direct-target spiral scene at `z=2`;
- the same smooth disk+bulge component and target Gaussian PSF surrogate used by P1/P2.

The true injected orientation is the existing P1 phase (`phase_offset_deg = 0`).

## Frozen phase bank

The logarithmic two-arm (`m=2`) phase is evaluated analytically before PSF convolution at four phase offsets:

`0, 45, 90, 135 deg`.

Because the arm coefficient in the linear measurement remains signed and unconstrained, a 180-deg phase shift is exactly degenerate with changing the coefficient sign. The four frozen offsets therefore cover the distinct orientation family needed by this diagnostic without duplicated signed-template states. For an `m=2` pattern, these correspond to physical image rotations of `0, 22.5, 45, 67.5 deg` modulo the signed-template degeneracy.

No post-hoc phase values may be added after inspecting results.

## Rendering semantics

For every phase template:

1. render the same fixed physical disk+bulge scene on the P1 `z=2` target physical grid;
2. apply the same band-integrated Tolman factor exactly once, `(1+z)^-4`;
3. convolve with the same declared target Gaussian PSF used by P1;
4. normalize the spiral and smooth templates to unit total flux exactly as in P2;
5. define the signed arm residual as `spiral_phase - smooth`.

No image-space rotation/interpolation is used to generate null templates; the phase change is analytic in the latent scene. This avoids adding an interpolation operator to the null test.

## Injection and measurement

The injected source is always the true `phase_offset_deg=0` spiral. For each of the 18 frozen placement/magnitude cases, P3 measures only the raw injected patch for its scientific phase ranking.

For each frozen phase template, fit the same unconstrained diagonal-ERR weighted linear model used by P2:

- constant;
- x gradient;
- y gradient;
- smooth disk+bulge template;
- signed arm-residual template for that phase.

Record for every phase:

- signed arm coefficient;
- smooth coefficient;
- weighted residual norm;
- squared weighted-residual score (`weighted_residual_norm**2`);
- raw and column-normalized design condition numbers.

The scientific descriptive quantities are:

- phase with the minimum raw-scene score;
- rank of the true phase among the four frozen phases (`1` is lowest score);
- true-phase score minus best score;
- true-phase arm coefficient;
- full phase-score vector.

No score threshold, significance threshold, or success fraction is defined before or after execution. The rank distribution itself is the result.

## Paired-difference control

For identifiability only, repeat the same frozen phase bank on `(injected - original)`. This control is expected to prefer the true phase if template construction and fitting are internally coherent. It is **not** independent cross-code validation and is not used to rescue a poor raw-scene rank.

## Guardrails

- SCI input modified in place: `false`;
- ERR modified: `false`;
- WHT modified: `false`;
- background/sky noise added: `false`;
- source-shot noise generated: `false`;
- extra Tolman factor: `false`;
- PSF sharpening/deconvolution: `false`;
- coefficient clipping/positivity bounds: `false`;
- post-hoc acceptance threshold: `false`.

P3 remains a real-mosaic L1 context experiment, not literal exposure-space COSMOS-Web reproduction.

## Interpretation rule

Workflow completion is software success only. If the true injected orientation is not preferentially ranked in raw scenes, preserve that as the scientific result. Do not alter the phase bank, coefficients, placement set, flux levels, or fitting bounds to improve the outcome.
