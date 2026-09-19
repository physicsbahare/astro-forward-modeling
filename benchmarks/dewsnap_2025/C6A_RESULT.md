# C6a result receipt — AstroPhot signed-PSF compatibility preflight

**Workflow run:** `33849387267`  
**Conclusion:** `completed / success`  
**Scope:** installation, signed empirical-PSF handling, array orientation, normalization, and AstroPhot v0.18 convolution convention only. This is **not** a Sérsic-fit, morphology-recovery, photon-readiness, or survey-reproduction pass.

## Frozen environment

- AstroPhot `0.18.0`, source tag commit `b20c98b4acba4b9708938610e61aced60f205620`
- CPU PyTorch `2.14.0+cpu`
- Python 3.12 workflow environment
- exact C5r module-A and module-B signed empirical PSF arrays
- negative PSF samples preserved; no clipping
- centered 201 x 201 unit-delta convolution identity check
- predeclared absolute orientation/convolution identity tolerance: `1e-12`

## Artifact audit

Module A:

- input PSF sum: `1.0055926166996918`
- input minimum: `-1.4324881810430093e-05`
- negative pixels: `13685`
- public `PSFImage.data` round-trip max absolute error: `0.0`
- normalized signed sum: `0.9999999999999999`
- normalized minimum: `-1.4245213789898026e-05`
- convolution sum: `1.0000000000000004`
- internal-transpose identity max absolute error: `8.456776945386935e-18`
- deliberately untransposed comparison error: `0.0036190594373100102`

Module B:

- input PSF sum: `0.9900868904443976`
- input minimum: `-6.172357403156517e-05`
- negative pixels: `13732`
- public `PSFImage.data` round-trip max absolute error: `0.0`
- normalized signed sum: `1.0`
- normalized minimum: `-6.234157287332703e-05`
- convolution sum: `1.0`
- internal-transpose identity max absolute error: `6.938893903907228e-18`
- deliberately untransposed comparison error: `0.004157804274456427`

All declared C6a numerical identity checks are many orders of magnitude tighter than the predeclared `1e-12` criterion. The signed negative wings survive the public-array round trip and AstroPhot's actual convolution path.

## Scientific decision

C6a closes the software/convention preflight only. It does not establish that AstroPhot and Imfit recover the same host morphology, and it does not make the signed C5 PSFs physically photon-ready.

The next stage is **C6b: matched-PSF, noiseless common-scene AstroPhot-versus-Imfit comparison**, using the clean archived C5o `n=1` control so fitting/renderer differences are isolated before introducing PSF-construction mismatch or noise. Any convergence failures, bound hits, parameter degeneracies, or morphology disagreement are observables and must not be hidden by post-hoc tolerance changes.
