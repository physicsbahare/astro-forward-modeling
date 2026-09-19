# C6a: AstroPhot signed-PSF compatibility preflight

Frozen 2026-09-04 UTC after auditing C5r run `33842347328`. C5r completed
successfully as a diagnostic, but all four selected wrong-PSF solutions hit a
bound and six of twelve starts timed out. In the A-data/B-PSF direction the
selected fits assigned essentially the full AGN+host flux to a subpixel host
and drove point-source flux to zero. Target noise is therefore not introduced.

## Question and frozen checks

Can the maintained AstroPhot implementation ingest the two signed empirical
PSFs without clipping or silently changing their public array orientation, and
does its actual FFT convolution preserve the declared v0.18 coordinate
convention, signed samples and unit flux on a centered delta image?

- reuse the exact module-A and module-B PSF FITS arrays archived by C5r;
- use AstroPhot 0.18.0 (tag commit
  `b20c98b4acba4b9708938610e61aced60f205620`) and CPU-only PyTorch
  `2.14.0+cpu` on Python 3.12;
- require exact public `PSFImage.data` round-trip equality;
- normalize by the signed array sum, never clip negative pixels;
- convolve a centered 201-square unit delta through AstroPhot's maintained
  convolution function and require agreement with AstroPhot's documented
  internal `(j,i)`/public `(i,j)` transpose convention to `1e-12` absolute;
- record input sum, minimum, negative-pixel count, normalized sum, convolution
  sum, orientation errors, wall time and complete arrays for both modules.

The `1e-12` check is a numerical identity test fixed before CI, not a
morphology-recovery band. C6a contains no Sérsic fit and cannot validate a
cross-fitter, establish physical recovery, or make the signed PSFs photon-ready.
It is only the required installation, convention and resource preflight before
freezing a controlled common-scene AstroPhot/Imfit comparison.

## Software-first decision

Dewsnap, Barmby & Gallagher report that GALFIT and AstroPhot can occupy
different host-morphology regions even when fit quality is similar. AstroPhot
is selected for the next reproducible adapter because it is maintained,
open-source (GPL-3.0), supports PSF-convolved component models, and publishes a
current Python package. GALFIT 3.0.5 was considered but is distributed as a
binary with unavailable source, making exact CI and implementation inspection
weaker. PyImfit does not provide an independent fitting engine, and PetroFit is
not the independent fitter used in the Dewsnap comparison.

Sources checked before freezing:

- Dewsnap et al. 2025: https://arxiv.org/abs/2510.27214
- AstroPhot methods paper: https://arxiv.org/abs/2308.01957
- AstroPhot 0.18.0 source/tag: https://github.com/Autostronomy/AstroPhot/tree/v0.18.0
- AstroPhot model documentation: https://astrophot.readthedocs.io/en/v0.17.0/tutorials/ModelZoo.html
- GALFIT distribution: https://users.obs.carnegiescience.edu/peng/work/galfit/galfit.html
