# C5 — Zhuang & Shen PSF-mismatch verification

Status: IN PROGRESS. C5a/C5b/C5c reviewed; C5d empirical-PSF transfer and
fixed-shape flux diagnostic frozen 2026-09-03 UTC before its execution.

Primary reference: Zhuang & Shen (2024), ApJ 962, 139,
https://arxiv.org/abs/2304.13776 (abstract checked 2026-09-03).
The authors find PSF mismatch can bias host flux and structure, with different
concentration trends for broader/narrower adopted PSFs. Reported F444W spatial
FWHM variation reaches about 3%; this is not a universal PSF specification.
Our existing pinned public-table analyzer and BDATA-001 remain separate.

## C5a frozen experiment

Question: how does an explicitly wrong PSF width bias decomposition when
noise, source geometry and fitting policy are held fixed? Reuse ACTUAL
noiseless images from independent-GalSim run `33661985266`, commit
`94fc982e17b248b0227230554d6b47c5e1d40de8`, artifacts `agn-galsim-n1`
(`9859077660`) and `agn-galsim-n4` (`9859083212`). Verify source commit,
host identity and exact data hashes. GalSim host accuracy/refinement and
the matched 8x fitting floor were reviewed in the preceding AGN gate.

Retain true Gaussian FWHM=3 pixels, n=1/4, Re=16 pixels, q=0.6, PA=45
degrees, unit analytic host flux and AGN/host=0.1/1/10. Fit FWHMs
2.91, 3.00 and 3.09 pixels (factors 0.97/1/1.03). The symmetric 3% perturbation
is a controlled width-scale choice motivated by the published variation,
NOT the authors' empirical broader/narrower PSFs or a literal F444W scene.
In particular equal FWHM need not mean equal core/wing structure.

Change BOTH the host-convolution PSF and nuclear template consistently.
Render each directly using an 8x padded fine grid and analytic Gaussian
nuclear pixel integral; no deconvolution or sharpening kernel is constructed.
Matched-width control must reproduce the inherited renderer algebraically
(unit test); it measures the numerical baseline within this new diagnostic.
No noise, PSF core/wing changes, source-SED changes, free center/PA or sky fit.

Fit Re,n,q and NNLS amplitudes using all inherited starts, bounds, tolerances
and max_nfev=160. Retain minimum-cost winners regardless of success, all starts,
boundary flags, predictions/residuals and fitted PSF images. Eighteen winners,
54 starts, two host shards with maximum two concurrent. Config is written
before fitting. CI checks complete finite output, never agreement with a
desired sign or a new recovery band. Report signed host/nuclear flux and
structural biases versus matched controls and truth; retain bound-limited
outcomes. A disagreement with a published tendency is a diagnostic, not a
reason to retune widths or bounds.

Next: compare systematic width effects with the measured numerical baseline,
then select empirical/core-wing and centroid tests under the existing C5
protocol. C5a alone cannot close C5, Dewsnap, chromatic PSF, or survey gates.
Workflow `gate-c-agn-psf-width`, resolved by implementation commit; do not
duplicate active runs. No production implementation is authorized.

Local implementation checks: nine targeted tests passed, including exact
matched-renderer identity and predeclared PSF normalization/symmetry checks.
The first n=4, ratio=0.1 three-width smoke cases completed; saved hashes,
residuals and L1 metrics were verified. This is not C5a GitHub success.

## C5a GitHub review — 2026-09-03 UTC

Run `33701100594`, commit `47ea514056fcdcf0af19eaf637ef1a9a9948c9c6`,
explicitly completed/success at 00:52:44Z; both jobs succeeded. Artifacts
`agn-psf-width-n1` (`9873614863`) and `agn-psf-width-n4` (`9873583567`)
were downloaded and reviewed: 18 winners, 54 starts, 18 image bundles.
CSV/JSON fields, configuration, commit, truth hashes, finite image arrays,
residual identities, normalized costs/L1 metrics and minimum-cost winner
selection were checked. All 54 starts report optimizer success, but 15 starts
and five winners have at least one boundary flag. No bounds were changed.

Matched-width n=4 Re bias remains -0.014582% and n=1 -0.0002394%.
At ratio=0.1, n=4 narrower/broader PSFs yield delta-n +0.4621/-0.4034
and host-flux errors +4.7405%/-4.3056%. Thus concentration trends agree
qualitatively with the primary reference, but a host-flux overestimate is
not universal in this width-only Gaussian experiment. At ratio=10, the
narrower PSF drives both hosts to Re=0.5 pixels; the broader PSF drives
n=1 to n=0.5 and n=4 to zero host amplitude. These are severe model-mismatch
outcomes, not evidence of morphology recovery or literal survey reproduction.

