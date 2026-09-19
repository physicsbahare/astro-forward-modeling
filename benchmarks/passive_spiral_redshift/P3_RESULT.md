# Passive Spiral P3 — raw-scene spiral phase/orientation null test result

Status: **WORKFLOW PASS / SCIENTIFIC NON-RECOVERY**

## Immutable execution receipt

- Frozen protocol: `benchmarks/passive_spiral_redshift/P3_PROTOCOL.md`.
- Branch under verification: `verification-v0.1`.
- Code/workflow HEAD used by the successful run: `6349b3e44f8c62c46a1908d87b6c2fb78cac7c56`.
- GitHub Actions run: `34045952422` (`passive-spiral-p3-phase-null`, run number 2).
- Job: `p3-phase-null`.
- Regression tests: `4 passed`.
- Frozen real input: `cosmosweb_f444w_30mas_A1_ID4204_real_cutout.fits`.
- Input SHA-256: `764d542f2417810c904bce711455b3eb69c70cf388f97348cb857b056b2dd66d`.
- Artifact: `passive-spiral-p3-phase-null`, artifact ID `9993098633`.
- Artifact digest: `sha256:e2a6dfa8a9dab37d78c60a21f3ee3e56501d0b2a6d0e6a81bda8e80e6e6a1cdc`.
- Software recorded by the run: Python 3.12.14, NumPy 2.5.3, SciPy 1.18.1.

The workflow completed successfully. That is software/execution success only; it is not the scientific conclusion.

## Frozen experiment

P3 kept the predeclared four-phase bank `0, 45, 90, 135 deg`, the same 18 frozen real-context cases (nine positions x AB=26/29), and the P1/P2 source and PSF semantics. The true injected phase was always `0 deg`. The scientific ranking used the raw injected real-mosaic patch and did not use the pre-injection original scene. Paired difference was retained only as an identifiability/numerical control.

No phase values, thresholds, bounds, or acceptance bands were changed after execution.

## Main numerical result

Raw true-phase ranks by frozen crowding/flux group were:

| crowding class | AB | true-phase ranks | median rank | median true-score minus best-score |
|---|---:|---|---:|---:|
| intermediate 8–20 px | 26 | 4, 3, 3 | 3 | 328.1696 |
| intermediate 8–20 px | 29 | 4, 4, 3 | 4 | 321.6951 |
| near source 2–5 px | 26 | 2, 4, 3 | 3 | 583.7226 |
| near source 2–5 px | 29 | 2, 2, 3 | 2 | 574.1135 |
| relatively isolated >=30 px | 26 | 3, 2, 1 | 2 | 4.6006 |
| relatively isolated >=30 px | 29 | 4, 3, 1 | 3 | 5.5379 |

Across all 18 raw-scene cases, the frozen true-phase rank distribution was:

- rank 1: 2/18;
- rank 2: 4/18;
- rank 3: 7/18;
- rank 4: 5/18;
- median rank: 3;
- mean rank: 2.8333.

The two rank-1 raw cases were the same relatively isolated frozen placement (`x=268`, `y=328`) at AB=26 and AB=29. These counts are descriptive only. P3 did not preregister a statistical detection threshold, so no post-hoc significance claim is made against a random-ranking null.

By contrast, the paired-difference identifiability control ranked the true phase first in **18/18** cases. This establishes that the phase bank, rendering, and linear fitting are internally capable of identifying the injected phase when the real scene is removed. It is not independent cross-code validation and does not rescue the raw-scene result.

## Scientific interpretation

P3 is a scientific non-recovery result. In the frozen real COSMOS-Web L1 context, the known injected spiral orientation is **not reliably preferred by the raw-scene phase fit**. Intermediate and near-source placements are especially dominated by unrelated real-scene structure, but even the relatively isolated class does not provide consistent true-orientation recovery. The much smaller score gaps in the isolated group show that crowding/scene structure changes the severity of the confusion, not that the raw estimator becomes generally reliable.

Together with P2, this strengthens the conclusion that a raw matched spiral-arm coefficient or a single best-fitting spiral phase cannot be treated as evidence of observable spiral structure without an explicit contamination/background treatment. The failure is preserved rather than repaired by changing the phase bank or acceptance rule.

## Guardrail audit

The successful run records:

- SCI input modified in place: `false`;
- ERR modified: `false`;
- WHT modified: `false`;
- background/sky noise added: `false`;
- source-shot noise generated: `false`;
- extra Tolman factor applied: `false`;
- PSF sharpening applied: `false`;
- arm coefficients constrained: `false`;
- scientific detection threshold applied: `false`;
- scientific ranking uses original scene: `false`.

P3 therefore remains a synthetic-source injection into real COSMOS-Web mosaic context, not literal exposure-space survey reproduction.

## Next scientific decision

Do **not** densify the phase grid or tune a success criterion to improve P3. The next Passive Spiral experiment should address a distinct failure mode: whether an independently frozen local contamination treatment (for example, segmentation/masking or a pre-injection-fitted nuisance scene) can improve spiral-orientation/arm recovery without using paired subtraction and without erasing genuine morphology loss. Its protocol must be frozen before inspecting its outputs, and any non-recovery must remain a valid result.
