# COSMOS-Web Gate D1n-a — ideal STPSF detector-field bracket result

## Immutable execution receipt

Workflow: `gate-d-cosmosweb-psf-field-bracket`

Confirmed GitHub Actions run: `33985869245`

- status: `completed`
- conclusion: `success`
- head SHA: `5e20f3f026f10e607cd035da3206485af2ca9146`
- artifact: `gate-d-cosmosweb-psf-field-bracket`
- artifact id: `9975138623`
- artifact SHA256: `81815f62ffeaf75cfd2426df401be9733e4ebda16696ad402eeffc71ffe14acb`

The matching verification-suite run `33985869240` also completed with conclusion `success`. This receipt records execution and the inspected machine-readable result; it does not claim that ideal STPSF field dependence reproduces the real COSMOS-Web effective mosaic PSF.

## Machine-readable result

Baseline detector position was `(1024,1024)`. The frozen field bracket used `(256,256)`, `(1792,256)`, `(256,1792)`, and `(1792,1792)`.

Relative to baseline:

| detector position | normalized L1 | normalized cross-correlation | EE50 (pix) | EE80 (pix) | sigma-major (pix) | sigma-minor (pix) |
|---|---:|---:|---:|---:|---:|---:|
| 256,256 | 0.03458 | 0.999884 | 2.9801 | 8.4773 | 9.4843 | 8.1295 |
| 1792,256 | 0.04135 | 0.999826 | 2.9380 | 8.4787 | 9.4090 | 8.0719 |
| 256,1792 | 0.03160 | 0.999911 | 2.9585 | 8.5639 | 9.6419 | 8.2888 |
| 1792,1792 | 0.03106 | 0.999915 | 2.9392 | 8.5323 | 9.6033 | 8.2583 |

Baseline EE50/EE80 were 2.9481/8.5390 pixels and baseline moment sigmas were 9.5802/8.2275 pixels. The field changes are therefore real but modest in this ideal-STPSF bracket: image-level normalized L1 is about 3.1–4.1%, cross-correlation remains above 0.9998, and the moment/EE changes are at percent-scale.

## Scientific interpretation

D1n-a does not support ideal detector-position dependence as a sufficient explanation for the two severe interior AB=26 failures that remain in D1m. It also cannot rule out PSF realism as a broader issue: a COSMOS-Web mosaic combines resampling and potentially heterogeneous exposure/detector/orientation histories, so its effective PSF need not be equal to any one ideal STPSF.

The next evidence should therefore come from the real mosaic itself: first audit compact point-source-like empirical support without forcing an underconstrained ePSF, and separately quantify background/residual structure at all nine AB=26 D1m locations. No target bounds, segmentation settings, noise model, Tolman factor or PSF kernel is changed by this conclusion.
