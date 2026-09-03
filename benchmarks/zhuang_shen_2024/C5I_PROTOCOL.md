# C5i: compact-boundary renderer diagnosis (frozen 2026-09-03)

Frozen before any C5i science-image evaluation. This is a diagnostic selected
after actual C5h CI review, not a change to C5h or a pass/fail morphology band.

## Prerequisite and question

GitHub explicitly confirmed C5h run **33759931812**, commit
`391efc236c440e76ed5dcd7c7b7e71e444fea012`, completed/success for both jobs.
Artifacts **9895134048** (n=1 shard) and **9895141857** (n=4 shard) were
downloaded and checksum-verified. The reproducible audit
`imfit_renderer_33759931812.json` covers all 72 renders, 72 direct fits/start
records, and 600 new arrays. At Re=0.5, n=6, q=0.15, the 4x-to-8x image L1
change is 1.61--1.63%. Successful execution does not validate the renderer
over the unchanged structural box. Do not free host shape yet.

Question: at the compact boundary, how do the archived Imfit sampling levels
compare with GalSim's own accuracy refinement, and how much difference is
attributable to the two packages' definitions of the Sersic b_n constant?
Agreement is evidence about these implementations, not independent PSF
truth or proof of global convergence.

## Software-first decision and sources checked 2026-09-03

Reuse **GalSim 2.8.4**, already installed and pinned by C5d, for its existing
Sersic Hankel/Fourier renderer. Its documented range contains n=0.5 and 6;
its true half-light-radius convention must be distinguished from Imfit's
approximate b_n. Keep the inherited coarse/fine GSParams. GalSim's maximum
FFT size normally warns rather than imposing a hard memory cap, so isolate
bounded workers; never relax accuracy to meet resource limits. BSD-3-Clause
and the existing wheel/CI installation are retained. Documentation:
https://galsim-developers.github.io/GalSim/_build/html/gal.html
https://galsim-developers.github.io/GalSim/_build/html/gsparams.html
https://github.com/GalSim-developers/GalSim/blob/v2.8.4/LICENSE

The tagged Imfit 1.9 source implements finite central subsampling and uses
the Ciotti--Bertin approximate b_n. These are candidate numerical/convention
contributions, not a diagnosis established merely by reading code. Reuse the
C5h b_n conversion helper; do not write another image integrator. PyImfit
shares this engine, so changing wrappers would not independently isolate
this question. Imfit remains GPL-3.0-or-later; no binary is vendored here.
Sources (Git blob IDs also recorded in the experiment config):
https://github.com/perwin/imfit/blob/v1.9/function_objects/func_sersic.cpp
https://github.com/perwin/imfit/blob/v1.9/function_objects/helper_funcs.cpp
https://arxiv.org/abs/1408.1097
https://imfit.readthedocs.io/en/latest/api_ref/design-and-architecture.html

Only a thin convention/provenance/resource adapter is new. No replacement
optimizer, profile quadrature, clipping, profile truncation or alternative
galaxy law is introduced. A Gaussian identity control uses GalSim's existing
Gaussian implementation, not a custom Sersic integrator.

## Frozen images and conventions

- The four compact corners: Re=0.5 native pixel, n in {0.5,6}, q in {0.15,1};
  PA=45 degrees. These are diagnostics inside the original box, not narrowed
  fitting bounds. The four extended C5h corners remain historical evidence.
- Both original signed A/B effective F444W PSFs; raw/normalized input and
  Imfit native images are copied byte-for-byte from audited C5h products.
  Verify the complete parent manifest before selecting inputs. Record every
  selected path/hash and retain the published PSF license/source manifest.
- Same 201x201 centered native crop, 0.03 arcsec/pixel, PSF samples at
  0.015 arcsec. Quintic x/k interpolation, pad factor 4, no depixelization,
  noise padding, shift, clipping or output normalization. The PSF already
  includes detector response: GalSim `no_pixel`, never another Pixel kernel.
- Analytic host flux=1, no AGN, sky, noise, centroid or shape optimization.
  Elliptical profiles use circularized half-light radius and area-preserving
  shear q at 45 degrees; no profile truncation.
- Two explicitly labelled conventions: `nominal_hlr` uses Re=0.5 as a true
  half-light radius; `imfit_bn_equivalent` uses
  `Re_G = Re_I * (b_exact / b_Imfit)**n`, where
  `b_exact = scipy.special.gammaincinv(2*n, 0.5)`.
  The latter represents the same analytic law as Imfit, not a fitted radius
  adjustment. Both variants retain unit total flux and are always reported.
  Historical Imfit radii/images are never overwritten.
- GalSim inherited coarse parameters: folding_threshold=1e-4,
  maxk_threshold=1e-5, kvalue_accuracy=xvalue_accuracy=1e-7; fine:
  1e-5, 1e-6, 1e-8, 1e-8 respectively. Other GSParams remain pinned defaults.
- For n=0.5, draw a GalSim Gaussian with the same circularized half-light
  radius, flux, shear, PSF and settings as each Sersic variant. Record their
  pixel-wise differences; this identity is a control, not an external PSF.

## Frozen comparisons, outputs and resource limits

Two jobs, indexed by inherited parent shard n=1/4, diagnose n=0.5/6.
Eight worker calls/job: q x module x accuracy; each renders both conventions.
In total: **32 Sersic images**, **16 n=0.5 Gaussian control images**,
**16 coarse/fine comparisons**, and **48 Imfit/GalSim direct amplitude fits**
(four shapes x two modules x three archived Imfit levels x two conventions).
All coarse/fine and Gaussian residual products are stored.

For every archived Imfit 2x/4x/8x native image, compare to each fine GalSim
variant without rescaling, and fit just one nonnegative amplitude using the
existing SciPy NNLS helper. Treat GalSim as a comparison reference, not truth.
Store template, reference, amplitude-scaled prediction/residual; unscaled
and scaled L1/reference-L1, signed sums, negative pixels, image hashes,
centroids/moments, RMS-normalized cost, gradient/KKT value and zero flag.
One direct start per fit is recorded explicitly; this is not multistart
optimization or host recovery. Retain both conventions even if one is closer.

Use the existing pinned environment: NumPy 2.5.2, SciPy 1.18.1, GalSim 2.8.4,
Astropy 8.0.1, Photutils 3.0.0. BLAS/OpenMP threads=1. Workers run sequentially
within each job, maximum two jobs. Each worker has 120 seconds wall time
with a 5-second GNU-timeout kill grace, and a 6 GiB address-space cap via
Python's standard `resource.RLIMIT_AS`. These are resource observables, not
scientific accuracy settings. A worker that cannot render retains its
configuration, stdout/stderr, warnings and error, and is not retried with
changed settings. Record parent/child runtime and peak RSS.

Pass only complete, finite, provenance-consistent bookkeeping; retain every
attempt/failure and fail completeness if required products are missing.
Algebra/identity checks use the existing 1e-12 floating-bookkeeping scale;
no cross-renderer, Gaussian-identity or empirical recovery threshold is
introduced. Report all differences descriptively. Signed PSFs remain
non-photon-ready; float32 archived Imfit FITS remain float32 evidence.

## Next decision

After explicit CI success and inspection of all outputs, compare Imfit
sampling drift with GalSim refinement, Gaussian identity and b_n effects.
Decide whether a renderer integration/convention repair is needed before
free-shape fitting. Neither a smaller residual nor package agreement alone
closes Zhuang--Shen, Dewsnap, real-survey, or production gates. No prior
experiment, acceptance criterion or structural bound is modified.
