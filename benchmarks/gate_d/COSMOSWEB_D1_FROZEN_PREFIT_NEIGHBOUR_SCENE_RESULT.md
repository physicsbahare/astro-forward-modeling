# COSMOS-Web Gate D1m — pre-injection fitted, frozen-neighbour scene result

## Immutable execution receipt

Workflow: `gate-d-cosmosweb-frozen-prefit-neighbour-scene`

Confirmed GitHub Actions run: `33978251853`

- status: `completed`
- conclusion: `success`
- head SHA: `348a4052b43a6d22b8938c8acfd1a3e95a151433`
- artifact: `gate-d-cosmosweb-frozen-prefit-neighbour-scene`
- artifact id: `9972994002`
- artifact SHA256: `4e2416d695b169d0a76042f2bc3b902cd3cdd36fd789a4321c01947f9d1b3283`

The dedicated tests, pinned STPSF-data download, frozen D1d artifact download, D1m diagnostic, and artifact upload all completed successfully. This is an execution-success receipt, not a claim of scientifically correct morphology recovery.

## Frozen experiment semantics

D1m reuses D1l's exact already-frozen detection/deblending, nuisance-source selection, nuisance Sérsic parameterisation/bounds, target renderer/bounds, declared STPSF, ERR weighting, planar background, linear loss, and target optimizer settings. The only scientific change is diagnostic: selected nuisance neighbours are fitted once on the real pre-injection `SCI_ORIG` scene and then frozen while the injected target is recovered. The fitted pre-injection background is not frozen.

This use of `SCI_ORIG` is available only because this is an injection experiment. It is an identifiability/scene-model control, not a production measurement method, blind detection, independent cross-code validation, or literal reproduction of real COSMOS-Web source morphology.

The synthetic source remains injected into literal real COSMOS-Web F444W mosaic context by changing SCI only. ERR/WHT are unchanged; no extra sky/background noise, source shot noise, Tolman factor, or PSF sharpening is introduced. AB=29 remains an intentional low-information regime and is retained without rescue logic.

## Machine-readable scientific result

The D1m machine-readable result was inspected after the completed workflow. Relative to D1l:

- AB=26 target-bound-hit fits decrease from `2/9` to `0/9`.
- AB=29 target-bound-hit fits decrease from `8/9` to `7/9`, but the low-S/N regime remains strongly non-recovering.
- Two AB=26 solutions remain catastrophic morphology/flux failures despite being interior solutions with no target-bound hit.

Therefore the removal of AB=26 target-bound hits is real evidence that target-neighbour parameter competition was an important contributor to the D1l crowded-scene failures. It is **not** evidence that D1m achieves reliable morphology recovery: the remaining catastrophic interior solutions show again that optimizer success and absence of bound hits are insufficient scientific acceptance criteria.

No failed/low-information case is discarded and no target/nuisance bound, tolerance, convergence setting, segmentation threshold, support radius, or acceptance band is changed in response to this result.

## Scientific interpretation and next diagnostic

D1m separates one part of the problem: allowing the injected target and neighbour morphologies to compete simultaneously was materially destabilizing AB=26 recovery. However, freezing neighbours fitted on `SCI_ORIG` does not remove all severe failures. The residual failure family therefore still includes scene-model inadequacy, background structure, PSF mismatch/effective-PSF mismatch, and morphology identifiability.

The next diagnostic should not return to segmentation/support tuning and should not widen target bounds. A smaller and more orthogonal next step is to isolate **PSF realism** while preserving D1m's frozen scene and target objective/bounds. The current Gate-D injection/recovery path uses one declared STPSF generated at one frozen NIRCam detector position for all placements. STPSF itself supports detector-position-dependent JWST wavefront/PSF calculation and detector/distortion effects, while empirical ePSF methods are designed to capture the net pixel-convolved PSF and subpixel phase. Because a drizzled survey mosaic has an effective PSF that need not equal a single ideal detector PSF, the next protocol should first quantify local/effective-PSF mismatch and only then rerun a minimal failure/control subset. This remains a diagnostic, not a claim that an empirical ePSF is automatically ground truth.

No production framework implementation is authorized by D1m.
