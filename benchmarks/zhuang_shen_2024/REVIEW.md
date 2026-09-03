# C5 — Zhuang & Shen PSF-mismatch verification

Status: IN PROGRESS. C5a–C5f reviewed; C5g frozen in `C5G_PROTOCOL.md`.
Historical status: C5e subpixel-phase/interpolation
diagnostic frozen 2026-09-03 UTC before its execution. No nonlinear
empirical-PSF or physical-injection acceptance is implied.

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

## C5d GitHub review — 2026-09-03 UTC

GitHub explicitly confirms run `33717899427`, commit
`88f3fb646a0b89e6cb9b8b8ee1aacae377edca56`, completed/success at 06:07:38Z.
Jobs `100530837930` (n=1) and `100530837792` (n=4) both succeeded, including
the targeted tests and artifact upload. Downloaded artifacts
`agn-empirical-psf-transfer-n1` (`9880481087`) and
`agn-empirical-psf-transfer-n4` (`9880386950`). Their ZIP SHA256 values and
every constituent file hash are in `empirical_transfer_33717899427.json`.

Reviewed all 48 direct NNLS fits/start records, 12 truth bundles and 184
image arrays, including the Gaussian controls and original signed PSFs.
Checks covered source Git/SHA256 hashes, commit/config/runtime pins, complete
case coverage, CSV/JSON equality, predictions/residuals, costs/L1, singular
values and KKT bookkeeping. High-contrast truth/model/residual images were
also inspected visually. No solve failed or reached a zero-amplitude bound;
there were no nonlinear starts in this experiment.

The native Gaussian control L1 differences are 0.7–1.2e-14; convolved-Gaussian
differences are 0.62–1.11e-7. An intentionally duplicated pixel integration
changes the point image by 1.10%/3.60% in L1. This validates the scoped
effective-response convention, not the physical accuracy of an empirical PSF.
Matched fine-Quintic amplitudes recover by construction. For A-truth/B-fit
at AGN/host=10, host flux is 2.1063 (n=1) and 3.3317 (n=4) instead of 1;
the reverse B-truth/A-fit gives 0.6778/0.8495. These are conditional signed-
model flux biases with fixed shape, not structural recovery or pure width
effects. The supplied modules also differ in registration, wings and noise.

Input negative absolute-mass fractions are 3.2755% (A) and 9.3129% (B).
Native point sums remain 1.0055926 and 0.9900869 without renormalization.
The observed n=4 peak RSS is 2,561,332 KiB with four recorded large-FFT
warnings; the job completed without changing any accuracy or support choice.
These signed models remain invalid as Poisson intensity maps. At zero phase,
native pixels land on input grid nodes, so agreement between interpolants at
that phase does not test off-grid behavior. Subpixel sampling and finite-window
normalization must be characterized before choosing a nonlinear extension.

## C5e literature/software decision — 2026-09-03 UTC

Anderson & King (2000), https://arxiv.org/abs/astro-ph/0006325, motivates
effective-PSF and pixel-phase checks. Godden & Blundell (2025),
https://arxiv.org/abs/2512.16764v1, studies interpolation, oversampling and
pixel-phase errors; its instrument-specific outcomes are not NIRCam limits.
Checked the maintained Photutils 3.0.0 release, license, installed public
`ImagePSF` implementation and documentation:
https://photutils.readthedocs.io/en/stable/api/photutils.psf.ImagePSF.html,
https://github.com/astropy/photutils/releases/tag/3.0.0,
https://github.com/astropy/photutils/blob/3.0.0/LICENSE.rst.

Reuse `ImagePSF` (BSD-3-Clause, cubic SciPy spline, explicit origin and
oversampling) alongside GalSim's Quintic/Lanczos-4. Its oversampled input
must sum to oversampling squared for the same flux convention: supply four
times the C5d signed-normalized image, not a new stamp normalization.
Pin Photutils 3.0.0 while retaining every C5d NumPy/SciPy/GalSim/Astropy pin.
The package installs and imports in the isolated Python 3.12 environment;
its required Astropy>=6.1.4, NumPy>=2 and SciPy>=1.13 are satisfied.
This is an interpolation cross-check, not an independent physical truth or
independent galaxy fitter. No PSF reconstruction or custom interpolation is
needed. EPSFBuilder/PSFEx rebuilding still needs original selected star data
and weights; Imfit remains the later convention-controlled cross-fitter.

