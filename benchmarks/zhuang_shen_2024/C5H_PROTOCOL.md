# C5h: independent host-renderer convention and resource preflight

Frozen 2026-09-03 BEFORE evaluating C5h science images. Verification only.

## Decision and prerequisite

C5g run 33740141863 at de3ed949d3497263c458a897f703d5a5e9a6f295 and
regression 33740141703 explicitly completed/success. Both C5g artifacts were
downloaded and SHA-256 verified. All 24 fixed/free comparisons, 72 starts and
384 new arrays were audited against the archived C5d images and model algebra.
All starts report success; no centroid bound was active. A wrong PSF produces
apparent nuclear offsets up to 0.266074 native pixel. For n=4, true B / fit A,
AGN/host=10, releasing the nuclear position changes host flux from 0.849526
to zero. True A / fit B changes from 3.331675 to 1.744172. The true host flux
is one. These conditional signed-model solutions do not validate physical
astrometry or host morphology. See nuclear_centroid_33740141863.json.

Freeing host shape is the next scientific goal, but the existing GalSim n=4
reference already needed an approximately 12300-square FFT and 2.56 GB peak
RSS. Extending it blindly across the unchanged Re=[0.5,60], n=[0.5,6],
q=[0.15,1] box would make resource failures part of the optimizer landscape.
First test an existing independent Sérsic/convolution implementation. Do not
narrow that box, truncate the galaxy, weaken GalSim accuracy, or interpret a
renderer substitution as physical recovery.

## Software-first decision and pins

Reuse the author's Imfit 1.9.0 Linux x86-64 makeimage executable (GPL-3.0-or-
later), released 2022-11-27 and still the latest tagged release checked today:
https://www.mpe.mpg.de/~erwin/code/imfit/
https://github.com/perwin/imfit/releases/tag/v1.9
https://arxiv.org/abs/1408.1097

Author archive:
https://www.mpe.mpg.de/~erwin/resources/imfit/binaries/imfit-1.9.0-linux-64.tar.gz
SHA-256: 9eb10a62baab87de98744c247f7a10ea02b05d32996760b7cef100f5f02a7089
makeimage SHA-256:
4fe27a3d3e48f0c4931ee3fb5ad571330fdbf27f6c327f48990418bdcb965984

The author binary statically links FFTW/GSL/CFITSIO/NLopt and runs on the
Ubuntu 24.04 x86-64 runner. Save its version, archive/executable hashes,
README and license-bearing source metadata; no binary is vendored into this
repository or adopted as a production dependency. PyImfit 1.1 was considered:
same underlying algorithm, but Linux needs a source build; the published CLI
avoids adding a compiler/ABI dependency just for a renderer comparison.
This is not a claim that an older package release is universally reliable.

Official conventions and source checked:
https://imfit.readthedocs.io/en/latest/imfit_tutorial.html
https://pyimfit.readthedocs.io/en/latest/psf_convolution.html
https://pyimfit.readthedocs.io/en/latest/installation.html
https://github.com/perwin/imfit/blob/v1.9/function_objects/func_sersic.cpp
https://github.com/perwin/imfit/blob/v1.9/function_objects/helper_funcs.cpp
https://galsim-developers.github.io/GalSim/_build/html/gsobject.html

Imfit uses 1-based centers, ell=1-q and PA measured counterclockwise from +y;
our 45 degrees from +x becomes Imfit PA=-45 degrees. Re is semi-major-axis
Re in grid pixels. Its I_e is intensity per grid pixel, not total flux.
A small analytic-unit adapter uses the documented Ciotti-Bertin b_n formula
from the pinned source and SciPy gammaln to set total analytic Sérsic flux=1.
Record b_n versus scipy.special.gammaincinv(2n,0.5), rather than silently
replacing Imfit's approximation. Imfit's own central subsampling stays ON.

Do not use Imfit's native oversampled-region downsampling as a drop-in for
these effective PSFs: its final block averaging is not our no-second-pixel
convention. Instead invoke its unchanged renderer on a fine numerical grid
and take coincident detector centers, as specified below. This thin adapter
is necessary for unit/phase translation; no new profile integration,
interpolation, convolution or optimization algorithm is written.

## Frozen numerical and scientific design

