# C5k: bounded Fourier-spacing/cutoff diagnostic (frozen 2026-09-03)

Frozen before any C5k image. This is a new question, not a repaired or passed
C5j. C5j's original code, nine-arm protocol, outputs/failures and completeness
rule remain unchanged; its planned workflow is retained outside the active
workflow directory because rerunning its known allocation failure in CI adds
no scientific value.

## Evidence and question

C5i **33766246396** / `169018474ae502a537bc736a64ead778f24e42cd` is the
last GitHub-confirmed successful parent. Its actual artifacts were audited
in `compact_renderer_33766246396.json` (48 starts, 308 arrays). Neither
GalSim's up-to-0.903% coarse/fine change nor the percent-level Imfit comparison
establishes convergence.

The separately frozen **LOCAL** C5j attempted all 72 workers. It produced
68 Sersic images, 36 Gaussian controls, 68 direct starts and 892 new arrays;
four n=6 conservative-bandlimit workers failed with MemoryError under the
unchanged 6 GiB cap. That stage is **incomplete**, not passed. Its audit
`c5j_local_20260903.json` retains every result, warning, failed command,
source/protocol/input hash and available file. The four failed arms are not
silently removed, rerun with a larger cap, or relabelled as successes.

For flattened n=6, changing only folding_threshold reproduces the C5i fine
image to within 7.81e-8 L1 (A) / 5.11e-8 (B), whereas changing only maxk or
xvalue settings leaves the coarse image unchanged. Tightening the separate
Hankel integration tolerances changes the fine image by about 7e-7 L1.
These are local, same-renderer diagnostic results, not CI confirmation or
independent truth. They implicate grid spacing rather than b_n or radial
quadrature as the dominant coarse/fine effect in these cases.

The public calculate_maxk=False option instead takes the very long Fourier
tail of the Quintic interpolant. For n=6 it requests roughly 243000--364000
square FFTs; requested single allocations were about 440--989 GiB. This
candidate is infeasible, not a reason to loosen the limit. Its failure does
not answer whether *modest, nested increases* beyond the inherited PSF
cutoff change the same sampled empirical model at controlled grid spacings.
That narrower, resource-bounded sensitivity question is C5k. Finite nested
cutoffs are not equivalent to the failed full-interpolant-range option and
cannot prove convergence over all frequencies.

## Software-first assessment

Sources rechecked 2026-09-03 after the resource failure:

- GalSim's tagged convolution implementation uses the minimum component
  maxk, not an optimized cutoff based on their product. The large Sersic
  maxk and interpolant range therefore combine into a conservative grid:
  https://github.com/GalSim-developers/GalSim/blob/v2.8.4/src/SBConvolve.cpp
  https://github.com/GalSim-developers/GalSim/blob/v2.8.4/include/galsim/SBConvolve.h
- InterpolatedImage documents `_force_maxk` explicitly for Fourier artifacts
  not addressed by lowering maxk_threshold. Despite being documented, its
  underscored API is version-sensitive; pin GalSim 2.8.4, retain source blob
  `9ed6d853f0eb63dc6ca6bd6c8bc3a12d9611abbf`, and test the applied physical
  units and propagation rather than assuming the override survives:
  https://galsim-developers.github.io/GalSim/_build/html/_modules/galsim/interpolatedimage.html
- The existing GSParams minimum_fft_size and actual FFT-grid helper provide
  the spacing intervention without writing an FFT or quadrature routine:
  https://galsim-developers.github.io/GalSim/_build/html/gsparams.html
  https://galsim-developers.github.io/GalSim/_build/html/_modules/galsim/gsobject.html
- The prior Bernstein & Gruen interpolation analysis remains relevant, but
  its numerical error figures are not adopted as thresholds:
  https://arxiv.org/abs/1401.2636v2