The broader-PSF ratio=10 cases require an optimizer-landscape diagnostic:
for n=1, two starts stop at zero host amplitude (cost 5.7938637726), while
one finds nonzero host flux (cost 5.5386592719). For n=4 all three stop at
zero host amplitude with cost 4.5914188479 and unchanged starting shapes.
With the NNLS host coefficient zero, the profiled objective is locally
independent of host shape: zero gradient does NOT show that the host is
physically absent or that no better basin exists. The observed n=1 start
cost spread is 0.2552045007; n=4 starts agree in cost but not inferred shape.

## C5b frozen experiment — before inspecting new results

Search the objective landscape of ONLY the two archived ratio=10,
width-factor=1.03 images from C5a. No new noise, PSF, geometry, or bounds.
Verify source commit/host/hash and retain source winner plus all three starts.
Evaluate NNLS fluxes at the Cartesian product Re=(0.5,1,2,4,8,12,16,24,40,60),
n=(0.5,1,2.5,4,6), q=(0.3,0.6,0.75,1): 200 grid points per host.
Select the three lowest-cost points, with stable grid-index tie breaking,
without filtering by host flux or proximity to truth. Refine all three using
the inherited TRF bounds, max_nfev=160, ftol/xtol=1e-10 and gtol=1e-7.
This is explicitly a NEW diagnostic start policy; historical C5a is immutable.

Record every grid evaluation, all refinement starts, signed cost differences
against the original winner, predictions, residuals, host truth and PSF.
No post-hoc acceptance band: CI requires complete finite outputs, not improved
cost, positive host flux or desired bias signs. A finite grid plus local
refinement cannot certify global optimality. If a lower-cost solution is
found, distinguish the corrected diagnostic from the original start-limited
result before proceeding to core/wing, empirical PSF and centroid tests.
Workflow `gate-c-agn-psf-plateau` is resolved by its implementation commit;
do not duplicate an active run. Two host jobs, maximum concurrency two.

C5b local implementation checks: eleven targeted tests passed, including an
explicit NNLS zero-host plateau counterexample and unchanged renderer tests.
A full LOCAL n=4 smoke execution completed 200 grid points and three
refinements; all saved start costs and image residuals were checked. It found
a nonzero-host candidate with cost 4.5178548622 (difference -0.0735639857
from C5a), Re about 31.282 pixels and n at its lower bound 0.5. This supports
running the diagnostic, not morphology recovery. It is NOT GitHub success;
both CI host shards must be inspected before advancing dependent science.

## C5b GitHub review — 2026-09-03 UTC

GitHub confirms run `33705072892` completed/success on commit
`9159a6342880d5b2d21eee7371ba577736a923bc`, both jobs successful. Downloaded
artifacts `agn-psf-plateau-n1` (`9874939966`, ZIP SHA256
`096daa27745511a54a28d2f710a128cffa9bb6d2d440c632eee62b96b03b965b`)
and `agn-psf-plateau-n4` (`9874933610`, ZIP SHA256
`cacdae7157199d2e95a752dae88cb1a918734961dfcafd67aff04d090ad7537c`).
Reviewed all 400 grid evaluations, six refinements and both image bundles:
CSV/JSON equality, frozen grids/seeds, provenance/config, exact data hashes,
finite arrays, original/new residual identities, every refinement cost and
the minimum-cost selection. The CI environment records NumPy 2.5.2 and
SciPy 1.18.1. All six refinements report success, nonzero host flux and the
lower n boundary. Zero host flux occurs at 155/200 and 162/200 grid points
for true n=1 and n=4 respectively; these are grid counts, not probabilities.

The n=1 winner remains the C5a basin (cost 5.538659271932353 versus
5.538659271948071; signed difference -1.5718e-11 retained). For n=4 the
best grid point already improves the old zero-host result, and refinement
reduces cost from 4.5914188479068105 to 4.5178548622094645, difference
-0.07356398569734601. The corrected diagnostic has Re=31.28269785 pixels,
n=0.5, q=0.58898643, host flux=0.47542425, nuclear flux=10.41363161.
Thus the historical n=4 zero-host result is start-limited, NOT evidence that
the image contains no host. The better fit still badly misrecovers a true
Re=16, n=4, unit-flux host; wrong PSF physics remains after optimizer repair.
This finite search establishes a counterexample, not a global-optimum proof.

## Literature/software decision — 2026-09-03 UTC