## C5e frozen experiment — before inspecting new results

Question: how much do native-sampled flux, signed-wing statistics and a
fixed-position point-source flux fit vary with subpixel phase or interpolation?
Reuse the ACTUAL C5d n=1 artifact for both published A/B PSFs (its PSF bytes
match the reviewed n=4 artifact). Verify the parent commit, selected files
against the C5d audit SHA256 record, Git blob hashes and zero-phase point
template. Do not regenerate a substitute parent or silently redownload changed
author data. Keep the original 401x401 arrays, signed-sum normalization,
0.015/0.03 arcsec sample/effective-pixel scales and zero-extended input support.

Use the Cartesian phases x,y=(0,0.25,0.5,0.75) in native pixels, 16 per module.
Positive phases shift the source toward increasing array x/y. Render a unit
point source only; there is NO galaxy, added noise, free center, structural fit
or new PSF construction. This calibration sub-experiment does not revise any
historical host fit. Compare GalSim fine-Quintic, GalSim fine-Lanczos4 and
Photutils cubic `ImagePSF(oversampling=2, flux=1, fill_value=0)` at identical
geometric centers. Photutils receives eight zero sample rows/columns on each
edge so its spline can represent the same zero-extension assumption; this
padding contains no new measured wings. Its origin follows the padded center.
Do not depixelize, integrate a second detector pixel, clip, smooth or recenter.

Save 211x211 native point templates, covering the known support plus a fixed
margin, and their central 201x201 crops. Report full/crop signed sums separately;
neither is rescaled to unity. Record all four disjoint even/odd input-grid
phase sums: their average must equal the input signed normalization as an
algebraic partition, not as evidence of physical flux conservation. Report
signed/absolute mass and negative mass inside radii 0.1/0.2/0.5/1/2/3 arcsec,
using pixel-center membership around the declared source position. These are
diagnostic apertures, not corrections or acceptance cuts. Signed centroids
are explicitly not physical astrometric truth for a noisy signed model.

At each phase use the GalSim fine-Quintic 201-pixel crop as the labelled
reference data; fit one nonnegative amplitude with EACH of the three models
at the SAME fixed position, reusing the inherited SciPy NNLS helper without
an upper bound. Archive all 48 direct solves per module (96 total), including
same-model controls, costs, KKT gradients, zero-amplitude flags and all data,
templates, predictions and residuals. There is one start record per direct
solve, not a nonlinear multistart or a morphology inference.

Run the inherited analytic Gaussian effective-pixel controls at both optical
FWHMs 0.09/0.165 arcsec and all 16 phases, with each implementation. Report
the full image L1 differences, signed-sum and fitted-flux diagnostics. Existing
zero-phase Gaussian sanity/identity checks remain; off-grid errors have no new
post-hoc pass band. CI requires finite complete output and algebraic/provenance
checks, not a desired flux, bias sign, positive wings or package agreement.

Workflow `gate-c-agn-empirical-psf-phase`, two module jobs, maximum two concurrent,
is resolved by its implementation commit; never duplicate an active run.
Only after its actual CI products are reviewed should we choose between a
bounded signed-model nonlinear diagnostic and a separately specified physical
PSF construction requiring additional data/validation. No photon injection,
global identifiability, C5 closure or production implementation is authorized.

### C5e local implementation checks (not GitHub results)

All 29 targeted tests pass with the frozen environment, including 10 new
phase/normalization/source-integrity tests and four CI-routing checks. The
full local ordinary test suite also passes: 83 tests. Both LOCAL module
executions completed under the frozen settings. The 96 point fits, 192
Gaussian-control rows, 576 aperture rows and all saved phase/control image
arrays were checked for finiteness, CSV/JSON identity, source hashes and
prediction/residual/cost bookkeeping. Negative samples and every direct solve
remain present; no observed discrepancy was used to tune a setting or a band.
These are implementation checks, NOT C5e GitHub success or physical accuracy.

### CI replay repair — 2026-09-03 UTC

