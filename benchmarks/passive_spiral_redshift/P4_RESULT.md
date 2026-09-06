# Passive Spiral P4 — pre-injection source-mask contamination control result

Status: **WORKFLOW PASS / SCIENTIFICALLY HETEROGENEOUS, NOT GENERAL RECOVERY**

This receipt records the frozen P4 experiment defined in `P4_PROTOCOL.md`. Historical P3 results are unchanged.

## Execution receipt

- GitHub Actions workflow: `passive-spiral-p4-mask-control`
- Run: `34052530258`
- Job: `101538573287` (`p4-mask-control`)
- Workflow/job conclusion: `success`
- Regression tests: `4 passed in 0.53s`
- Frozen real input SHA-256: `764d542f2417810c904bce711455b3eb69c70cf388f97348cb857b056b2dd66d`
- Artifact: `passive-spiral-p4-mask-control`, ID `9994983241`
- Artifact ZIP SHA-256: `34f737b26e5ffdb817b602720d0bac12ae85c5f8ea268ad870b5fa5937b71408`

Workflow success establishes reproducible execution only; it is not scientific success.

## Frozen mask and semantics

The experiment used exactly the pre-injection D1c mask

`(SCI_ORIG - 4.1250608e-4 MJy/sr) / ERR > 5`

with global masked fraction `0.031078338623046875`. The mask was derived from the original scene only, was not dilated or tuned, and original-scene values were not subtracted or fitted as nuisance data.

No sky/background noise or source-shot noise was generated; no extra Tolman factor or PSF sharpening was applied. SCI was not modified in place, ERR/WHT data products were not modified, and only a fitting copy of ERR received NaNs at frozen mask pixels. Arm coefficients remained unconstrained and no scientific detection threshold or post-hoc acceptance band was introduced. Paired difference remains an identifiability control only.

## Main numerical result

Across the 18 frozen cases, the unmasked P3 true-phase rank-1 count was `2/18`. After applying the frozen pre-injection mask, the true phase ranked first in `4/18` cases. The all-case median true-phase rank changed from `3.0` unmasked to `2.5` masked.

Case-by-case rank changes were heterogeneous: `6/18` improved, `10/18` were unchanged, and `2/18` worsened. Therefore the mask does not provide a coherent general recovery.

By frozen crowding/magnitude subgroup:

| crowding class | AB | unmasked ranks | masked ranks | median unmasked -> masked |
| --- | ---: | --- | --- | --- |
| intermediate 8–20 px | 26 | 4, 3, 3 | 2, 3, 2 | 3 -> 2 |
| intermediate 8–20 px | 29 | 4, 4, 3 | 2, 4, 2 | 4 -> 2 |
| near source 2–5 px | 26 | 2, 4, 3 | 1, 4, 4 | 3 -> 4 |
| near source 2–5 px | 29 | 2, 2, 3 | 1, 4, 3 | 2 -> 3 |
| relatively isolated >=30 px | 26 | 3, 2, 1 | 3, 2, 1 | 2 -> 2 |
| relatively isolated >=30 px | 29 | 4, 3, 1 | 4, 3, 1 | 3 -> 3 |

The intermediate regime improves descriptively, the near-source regime is mixed and its median rank worsens, and the relatively isolated regime is unchanged. Patch-level masked fractions themselves are highly heterogeneous (including zero in several isolated cases and >0.2 in one intermediate placement), so these results must not be collapsed into a universal correction.

The masked paired-difference control ranks the true phase first in `18/18` cases. This confirms that the frozen phase bank and numerical recovery retain identifiability when real-scene contamination is removed; it is not independent cross-code validation.

## Scientific interpretation

P4 provides evidence that masking only the pre-existing >5-sigma source-like pixels can reduce contamination in some real-mosaic contexts, but it is insufficient as a general morphology/orientation recovery treatment. In particular, near-source behavior remains inconsistent and can worsen after masking, while isolated cases show no change.

Per the frozen protocol, the 5-sigma mask must not now be dilated, retuned, or combined with a post-hoc rank criterion to improve the result. The scientifically meaningful next decision is to test a distinct, predeclared contamination operator rather than tuning this mask.

This remains synthetic-source injection into real COSMOS-Web L1 mosaic context, not literal exposure-space survey reproduction. The D1o/D2 source-shot line remains blocked unless exposure-level provenance makes such a realization defensible.
