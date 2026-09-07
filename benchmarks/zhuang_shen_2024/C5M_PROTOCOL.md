# C5m: bounded Imfit sampling refinement

Frozen before new images, 2026-09-03 UTC. Prerequisite: C5l run
33798675379 at 094de88e88b668015658536d13583c201cfaaaf2, explicitly
completed/success for both jobs and all steps. All 96 direct starts and
720 new arrays passed the unchanged read-only audit. Its uniform-cell
surrogate does not consistently explain the Imfit difference. In particular,
matched cell8 still differs by 1.700%/1.693% for flattened n=0.5, A/B.
No cell response is adopted as a physical model or correction.

## Question and reuse decision

Does doubling Imfit's external numerical sampling from 8 to 16 reduce the
remaining discrepancy, and is it feasible under the existing resource cap?
This is not a convergence or recovery pass/fail test. Preserve nonmonotonic
behavior and failures. Do not free host shape based on CI completion alone.

Focused source check: Imfit v1.9 Sersic::GetValue averages over subpixels;
CalculateSubsamples uses elliptical radius and stops subsampling at r>=10
in computational pixels. Consequently the C5l uniform box is not its exact
operation. Reuse the unmodified checksum-pinned Imfit 1.9.0 makeimage and
existing C5h adapter with a scoped numerical-sampling allowlist. Do not
rewrite that integration algorithm or modify the historical C5h module.

- https://github.com/perwin/imfit/blob/v1.9/function_objects/func_sersic.cpp
- https://imfit.readthedocs.io/en/latest/api_ref/design-and-architecture.html
- https://www.mpe.mpg.de/~erwin/code/imfit/
- Erwin (2015), https://arxiv.org/abs/1408.1097

PyImfit uses the same engine and is not an independent answer; a new binary
build or cross-fitter adds packaging/convention changes without isolating
this question. GalSim 2.8.4 supplies only the existing PSF interpolant here.
The shared PSF interpolation and finite GalSim cutoff remain limitations.
Imfit GPL-3.0-or-later license files and binary identity are retained; GalSim
BSD-3-Clause and existing Python pins are unchanged. No new dependency,
production implementation or bespoke renderer is introduced.

## Frozen design

- Four compact corners: n=0.5/6, Re=0.5 native pixel, q=0.15/1, PA=45 deg,
  intrinsic analytic flux one; empirical A/B PSFs. Eight distinct scenes.
- External numerical sampling 8 and 16: 16 new Imfit renders total, two
  sequential-worker jobs (n=0.5 and n=6, historical shard labels 1 and 4).
- Sampling8 is a replay of the archived C5h/C5i output within the inherited
  absolute 1e-12 bookkeeping check. Historical arrays are never replaced.
- C5h conventions unchanged: semi-major Re, Imfit b_n amplitude conversion,
  one-based center 100*s+1, PA=-45, ell=1-q; 200*s+1 fine image; kernel
  208*s+1 with h=.03/s arcsec, sampled SB times h^2. Signed kernel retained
  with --no-normalize. Native image is s^2*fine[::s,::s]. No extra physical
  detector integration, sharpening, clipping, padding change or renormalizing.
- For every render, direct nonnegative amplitude comparisons to archived
  Imfit8 and C5l canonical no_cell: 32 fits, all saved, no amplitude ceiling.
  Also eight explicit within-Imfit 16-minus-8 image comparisons. No fit
  selects or changes shape, centroid, nuclear flux or physical PSF.
- No AGN, noise, image phase change or new morphology tolerance. Gaussian
  equivalence products from C5l remain in the parent; this isolates Imfit
  refinement, not a new independent ground truth.

## Resources and completeness

Each isolated worker generates its kernel and invokes makeimage under the
existing 120-second timeout, five-second kill grace, six-GiB address-space
cap and one thread. No altered-setting retry. New 16x arrays are four times
the area of 8x arrays; allocation and timeout failures are recorded, not
removed by raising caps. Job wall limit 35 minutes. Science settings are
identical locally and in CI; the binary integration test may be skipped
locally only if the pinned executable is unavailable, explicitly reported.

Archive config/protocol/producer/binary and parent hashes, full stdout and
stderr, commands, FITS including BITPIX, native and kernel arrays, all fit
starts, residuals, costs, gradients, KKT checks, image statistics, timings,
failures and complete file/array manifests. A worker failure makes the
experiment incomplete and CI nonzero but retains completed products.
Expected complete new NPZ array count: 168 (84 per shard). All 16 FITS
outputs are also retained and checked against the native reduction.

Interpret sampling drift and cross-code difference descriptively, including
flux and signed wings. Neither agreement nor better residual establishes
full-range convergence, identifiability, photon readiness or survey recovery.