The GitHub run list exposed unnecessary historical benchmark replays on each
update to the long-lived draft PR. A focused official-documentation check
confirmed cumulative three-dot PR path matching and the supported native
job-condition mechanism. `docs/VERIFICATION_CI_ROUTING.md` records the narrow
draft-PR #5 routing repair and one-parent bootstrap guard. The full ordinary
regression suite still runs on every branch push; the new C5e workflow remains
mandatory for its own experiment. Existing active jobs are not cancelled.

Parsed before/after YAML for all 32 affected workflows and verified all 33
scientific job bodies are unchanged after removing only the declared routing
keys. The machine-readable audit `ci_routing_20260903.json` records the parent
blob hashes and identical scientific-job fingerprints. No parameter, bound,
acceptance criterion, test command or previous result changed. A skipped legacy
job is NOT a newly successful scientific run. No merge or production approval
is inferred; PR #5 remains draft.

### C5e launch and separate calibration-CI repair — 2026-09-03 UTC

C5e was committed as `b23d2a21f1d6cb2823b1adb44c04e9a14b55fac7` and
GitHub launched `gate-c-agn-empirical-psf-phase` run `33727185586`
(explicitly QUEUED, not completed/success). Its ordinary regression push run
is `33727185557`. Follow the phase run at this SHA even after the following
infrastructure-only repair; none of its frozen scripts, tests, requirements,
inputs or workflow is modified. No dependent science decision is made now.

GitHub also rejected old calibration workflow run `33727184271` before any
job: `runner.temp` is not an allowed job-level environment context. The same
failure is explicitly present in parent run `33717897774`, so the defect
predates C5e. Plain YAML parsing was insufficient. Consulted the official
GitHub context/environment-file documentation and the authors' maintained
actionlint release; reused pinned actionlint 1.7.12 (MIT, archive SHA verified)
instead of implementing an expression checker. It reproduced that one error
across all 48 workflows. Resolve the same CRDS cache path on the runner via
`GITHUB_ENV`, preserving `jwst_1584.pmap`, all package pins and science commands.
Add the pinned semantic check to the ordinary regression suite, without
replacing or bypassing any scientific test. All 48 workflows now validate
locally and all 85 local tests pass. These are NOT calibration-CI success.

See `docs/VERIFICATION_CI_ROUTING.md` for source links, implementation scope,
license and checksum, and `ci_validation_33727184271.json` for the separate
failure/repair record. The earlier routing audit and historical science
results remain intact. Only the affected calibration rerun and normal push
regression are expected from this repair; C5e must remain a single active run.

## C5e reviewed / C5f frozen — 2026-09-03

GitHub explicitly confirmed C5e run `33727185586` completed/success in both
module jobs. Reviewed all 96 direct fit/start rows, 192 analytic Gaussian
control rows, 576 aperture rows and 964 arrays, including algebra, parent/source
hashes and negative wings. See `phase_33727185586.json` for the machine-readable
audit and complete artifact hashes. Module B native signed sums range from
0.976862 to 1.048114; crop loss is too small to explain this phase variation.
Fixed-position cubic amplitudes relative to Quintic remain within 0.19% of
unity. This is interpolation agreement, not physical PSF validity.

The calibration repair also succeeded (`33727866409`); ordinary regression
`33727866435` passed on both Python versions (65 passed, 4 skipped each).
Earlier failed records remain intact. See `C5F_PROTOCOL.md` for artifact
provenance, limitations and the frozen next experiment: bounded point-source
centroid fits with the existing Photutils cubic model and SciPy TRF/NNLS.
The protocol was recorded before executing its fits. No galaxy parameters,
noise, signed-wing clipping, or post-hoc recovery band is introduced.
All 91 local tests pass with the pinned phase environment; these are not a
claim of C5f GitHub success. Follow the next `gate-c-agn-empirical-psf-centroid`
run at the implementing commit, not a repeat of C5e.

## C5f reviewed / C5g nuclear-centroid release — 2026-09-03

GitHub explicitly confirms C5f `33734876563` at
`0cc3f757a1746d1801d06b71e09a41f58e130d0c` completed/success, both A/B
jobs, as did regression `33734876499`. Artifacts `9885650816` and
`9885656093` were downloaded and verified against GitHub ZIP digests.
The complete review of 128 winners, 384 starts and 1282 arrays includes
parent/source hashes, frozen configuration, CSV/JSON identity, template
evaluation, residual/cost/KKT algebra and minimum-cost winner selection.
See `centroid_33734876563.json` for exact artifact/file hashes and all groups.