The user's literature/software-first policy applies before further custom
algorithm development. Checked the SciPy public differential_evolution API
(https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html)
and its installed documentation: bounded population search, seeded RNG,
Sobol initialization and iteration callbacks are already provided. The
SciPy source distribution uses BSD-3-Clause licensing; it is an existing
dependency. Choose a thin public-API adapter, not a custom global optimizer.
Pin NumPy 2.5.2 / SciPy 1.18.1 to the actual C5b CI environment, avoiding
a deliberate dependency-version change in this comparison.

Also checked Erwin (2015), https://arxiv.org/abs/1408.1097, and the author's
Imfit documentation https://www.mpe.mpg.de/~erwin/code/imfit/. Imfit offers
Sersic plus PointSource models, supplied PSFs, multiple minimizers including
DE, variance-map choices and PyImfit integration. It remains an independent
image-fitter candidate, not the immediate replacement here: adopting it
now would change rendering/pixel-integration/PSF-interpolation conventions
at the same time as search. Its GPL-3 license and compiled dependencies
require explicit review before any future integration; no production
dependency is introduced. Separate convention-controlled cross-fitter tests
remain on the roadmap. Neither package can recover information missing from
the data or make a wrong PSF physically correct.

## C5c frozen experiment — before inspecting new results

Question: does a population-based, non-gradient search independently of the
C5b grid discover the same or a better basin? Reuse ONLY the two actual C5b
ratio=10, width-factor=1.03 images; verify source commit/host/data hashes and
fitted point-template identity. Save source summary plus file SHA256 manifest.
Keep 129-pixel stamp, 8x renderer, NNLS nonnegative amplitudes, RMS-normalized
noiseless objective, fixed centers/PA/sky, and Re=[0.5,60], n=[0.5,6],
q=[0.15,1]. Recompute the archived C5b winner's objective and report numerical
drift explicitly. No new PSF/noise/scene effect and no new recovery band.

Use scipy.optimize.differential_evolution in (ln Re, ln n, q), best1bin,
Sobol initialization, popsize=10 (32 members after Sobol rounding),
maxiter=60, tol=1e-7, atol=0, mutation=(0.5,1), recombination=0.7,
updating='deferred', workers=1, vectorized=False, polish=False and x0=None.
Two fixed numpy default_rng seeds 20260903/20260904, NOT noise realizations;
no C5b winner or truth seed is injected. At most 1952 DE objective evaluations
per seed, four searches total in two host jobs. DE's population-energy
stopping test is an algorithm criterion, not morphology acceptance or proof
of global optimality. Retain budget exhaustion and all success/failure flags.

After each search, perform exactly one inherited C5b TRF refinement with
unchanged tolerances/bounds/max_nfev; save raw DE and refined outcomes
separately. Keep every evaluated DE trial (including initial members), every
generation's population/energies, final populations, all four candidates per
host, truth/prediction/residual products, and signed costs versus C5a/C5b.
CI only checks complete finite records and bookkeeping identities. Retain
the minimum-cost candidate even if an optimizer did not report success.
Do not retune if seeds disagree or the finite budget is exhausted.

Workflow `gate-c-agn-psf-de`, identified by its implementation commit;
maximum two concurrent jobs. After review, decide whether the width-only
optimizer diagnostic is sufficient to proceed to empirical/core-wing PSF
tests, or document a specific unresolved search discrepancy. No claim of
global optimality, independent renderer agreement or production readiness.

Local C5c implementation checks: thirteen targeted tests pass under the exact
NumPy 2.5.2 / SciPy 1.18.1 pins. Tests cover seeded repeatability, callback
population/energy bookkeeping, bounds and retained budget-exhaustion status.
The n=4 execution smoke check reproduces the archived C5b objective with
zero recorded cost drift; its partial trial/population trace was checked.
This is NOT a completed local search or GitHub success. Full two-seed,
two-host outcomes must come from the new workflow and be reviewed separately.

## C5c GitHub review — 2026-09-03 UTC

Run `33709361250`, commit `ce53c12e50a907c343b067c25545555bec143dcc`,
explicitly completed/success at 04:30:40Z. Both jobs (`100505353079`,
`100505353157`) succeeded. Downloaded artifacts `agn-psf-de-n1`
(`9876858846`) and `agn-psf-de-n4` (`9878277937`); ZIP digests, exact
source image/file hashes and detailed results are in `de_33709361250.json`.
Reviewed every one of 6,816 objective evaluations, 209 generation populations,
eight DE/TRF candidates and four image bundles. Checks include all trial bounds
and flags, population members' evaluated ancestors/energies, CSV/JSON identity,
source and runtime pins, residual/cost/L1 identities and unfiltered selection.
Recomputed C5b costs have zero recorded drift. No historical result is replaced.

