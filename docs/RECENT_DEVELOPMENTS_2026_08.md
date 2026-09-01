# Verification-relevant developments — August 2026

This note records developments that materially affect the verification roadmap.
It is not a production dependency list. New external packages or methods must
first enter as independently reviewable verification cases.

## PyAutoGalaxy / PyAutoArray

PyAutoGalaxy v2026.8.29.1 was published on 2026-08-29. The release includes
batched PSF convolution for MGE linear functions and sharing of eccentric-radius
grids, while its PyAutoArray dependency includes reuse/caching of convolution
state and a correction to PSF-kernel axis handling. The same release stack also
contains gradient-search parameter-transform and covariance-related fixes in
upstream packages.

Verification action:

- Add a pinned PyAutoGalaxy/PyAutoArray morphology cross-code benchmark before
  production architecture freeze.
- Use it as an independent numerical reference for PSF-convolved profile/MGE
  rendering and fitting; do not make it the ground truth and do not make it a
  production dependency solely for this benchmark.
- Record exact package versions and compare flux, centroid, second moments,
  profile shape and recovered structural parameters on identical analytic
  scenes.

Reference: https://github.com/PyAutoLabs/PyAutoGalaxy/releases/tag/2026.8.29.1

## AGN-host PSF mismatch and decomposition

Dewsnap, Barmby & Gallagher compare JWST/NIRCam AGN-host fits using different
PSF-construction methods and both GALFIT and AstroPhot. Their results show that
acceptable fit quality does not guarantee unique host morphology, and that
Sérsic index and effective radius can be strongly covariant.

Verification action:

- PSF provenance remains mandatory metadata.
- Add explicit perfect-PSF versus mismatched-PSF recovery experiments.
- Keep cross-fitter AGN-host decomposition as a verification gate rather than
  accepting one fitter as truth.

Reference: https://arxiv.org/abs/2510.27214

Kawase, Shibuya & Matsuda (2026) introduce an AGN-host deconvolution formulation
with a smooth extended host, sparse point-source component and a point-source
balance constraint.

Verification action:

- Reproduce a controlled synthetic case from this method as an independent
  AGN-host validation experiment before considering any implementation for
  production use.
- Compare host-flux, host-size and nuclear-residual behavior against the
  standard Sérsic+PSF stress test.

Reference: https://arxiv.org/abs/2605.13735

## Chromatic / SED-dependent PSFs

Berlfein et al. (2026) show in Roman image simulations that color information is
required to suppress chromatic-PSF shear calibration residuals to about the
10^-3 level in their multi-band cases. Although the science case is weak
lensing, the operator-level lesson applies generally: a broadband PSF can
meaningfully depend on the source SED.

Verification/architecture action:

- Keep SED-dependent, bandpass-integrated PSFs as a first-class capability.
- Preserve the existing chromatic non-commutativity tests.
- Add an explicit source-SED/PSF mismatch stress test before architecture
  freeze, including a color-gradient scene.

Reference: https://arxiv.org/abs/2603.15763

## ScopeSim

ScopeSim 0.11.4 was released on 2026-05-19. Its source -> optical train ->
detector abstraction is conceptually relevant to the intended instrument-
independent architecture.

Architecture action:

- Use ScopeSim as a design/cross-validation reference during Gate F.
- Do not add ScopeSim as a production dependency at this stage.

Reference: https://github.com/AstarVienna/ScopeSim

## Current immediate Gate-C target

The former Paulino-Afonso high-`n` blocker is resolved. The diagnostic sequence
showed that exact same-model noiseless fitting is numerically recoverable, then
identified a detector-pixel point-sampling mismatch and a separate sub-pixel
centering/phase error. A detector-centred 4x pixel-integrated fitter recovers the
full noiseless single-Sérsic set cleanly, while the noisy ensemble remains
unstable only when the extended-source information becomes weak. Gate C2 is
therefore reviewed as **PASS WITH EXPLAINED DIFFERENCE** for the controlled
synthetic-equivalent benchmark; the historical outputs remain preserved.

The next Gate-C target is Yu et al. (2023), arXiv:2307.04753, which directly
parameterizes morphology bias by the resolvedness quantity `R_p / FWHM`. The
first verification step should freeze the paper's definitions and qualitative
bias directions before any fitting or correction function is implemented:
non-parametric `R_p`/`R50` can be biased high by PSF smoothing, asymmetry and
concentration are suppressed as resolution worsens for intrinsically structured
galaxies, model-fit `R50`, `q`, and `n` are reported as much more stable, and
asymmetry is only robust for large objects at approximately `R_p/FWHM >= 5` in
the authors' corrected analysis. These are literature anchors, not production
acceptance thresholds.