No start reported failure, zero flux or an active centroid bound. Largest
cross-interpolator radial offsets: 0.006804 pixel (A), 0.009953 pixel (B).
The largest amplitude change from freeing the position is 0.002647 in B.
Same-interpolator winners recover to floating precision; cross-interpolator
starts agree to about 1.75e-8 pixel per coordinate. This does not certify a
global optimum or physical PSF/astrometric validity; signed wings remain.

The next bounded nonlinear experiment isolates the nuclear centroid inside
the existing C5d AGN+host scenes. Host Re,n,q,PA and center stay fixed; both
amplitudes are profiled with NNLS. This measures apparent nucleus–host offsets
and conditional host-flux changes, NOT free-shape morphology recovery.
`C5G_PROTOCOL.md` freezes all cases, starts, bounds, outputs and software reuse
before any C5g result. It documents why adding host-shape freedom or changing
cross-fitter/convolution simultaneously would confound the comparison.

The implementation reuses pinned Photutils/SciPy and archived GalSim host
templates, without any new interpolation/optimization algorithm. All 100
local tests passed, including explicit zero-amplitude plateaus, fixed-baseline
identity and retention of an injected failed start. Pinned actionlint 1.7.12
accepts the narrow two-job workflow. These checks are not GitHub success.
Follow `gate-c-agn-empirical-agn-centroid` at its implementation commit, with
the run ID and SHA saved by the workflow into the output config. No duplicate
C5d/C5e/C5f run or production implementation is required.

Both full LOCAL C5g host executions completed: 24 paired comparisons, 72
nonlinear starts and 384 newly saved arrays audited. All data hashes,
CSV/JSON values, prediction/residual/cost/KKT identities, singular values and
winner choices were checked. Fixed-baseline host flux differs from C5d by
at most 7.6e-14; the comparison did not silently change the zero-phase model.
Every local start reports success; one n=4 winner has zero host amplitude,
which is retained without altering bounds or selecting another winner.
These local observations are NOT GitHub results or physical recovery.
Runtime was about 25–26 seconds per host with about 244000 KiB peak RSS;
no warning was recorded. Scientific settings remain as frozen.

## C5g CI reviewed / C5h independent host-renderer preflight — 2026-09-03

GitHub explicitly confirms run `33740141863` at
`de3ed949d3497263c458a897f703d5a5e9a6f295` completed/success in both host
jobs (`100599888971`, `100599888716`). Ordinary regression `33740141703`
also succeeded. Downloaded artifacts `9887407188` and `9887408196` were
verified against GitHub ZIP SHA-256 digests. These are actual CI products,
not a substitution of the earlier local execution. No newer active experiment
was present when selecting C5h.

The reproducible audit `scripts/audit_agn_empirical_agn_centroid.py` reviews
24 fixed baselines, 24 free-position winners, all 72 starts and all 384 new
arrays, with complete C5d parent provenance. It verifies CSV/JSON identity,
saved Photutils templates at every start, prediction/residual/cost/KKT and
singular-value algebra, minimum-cost winners, finite values and zero/bound
flags. `nuclear_centroid_33740141863.json` preserves the full review, source
file hashes, explicitly queried job conclusions and numerical summaries.

Every start reports convergence; no centroid bound is active. Wrong-PSF
apparent radial offsets reach 0.266074 native pixel (0.03 arcsec/pixel).
The maximum per-coordinate start spread is about 3.70e-6 pixel, and the
maximum absolute cost spread is about 3.43e-9. For n=4, true B / fit A,
AGN/host=10, the fixed host amplitude 0.849526 becomes exactly zero with the
released nucleus. Reversing the mismatch changes host amplitude from
3.331675 to 1.744172; the true amplitude is one. The matched-PSF controls
retain floating-precision recovery. The fixed baseline differs from the C5d
host amplitude by at most 7.6e-14, so the release did not silently alter the
zero-phase convention. CI runtime was 29.03/27.39 seconds (n=1/4), with peak
RSS 247160/245268 KiB and no recorded warnings.

These are conditional fixed-host-shape solutions, not physical offsets or
host morphology. Search agreement and a lower cost cannot validate a noisy
signed PSF; negative wings and phase-dependent normalization remain. The
zero-host result is retained without changing bounds or selecting another
winner. C5g and its historical predecessors are not overwritten or rerun.