Both DE seeds terminate successfully for each host (n=1: 52/59 generations,
1,696/1,920 evaluations; n=4: 50/48 generations, 1,632/1,568 evaluations).
All four inherited TRF refinements succeed. All eight candidates retain the
lower-n boundary; none has zero host flux. The refined n=1 seed costs differ by
5.44e-11 and radii by 0.000247 pixels; for n=4 the differences are 1.92e-12
and 0.0000466 pixels. These are observed spreads, not new acceptance bands.

The n=4 winner has Re=31.2824463 pixels, n=0.5, q=0.58898767, host flux
0.47542100 and nuclear flux 10.41363158. Its signed cost difference from C5b
is -2.58e-12, not a substantive new physical improvement. The n=1 winner has
Re=26.1270433, n=0.5 and host flux 0.73727560. Independent search seeds and
the finite grid agree on these biased basins: the zero-host plateau diagnosis
is sufficiently characterized for this scoped width test, without a claim of
global optimality. Better optimization does not correct PSF/model mismatch.

## Empirical PSF reuse decision — 2026-09-03 UTC

The next question is how to transfer published effective PSFs without changing
their pixel-response convention. Inspected the authors' existing BDATA-001
commit `0a55283e973e2dc055ab807e29a04d89733fee48`, `CEERS_PSF/PSF_statistics.ipac`,
MIT license and the two Pointings12 F444W module A/B FITS headers. These contain
401x401 primary arrays without WCS; the accompanying metadata and paper specify
15-mas model sampling, twice the sampling of the 30-mas mosaics. The metadata
comment's "has/pixel" typo is not a new unit. Its quoted FWHMs are 0.165/0.163
arcsec, not the mock-table fiducial/broader/narrower models. No new fit outcome
was inspected to select this pair.

Sources: https://github.com/mingyangzhuang/JWST-NIRCam-Data-Product/tree/0a55283e973e2dc055ab807e29a04d89733fee48/CEERS_PSF,
https://arxiv.org/pdf/2304.13776 (v1, section 2.3), and
https://psfex.readthedocs.io/en/latest/Working.html (pixel-basis interpolation).
The PSFEx model describes pixel-response-convolved star samples, not a purely
optical kernel. A second detector-pixel integration would change the PSF.

Reuse GalSim 2.8.4 `InterpolatedImage`/`Convolve` and `drawImage(no_pixel)`:
https://galsim-developers.github.io/GalSim/_build/html/arbitrary.html and
https://galsim-developers.github.io/GalSim/_build/html/gsobject.html. Keep
`depixelize=False`; do not deconvolve, sharpen or reconstruct missing frequencies.
Use its default Quintic interpolation as the baseline and its Lanczos-4 option
as a separately labelled sensitivity diagnostic, motivated by PSFEx's documented
interpolation. Neither setting is asserted to reproduce the authors' fitter.
GalSim is BSD-licensed and already used in C4; retain that version although
2.8.5 is available. Astropy 8.0.1 (BSD-3-Clause, matching the existing table
workflow) reads FITS/metadata. NumPy 2.5.2 / SciPy 1.18.1 retain C5c pins.
Linux CPython 3.12 wheels install locally. Record the full dependency freeze.

PSFEx/photutils rebuilding would require the original selected star cutouts,
weights and rejection settings and would introduce a second construction
experiment. The available licensed author products are the appropriate reuse
here. Imfit/PyImfit remains the later cross-fitter candidate, not a prerequisite
for this transfer check. Custom code is limited to checksums, a thin GalSim
adapter and diagnostic bookkeeping; NNLS reuses the existing SciPy helper.

## C5d frozen experiment — before inspecting new results

Use only the two author Pointings12 F444W module A/B PSFs above. Pin/check their
Git blob hashes, the statistics table and license; save original bytes and
SHA256 provenance. Cast to float64, divide each FULL signed 401x401 array by
its signed sum, and record that normalization. Do not clip negative pixels,
smooth, shift/recenter, rotate, rescale widths or renormalize the output stamp.
The finite model is zero outside the published support; unprovided physical
wings remain unknown. Nonfinite arrays or nonpositive total normalization are
input errors. Negative values, signed centroids, core/wing aperture sums and
finite-output flux loss are diagnostics, not reasons to repair the data.

