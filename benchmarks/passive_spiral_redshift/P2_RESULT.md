# Passive Spiral P2 — real COSMOS-Web context arm-recovery result

Status: **SCIENTIFIC FAILURE OF RAW ARM RECOVERY IN REAL CONTEXT / PAIRED-DIFFERENCE IDENTIFIABILITY CONTROL PASSES**

This receipt records the first execution of the frozen P2 protocol against the exact checksummed COSMOS-Web DR1 F444W 30-mas A1 Gate-D cutout. The workflow completed successfully as software, but the scientific result is that the un-deblended real mosaic context can dominate the signed arm-template measurement by far more than the injected arm signal.

## Frozen protocol and run

- Protocol: `benchmarks/passive_spiral_redshift/P2_PROTOCOL.md`
- Protocol freeze commit: `81d2d6554bd8091a91f0f740a3045511152f9d65`
- Implementation head executed: `2adc10cba498d872df90c9fb4cbd71e1d08a899d`
- Workflow: `passive-spiral-p2-real-context`
- GitHub Actions run: `34029687968`
- Job: `101476824624`
- Numerical-invariant tests: `4 passed`
- Artifact: `passive-spiral-p2-real-context`, ID `9988185830`
- Artifact SHA256: `46eba841d504cfe93042996b81705715d3420731b2723574cae09a1b7d4fc4e2`

The workflow re-downloaded and verified the exact frozen real cutout:

`cosmosweb_f444w_30mas_A1_ID4204_real_cutout.fits`

with SHA256:

`764d542f2417810c904bce711455b3eb69c70cf388f97348cb857b056b2dd66d`.

## Experiment identity

P2 used the frozen P1 direct-target spiral morphology at `z=2`, the target redshift with the largest resolution-only arm suppression in the prior immutable P1 grid. The deterministic source was normalized to the predeclared Gate-D observed-flux stress levels AB=26 and AB=29 and injected at the same nine pre-injection-selected real-context positions: three near-source, three intermediate, and three relatively isolated.

The measurement was an unconstrained diagonal-ERR weighted linear fit of:

- constant background;
- x/y gradients;
- scaled smooth disk+bulge template;
- signed arm-residual template.

The truth coefficients of the injected deterministic source are `smooth=1` and `arm=1`. No coefficient clipping or positivity bound was applied.

## Main numerical result

The raw injected arm coefficient is strongly contaminated by pre-existing real-scene projection onto the same arm template. Descriptive medians by frozen crowding class are:

| crowding class | AB | median raw arm coeff | median |arm-1| | median background arm-equivalent | median paired-difference arm coeff |
|---|---:|---:|---:|---:|---:|
| intermediate 8–20 px | 26 | 2.8108 | 4.7398 | 1.8108 | 1.0000000000000013 |
| intermediate 8–20 px | 29 | 29.6997 | 75.1202 | 28.6997 | 1.0000000000000004 |
| near-source 2–5 px | 26 | -0.2046 | 13.1029 | -1.2046 | 1.0000000000000002 |
| near-source 2–5 px | 29 | -18.0917 | 207.6666 | -19.0917 | 1.0000000000000009 |
| relatively isolated >=30 px | 26 | 0.9216 | 1.1309 | -0.0784 | 1.0000000000000007 |
| relatively isolated >=30 px | 29 | -0.2420 | 17.9241 | -1.2420 | 1.0000000000000000 |

These medians are descriptive only. They are not pass/fail bands and do not define a spiral-detection threshold.

The individual raw coefficients preserve extreme and negative outcomes rather than filtering them. Examples include:

- intermediate AB=26: arm coefficients `-3.7398`, `2.8108`, `8.9074`;
- near-source AB=26: `-18.0324`, `-0.2046`, `14.1029`;
- relatively isolated AB=26: `0.9216`, `2.1309`, `-1.7977`;
- at AB=29, raw coefficients reach magnitudes of tens to hundreds because the fixed real background is being measured in units of a source template that is 3 magnitudes fainter.

The three-magnitude change reduces source flux by about a factor of 15.85, and the same fixed-background template projection correspondingly grows by approximately that factor when expressed as a source-equivalent coefficient. This is expected from the frozen linear measurement and demonstrates the severity of the context term rather than a numerical instability introduced by the injection.

## Identifiability control

The paired-difference path `(injected - original)` recovers the deterministic source essentially exactly in every case:

- paired-difference smooth coefficient: approximately `1`;
- paired-difference arm coefficient: approximately `1`;
- coefficient linear-closure errors: about `1e-15` to `2e-13`;
- requested-to-realized injected flux relative errors: at floating-point level (`0` to a few `1e-15`).

Therefore the large raw-context arm biases are not caused by failure to construct or recover the injected template on the same renderer. They arise because real COSMOS-Web scene structure projects strongly onto the arm-sensitive basis when no scene/deblending model removes it.

This paired-difference result is an identifiability/numerical control, not independent cross-code validation.

## Scientific interpretation

P1 showed that resolution alone suppresses the known arm signal by about 16.4% at z=2 in a noiseless controlled scene. P2 now shows a distinct and substantially larger failure mode: in literal real-mosaic context, unrelated scene structure can dominate an arm-sensitive measurement even for AB=26, and the problem becomes much more severe at AB=29.

The relatively isolated class is less contaminated in its median AB=26 arm coefficient than the near-source/intermediate classes, but its individual outcomes still include strong positive and negative biases. Therefore distance to the nearest >5-sigma source-like pixel is not by itself a sufficient universal criterion for reliable spiral-arm recovery.

P2 does not claim that spiral morphology is intrinsically absent or undetectable in these scenes. It demonstrates that a raw arm-template measurement without an explicit nuisance-scene/deblending strategy is not a robust morphology estimator in this real survey context.

## Guardrail audit

- SCI input modified in place: `false`
- ERR modified: `false`
- WHT modified: `false`
- background/sky noise added: `false`
- source-shot noise generated: `false`
- extra Tolman factor applied: `false`
- PSF sharpening/deconvolution applied: `false`
- post-hoc scientific acceptance threshold applied: `false`

The P1 Gaussian target PSF remains a controlled surrogate and is not promoted to the literal COSMOS-Web effective PSF.

## Next non-redundant decision

The next Passive-Spiral experiment should test whether arm information can be distinguished from real-context template projection **without access to the pre-injection original scene**. A phase/orientation null test is a minimal next diagnostic: compare the frozen true injected arm phase with otherwise identical rotated-arm templates on the same raw injected scene, while preserving all coefficients and avoiding a post-hoc detection threshold. This tests whether the correct spiral geometry is preferentially supported over background-induced arm-like projections rather than merely measuring a large raw coefficient.
