# Gate D1k — multi-threshold deblended neighbour-template diagnostic

## Purpose

D1h showed that simultaneous fixed empirical neighbour templates can reduce some real-scene contamination, D1i showed that simply growing template support does not improve all crowding regimes, and D1j showed that moment-extrapolated Gaussian neighbour shapes improve some near-source cases while worsening intermediate cases. D1k therefore asks a narrower question before introducing free neighbour morphology: **are multiple astrophysical peaks being incorrectly tied together because the frozen >5-sigma connected-component map treats them as one nuisance template?**

This is a diagnostic only. It is not blind detection, not a production deblender, and not literal COSMOS-Web source reproduction.

## External-method check before implementation

The design follows established practice rather than relaxing the target fit. Photutils 3.0 documents `deblend_sources` as multi-threshold plus watershed segmentation and uses defaults `n_levels=32`, `contrast=0.001`, `mode=exponential`, and 8-connectivity; the contrast default corresponds to separating peaks differing by roughly 7.5 mag when topology permits. Source separation requires a saddle point. GALFIT guidance independently recommends either masking neighbours or fitting them simultaneously, and its technical paper reports that simultaneous fitting of overlapping objects can outperform simply masking them. These references motivate testing neighbour identity/deblending before freeing target bounds or adding more target complexity.

References consulted:
- Photutils 3.0 `deblend_sources`: https://photutils.readthedocs.io/en/stable/api/photutils.segmentation.deblend_sources.html
- Photutils segmentation guide: https://photutils.readthedocs.io/en/stable/user_guide/segmentation.html
- GALFIT rules of thumb: https://users.obs.carnegiescience.edu/peng/work/galfit/TOP10.html
- Peng et al. GALFIT technical paper: https://users.obs.carnegiescience.edu/peng/work/galfit/galfit3.pdf

## Frozen design

1. Parent detection is unchanged from D1c/D1g/D1h: 8-connected pixels satisfying `(SCI_ORIG - robust_background_median)/ERR > 5`.
2. Parent support is immutable. Deblending may partition those pixels but may not add or remove any parent-mask pixel. This is checked at runtime.
3. Photutils 3.0.0 performs multi-threshold watershed deblending with `n_pixels=3`, `n_levels=32`, `contrast=0.001`, `mode=exponential`, and connectivity 8. `n_pixels=3` is frozen before seeing D1k results to reject one- or two-pixel child peaks as nuisance components while retaining the package's documented deblending defaults otherwise.
4. Each deblended child gets an empirical observed-space template made from positive `SCI_ORIG-background` values inside its child footprint, L2-normalized. Only its amplitude is free and constrained non-negative.
5. Observed-space neighbour templates are **not PSF-convolved again**.
6. The injected target uses exactly the D1e/D1h Sérsic renderer, STPSF target PSF, 65x65 patch, ERR weighting, linear least-squares loss, and target bounds. No target tolerance, bound, or acceptance criterion changes.
7. No additional background, source shot noise, or Tolman factor is applied. D1d already defines the injected scene.
8. Every optimizer failure, low-S/N outcome, and target bound hit remains in the artifact.

## Interpretation

Workflow success means only that the frozen diagnostic executed. Scientific improvement requires a coherent reduction of target bias/bound hits in the informative AB=26 near/intermediate regimes without degrading relatively isolated controls. AB=29 remains a deliberately low-S/N stress regime and is not required to recover. If deblending does not produce a coherent improvement, the next justified diagnostic is limited free/parametric neighbour morphology rather than more aggressive support growth or relaxed target constraints.
