# C5l: finite numerical-cell response diagnostic

Frozen 2026-09-03 UTC, before any C5l image. Verification only.

## Reviewed prerequisite and question

C5k run 33788705952 / 7ad6e1ca1b6a78dcde83d6cdea9e3c1bc26bd33b
explicitly completed/success in both jobs. All 56 starts, 168 pairwise
comparisons and 896 arrays were inspected. No failed worker, zero amplitude
or missing FFT receipt remains in CI; all 16 large-FFT warnings are retained.
See fourier_grid_33788705952.json and the reproducible read-only review.

At the fourfold PSF cutoff, changing grid size 1024 to 1536 changes images
by at most 3.29e-6 L1. However, at grid1536, doubling to quadrupling the
cutoff changes n=6 images by 0.0660--0.1067%. Cross-renderer differences
against Imfit8 are 0.214--0.273% for n=6, and 1.699--1.740% for flattened
n=0.5. This does not establish either renderer as truth or justify shape fits.

The Imfit adapter integrates its intrinsic profile over finite *numerical*
cells before sampled convolution. The canonical GalSim comparison uses no
extra cell response. Can that finite-cell convention explain part of the
remaining differences, with the cell size approaching zero? Test a uniform
square-cell surrogate explicitly; do not assert it exactly reproduces
Imfit's adaptive subsampling/discrete convolution.

## Software-first decision

Sources checked 2026-09-03:

- Erwin 2015: https://arxiv.org/abs/1408.1097
- Pinned Imfit source: https://github.com/perwin/imfit/blob/v1.9/function_objects/func_sersic.cpp
  GetValue averages subpixels, while CalculateSubsamples depends on elliptical
  radius and switches to center evaluation outside its central region.
  A single uniform box is therefore a diagnostic surrogate, not exact
  equivalence. Preserve existing Imfit 1.9.0 C5h 2x/4x/8x images and binary
  provenance; do not rerun or edit that historical experiment.
- GalSim's existing unit-flux Pixel and convolution implement the square-cell
  response; no new integrator, renderer or FFT is needed:
  https://galsim-developers.github.io/GalSim/_build/html/gsobject.html
  https://github.com/GalSim-developers/GalSim/blob/v2.8.4/galsim/box.py
- Keep GalSim 2.8.4 (BSD-3-Clause), NumPy2.5.2, SciPy1.18.1,
  Astropy8.0.1 and Photutils3.0.0. Existing wheels and bounded workers suffice.
  PyImfit shares Imfit's engine and would not independently test this convention.

Thin adapters only assemble existing objects, verify parent inputs and
serialize comparisons. Additional finer Imfit runs and larger Fourier
cutoffs are deferred: this smaller convention test isolates a specific
unresolved effect without increasing the established resource caps.

## Frozen experiment

Same four compact corners: Re=.5 native pixel, n=.5/6, q=.15/1,
PA45, analytic flux1, centered 201x201 crop, .03 arcsec native pixels,
.015 arcsec PSF samples, both unchanged signed empirical A/B PSFs.
No AGN, noise, centroid shift, clipping, truncation, normalization or
structural-bound changes. Same nominal half-light-radius convention.

Use C5k grid1536_k4 settings for every arm; retain its finite-cutoff limitation
and warnings. Four arms per shape/module:

- no_cell: exactly replay the archived C5k grid1536_k4 image.
- cell2, cell4, cell8: convolve the same continuous model with a unit-flux
  square Pixel of side .03/2, .03/4, .03/8 arcsec, respectively.

Always draw with no_pixel. These three intentionally added *numerical-cell*
responses are NOT another physical detector pixel and are NOT adopted for
production or as corrections to empirical PSFs. The canonical physical
effective-PSF model remains no_cell. Report each response separately.
Represent the PSF plus optional cell as a composite object so the recorded
host-times-PSF Fourier product includes that cell explicitly.

Compare every arm with ALL archived Imfit2/4/8 native images, retaining
unscaled L1/flux/image differences and the same single nonnegative,
no-ceiling amplitude projection, predictions, residuals, costs and KKT
diagnostics. Label comparisons where cell size matches Imfit sampling;
retain off-diagonal comparisons and no_cell, not just the closest fit.
Save all six arm-pair residuals per shape/module, plus n=.5 Gaussian controls,
260 Fourier probes, exact FFT receipts, warnings, runtimes and file hashes.

Two jobs: 32 Sersic images, 16 Gaussian controls, 96 direct starts,
48 arm-pair comparisons. C5k and C5i artifacts are checksum-verified;
C5i supplies its archived C5h Imfit2/4/8 images. No parent result is refitted
nonlinearly or overwritten. Parent run/commit/protocol/array provenance is saved.

The inherited no_cell replay scale is 1e-12 absolute. All finite-product,
source-identity, Fourier-product, archive and complete-receipt checks remain.
There is no numerical recovery band or physical acceptance cut. Preserve
every failure. Use 120-second workers, 5-second kill grace, 6 GiB address-space
cap, single threads, sequential workers/job and max two parallel jobs.
No retries with changed settings. Thirty-five minutes/job covers 16 capped
workers plus setup and uploads.

## Decision after CI review

Check whether matched-cell comparisons account for the sampling trend,
whether residuals persist or behave nonmonotonically, and how the remaining
Fourier-cutoff error limits attribution. An improved numerical match does
not validate morphology or make a uniform box identical to Imfit. Only then
select further sampling controls or a free-shape implementation. All later
physical/chromatic PSF, cross-fitter and survey-injection gates remain open.