Reuse GalSim (BSD-3-Clause), its existing interpolated-image/Fourier engine,
NumPy atomic archive writes and SciPy NNLS. Same exact dependency pins as
C5i/C5j. Reuse C5j's bounded worker through an explicit model-construction
adapter in a separate process; its historical construction is not changed.
No independent implementation, deconvolution, optical band limit or
production dependency is claimed. A different fitter cannot by itself
settle a rendering-support question. The estimated maximum new k-grid is
orders of magnitude below the failed full-range option; retain the same
hard caps and record any failure instead of promising resource success.

## Frozen settings and comparisons

Same four C5i corners (Re=0.5 native pixel, n=0.5/6, q=0.15/1), both raw
signed PSFs, nominal_hlr, analytic flux=1, PA=45, centered 201x201 output,
0.03 arcsec native pixels and 0.015 arcsec PSF samples. Same Quintic x/k,
pad_factor=4, no depixelization, truncation, extra Pixel, AGN, noise, shift,
clipping or output normalization. `no_pixel` remains mandatory because the
effective PSF already includes detector response. No structural bound changes.

Seven arms per shape/module, always retained:

- `replay`: unchanged C5i fine source/PSF/settings and automatic support.
- Six crossed arms: minimum_fft_size **1024 or 1536** and forced PSF
  maxk **1x, 2x or 4x** the same module's unchanged C5i-fine PSF maxk.
  These two FFT-friendly grid sizes are frozen numerical padding choices,
  not changed output apertures. All other GSParams remain C5i fine, including
  the original integration tolerances.
- For all six crossed arms, calculate_stepk=False uses the full published
  PSF input extent (including signed wings); calculate_maxk=True is retained
  but overridden by the documented `_force_maxk` value. Each crossed arm is
  built fresh. Verify the override is identical before/after convolution;
  both components carry identical GSParams so propagation cannot reset it.
  Record physical source/PSF/convolution stepk and maxk plus actual grids.
- The reference cutoff is calculated from the unchanged effective PSF,
  not fitted to science images. Multipliers only increase that cutoff;
  no arm is selected after seeing residuals. Nested comparisons inspect
  spacing at fixed cutoff and cutoff at fixed spacing, including possible
  nonmonotonicity. The original failed full-range option remains unresolved.

Two inherited jobs, **56 Sersic images, 28 Gaussian controls and 56 direct
amplitude starts**. Each n=0.5 arm retains its exact-form GalSim Gaussian
control. Use the same 260 physical Fourier probes, actual-grid observer,
per-worker warning/error capture, atomic/read-back arrays and manifests as
C5j. Preserve every new image and signed residual product. Each arm retains
the inherited nonnegative, no-ceiling amplitude comparison to the archived
C5i fine image, CSV/JSON start record, prediction/residual/cost/KKT values,
plus unscaled comparisons with C5i and Imfit 8x. Save all seven-arm pairwise
image differences descriptively; no optimizers are rerun on parent images.

The replay must match C5i at the inherited 1e-12 bookkeeping scale. Check
same-grid Fourier products, normalization/units, source identity and complete
finite products. There is **no numerical or morphology recovery band**.
All parent files are checksum-verified before selecting inputs; record the
actual GitHub parent/run/commit, protocol/audit/adapter-source hashes.

Keep **120-second workers, 5-second kill grace, 6 GiB address-space cap**,
single BLAS/OpenMP threads and sequential workers within each of two jobs.
There are 28 attempts per job; a 70-minute job ceiling accommodates all
possible individual timeouts plus setup/upload without changing any worker
limit. Warnings and failures are saved; missing required images still fail
completeness. No retries with altered settings and no reclassification of
the C5j failure.

## Next scientific decision

After explicit C5k GitHub success and full artifact review, compare both axes
of numerical sensitivity with the archived Imfit differences. Determine
whether a bounded cutoff/spacing sequence is stabilizing, whether the
observed difference instead remains unresolved, or whether a different
maintained rendering approach needs controlled comparison. Do not free
host shape solely because CI succeeds. Physical PSF, identifiability/noise,
later literature gates and real-survey validation remain separate and open.