### Software-first choice and frozen next question

Freeing host Re,n,q is the next scientific goal. However, the archived n=4
GalSim reference already required a roughly 12300-square FFT and 2.56 GB
peak RSS. A new renderer needs convention and full-bound resource checks
before its behavior can enter a shape optimizer. `C5H_PROTOCOL.md` freezes
these checks before any C5h science-image evaluation: Imfit 1.9.0 rendering
at 2x/4x/8x numerical sampling, the existing truth shapes, all eight corners
of the unchanged Re/n/q box, exact Gaussian controls, and fixed-shape flux
sensitivity on the original C5d images. No host-shape inference yet.

Consulted the author's Imfit paper, tagged source, CLI documentation and
PyImfit installation/convolution documentation (links and checksums in the
protocol). Reuse the checksum-pinned Linux makeimage executable and its
existing profile subsampling/convolution; no new renderer or optimizer is
written. PyImfit uses the same engine but adds a Linux source-build/ABI
requirement, so it is not necessary for this preflight. Imfit's GPL-3.0-or-
later license and bundled source metadata are recorded; no executable is
vendored or adopted as a production dependency. The small adapter translates
1-based centers, PA/ellipticity, analytic flux units and already-integrated
effective-PSF sampling. The original GalSim PSF interpolant is shared, so
only the host renderer/convolution is independently compared. Do not infer
independent physical PSF truth, universal numerical convergence or readiness
for photon injection from package agreement.

### Local implementation checks and setup diagnoses (not CI results)

All 112 local tests pass with the frozen dependency pins and the real
checksum-verified Imfit binary, including 18 targeted renderer/transfer
tests. Pinned actionlint 1.7.12 accepts all workflows. The ordinary regression
suite remains enabled and the new workflow has narrow push paths and two
host jobs; no historical heavy science batch is intentionally relaunched.

An interrupted local package installation left the NumPy OpenBLAS library
truncated at 8388608 instead of the wheel RECORD's 25210641 bytes. Offline
RECORD/hash comparison identified that one corrupt binary. Re-extracting the
same library from the cached pinned wheel restored imports; no numerical
dependency version or scientific setting was changed. Consulted NumPy's
official import-troubleshooting guidance and the documented truncated-file
SIGBUS case, rather than diagnosing this as a numerical failure:
https://numpy.org/devdocs/user/troubleshooting-importerror.html
https://bugs.python.org/issue40720

The first external-binary smoke checks also caught a missing local GNU time
utility and then Imfit 1.9's documented `--print-fluxes` behavior: that mode
disables image saving, even with an output filename. Used the official
Ubuntu time package locally (relocatable path, hash/version recorded), and
removed that reporting-only flag so makeimage actually saves the requested
FITS. A regression assertion prevents its return. These pre-science setup
failures did not evaluate, discard or tune any C5h science result. Sources:
https://packages.ubuntu.com/noble/time
https://imfit.readthedocs.io/en/latest/frequently_asked_questions.html
https://www.mpe.mpg.de/~erwin/resources/imfit/CHANGELOG.html

Follow `gate-c-agn-imfit-renderer` at the commit implementing C5h, not an old
centroid run. Its config records the actual GitHub run ID/SHA, prerequisite
audit/protocol hashes, software identities and every frozen case. Only after
explicit completed/success and review of all renderer, flux, residual and
resource products may C5h inform the free-shape implementation decision.
No acceptance band, morphology bound or production gate is changed here.

Both full LOCAL C5h executions subsequently completed under that frozen
protocol: 72 render cases (including all structural corners and Gaussian
controls), 72 direct fits/start records and 600 new NPZ/FITS image arrays.
All were audited for complete finite products, source identity, native/fine
grid and area mapping, CSV/JSON identity, comparison/refinement bookkeeping,
amplitude-zero flags and prediction/residual/cost/KKT algebra. No renderer
timed out; no warning was recorded. Each host job took about 485 seconds;
maximum measured child RSS was 2301872 KiB. The author CLI writes float32
FITS, which is explicitly retained in the record rather than presented as
double-precision independent agreement. No setting was changed in response
to these outputs. These local checks are NOT GitHub Actions success, a
physical PSF validation, or approval to advance to free-shape fitting yet.