Treat the 15-mas grid as samples of a 30-mas effective response. GalSim
`InterpolatedImage(normalization='flux', depixelize=False, pad_factor=4,
use_true_center=True)` with explicit 0.015-arcsec scale represents that response.
Convolve the intrinsic source and draw at 0.03 arcsec using `no_pixel` on a
201x201 stamp, centered geometrically. No additional Pixel or block integration
is used in science images. The output stamp is deliberately larger than C5a's
129 pixels to cover the supplied PSF support; this is a new baseline, not a
one-variable numerical comparison with C5a. Preserve registration differences
between the supplied models; no claim of isolated pure width or core/wing change.

Use n=1/4, semi-major Re=16 native pixels (0.48 arcsec), q=0.6, PA=45 degrees,
unit analytic intrinsic host flux and nuclear/host ratios 0.1/1/10. Reuse the
existing GalSim circular-HLR conversion Re*sqrt(q) and C4 coarse/fine GSParams.
Render host/point templates for coarse-Quintic, fine-Quintic and fine-Lanczos4.
Fine-Quintic defines each A/B truth scene. Report image/flux/centroid differences
from numerical refinement and interpolation; neither proves independent
convergence or recovers information absent from the empirical models.

For each truth module and ratio, fit only nonnegative host/nuclear amplitudes
using the inherited `profile_flux` (SciPy NNLS), with each A/B adopted PSF and
each fine interpolation choice. Hold shape and intrinsic centers/PA fixed at
truth to isolate amplitude effects before introducing nonlinear ambiguity.
There are 24 direct linear solves per host, 48 total, and 12 truth image bundles.
`fit_starts.csv` has one row per direct solve, not invented nonlinear starts.
There is no change to historical structural bounds, starts or optimizer budgets;
this experiment makes NO structural-recovery or free-centroid inference.
Retain all flux-zero constraints, costs, residuals, template singular values
and failures. No bias-sign or truth-recovery threshold is applied.

Before empirical output review, validate pixel convention with closed-form
Gaussian effective PSFs of optical FWHM=0.09/0.165 arcsec and a Gaussian source
sigma=0.12 arcsec. Sample the known 30-mas integrated response on the 15-mas
grid. Compare native redraws and convolution with the corresponding analytic
Gaussian pixel integrals. Save an intentionally double-integrated negative
control separately; NEVER use it as an empirical science model. The inherited
Gaussian point-template unit check remains L1<1e-6; numerical convolution
errors are reported without inventing a general empirical acceptance band.

Workflow `gate-c-agn-empirical-psf-transfer`, two host shards, maximum two
concurrent. CI verifies pins, finite complete products and bookkeeping, not
survey accuracy. Review all templates, controls, 48 rows and residual products
before selecting nonlinear empirical-PSF fits. C5, Dewsnap, chromatic/SED,
real-survey and production decisions remain open.

### C5d local checks and resource assessment (not GitHub results)

Fifteen targeted tests passed with the frozen dependency pins, including the
inherited Gaussian integration checks, signed-input preservation, immutable
download/cache verification and NNLS zero-amplitude bookkeeping. Both LOCAL
host executions completed (48 direct solves and 12 truth bundles); source
checksums, CSV/JSON fields, all data hashes and residual/cost/L1 identities
were checked. Gaussian native-redraw L1 differences are about 1e-14; the
Gaussian-convolution controls differ by 0.6–1.1e-7. These are local diagnostics,
not a new empirical tolerance or a claim that the workflow has passed.

The unmodified published inputs contain negative wings (negative absolute
mass fractions about 3.28%/9.31% for A/B), and native-sampled signed sums are
about 1.00559/0.99009. These are retained as part of the signed empirical-model
diagnostic; neither clipping nor native-stamp renormalization is justified
post hoc. Negative model scenes cannot be used as Poisson intensity maps.
Before a later physical injection or nonlinear extension, review these input
limitations together with the actual CI transfer controls. This is not a
validated nonnegative optical PSF or a newly closed survey/centroid gate.

The n=4 local run emits GalSim's large-FFT warning for size 12300x12300.
Checked the official GSParams documentation:
https://galsim-developers.github.io/GalSim/_build/html/gsparams.html.
`maximum_fft_size` is a warning threshold, not permission to truncate or
loosen accuracy. No GSParams, support, interpolation or scientific setting was
changed. The instrumented local repeat produced identical scientific outputs,
used 2,547,332 KiB peak RSS and completed in about 65 seconds. Standard public
repository ubuntu-24.04 runners currently provide 16 GB RAM according to
https://docs.github.com/en/actions/reference/runners/github-hosted-runners
(checked 2026-09-03). Retain that standard runner, not a paid/larger resource.
`runtime.json` and `warnings.json` record observed resource use and every
warning; actual CI installation, execution and artifacts still need review.
