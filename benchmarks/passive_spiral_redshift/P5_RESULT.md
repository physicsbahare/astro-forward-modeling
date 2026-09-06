# Passive Spiral P5 — Huber robust-loss contamination control result

Status: **WORKFLOW PASS / SCIENTIFICALLY LIMITED AND HETEROGENEOUS IMPROVEMENT**

This is an immutable result receipt for the frozen protocol in `P5_PROTOCOL.md`. It does not redefine the protocol, tune the robust loss after seeing the data, or establish a production classifier.

## Frozen provenance

- Protocol frozen before implementation: commit `2aa1cdaf3b5a89213ef503e2cebf45aa7294c742`.
- Implementation/workflow branch head used for the run: `6f4e50a88e718ee503e861b602a6f99b30c6e9ae`.
- Pull-request merge test SHA used by GitHub Actions: `f6f880c87433afcadd973a0379780f5a5205820c`.
- Workflow: `passive-spiral-p5-robust-loss`.
- Run: `34061676941`.
- Job: `101563186805`.
- Exact frozen real COSMOS-Web cutout SHA-256: `764d542f2417810c904bce711455b3eb69c70cf388f97348cb857b056b2dd66d`.
- Artifact: `9997671093`, `passive-spiral-p5-robust-loss`.
- Artifact digest: `sha256:65fe6a6e38914e0dc2a3d7088428d04414351e4665375529ee92cafbfb44ba27`.
- Software recorded by the run: Python `3.12.14`, NumPy `2.5.3`, SciPy `1.18.1`.
- Regression tests: `4 passed`.

## Frozen fitting change

P5 changes only the residual objective relative to P3. The 18 frozen placements/magnitudes, the four phase offsets (`0, 45, 90, 135 deg`), target rendering, diagonal `ERR` standardization, and raw-scene scientific ranking are retained.

The robust objective is SciPy `least_squares` with:

- `loss='huber'`;
- `f_scale=1.0` in standardized-ERR residual units;
- no parameter bounds;
- no clipping or pixel masking;
- deterministic initialization from the ordinary diagonal-ERR weighted solution for the same phase.

Neither the loss family nor `f_scale` may be retuned after this result.

## Aggregate result

For the raw injected real-scene measurements:

- P3 true-phase rank-1 count: **2/18**;
- P5 Huber true-phase rank-1 count: **4/18**;
- P3 median true-phase rank: **3.0**;
- P5 median true-phase rank: **3.0**;
- case-by-case P5 versus P3: **4 improved, 11 unchanged, 3 worsened**.

For the paired-difference identifiability control:

- P5 true phase rank-1: **18/18**.

Numerical/optimizer audit:

- raw robust phase-fit optimizer failures: **0**;
- paired robust phase-fit optimizer failures: **0**;
- raw non-finite solutions: **0**;
- paired non-finite solutions: **0**.

Thus the heterogeneous scientific behavior is not explained by a recorded optimizer or non-finite-solution failure.

## Breakdown by frozen context

| Crowding class | AB | P3 ranks | P5 ranks | Rank-1 P3 -> P5 | Case change |
| --- | ---: | --- | --- | --- | --- |
| intermediate 8–20 px | 26 | `[4,3,3]` | `[1,3,3]` | `0 -> 1` | 1 improved, 2 unchanged |
| intermediate 8–20 px | 29 | `[4,4,3]` | `[1,3,3]` | `0 -> 1` | 2 improved, 1 unchanged |
| near-source 2–5 px | 26 | `[2,4,3]` | `[2,3,4]` | `0 -> 0` | 1 improved, 1 unchanged, 1 worsened |
| near-source 2–5 px | 29 | `[2,2,3]` | `[2,4,4]` | `0 -> 0` | 1 unchanged, 2 worsened |
| relatively isolated >=30 px | 26 | `[3,2,1]` | `[3,2,1]` | `1 -> 1` | 3 unchanged |
| relatively isolated >=30 px | 29 | `[4,3,1]` | `[4,3,1]` | `1 -> 1` | 3 unchanged |

The strongest benefit occurs in the intermediate-crowding cases. The faint near-source (`AB=29`) subset becomes worse under the frozen Huber objective, while the relatively isolated cases are unchanged.

## Scientific interpretation

The frozen Huber loss is a **limited contamination-resilience diagnostic, not a general recovery solution**. It doubles the number of raw scenes for which the injected orientation is ranked first (`2/18` to `4/18`), but it does not improve the overall median rank and worsens three cases, concentrated in the near-source regime.

The paired-difference `18/18` recovery remains an identifiability/numerical control only. It shows that the frozen renderer/template/fitter combination can recover the inserted phase when the real scene is algebraically removed; it is not independent cross-code validation and cannot be used as a scientific measurement path for unknown real galaxies.

P5 therefore supports the same broad conclusion as P3/P4: real-scene contamination is phase-structured and cannot be made generally harmless by a single simple operator such as hard source masking or one frozen robust loss.

No acceptance threshold is inferred from these 18 cases.

## Mutation and physical-semantics audit

- science input modified in place: `false`;
- `ERR` data product modified: `false`;
- `WHT` modified: `false`;
- existing background/sky noise re-added: `false`;
- source-shot noise generated: `false`;
- extra Tolman factor applied: `false`;
- PSF sharpening applied: `false`;
- scientific detection threshold applied: `false`;
- parameter bounds introduced: `false`;
- post-hoc Huber tuning performed: `false`.

## Next scientific decision

Do **not** tune `f_scale`, change the Huber transition, or cycle through robust-loss families to optimize these 18 outcomes. The next passive-spiral experiment, if pursued, should test a genuinely different contamination operator with independently frozen information—for example catalog/segmentation-informed nuisance modeling—rather than another parameter search over the P5 objective. Any such experiment requires a new immutable protocol before execution.
