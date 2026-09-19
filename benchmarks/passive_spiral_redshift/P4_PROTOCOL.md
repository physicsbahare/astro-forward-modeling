# Passive Spiral P4 — pre-injection source-mask contamination control

Status: **PROTOCOL FROZEN BEFORE EXECUTION**

## Purpose

P3 showed that the true injected spiral phase is ranked first in only 2/18 raw COSMOS-Web scenes, despite 18/18 recovery in paired difference. P4 tests one distinct, minimal contamination treatment: **does masking only pre-existing high-significance source-like pixels, identified before injection, change raw-scene phase/orientation recovery?**

This is a verification diagnostic, not a production classifier and not a universal spiral-detection rule.

## Methodological motivation frozen before execution

The COSMOS-Web morphology workflow uses segmentation information to model nearby companions and mask remaining contamination during morphology measurements. Maintained Photutils documentation likewise treats segmentation-derived source masks as a standard way to exclude detected-source pixels from subsequent measurements/background estimation. P4 deliberately does not introduce a new segmentation algorithm or tune new deblending parameters: it reuses the already frozen Gate-D D1c source-like mask definition.

## Frozen inputs

P4 reuses unchanged:

- the checksummed COSMOS-Web DR1 NIRCam F444W 30-mas A1 Gate-D cutout;
- the nine pre-injection-selected Gate-D placements;
- AB=26 and AB=29 stress levels;
- the P1/P2 z=2 deterministic spiral source;
- the P3 analytic phase bank `0, 45, 90, 135 deg`;
- the same smooth disk+bulge template and target Gaussian PSF surrogate.

The true injected phase remains `0 deg`.

## Frozen contamination mask

Use the exact D1c diagnostic definition already recorded before P2/P3:

`source_like = (SCI_ORIG - 4.1250608e-4 MJy/sr) / ERR > 5`

where `4.1250608e-4 MJy/sr` is the immutable D1c robust-background median. D1c recorded a 3.1078% global masked fraction and 43 8-connected source-like islands.

Rules:

1. Construct this mask from **SCI_ORIG and ERR before injection only**.
2. Do not recompute the mask from an injected image.
3. Do not dilate, erode, deblend, tune, or otherwise modify the mask after inspecting P4 output.
4. Do not use original-scene pixel values for subtraction or nuisance fitting; the original scene is used only to determine the frozen boolean mask.
5. In the weighted phase fit, masked pixels are excluded from all design columns and residual scoring by marking their fitting ERR values non-finite. SCI pixel values themselves are not altered.

This intentionally tests only the already-defined >5-sigma contamination mask. Faint wings and undetected structure remain in the data and may still cause scientific non-recovery.

## Measurement

For every one of the 18 frozen cases:

1. inject the true phase-0 spiral into a copy of SCI only;
2. extract the same P3 fitting patch;
3. fit the unchanged four-phase P3 bank to the raw injected patch using the D1c mask;
4. retain the original unmasked P3 ranking as a historical comparator; do not overwrite P3;
5. for identifiability only, run the same masked bank on paired difference.

Record:

- masked pixel fraction in each patch;
- masked raw phase-score vector;
- masked raw best phase and true-phase rank;
- masked raw true-phase score minus best score;
- masked true-phase arm coefficient;
- masked paired-difference true-phase rank;
- unmasked P3 true-phase rank for direct case-by-case comparison.

No rank threshold, success fraction, significance threshold, or acceptance band is defined. Rank changes are descriptive results only.

## Guardrails

- SCI input modified in place: `false`;
- ERR/WHT data products modified: `false`;
- fitting-only ERR copy may receive NaN at frozen mask pixels: `true`;
- existing sky/background noise re-added: `false`;
- source-shot noise generated: `false`;
- extra Tolman factor applied: `false`;
- PSF sharpening/deconvolution: `false`;
- arm coefficients constrained: `false`;
- paired subtraction used for scientific ranking: `false`;
- mask parameters tuned after execution: `false`;
- post-hoc acceptance threshold: `false`.

P4 remains synthetic-source injection into real COSMOS-Web L1 mosaic context, not literal exposure-space survey reproduction.

## Interpretation rule

Workflow success is software success only. If the frozen pre-injection mask does not improve orientation recovery, preserve that result. If it improves some regimes but not others, preserve the heterogeneity. Do not dilate the mask, alter the 5-sigma definition, change the phase bank, or remove failed/low-information cases to make the result look better.
