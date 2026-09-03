# C5j: isolate compact-profile Fourier sensitivity (frozen 2026-09-03)

Frozen before any C5j science evaluation. This does not alter C5i, its
accuracy settings, the original structural bounds, or any recovery criterion.

## Prerequisite and question

GitHub explicitly confirmed C5i **33766246396** at commit
`169018474ae502a537bc736a64ead778f24e42cd` completed/success for both jobs.
The checksum-verified artifacts **9898810716 / 9898833104** were completely
audited: 32 Sersic images, 16 Gaussian controls, 48 direct amplitude starts,
and 308 new arrays. The audit and actual GitHub receipt are preserved in
`compact_renderer_33766246396.json`.

At compact n=6, GalSim coarse/fine image L1 changes reach 0.90315%; the
maximum radius-convention image change is only 1.381e-8. At 8x, Imfit/GalSim
image differences remain 1.55--2.70% for n=6 and reach 3.66% for the flattened
n=0.5 control. Neither renderer is established as truth. The question is
which existing GalSim numerical control accounts for its own sensitivity:
Fourier extent/spacing, transform interpolation, or radial quadrature?

## Focused source review and reuse decision

Sources checked 2026-09-03, before implementation:

- GalSim 2.8.4 GSParams documentation distinguishes folding, Fourier cutoff,
  value accuracy and the separate integration tolerances:
  https://galsim-developers.github.io/GalSim/_build/html/gsparams.html
- Tagged `SBSersic.cpp` uses the integration tolerances for its existing
  Hankel transform; changing kvalue_accuracy alone does not tighten those
  integration tolerances. This is a candidate contribution, not a diagnosis:
  https://github.com/GalSim-developers/GalSim/blob/v2.8.4/src/SBSersic.cpp
  (blob `a8d1968253b408cf062afa47fb95b3dbad307d0f`).
- `InterpolatedImage` estimates stepk from enclosed signed flux. Its public
  calculate_stepk=False option instead uses the input extent; its public
  calculate_maxk=False option uses the interpolant Fourier range. These can
  isolate support/cutoff estimation without changing any signed input sample:
  https://galsim-developers.github.io/GalSim/_build/html/_modules/galsim/interpolatedimage.html
  (tagged blob `9ed6d853f0eb63dc6ca6bd6c8bc3a12d9611abbf`).
- Convolution normally propagates its GSParams to both components. This
  diagnostic intentionally changes one *global* setting and records both
  component settings; it does not pretend these are independent component
  interventions. The documented FFT helper permits recording actual grids:
  https://galsim-developers.github.io/GalSim/_build/html/_modules/galsim/convolve.html
  https://galsim-developers.github.io/GalSim/_build/html/_modules/galsim/gsobject.html
  (tagged blobs `a34ebd5565ac3a400a9b7e94dd008f9c7c0404f0` and
  `84c935bc5b23b5a115ecb222473388b33c221e73`).
- Bernstein & Gruen's Fourier-resampling analysis motivates retaining the
  existing fourfold padding and Quintic interpolants while isolating the
  other controls. Its reported accuracy is not an acceptance band here:
  https://arxiv.org/abs/1401.2636v2

Reuse the existing **GalSim 2.8.4** renderer and public support options;
retain NumPy 2.5.2, SciPy 1.18.1, Astropy 8.0.1 and Photutils 3.0.0 pins.
GalSim is BSD-3-Clause and already wheel-installed in this CI environment.
No new quadrature, FFT, PSF reconstruction or optimizer is implemented.
PyImfit remains the same Imfit engine, not a substitute for this GalSim
diagnosis. An independent new cross-fitter would change too many numerical
conventions at once. The adapter only freezes settings, records Fourier
probes/grids, applies the inherited one-amplitude projection and retains
provenance/failures. These packages are verification tools, not new production
dependencies. Existing software does not guarantee correctness or restore
missing physical information.

## Frozen cases and nine interventions

Retain the four C5i compact corners: Re=0.5 native pixel, n={0.5,6},
q={0.15,1}, PA=45 degrees, analytic flux=1; both signed A/B empirical PSFs.
Use the C5i **nominal_hlr** convention for every new arm, retaining both
historical conventions. Same 201x201 centered native stamp, 0.03 arcsec
pixels, 0.015 arcsec PSF samples, full signed normalization, Quintic x/k
interpolation, pad_factor=4, no truncation/shift/depixelization/noise/extra
Pixel convolution. Native `no_pixel` drawing remains essential: the empirical
PSF already contains detector response. No sharpening is attempted.

