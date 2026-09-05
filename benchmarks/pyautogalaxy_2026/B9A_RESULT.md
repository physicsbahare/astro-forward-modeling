# B9a result receipt — PyAutoGalaxy/PyAutoArray morphology convention preflight

**Workflow run:** `33910050145`  
**Conclusion:** `completed / success`  
**Verification suite:** `33910050105` — `completed / success`

This closes the B9a convention/operator preflight only. It is not a recovered-parameter validation and does not make PyAutoGalaxy a production dependency.

## Frozen software and artifact

- `autogalaxy==2026.8.14.1`
- `autoarray==2026.8.14.1`
- artifact `pyautogalaxy-morphology-preflight-b9a`, id `9951043224`
- artifact digest `sha256:6629e218bb574ced122bac11b386d41960a70c0ea1fd3f99b0140a8d022f974b`
- four 101x101 Sérsic scenes, `n={1,4}`, `q={1,0.6}`
- real-space PyAutoArray convolution versus independent SciPy `convolve2d`
- normalized 9x9 Gaussian PSF, sigma 1.2 pixels

## Numerical evidence

All four scenes were finite and the PSF sum was `1.0000000000000002`.

For the elliptical `q=0.6`, 37-degree cases, the independent and PyAutoGalaxy raw-image moment geometry was effectively identical: the moment axis ratio differed by about `2.7e-7` for `n=1` and `1.3e-8` for `n=4`; raw moment angle differed by about `1.3e-5` deg and `1.5e-7` deg respectively.

The normalized raw-image L1 differences were `2.61e-5` for `n=1` and `3.86e-7` for `n=4`. After PSF convolution, the interior-crop L1 differences were `2.55e-5` and `3.86e-7` respectively. The larger global convolved discrepancy for `n=4` (`~4.0e-4`) is localized to the image boundary and is consistent with the already-declared difference between PyAutoGalaxy's unmasked padded evaluation and zero-filled same-mode SciPy convolution.

The convolved elliptical moment axis ratios remained close: `0.608214` versus `0.608299` for `n=1`, and `0.693246` versus `0.693704` for `n=4`. These are recorded differences, not post-hoc acceptance thresholds.

## Scientific decision

The PyAutoGalaxy eccentric-radius convention, `(y,x)` coordinate convention, angle mapping, and maintained real-space PSF operator are now sufficiently understood to proceed to a recovered-parameter diagnostic without conflating those conventions with a fitting failure.

B9b will therefore use independent noiseless common scenes, fit only the interior region that B9a showed is free of the edge-padding confounder, and compare recovered centroid, axis ratio, Sérsic index, effective radius, and flux-like normalization. The same SciPy least-squares optimizer and the same predeclared starts/bounds will be used for the independent renderer and the PyAutoGalaxy renderer so B9b isolates renderer/parameterization recovery rather than optimizer choice. No morphology acceptance band will be invented after the result.