Use actual C5g artifacts 9887407188 (n=1) and 9887408196 (n=4), including their
unchanged C5d parent files; verify against the committed C5g/C5d audits.
The 201x201 native crop, 0.03 arcsec pixels, 0.015 arcsec empirical samples,
original signed normalization, finite published support, negative wings,
source registration, host center and PA are unchanged. No noise, physical
PSF reconstruction, clipping, recentering, deconvolution or sharpening.

For each module A/B and each numerical sampling s=2,4,8:

1. Sample the SAME C5d continuous GalSim fine-Quintic effective PSF on a grid
   h=0.03/s arcsec. Use surface-brightness rendering and multiply by h^2.
   Include eight original-sample zero-padding rows per edge: kernel size
   208*s+1. Do not renormalize the fine-grid kernel; record signed sum and
   negative mass. The shared PSF interpolator is NOT independent ground truth.
2. Render Imfit's intrinsic Sérsic and its existing PSF convolution on an odd
   grid 200*s+1, centered at 100*s+1 in 1-based coordinates. Use --no-normalize
   and --max-threads 1; leave central profile subsampling enabled. Keep its
   native finite-kernel convolution padding. Record output FITS precision.
3. Obtain the native image as s^2 * fine[::s,::s], with no block sum. The
   finite-grid intrinsic-cell integration is a numerical quadrature whose
   error must be measured by refinement; it is not another detector response.
   No cropped-image flux normalization is permitted.

Truth-shape rows: n=1 or4, Re=16 native pixels, q=0.6, PA=45 degrees.
Each of the six templates per host is compared with the archived C5d GalSim
fine-Quintic host, saving image differences and L1/flux/centroid/moment
diagnostics. Compare successive sampling levels without a new pass band.

Resource/sampling probes cover all eight corners of the unchanged structural
box: n=.5/6, Re=.5/60, q=.15/1, both modules and all three sampling levels.
The n=1 job handles n=.5 corners; the n=4 job handles n=6 corners. These are
48 probe templates, not fits or replacement truth cases. Compare refinements,
save every native image, timing, peak child RSS, warnings/errors and partial
output. Do not interpret failure of a renderer probe as astrophysical loss.

Using the existing 12 C5d AGN+host data images, fit both nonnegative amplitudes
at each new truth-shape template and the ORIGINAL C5d zero-position point
template for the adopted module. Host and nuclear positions stay fixed here;
C5g's released positions are not used to tune the new renderer. Same inherited
full-crop RMS-normalized NNLS, no amplitude ceiling. 72 direct flux solves,
with one start record each, record all zero amplitudes/costs/residuals/KKT
quantities and differences from C5d. These are renderer-sensitivity
diagnostics, not free-shape or optimizer comparisons.

Analytic controls in each job: circular Gaussian source sigma=.12 arcsec,
effective Gaussian PSFs of optical FWHM=.09/.165 arcsec, s=2/4/8. Use Imfit
Gaussian with analytic total flux=1 and compare to the existing exact
Gaussian-plus-native-pixel integral. Save expected/image/residual arrays;
report errors without a new empirical recovery threshold. Point-template
identity, grid-center/area identities, completeness, provenance and finite
algebra are implementation checks. Preserve all old tests and criteria.

Two host jobs, max-parallel=2, 30 minutes each, Python3.12 and the exact C5e/g
requirements. A per-render 120-second timeout is an explicit resource probe
limit, not a scientific rejection threshold. Capture failure and proceed to
remaining predeclared renderer cases; if any case fails, archive the partial
record and fail the job. Never drop a difficult corner or change sampling
after inspecting a result. No automated tolerance selection or gate closure.
GNU time records per-child peak RSS; its executable hash/version are saved.
GNU timeout terminates the process group at 120 seconds (five-second kill
grace), avoiding an orphan renderer. A relocated GNU time executable may be
selected by GNU_TIME in a minimal local container; this changes no images.
https://www.gnu.org/software/coreutils/manual/html_node/timeout-invocation.html

Next decision: inspect cross-renderer differences, refinement and all bound-
corner resource outcomes before selecting a free-shape implementation. Imfit
is a candidate, not yet a validated replacement; Dewsnap/cross-fitter and
physical/chromatic-PSF gates remain open.