The baseline coarse dictionary is exactly C5i's: folding_threshold=1e-4,
maxk_threshold=1e-5, kvalue_accuracy=xvalue_accuracy=1e-7. The inherited fine
dictionary is 1e-5, 1e-6, 1e-8, 1e-8 respectively. Other defaults are pinned.
All nine arms are always retained:

1. `coarse`: unchanged coarse replay.
2. `folding_only`: coarse plus fine folding_threshold only.
3. `maxk_only`: coarse plus fine maxk_threshold only.
4. `kvalue_only`: coarse plus fine kvalue_accuracy only.
5. `xvalue_only`: coarse plus fine xvalue_accuracy only.
6. `fine`: unchanged fine replay.
7. `fine_hankel`: fine plus integration_relerr=1e-8 and
   integration_abserr=1e-10 (a fixed two-order quadrature refinement).
8. `fine_psf_extent`: fine plus calculate_stepk=False only, preserving
   calculate_maxk=True.
9. `fine_psf_bandlimit`: fine plus calculate_maxk=False only, preserving
   calculate_stepk=True. This is the existing interpolant's conservative
   frequency support, not an inferred optical band limit or a deconvolution.

The four single-setting changes test contributions to the existing coarse/
fine difference. They are not alternative acceptance settings or permission
to select the fastest/closest arm. Higher-order interactions can remain.
The three further controls test identified numerical hypotheses, not a
post-hoc search for a setting that passes. No physical shape is fitted.

## Outputs, controls, and decision rules

Two inherited host shards (1 -> n=0.5, 4 -> n=6). Four shape/module groups
per shard, nine isolated workers per group: **72 Sersic images, 36 Gaussian
identity images, 72 one-amplitude NNLS comparisons/start records**. For
n=0.5, every arm also draws the same-size/shear/unit-flux GalSim Gaussian.
The unchanged coarse/fine replays are checked against archived nominal C5i
images at the inherited 1e-12 bookkeeping scale; no general numerical
agreement band is introduced.

For each arm record source, PSF and convolution stepk/maxk (1/arcsec), full
GSParams, actual FFT k-grid shape/spacing and wrap size. Observe the existing
`drawFFT_makeKImage` helper without changing its returned objects. Save
complex kValue probes for host, PSF and convolution, using four directions
0/45/90/135 degrees and 65 radial values: zero followed by 64 log-spaced
values from 1e-3 to 8*pi/0.015 (1/arcsec). Compare component products to the
convolution at these same points. The probes do not exhaust Fourier space
or constitute convergence proof. Save Gaussian probes where applicable.

Save every new image, Gaussian residual and probe array with the inherited
atomic/read-back NPZ helper and per-file/per-array hashes. Compare images
to archived C5i coarse/fine and archived Imfit 8x without rescaling. Also
project each new image as one nonnegative-amplitude template onto the
archived C5i fine image using the inherited NNLS objective; save reference,
template, prediction, residual, cost, gradient and zero flag. This describes
flux sensitivity, not structural recovery. Save all rows/starts as CSV/JSON.

Verify all parent file hashes before selecting unchanged images/PSFs;
record the parent ZIP identity, audit/protocol hashes and actual run/commit.
Workers run sequentially within each of two jobs, BLAS/OpenMP/MKL threads=1.
Each worker retains the existing **120 seconds / 6 GiB address space** cap
and 5-second kill grace. All 36 attempts per job are retained even if some
fail; no setting is altered or retried. The job time ceiling is 90 minutes
to cover the worst case of 36 sequential timeouts plus setup/upload; this
does not relax the per-worker cap. Expected ordinary runtime is much less.

Only complete finite provenance/identity/bookkeeping passes; missing products
fail completeness. Warnings, resource failures, zero amplitudes and signed
tails remain observables. Numerical agreement is descriptive, never an
empirical morphology acceptance criterion.

After actual CI review, identify which control changes the image and whether
the corresponding Fourier component/grid changes support the hypothesis.
A residual not explained by these interventions remains open. No automatic
choice of the closest arm and no free-shape fitting based on unreviewed local
output. Noise, physical PSF mismatch, chromatic effects, downstream gates and
production remain separate; signed PSFs remain non-photon-ready.
