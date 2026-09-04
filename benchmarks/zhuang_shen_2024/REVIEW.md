# C5 â€” Zhuang & Shen PSF-mismatch verification

Status: IN PROGRESS. C5aâ€“C5i reviewed from actual CI artifacts. C5j remains
an incomplete LOCAL diagnostic with four retained resource failures; it was
not dispatched. C5k subsequently succeeded and its actual artifacts are
reviewed below. C5l's finite-cell convention test is frozen in
`C5L_PROTOCOL.md`. Host shape is not freed yet.
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

## C5a GitHub review â€” 2026-09-03 UTC

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

## C5b frozen experiment â€” before inspecting new results

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

## C5b GitHub review â€” 2026-09-03 UTC

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

## Literature/software decision â€” 2026-09-03 UTC

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

## C5c frozen experiment â€” before inspecting new results

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

## C5c GitHub review â€” 2026-09-03 UTC

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

## Empirical PSF reuse decision â€” 2026-09-03 UTC

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

## C5d frozen experiment â€” before inspecting new results

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
Gaussian-convolution controls differ by 0.6â€“1.1e-7. These are local diagnostics,
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

## C5d GitHub review â€” 2026-09-03 UTC

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

The native Gaussian control L1 differences are 0.7â€“1.2e-14; convolved-Gaussian
differences are 0.62â€“1.11e-7. An intentionally duplicated pixel integration
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

## C5e literature/software decision â€” 2026-09-03 UTC

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

## C5e frozen experiment â€” before inspecting new results

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

### CI replay repair â€” 2026-09-03 UTC

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

### C5e launch and separate calibration-CI repair â€” 2026-09-03 UTC

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

## C5e reviewed / C5f frozen â€” 2026-09-03

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

## C5f reviewed / C5g nuclear-centroid release â€” 2026-09-03

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
amplitudes are profiled with NNLS. This measures apparent nucleusâ€“host offsets
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
Runtime was about 25â€“26 seconds per host with about 244000 KiB peak RSS;
no warning was recorded. Scientific settings remain as frozen.

## C5g CI reviewed / C5h independent host-renderer preflight â€” 2026-09-03

GitHub explicitly confirms run `33740141863` at
`de3ed949d3497263c458a897f703d5a5e9a6f295` completed/success in both host
jobs (`100599888971`, `100599888716`). Ordinary regression `33740141703`
also succeeded. Downloaded artifacts `9887407188` and `9887408196` were
verified against GitHub ZIP SHA-256 digests. These are actual CI products,
not a substitution of the earlier local execution. No newer active experiment
was present when selecting C5h.

The reproducible audit `scripts/audit_agn_ëú¶‰Ëkºwµçuµ¥Ğ°ÕÍ¥¹œ…ÑÕ…°)Õ¤ÉÕ¸€ÌÌÜØØÈĞØÌäØ…ÌÑ¡”$¥¹ÁÕĞÁ…É•¹Ğ…¹Ñ¡”Í•Á…É…Ñ”Õ¨±½…°…Õ‘¥Ğ)…Ì‘•Í¥¸ÁÉ½Ù•¹…¹”¸Õ¬É•ÅÕ¥É•Ì…±°¥ÑÌ½İ¸™É½é•¸ÁÉ½‘ÕÑÌ…¹Ñ¡”)Õ¹¡…¹•É•Á±…ä½‰½½­­••Á¥¹œ¡•­Ì¸9¼µ¥ÍÍ¥¹œ¥µ…”¥Ì…•ÁÑ•°…¹¹¼)Á¡åÍ¥…°½Èµ½ÉÁ¡½±½ä…•ÁÑ…¹”Ñ¡É•Í¡½±¡…Ì‰••¸…‘‘•¸((ŒŒŒÕ¬±½…°Ù•É¥™¥…Ñ¥½¸‰•™½É”‘¥ÍÁ…Ñ ƒŠP€ÈÀÈØ´Àä´ÀÌUQ()±°€¨¨ÔØM•ÉÍ¥Œ¥µ…•Ì°€Èà…ÕÍÍ¥…¸½¹ÑÉ½±Ì°€ÔØ‘¥É•Ğ…µÁ±¥ÑÕ‘”ÍÑ…ÉÑÌ°(ÄØàÁ…¥Éİ¥Í”½µÁ…É¥Í½¹Ì…¹€àäØ¹•Ü…ÉÉ…åÌ¨¨İ•É”É•…‰…¬…¹…Õ‘¥Ñ•)İ¥Ñ ÍÉ¥ÁÑÌ½…Õ‘¥Ñ}…¹}™½ÕÉ¥•É}É¥¹Áå€¸Q¡•É”İ•É”¹¼™…¥±•É•¹‘•È)ÁÉ½•ÍÍ•Ì½Èé•É¼…µÁ±¥ÑÕ‘•Ì¸	½Ñ ½É¥¥¹…°µ™¥¹”É•Á±…åÌÁ…ÍÍ•Ñ¡”¥¹¡•É¥Ñ•)‰½½­­••Á¥¹œ¡•¬ì…±°Í…Ù•ÁÉ•‘¥Ñ¥½¹Ì°É•Í¥‘Õ…±Ì°½ÕÉ¥•ÈÁÉ½‘ÕÑÌ°)½ÍÑÌ°É…‘¥•¹ÑÌ…¹…ÉÉ…ä½™¥±”¥‘•¹Ñ¥Ñ¥•Ìİ•É”¡•­•¸Q¡”µ…¡¥¹”µÉ•…‘…‰±”)É•½É¥ÌŒÕ­}±½…±|ÈÀÈØÀäÀÌ¹©Í½¹€ì¥ÑÌ¥Ñ!ÕˆÉÕ¸%Ì…É”¹Õ±°¸Q¡¥Ì¥Ì(¨©1=0Ù•É¥™¥…Ñ¥½¸°¹½Ğ„¥Ñ!ÕˆÍÕ•ÍÌÉ••¥ÁĞ¨¨¸()I•Ñ…¥¹•…±°€¨¨ÄØ…±M¥´PµÍ¥é”İ…É¹¥¹Ì¨¨€¡•¥¡ĞÁ•ÈÍ¡…É¤¸Q¡”±…É•ÍĞ)É•ÅÕ•ÍÑ•Pİ…Ì€ÄÈÌÀÀÍÅÕ…É”ìµ…á¥µÕ´¡¥±IMLİ…Ì€ÈØÀÌÜÌØ-¥°İ¥Ñ¡¥¸)Ñ¡”Õ¹¡…¹•Í¥àµ¥…À¸=É¥¥¹…°Í¡…ÉÉÕ¹Ñ¥µ•Ìİ•É”€ÄÀÀ¸ĞÌ…¹€ÄÌÀ¸ää)Í•½¹‘Ììİ…É¹¥¹œÑ¡É•Í¡½±‘Ì…¹İ½É­•È±¥µ¥ÑÌİ•É”¹½ĞÉ…¥Í•¸()Q¡”…Õ‘¥Ğ…±Í¼É•©•Ñ•Ñİ¼¥¹½µÁ±•Ñ”½É¥¥¹…°P±½ÌèÑ¡”É½Õ¹¸ôÀ¸Ô°)É¥ÄÀÈÑ}¬Ñ€½¥µ…”‰Õ¹‘±•Ì•á¥ÍÑ•°‰ÕĞ½¹±ä½¹”½˜Ñ¡”Ñİ¼É•ÅÕ¥É•)‘É…ÜÉ••¥ÁÑÌÍÕÉÙ¥Ù•¸Q¡•¥È…ÕÍ”¥Ì¹½Ğ•ÍÑ…‰±¥Í¡•¸M•Á…É…Ñ”°Í…µ”µÍ•ÑÑ¥¹œ)İ½É­•ÈÉ•¡•­ÌÁÉ½‘Õ•‰½Ñ É••¥ÁÑÌ…¹€¨©‰¥Ñİ¥Í”µ¥‘•¹Ñ¥…°¥µ…•Ì…¹)½ÕÉ¥•ÈÁÉ½‰•Ì¨¨¸=É¥¥¹…°™¥±•Ìİ•É”¹½ĞÉ•Á±…•ìÑ¡”…Õ‘¥ĞÉ•Ñ…¥¹Ì‰½Ñ )Ñ¡”¥¹½µÁ±•Ñ”±½Ì…¹Í•Á…É…Ñ”É•¡•¬¥‘•¹Ñ¥Ñ¥•Ì¸¹•Ü½µÁ±•Ñ•¹•ÍÌµ½¹±ä)Õ…É¹½Ü™…¥±Ì„İ½É­•È¥˜…¹ä‘É…ÜÉ••¥ÁĞ¥Ìµ¥ÍÍ¥¹œ°ÁÉ•Í•ÉÙ¥¹œÑ¡”)É•¹‘•É•‘…Ñ„…¹Ñ¡”™…¥±ÕÉ”É…Ñ¡•ÈÑ¡…¸…•ÁÑ¥¹œ…¸¥¹½µÁ±•Ñ”É•½É¸)Q¡”½É¥¥¹…°±½…°ÁÉ½‘Õ•ÈM!ÈÔØ¥ÌÉ•½É‘•Í•Á…É…Ñ•±ä™É½´Ñ¡¥ÌÕ…É¸()Q¡”™Õ±°±½…°ÍÕ¥Ñ”Á…ÍÍ•€¨¨ÄĞàÑ•ÍÑÌ¨¨ì½¹”‘•‘¥…Ñ••áÑ•É¹…°µ%µ™¥Ğµ‰¥¹…Éä)Ñ•ÍĞİ…ÌÍ­¥ÁÁ•…¹½¹”‘•±¥‰•É…Ñ”™…¥±ÕÉ”µ…ÁÑÕÉ”İ…É¹¥¹œİ…ÌÉ•Ñ…¥¹•¸)A¥¹¹•…Ñ¥½¹±¥¹Ğ€Ä¸Ü¸ÄÈ…•ÁÑ•…±°İ½É­™±½İÌ¸9¼Õ¬¥µ…”İ…ÌÕÍ•Ñ¼)¡…¹”¥ÑÌ™É½é•¸Í•ÑÑ¥¹Ì°‰½Õ¹‘Ì½È…•ÁÑ…¹”ÉÕ±•Ì¸9•áĞè±…Õ¹ Ñ¡”)Ñİ¼µ©½ˆÕ¬İ½É­™±½Ü°¥¹ÍÁ•Ğ¥ÑÌ…ÑÕ…°É••¥ÁÑÌ½ÁÉ½‘ÕÑÌ°…¹½¹±äÑ¡•¸)‘•¥‘”İ¡•Ñ¡•È™ÕÉÑ¡•È¹Õµ•É¥…°½¹ÑÉ½±Ì½È™É•”µÍ¡…Á”™¥ÑÌ…É”©ÕÍÑ¥™¥•¸((ŒŒŒÕ¬…ÑÕ…°$É•Ù¥•Ü…¹Õ°™É••é”ƒŠP€ÈÀÈØ´Àä´ÀÌUQ()¥Ñ!Õˆ•áÁ±¥¥Ñ±ä½¹™¥ÉµÌÉÕ¸€¨¨ÌÌÜààÜÀÔäÔÈ¨¨°½µµ¥Ğ)€İ…Ù”Å„ÅˆÙ„Üá‘‘”àÍÙ‘•„å”ÍŒÅ‰ŒÈÙ‰ÌÍ‰€°½µÁ±•Ñ•½ÍÕ•ÍÌ…Ğ(ÄàèÔØèÌÁh¸	½Ñ ©½‰Ì€ÄÀÀÜÔäÜÄàÜäÔ¼ÄÀÀÜÔäÜÄäÀØà…¹•Ù•ÉäÍÑ•ÀÍÕ••‘•¸)ÉÑ¥™…ÑÌ€ääÀàÀÈÄĞÀÀ€¡¸Ä¤…¹€ääÀàÈÈàÌÈÀ€¡¸Ğ¤İ•É”‘½İ¹±½…‘•…¹Ñ¡•¥È)i%@M!ÈÔØÙ…±Õ•ÌÙ•É¥™¥•¸™½ÕÉ¥•É}É¥‘|ÌÌÜààÜÀÔäÔÈ¹©Í½¹€É•Ñ…¥¹ÌÑ¡”)É••¥ÁĞ…¹É•ÁÉ½‘Õ¥‰±”™Õ±°…Õ‘¥Ğè€ÔØÉ•¹‘•ÉÌ½‘¥É•ĞÍÑ…ÉÑÌ°€Èà…ÕÍÍ¥…¸)½¹ÑÉ½±Ì°€ÄØà…É´µÁ…¥È½µÁ…É¥Í½¹Ì…¹€¨¨àäØ¹•Ü…ÉÉ…åÌ¨¨¸±°MX½)M=8°)Á…É•¹Ğ¥‘•¹Ñ¥Ñ¥•Ì°ÁÉ•‘¥Ñ¥½¹Ì°É•Í¥‘Õ…±Ì°½ÍÑÌ°--PÅÕ…¹Ñ¥Ñ¥•Ì°½ÕÉ¥•È)ÁÉ½‘ÕÑÌ…¹…ÑÕ…°PÉ••¥ÁÑÌİ•É”¡•­•¸9¼™…¥±•İ½É­•È°é•É¼)…µÁ±¥ÑÕ‘”½È¥¹½µÁ±•Ñ”P±½œ½ÕÉÌ¥¸Ñ¡•Í”$…ÉÑ¥™…ÑÌ¸±°€¨¨ÄØ)±…É”µPİ…É¹¥¹Ì¨¨É•µ…¥¸ìµ…á¥µÕ´¡¥±IMLİ…Ì€ÈØÄÌààà-¥¸Q¡”Ñİ¼)Í¥•¹”µÍÉ¥ÁĞÉÕ¹Ñ¥µ•Ìİ•É”€ØÔ¸ÌÔ…¹€ÄÄÜ¸ÀÈÍ•½¹‘Ì¸()Q¡”™¥ÉÍĞÉ•…µ½¹±ä…Õ‘¥Ğ•áÁ½Í•„Á½ÉÑ…‰¥±¥Ñä¥ÍÍÕ”°¹½Ğ„$™…¥±ÕÉ”è(ÄÄ¼ÈØÀÉ••¹•É…Ñ•¸Ğ­à½½É‘¥¹…Ñ•Ì‘¥™™•É•™É½´Ñ¡”Í…Ù•Ù…±Õ•Ì‰ä…Ğ)µ½ÍĞ€Ü¸ÄÅ”´ÄÔ€¡É•±…Ñ¥Ù”‘¥™™•É•¹•Ì…Ğ™±½…Ñ¥¹œµÁ½¥¹ĞÉ½Õ¹‘¥¹œÍ…±”¤¸)½±±½İ¥¹œ9ÕµAäÌ‘½Õµ•¹Ñ•ATµ‘¥ÍÁ…Ñ ½¹ÑÉ½±Ì°É•ÍÑÉ¥Ñ¥¹œÑ¡”…Õ‘¥Ğ)ÁÉ½•ÍÌİ¥Ñ 9Ae}%M	1}AU}QUILõ`àÙ}XĞ±Y`ÔÄÉ}%1€É•ÁÉ½‘Õ•Ñ¡”)Í…Ù•¸Ğ½½É‘¥¹…Ñ•Ì•á…Ñ±ä¸Q¡”¸Ä…Õ‘¥ĞÕÍ•‘•™…Õ±Ğ‘¥ÍÁ…Ñ ¸	½Ñ ™Õ±°)…Õ‘¥ÑÌÑ¡•¸Á…ÍÍ•Ñ¡”€¨©½É¥¥¹…°•á…Ğ…ÍÍ•ÉÑ¥½¹Ì¨¨°İ¥Ñ¡½ÕĞ¡…¹¥¹œ…¹ä)Ñ½±•É…¹”°¥µ…”°½½É‘¥¹…Ñ”™¥±”½ÈÍ¥•¹Ñ¥™¥ŒÍ•ÑÑ¥¹œ¸Q¡”½É¥¥¹…°)™…¥±ÕÉ”…¹…Õ‘¥Ğ•¹Ù¥É½¹µ•¹ÑÌ…É”É•½É‘•ìÑ¡¥Ì‘½•Ì¹½Ğ•ÍÑ…‰±¥Í Ñ¡…Ğ)…±°™±½…Ñ¥¹œµÁ½¥¹Ğ½ÕÑÁÕÑÌ…É”Á½ÉÑ…‰±”…É½ÍÌ•Ù•ÉäÁ±…Ñ™½É´¸)¡ÑÑÁÌè¼½¹ÕµÁä¹½Éœ½‘½Œ½ÍÑ…‰±”½É•™•É•¹”½Í¥µ½‰Õ¥±µ½ÁÑ¥½¹Ì¹¡Ñµ°ÉÕ¹Ñ¥µ”µ‘¥ÍÁ…Ñ )¡ÑÑÁÌè¼½¹ÕµÁä¹½Éœ½‘½Œ½ÍÑ…‰±”½É•™•É•¹”½•¹•É…Ñ•½¹ÕµÁä¹•½µÍÁ…”¹¡Ñµ°)I•ÁÉ½‘Õ”İ¥Ñ ÍÉ¥ÁÑÌ½É•Ù¥•İ}…¹}™½ÕÉ¥•É}É¥‘}¤¹Áå€…¹Ñ¡”Ñİ¼i%AÌ¸()ĞÑ¡”™½ÕÉ™½±ÕÑ½™˜°¥¹É•…Í¥¹œÑ¡”É¥™É½´€ÄÀÈĞÑ¼ÄÔÌØ¡…¹•ÌÑ¡”)•¥¡Ğ¥µ…•Ì‰ä€à¸ØÙ”´Ü´´Ì¸Èå”´Ø0Ä¸e•Ğ…ĞÉ¥ÄÔÌØ°¥¹É•…Í¥¹œÑ¡”ÕÑ½™˜)™É½´€ÉàÑ¼Ñà¡…¹•Ì¸Ø‰ä€¨¨À¸ÀØØÀ´´À¸ÄÀØÜ”¨¨ì¸À¸Ô™±…ÑÑ•¹•…Í•Ì¡…¹”)‰ä€À¸ÀÀÄÄÌ´´À¸ÀÀÄĞÀ”°…¹É½Õ¹…Í•Ì…É”¥‘•¹Ñ¥…°…ĞÑ¡½Í”Ñİ¼ÕÑ½™™Ì¸)Q¡ÕÌÍµ…±°ÍÁ…¥¹œÍ•¹Í¥Ñ¥Ù¥Ñä…±½¹”‘½•Ì¹½ĞÁÉ½Ù”½ÕÉ¥•È½¹Ù•É•¹”¸)ĞÉ¥ÄÔÌØ½¬Ğ°%µ™¥Ğà‘¥™™•É•¹•Ì…É”€¨¨À¸ÈÄĞ´´À¸ÈÜÌ”™½È¸Ø¨¨°(¨¨Ä¸Øää´´Ä¸ÜĞÀ”™½È™±…ÑÑ•¹•¸À¸Ô¨¨°…¹€À¸ÀäĞÄ´´À¸ÀääÄ”™½ÈÉ½Õ¹¸À¸Ô¸)9•¥Ñ¡•È½‘”¥Ì¥¹‘•Á•¹‘•¹Ñ±ä•ÍÑ…‰±¥Í¡•…ÌÑÉÕÑ ¸9¼Ñ½±•É…¹”½È‰½Õ¹)İ…Ì¡…¹•…¹¹¼¡½ÍĞµÍ¡…Á”½ÈÁ¡åÍ¥…°µÉ•½Ù•Éä±…¥´™½±±½İÌ¸()Q¡”¹•áĞÍÁ•¥™¥ŒÅÕ•ÍÑ¥½¸¥Ìİ¡•Ñ¡•È™¥¹¥Ñ”¥¹ÑÉ¥¹Í¥Œ¹Õµ•É¥…°µ•±°)¥¹Ñ•É…Ñ¥½¸½¹ÑÉ¥‰ÕÑ•ÌÑ¼Ñ¡”É½ÍÌµ½‘”‘¥™™•É•¹”¸¡•­•%µ™¥ĞÌ)Ñ…••ÑY…±Õ”½…±Õ±…Ñ•MÕ‰Í…µÁ±•Ì¥µÁ±•µ•¹Ñ…Ñ¥½¸…¹…±M¥´Ì•á¥ÍÑ¥¹œ)A¥á•°½½¹Ù½±ÕÑ¥½¸½‰©•ÑÌ‰•™½É”™É••é¥¹œÕ1}AI=Q==0¹µ‘€¸I•ÕÍ”Ñ¡”)ÁÕ‰±¥Í¡•%µ™¥ĞÈ¼Ğ¼à…ÉÉ…åÌ™É½´Õ¤ì‘¼¹½ĞÉ•É•¹‘•ÈÑ¡…Ğ¡¥ÍÑ½É¥…°ÍÑ…”¸)½µÁ…É”…¹½¹¥…°¹½}•±°…¹Í•Á…É…Ñ•±ä±…‰•±±•ÍÅÕ…É”µ•±°É•ÍÁ½¹Í•Ì)½˜İ¥‘Ñ €Ä¼È°€Ä¼Ğ…¹€Ä¼à¹…Ñ¥Ù”Á¥á•°°İ¥Ñ …±°™½ÕÈ…ÉµÌ½µÁ…É•……¥¹ÍĞ)…±°Ñ¡É•”%µ™¥ĞÍ…µÁ±¥¹Ì¸Q¡¥ÌÕ¹¥™½É´µ•±°ÍÕÉÉ½…Ñ”¥Ì‘•±¥‰•É…Ñ•±ä9=P)…ÍÍ•ÉÑ•Ñ¼•ÅÕ…°…‘…ÁÑ¥Ù”%µ™¥Ğ¥¹Ñ•É…Ñ¥½¸½È„¹•ÜÁ¡åÍ¥…°AMµ½‘•°¸)A¥¹Ì°‰½Õ¹‘Ì…¹É•Í½ÕÉ”…ÁÌÉ•µ…¥¸Õ¹¡…¹•¸9¼‰•ÍÁ½­”¹Õµ•É¥…°)¥¹Ñ•É…Ñ½È½É•¹‘•É•È½ÈÁÉ½‘ÕÑ¥½¸½‘”¥Ì¥¹ÑÉ½‘Õ•¸½±±½Ü(¨©…Ñ”µŒµ…¸µ•±°µÉ•ÍÁ½¹Í”¨¨…Ğ¥ÑÌ¥µÁ±•µ•¹Ñ¥¹œ½µµ¥Ğì¥ÑÌ½¹™¥ÌÉ•½É)Ñ¡”…ÑÕ…°¹•ÜÉÕ¸½M!¸Õ°¥Ì¹½Ğå•Ğ„¥Ñ!ÕˆµÍÕ•ÍÌ±…¥´¸()Õ°±½…°Ù•É¥™¥…Ñ¥½¸‰•™½É”‘¥ÍÁ…Ñ è…±°€ÌÈM•ÉÍ¥ŒÉ•¹‘•ÉÌ°€ÄØ…ÕÍÍ¥…¸)½¹ÑÉ½±Ì°€äØ‘¥É•ĞÍÑ…ÉÑÌ°€Ğà…É´µÁ…¥È½µÁ…É¥Í½¹Ì…¹€ÜÈÀ¹•Ü…ÉÉ…åÌİ•É”)É•…‰…¬…¹…Õ‘¥Ñ•¸9¼™…¥±•İ½É­•È°é•É¼…µÁ±¥ÑÕ‘”°µ¥ÍÍ¥¹œPÉ••¥ÁĞ)½È‰½½­­••Á¥¹œ‘¥ÍÉ•Á…¹äİ…Ì™½Õ¹¸±°€ÌÈ±…É”µPİ…É¹¥¹ÌÉ•µ…¥¸ì)µ…á¥µÕ´¡¥±IMLİ…Ì€ĞÌÜÄÄØà-¥Õ¹‘•ÈÑ¡”Õ¹¡…¹•Í¥àµ¥…À¸M¡…É)ÉÕ¹Ñ¥µ•Ìİ•É”€ÄÌÄ¸ÌÀ…¹€ÄÔä¸ÈÄÍ•½¹‘Ì¸ŒÕ±}±½…±|ÈÀÈØÀäÀÌ¹©Í½¹€•áÁ±¥¥Ñ±ä)¥Ì¹½Ğ„¥Ñ!ÕˆÉ••¥ÁĞìÉ•ÁÉ½‘Õ”İ¥Ñ ÍÉ¥ÁÑÌ½…Õ‘¥Ñ}…¹}•±±}É•ÍÁ½¹Í”¹Áå€¸)9¼Í•ÑÑ¥¹Ìİ•É”¡…¹•…™Ñ•ÈÑ¡•Í”¥µ…•Ì¸Õ±°±½…°Ñ•ÍÑÌè€¨¨ÄÔÜÁ…ÍÍ•°)½¹”•áÑ•É¹…°µ%µ™¥Ğµ‰¥¹…ÉäÑ•ÍĞÍ­¥ÁÁ•¨¨°½¹”¥¹Ñ•¹Ñ¥½¹…°™…¥±ÕÉ”µ…ÁÑÕÉ”)İ…É¹¥¹œ¸A¥¹¹•…Ñ¥½¹±¥¹Ğ€Ä¸Ü¸ÄÈ…•ÁÑ•…±°İ½É­™±½İÌ¸Q¡”ÁÉ•É•ÅÕ¥Í¥Ñ”)½É‘¥¹…ÉäÉ•É•ÍÍ¥½¸ÉÕ¸€ÌÌÜààÜÀØÀÜÈ…±Í¼•áÁ±¥¥Ñ±ä½µÁ±•Ñ•½ÍÕ•ÍÌ¸((ŒŒŒÕ°…ÑÕ…°$É•Ù¥•Ü…¹Õ´™É••é”ƒŠP€ÈÀÈØ´Àä´ÀÌUQ()¥Ñ!Õˆ½¹™¥ÉµÌ€¨¨ÌÌÜäàØÜÔÌÜä¨¨…Ğ€ÀäÑ‘”àá”àáˆØØàÀÄÔØÔàÔÌÙÄÌÔàÍŒÈÀÅ™………˜É€)½µÁ±•Ñ•½ÍÕ•ÍÌ°ÕÁ‘…Ñ•€ÄäèÔÈèÄÕh¸	½Ñ ©½‰Ì…¹•Ù•ÉäÍÑ•ÀÍÕ••‘•¸)ÉÑ¥™…ÑÌ€ääÄÀÈÔØäÈØ¼ääÄÀÈÜÄäØÈİ•É”‘½İ¹±½…‘•…¹i%@M!ÈÔØÙ•É¥™¥•¸)Q¡”Õ¹¡…¹•É•…µ½¹±ä…Õ‘¥Ğ¡•­•…±°€¨¨ÌÈÉ•¹‘•ÉÌ°€ÄØ…ÕÍÍ¥…¸½¹ÑÉ½±Ì°(äØ‘¥É•ĞÍÑ…ÉÑÌ°€Ğà…É´Á…¥ÉÌ…¹€ÜÈÀ¹•Ü…ÉÉ…åÌ¨¨°¥¹±Õ‘¥¹œÁ…É•¹Ğ¡…Í¡•Ì°)…±°ÁÉ•‘¥Ñ¥½¹Ì½É•Í¥‘Õ…±Ì°--P°½ÕÉ¥•ÈÁÉ½‘ÕÑÌ°PÉ••¥ÁÑÌ…¹µ…¹¥™•ÍÑÌ¸)Q¡•É”İ•É”¹¼™…¥±•İ½É­•ÉÌ½Èé•É¼…µÁ±¥ÑÕ‘•Ì¸±°€ÌÈPİ…É¹¥¹ÌÉ•µ…¥¸¸)M¥•¹”µÍÉ¥ÁĞÉÕ¹Ñ¥µ•Ìİ•É”€àà¸ÔÈ¼ÄÈÀ¸ÈØÍ•½¹‘Ì¸Õ±°…ÑÕ…°µ$É••¥ÁĞè)•±±}É•ÍÁ½¹Í•|ÌÌÜäàØÜÔÌÜä¹©Í½¹€¸()Q¡”™¥¹¥Ñ”µ•±°ÍÕÉÉ½…Ñ”‘½•Ì€¨©¹½Ğ¨¨½¹Í¥ÍÑ•¹Ñ±ä•áÁ±…¥¸Ñ¡”‘¥ÍÉ•Á…¹ä¸)½È™±…ÑÑ•¹•¸ôÀ¸Ô°µ…Ñ¡••±°à‘¥™™•ÉÌ™É½´%µ™¥Ğà‰ä€¨¨Ä¸ÜÀÀ”¼Ä¸ØäÌ”¨¨(¡½¤°½µÁ…É•İ¥Ñ …¹½¹¥…°¹½}•±°€¨¨Ä¸Øää”¼Ä¸ÜĞÀ”¨¨¸I½Õ¹¸ôÀ¸Ô)µ…Ñ¡••±°È¥µÁÉ½Ù•Ì%µ™¥ĞÈ…É••µ•¹ĞÑ¼€¨¨À¸ÀàÄÔ”¼À¸ÄÄÀÔ”¨¨°‰ÕĞÑ¡…Ğ¥Ì)¹½Ğ•Ù¥‘•¹”Ñ¡”Í…µ”½ÉÉ•Ñ¥½¸…ÁÁ±¥•Ì…É½ÍÌÍ¡…Á”½ÈÍ…µÁ±¥¹œ¸±…ÑÑ•¹•)¸ôØµ…Ñ¡••±°à‘¥™™•É•¹•Ì…É”€¨¨À¸ÈÌÀÜ”¼À¸ÈÔàÜ”¨¨°İ½ÉÍ”Ñ¡…¸¹½}•±°(¨¨À¸ÈÈĞØ”¼À¸ÈÄĞĞ”¨¨¸±°½™˜µ‘¥…½¹…°É•ÍÕ±ÑÌÉ•µ…¥¸¥¸Ñ¡”É••¥ÁĞì¹¼‰•ÍĞ)•±°¥ÌÍ•±•Ñ•½È…‘½ÁÑ•¸9•¥Ñ¡•ÈÉ•¹‘•É•È¥ÌÑÉÕÑ …¹¹¼½¹Ù•É•¹”°)¹•ÜÁ¡åÍ¥…°AM½È™É•”µÍ¡…Á”É•½Ù•Éä±…¥´™½±±½İÌ¸()I•¡•­•Ñ¡”Ñ…•%µ™¥ĞM•ÉÍ¥Œ¥µÁ±•µ•¹Ñ…Ñ¥½¸…¹½™™¥¥…°µ…­•¥µ…”)…É¡¥Ñ•ÑÕÉ”‘½Ì¸%ÑÌ…‘…ÁÑ¥Ù”¥¹Ñ•É…Ñ¥½¸‘•Á•¹‘Ì½¸•±±¥ÁÑ¥…°É…‘¥ÕÌ)¥¸¹Õµ•É¥…°Á¥á•±Ì°Í¼„Õ¹¥™½É´‰½à…¹¹½ĞÉ•ÁÉ½‘Õ”¥Ğ•á…Ñ±ä¸Q¡”¹•áĞ)¥Í½±…Ñ•ÅÕ•ÍÑ¥½¸¥Ìİ¡•Ñ¡•È%µ™¥Ğ€àµÑ¼´ÄØ¹Õµ•É¥…°Í…µÁ±¥¹œ¡…¹•ÌÑ¡”)½µÁ…Ğ…Í•Ì…¹™¥ÑÌİ¥Ñ¡¥¸Ñ¡”•á¥ÍÑ¥¹œ…ÁÌ¸Õ5}AI=Q==0¹µ‘€™É••é•Ì)…±°•¥¡ĞÍ•¹•Ì°€ÄØÉ•¹‘•ÉÌ°€ÌÈ…µÁ±¥ÑÕ‘”™¥ÑÌ…¹•¥¡Ğİ¥Ñ¡¥¸µ½‘”)½µÁ…É¥Í½¹Ì¸I•ÕÍ”Õ¹¡…¹•…ÕÑ¡½È%µ™¥Ğ€Ä¸ä¸À°Õ •½µ•ÑÉä½½¹Ù½±ÕÑ¥½¸°)Í…µ”Í¥¹•AMÌ…¹…É¡¥Ù•Õ°¹½}•±°¸9¼ÕÍÑ½´¥¹Ñ•É…Ñ½È°¹•Ü)É½ÍÌµ™¥ÑÑ•È°Á¡åÍ¥…°µ‰½Õ¹¡…¹”°½ÈÁ½ÍĞµ¡½ŒÑ½±•É…¹”¸Aå%µ™¥Ğ¥ÌÑ¡”)Í…µ”•¹¥¹”…¹İ½Õ±¹½Ğ…‘¥¹‘•Á•¹‘•¹”™½ÈÑ¡¥ÌÅÕ•ÍÑ¥½¸¸I•™•É•¹•Ì)…¹±¥•¹Í”½É•ÕÍ”½É•Í½ÕÉ”…ÍÍ•ÍÍµ•¹Ğ…É”¥¸Ñ¡”ÁÉ½Ñ½½°¸½±±½Ü(¨©…Ñ”µŒµ…¸µ¥µ™¥ĞµÉ•™¥¹•µ•¹Ğ¨¨½¸¥ÑÌ¥µÁ±•µ•¹Ñ¥¹œ½µµ¥Ğì¹½Ğå•Ğ„$)ÍÕ•ÍÌ±…¥´¸!¥¡•ÈÍ…µÁ±¥¹œ¥Ì„‘¥…¹½ÍÑ¥Œ°¹½ĞÁ•Éµ¥ÍÍ¥½¸Ñ¼•áÁ…¹)µ•µ½Éä½Ñ¥µ”…ÁÌ½È…ÍÍ•ÉĞµ½ÉÁ¡½±½äÉ•½Ù•Éä¸((ŒŒŒÕ´1=0É•Í½ÕÉ”™…¥±ÕÉ”ìÍ•Á…É…Ñ”Õ¸™É••é”()Õ´İ…Ì€¨©¹½Ğ‘¥ÍÁ…Ñ¡•¨¨¸Q¡”™¥ÉÍĞ±½…°…ÑÑ•µÁĞ•áÁ½Í•…¸…É¡¥Ù”µ­•ä)…‘…ÁÑ•È•ÉÉ½È€¡Õ°ÍÑ½É•ÌAMÌ…Ì½°¹½Ğ}¹½Éµ…±¥é•‘}¥¹ÁÕĞ½	}¹½Éµ…±¥é•‘}¥¹ÁÕĞ¤¸)½ÉÉ•Ñ•Ñ¡…ĞÍ¡•µ„…•ÍÌ…¹…‘‘•„É•É•ÍÍ¥½¸Ñ•ÍĞİ¥Ñ¡½ÕĞ¡…¹¥¹œ)…¹äÍ¥•¹”Í•ÑÑ¥¹œ¸Q¡”Í•Á…É…Ñ”½ÉÉ•Ñ•±½…°…ÑÑ•µÁĞÉ•Ñ…¥¹•…±°•¥¡Ğ)ÍÕ•ÍÍ™Õ°Í…µÁ±¥¹œàÉ•Á±…åÌ°‰ÕĞ…±°•¥¡ĞÍ…µÁ±¥¹œÄØ…±±Ì™…¥±•¥¸)%µ™¥Ğ½¹Ù½±Ù•Èèé½Õ±±M•ÑÕÀ…±±½…Ñ¥½¸°‰•™½É”É•¹‘•É¥¹œ¸9¼Ñ½±•É…¹”½È)É•Í½ÕÉ”…Àİ…ÌÉ…¥Í•¸	½Ñ ½É¥¥¹…°…¹É•Á…¥É•±½…°É•½É‘Ì°…ÑÕ…°)•ÉÉ½È±½Ì°½¹™¥ÕÉ…Ñ¥½¹Ì…¹…Ù…¥±…‰±”…ÉÉ…ä¥‘•¹Ñ¥Ñ¥•Ì…É”ÁÉ•Í•ÉÙ•¥¸)ŒÕµ}±½…±|ÈÀÈØÀäÀÌ¹©Í½¹€ìÕ5}]=I-1=]}9=Q}%MAQ!¹åµ±€ÁÉ•Í•ÉÙ•ÌÑ¡”)Õ¹‘¥ÍÁ…Ñ¡•Á±…¸½ÕÑÍ¥‘”Ñ¡”…Ñ¥Ù”İ½É­™±½Ü‘¥É•Ñ½Éä¸ÍÕ‰Í•ÅÕ•¹Ğ)•ÅÕ¥Ù…±•¹ĞÉ•™…Ñ½È•áÁÉ•ÍÍ•ÌÑ¡”Á…¥È±…‰•±ÌÕÍ¥¹œÑ¡”™É½é•¸M5A1L)ÑÕÁ±”¥¹ÍÑ•…½˜±¥Ñ•É…°€à¼ÄØ°…±±½İ¥¹œÉ•ÕÍ”İ¥Ñ¡½ÕĞ…±Ñ•É¥¹œÕ´Í¥•¹”¸()¡•­•Ñ…•%µ™¥Ğ5½‘•±=‰©•Ğ…¹½¹Ù½±Ù•È…±±½…Ñ¥½¸½‘”¸]¥Ñ Ñ¡”)Õ¹¡…¹•™Õ±°AMÍÕÁÁ½ÉĞ°Í…µÁ±¥¹œÄØ¹••‘Ì…‰½ÕĞ€¨¨Ü¸ÜÜ¥™½ÈÍ¥àP)…ÉÉ…åÌ…±½¹”¨¨°…±É•…‘ä‰•å½¹Ñ¡”Í¥àµ¥…Àì‰±¥¹‘±äÉ•ÉÕ¹¹¥¹œ¥Ğ¥¸$)İ½Õ±¹½Ğ…¹Íİ•È„¹•ÜÅÕ•ÍÑ¥½¸¸Í•Á…É…Ñ•±ä™É½é•¸€¨©Õ¸€à¼ÄÀ¨¨•áÁ•É¥µ•¹Ğ)ÕÍ•ÌÑ¡”Í…µ”•¹¥¹”…¹Á¡åÍ¥…°Í•¹”°İ¥Ñ …‰½ÕĞ€¨¨Ì¸ÀĞ¥¨¨™½ÈÑ¡½Í”)…ÉÉ…åÌ…ĞÍ…µÁ±¥¹œÄÀ€¡¹½Ğ„ÁÉ½µ¥Í”½˜Á•…¬ÁÉ½•ÍÌµ•µ½Éä¤¸Q¡¥ÌÍ…µÁ±•Ì)„™¥¹•ÈÉ¥İ¥Ñ ¡•…‘É½½´ì¥Ğ¥Ì¹½Ğ„ÍÕ‰ÍÑ¥ÑÕÑ•ÍÕ•ÍÌ™½ÈÕ´ÄØ½È)ÁÉ½½˜½˜½¹Ù•É•¹”¸9¼¹•Ü¡…¹‘İÉ¥ÑÑ•¸½¹Ù½±ÕÑ¥½¸°É½ÁÁ•AM°)…±Ñ•É¹…Ñ¥Ù”¥¹Ñ•É…Ñ¥½¸…±½É¥Ñ¡´½ÈÁ¡åÍ¥…°‰½Õ¹¥Ì¥¹ÑÉ½‘Õ•¸)M•”Õ9}AI=Q==0¹µ‘€™½ÈÑ¡”Í½ÕÉ”¥Ñ…Ñ¥½¹Ì°…¹‘¥‘…Ñ”…ÍÍ•ÍÍµ•¹Ğ…¹)™É½é•¸‘•Í¥¸¸½±±½Ü€¨©…Ñ”µŒµ…¸µ¥µ™¥Ğµ‰½Õ¹‘•¨¨½¸Ñ¡”¥µÁ±•µ•¹Ñ¥¹œ½µµ¥Ğ¸)Q¡”Õ°ÁÉ•É•ÅÕ¥Í¥Ñ”É•É•ÍÍ¥½¸€ÌÌÜäàØÜÔÌÈå€•áÁ±¥¥Ñ±ä½µÁ±•Ñ•½ÍÕ•ÍÌ¸()Õ¸±½…°Ù•É¥™¥…Ñ¥½¸è…±°€ÄØÉ•¹‘•ÉÌ½µÁ±•Ñ•Õ¹‘•ÈÕ¹¡…¹•…ÁÌì)µ…á¥µÕ´µ…­•¥µ…”IMLİ…Ì€ÌÔàäàÜØ-¥¸±°€ÌÈ…µÁ±¥ÑÕ‘”ÍÑ…ÉÑÌ°•¥¡Ğ)Í…µÁ±¥¹œÁ…¥ÉÌ°€ÄØ™¥¹”%QL½¹…Ñ¥Ù”É•‘ÕÑ¥½¹Ì…¹€ÄØà™¥¹…±¥é•9Ah…ÉÉ…åÌ)İ•É”¡•­•¸¸ĞÁ…ÍÍ•Ñ¡”™Õ±°ÍÑÉ¥Ğ…ÉÑ¥™…Ğ…Õ‘¥Ğ¸¸ÄÌ½É¥¥¹…°)…ÉÑ¥™…Ğ…Õ‘¥Ğ€¨©™…¥±•¨¨‰•…ÕÍ”„±•™Ñ½Ù•ÈÑ•µÁ½É…Éä­•É¹•°…É¡¥Ù”İ…Ì)ÁÉ•Í•¹Ğ‘•ÍÁ¥Ñ”ÍÕ•ÍÍ™Õ°™¥¹…±¥é…Ñ¥½¸¸%ÑÌM!ÈÔØ¥Ì•á…Ñ±ä¥‘•¹Ñ¥…°)Ñ¼Ñ¡”™¥¹…±¥é•­•É¹•°°‰ÕĞ¥Ğ¥ÌÉ•Ñ…¥¹•…Ì…¸Õ¹•áÁ±…¥¹•…ÉÑ¥™…Ğ´)½µÁ±•Ñ•¹•ÍÌ™…¥±ÕÉ”°¹½ĞÉ•±…‰•±±•ÍÕ•ÍÌ¸Í•Á…É…Ñ”‰åÑ”µÙ•É¥™¥•½Áä)½˜™¥¹…±¥é•¸ÄÁÉ½‘ÕÑÌÁ…ÍÍ•Ñ¡”Õ¹¡…¹•¹Õµ•É¥…°½…±•‰É„…Õ‘¥Ğì)Ñ¡…Ğ‘½•Ì¹½Ğµ…­”Ñ¡”½É¥¥¹…°…ÉÑ¥™…Ğ½µÁ±•Ñ”¸Q¡”$…Õ‘¥Ğ½¹Ñ¥¹Õ•Ì)Ñ¼É•©•Ğ…¹ä€¹Á…ÉÑ¥…±€™¥±”ì¹¼±•…¹ÕÀ°¥¹½É”ÉÕ±”½ÈÑ½±•É…¹”İ…Ì)…‘‘•¸AåÑ¡½¸Ì‘½Õµ•¹Ñ•½Ì¹É•Á±…”Í•µ…¹Ñ¥Ìİ•É”¡•­•ìÑ¡”…ÕÍ”)½˜Ñ¡”‘ÕÁ±¥…Ñ”¥Ì¹½Ğ•ÍÑ…‰±¥Í¡•¸9¼Í¥•¹Ñ¥™¥ŒÉ•É•¹‘•È½ÈÍ•ÑÑ¥¹œ)¡…¹”İ…Ìµ…‘”¸ŒÕ¹}±½…±|ÈÀÈØÀäÀÌ¹©Í½¹€‘¥ÍÑ¥¹Õ¥Í¡•ÌÑ¡•Í”…Õ‘¥ĞÍ½Á•Ì¸)Õ±°±½…°ÍÕ¥Ñ”è€¨¨ÄØÜÁ…ÍÍ•¨¨°¥¹±Õ‘¥¹œÑ¡”Á¥¹¹••áÑ•É¹…°µ‰¥¹…ÉäÍµ½­”)Ñ•ÍĞì½¹”‘•±¥‰•É…Ñ”™…¥±ÕÉ”µ…ÁÑÕÉ”İ…É¹¥¹œÉ•µ…¥¹Ì¸A¥¹¹•…Ñ¥½¹±¥¹Ğ(Ä¸Ü¸ÄÈ…•ÁÑ•…±°İ½É­™±½İÌ¸ÑÕ…°$½ÕÑÁÕÑÌÍÑ¥±°É•ÅÕ¥É”É•Ù¥•Ü¸((ŒŒŒÕ¸…ÑÕ…°$…¹µ¥¹¥µ…°µ•¹Ù¥É½¹µ•¹ĞÉ•É•ÍÍ¥½¸É•Á…¥ÈƒŠP€ÈÀÈØ´Àä´ÀÌUQ()IÕ¸€¨¨ÌÌàÀØÄäÌÜÄÈ¨¨°½µµ¥Ğ€Øå˜äÀÌİ„ÄÄÙ„Õ‘ÜÕ”İ˜äĞÅŒÌá™”ØÔĞÉäÅˆÔĞİ€°)•áÁ±¥¥Ñ±ä½µÁ±•Ñ•½ÍÕ•ÍÌ™½È‰½Ñ ©½‰Ì°¥¹±Õ‘¥¹œÑ¡•¥ÈÍÑÉ¥Ğ½ÕÑÁÕĞ)…Õ‘¥ÑÌ¸½İ¹±½…‘•…ÉÑ¥™…ÑÌ€ääÄÌÄÄÌÔÀĞ¼ääÄÌÄÄÌàäà°Ù•É¥™¥•i%@M!ÈÔØ°)…¹¥¹‘•Á•¹‘•¹Ñ±äÉ•É…¸Ñ¡”Õ¹¡…¹•É•…µ½¹±ä…Õ‘¥ÑÌ½¸‰½Ñ ½É¥¥¹…°)$…ÉÑ¥™…ÑÌ¸±°€ÄØÉ•¹‘•ÉÌ°€ÌÈ‘¥É•Ğ…µÁ±¥ÑÕ‘”ÍÑ…ÉÑÌ°•¥¡ĞÍ…µÁ±¥¹œ)Á…¥ÉÌ°€ÄØ™¥¹”%QL½¹…Ñ¥Ù”É•‘ÕÑ¥½¹Ì…¹€¨¨ÄØà¹•Ü9Ah…ÉÉ…åÌ¨¨Á…ÍÍ•¸)9¼½É¥¥¹…°$…ÉÑ¥™…Ğ½¹Ñ…¥¹ÌÑ¡”±½…°±•™Ñ½Ù•ÈµÁ…ÉÑ¥…°…¹½µ…±ä¸)Q¡”½µÁ±•Ñ”É••¥ÁĞ¥Ì¥µ™¥Ñ}‰½Õ¹‘•‘|ÌÌàÀØÄäÌÜÄÈ¹©Í½¹€¸()%µ™¥ĞàµÑ¼´ÄÀ¹½Éµ…±¥é•0Ä‘É¥™Ğ¥Ì€¨¨À¸ÈÌÓŠLÀ¸ÈÔÀ”¨¨™½È™±…ÑÑ•¹•¸ôÀ¸Ô°(¨¨À¸ÀÄÌÃŠLÀ¸ÀÄÜÜ”¨¨™½ÈÉ½Õ¹¸ôÀ¸Ô°€¨¨À¸ÈÜÇŠLÀ¸ÈÜÌ”¨¨™½È™±…ÑÑ•¹•¸ôØ°)…¹€¨¨À¸ÀØÈÃŠLÀ¸ÀØäÔ”¨¨™½ÈÉ½Õ¹¸ôØ¸ĞÍ…µÁ±¥¹œÄÀ°‘¥™™•É•¹•ÌÉ•±…Ñ¥Ù”)Ñ¼…¹½¹¥…°…±M¥´¹½}•±°…É”€¨¨Ä¸äÄÛŠLÄ¸äĞÀ”¨¨°€¨¨À¸ÄÀÌÓŠLÀ¸ÄÀÌà”¨¨°(¨¨À¸ÀØÀËŠLÀ¸ÀØàä”¨¨°…¹€¨¨À¸ÄàäÇŠLÀ¸ÈÀÌà”¨¨°É•ÍÁ•Ñ¥Ù•±ä¸Q¡•Í”…É”)‘•ÍÉ¥ÁÑ¥Ù”°İ¥Ñ Ñ¡”É•™•É•¹”¥µ…”‘•™¥¹¥¹œ•… ‘•¹½µ¥¹…Ñ½ÈìÕ°ÕÍ•)%µ™¥Ğ…Ì¥ÑÌÉ•™•É•¹”™½È¥ÑÌÉ½ÍÌµ½‘”½µÁ…É¥Í½¸¸9•¥Ñ¡•È‰•ÑÑ•È¹½È)İ½ÉÍ”…É••µ•¹Ğ•ÍÑ…‰±¥Í¡•ÌÑÉÕÑ °…¹™Õ±°µÉ…¹”½¹Ù•É•¹”É•µ…¥¹Ì½Á•¸¸()Q¡”Í•Á…É…Ñ”•¹•É…°É•É•ÍÍ¥½¸ÉÕ¸€¨¨ÌÌàÀØÄäÌÔàà™…¥±•½¸AåÑ¡½¸Ì¸ÄÄ)…¹Ì¸ÄÈ‘ÕÉ¥¹œ½±±•Ñ¥½¸¨¨°¹½Ğ‘ÕÉ¥¹œ„Í¥•¹”™¥Ğ¸ÑÕ…°±½ÌÍ¡½Ü)5½‘Õ±•9½Ñ½Õ¹‘ÉÉ½Èè9¼µ½‘Õ±”¹…µ•€…ÍÑÉ½Áä€¥¸Ñ¡”Ñİ¼¹•İ±ä…‘‘•)%µ™¥ĞÑ•ÍĞµ½‘Õ±•Ì¸Q¡”µ¥¹¥µ…°¡…É¹•ÍÌ¥¹Ñ•¹Ñ¥½¹…±±ä‘½•Ì¹½Ğ¥¹ÍÑ…±°)Ñ¡”½ÁÑ¥½¹…°…ÍÑÉ½¹½µäÍÑ…¬ì•á¥ÍÑ¥¹œ…ÍÑÉ½¹½µäÑ•ÍÑÌ…±É•…‘äÕÍ”ÁåÑ•ÍĞÌ)‘½Õµ•¹Ñ•¥µÁ½ÉÑ½ÉÍ­¥À¸ÁÁ±äÑ¡…ĞÍ…µ”µ½‘Õ±”µ±•Ù•°‘•Á•¹‘•¹äÕ…ÉÑ¼)Ñ¡”Ñİ¼¹•Ü™¥±•Ì¸¼¹½Ğ…‘…¸á™…¥°°…±Ñ•È…¸…ÍÍ•ÉÑ¥½¸°½ÈÉ•±…à„)Í¥•¹Ñ¥™¥ŒÉ¥Ñ•É¥½¸¸%¸Ñ¡”‘•‘¥…Ñ•Õ¸İ½É­™±½Ü°…‘µ…¹‘…Ñ½Éä¥µÁ½ÉÑÌ)…¹€¨©•á…ĞÁ¥¸•ÅÕ…±¥Ñä‰•™½É”Ñ•ÍÑÌ¨¨°…¹¥¹±Õ‘”Ñ¡”Õ´…‘…ÁÑ•ÈÑ•ÍÑÌ)…±½¹Í¥‘”Ñ¡”‰½Õ¹‘•…¹…ÕÑ¡½ÈµÉ•¹‘•É•ÈÑ•ÍÑÌ¸5¥ÍÍ¥¹œ‘•Á•¹‘•¹¥•ÌÑ¡•É”)É•µ…¥¸„¡…É™…¥±ÕÉ”°¹½Ğ„Í­¥À¸M¥•¹Ñ¥™¥ŒÍÉ¥ÁÑÌ½ÁÉ½Ñ½½±Ì…É”Õ¹¡…¹•¸)M½ÕÉ”è¡ÑÑÁÌè¼½‘½Ì¹ÁåÑ•ÍĞ¹½Éœ½•¸½ÍÑ…‰±”½¡½ÜµÑ¼½Í­¥ÁÁ¥¹œ¹¡Ñµ°Í­¥ÁÁ¥¹œµ½¸µ„µµ¥ÍÍ¥¹œµ¥µÁ½ÉĞµ‘•Á•¹‘•¹ä()1½…°Ù•É¥™¥…Ñ¥½¸è„™É•Í µ¥¹¥µ…°•¹Ù¥É½¹µ•¹ĞÁ…ÍÍ•Ì€¨¨ØÔÑ•ÍÑÌ¨¨°İ¥Ñ (ÄÌ½ÁÑ¥½¹…°µ½‘Õ±•Ì•áÁ±¥¥Ñ±äÍ­¥ÁÁ•ìÑ¡”Á¥¹¹•™Õ±°•¹Ù¥É½¹µ•¹ĞÁ…ÍÍ•Ì(¨¨ÄØÜÑ•ÍÑÌ¨¨°¹½¹”Í­¥ÁÁ•°¥¹±Õ‘¥¹œÑ¡”…ÕÑ¡½Èµ‰¥¹…ÉäÍµ½­”Ñ•ÍĞ¸Q¡”)¹•Üµ…¹‘…Ñ½ÉäÕ…ÉÉ•©•ÑÌÑ¡”µ¥¹¥µ…°•¹Ù¥É½¹µ•¹Ğ…¹…•ÁÑÌÑ¡”•á…Ğ)Á¥¹¹•½¹”¸A¥¹¹•…Ñ¥½¹±¥¹ĞÄ¸Ü¸ÄÈÁ…ÍÍ•Ì¸AÉ•Í•ÉÙ”‰½Ñ ™…¥±•É•É•ÍÍ¥½¸)©½‰Ì…¹Ñ¡”ÍÕ•ÍÍ™Õ°½É¥¥¹…°Õ¸¸Q¡”É•Á…¥È½µµ¥ĞÑÉ¥•ÉÌÑ¡”)É•É•ÍÍ¥½¸…¹Í…µ”µÍ•ÑÑ¥¹œÕ¸Ù•É¥™¥…Ñ¥½¸É•ÉÕ¹Ìì‘¼¹½Ğ…‘Ù…¹”Ñ¼¹•Ü)‘•Á•¹‘•¹ĞÍ¥•¹”‰•™½É”Ñ¡•Í”¹••ÍÍ…Éä¡•­ÌÍÕ••¸½±±½ÜÑ¡”¹•İ•ÍĞ)Ù•É¥™¥…Ñ¥½¸µÍÕ¥Ñ•€…¹…Ñ”µŒµ…¸µ¥µ™¥Ğµ‰½Õ¹‘•‘€½¸Ñ¡”É•Á…¥È½µµ¥Ğ¸((ŒŒŒÕ¸É•Á…¥ÈÉ•ÉÕ¹Ì½¹™¥Éµ•ìÕ¼™É½é•¸ƒŠP€ÈÀÈØ´Àä´ÀÌUQ()¥Ñ!Õˆ•áÁ±¥¥Ñ±ä½¹™¥ÉµÌ‰½Ñ É•Á…¥ÈÉÕ¹Ì…Ğ)€äØØáˆÅ•˜ØÜØÌØÜÙäÍİ™•™‘ˆĞàÀÀÔÑàÁŒàÄàÉ…€½µÁ±•Ñ•½ÍÕ•ÍÌ¸Y•É¥™¥…Ñ¥½¸)ÉÕ¸€¨¨ÌÌàÄÀÄàÜàÈÜ¨¨Á…ÍÍ•½¸AåÑ¡½¸€Ì¸ÄÄ…¹€Ì¸ÄÈìÑ¡”…ÑÕ…°AåÑ¡½¸Ì¸ÄÄ±½œ)É•Á½ÉÑÌ€ØÔÁ…ÍÍ•…¹€ÄÌ•áÁ±¥¥Ğ½ÁÑ¥½¹…°µ…ÍÑÉ½¹½µäÍ­¥ÁÌ¸•‘¥…Ñ•Õ¸)ÉÕ¸€¨¨ÌÌàÄÀÄàÜàØĞ¨¨Á…ÍÍ•‰½Ñ ¡½ÍĞ©½‰Ì¸… É•ÅÕ¥É•Ñ¡”•á…ĞÁ¥¹¹•)…ÍÑÉ½¹½µä•¹Ù¥É½¹µ•¹Ğ°Á…ÍÍ•€ÈÄÑ…É•Ñ•Ñ•ÍÑÌ°É•É…¸Ñ¡”Õ¹¡…¹•Õ¸)Í¥•¹”°…¹Á…ÍÍ•Ñ¡”ÍÑÉ¥Ğ™Õ±°µ½ÕÑÁÕĞ…Õ‘¥Ğ¸Q¡”¸ôĞ©½ˆ…Õ‘¥ĞÉ•Á½ÉÑÌ)•¥¡Ğİ½É­•ÉÌ°€ÄØÍÑ…ÉÑÌ°™½ÕÈÁ…¥ÉÌ°€àĞ¹•Ü…ÉÉ…åÌ…¹•¥¡Ğ%QL½ÕÑÁÕÑÌì)Ñ¡”Íåµµ•ÑÉ¥Œ¸ôÄ©½ˆÁ…ÍÍ•Ñ¡”Í…µ”ÍÑ•ÁÌ¸Q¡¥Ì½¹™¥ÉµÌÑ¡”Ñ•ÍĞµ½±±•Ñ¥½¸)É•Á…¥Èİ¥Ñ¡½ÕĞ¡…¹¥¹œÕ¸ÌÍ¥•¹Ñ¥™¥ŒÉ•ÍÕ±Ğ½È•É…Í¥¹œ™…¥±•É•É•ÍÍ¥½¸(ÌÌàÀØÄäÌÔàà¸()Õ±°µ‰½Õ¹¹Õµ•É¥…°½¹Ù•É•¹”É•µ…¥¹Ì½Á•¸…ĞÑ¡”•áÑÉ•µ”½µÁ…Ğ½É¹•ÉÌ¸)Q¡…Ğ‘½•Ì¹½ĞÉ•ÅÕ¥É”É•Á•…Ñ¥¹œ…¹½Ñ¡•È½É¹•ÈÍİ••À‰•™½É”Ñ•ÍÑ¥¹œÑ¡”…ÑÕ…°)¹½µ¥¹…°…¹¡½ÈèÕ …±É•…‘äµ•…ÍÕÉ•½¹±ä€À¸ÀÀÈ´´À¸ÀÈà”%µ™¥Ğà½…±M¥´¥µ…”)0Ä‘¥™™•É•¹•Ì…ĞI”ôÄØ°ÄôÀ¸Ø°¸ôÄ¼Ğ¸™Ñ•ÈÉ•¡•­¥¹œÑ¡”%µ™¥ĞÁ…Á•È°)½™™¥¥…°½¹™¥ÕÉ…Ñ¥½¸½AM½A½¥¹ÑM½ÕÉ”‘½Õµ•¹Ñ…Ñ¥½¸…¹Á¥¹¹••á•ÕÑ…‰±”°)Õ=}AI=Q==0¹µ‘€™É••é•Ì„µ…Ñ¡•µAM°¹½¥Í•±•ÍÌ°™É•”µ¡½ÍĞµÍ¡…Á”É½ÍÌ´)™¥ÑÑ•ÈÁÉ•™±¥¡Ğ…Ğ½¹±äÑ¡½Í”¹½µ¥¹…°…¹¡½ÉÌ¸I•ÕÍ”%µ™¥Ğ€Ä¸ä¸ÀÌ½İ¸M•ÉÍ¥Œ°)A½¥¹ÑM½ÕÉ”…¹½ÁÑ¥µ¥é•Èì¹¼ÕÍÑ½´É•¹‘•É•È½È½ÁÑ¥µ¥é•È¥Ì¥¹ÑÉ½‘Õ•¸()Õ¼­••ÁÌ¡½ÍĞ½¹Õ±•…È•¹Ñ•ÉÌ™¥á•…¹É•±•…Í•ÌA°Ä°¸°I”…¹‰½Ñ )¹½¹¹•…Ñ¥Ù”…µÁ±¥ÑÕ‘•Ì™½Èµ½‘Õ±•Ì½…¹8½¡½ÍĞ€Ä¼ÄÀ°İ¥Ñ Ñ¡É•”™É½é•¸)ÍÑ…ÉÑÌ¸Q¡”İÉ½¹œµAM…É´¥Ì‘•±¥‰•É…Ñ•±ä…‰Í•¹Ğè™¥ÉÍĞ•ÍÑ…‰±¥Í ¡½ÜÑ¡”)¥¹‘•Á•¹‘•¹Ğ¡½ÍĞÉ•¹‘•É•È½™¥ÑÑ•È‰•¡…Ù•Ìİ¥Ñ Ñ¡”µ…Ñ¡•Í¥¹••µÁ¥É¥…°)AM°Ñ¡•¸™É••é”µ¥Íµ…Ñ Í•Á…É…Ñ•±ä¥˜©ÕÍÑ¥™¥•¸±°Í¡…Á”‰½Õ¹‘Ì°É½À°)AMÙ…±Õ•Ì…¹™Õ±°µÁ¥á•°½‰©•Ñ¥Ù”É•µ…¥¸¸M¥¹•¹•…Ñ¥Ù”İ¥¹Ì…É”¹½Ğ)Á¡½Ñ½¸µÉ•…‘ä¸½µÁ±•Ñ”½ÕÑÁÕĞ…¹…±•‰É„…É”É•ÅÕ¥É•°‰ÕĞ¹¼É•½Ù•Éä‰…¹)¥Ì¥¹Ù•¹Ñ•¸½±±½Ü…Ñ”µŒµ…¸µ¥µ™¥Ğµ™É•”µÍ¡…Á•€ì±½…°Ñ•ÍÑÌ½È„ÍÕ•ÍÍ™Õ°)ÁÉ½•ÍÌ•á¥Ğ…É”¹½Ğ¥Ñ!ÕˆÍÕ•ÍÌ½ÈÁ¡åÍ¥…°É•½Ù•Éä¸()1½…°¥µÁ±•µ•¹Ñ…Ñ¥½¸Ù•É¥™¥…Ñ¥½¸è€¨¨ÄÜÄÑ•ÍÑÌÁ…ÍÍ•¨¨°İ¥Ñ Ñ¡”Õ¹¡…¹•)Õ •áÑ•É¹…°µµ…­•¥µ…”Íµ½­”Ñ•ÍĞÍ­¥ÁÁ•‰•…ÕÍ”Õ¼¥¹ÍÑ…±±ÌÑ¡”Í•Á…É…Ñ”)Á¥¹¹•¥µ™¥Ñ€•á•ÕÑ…‰±”ì¥ÑÌ½İ¸‰¥¹…Éä½™Õ¹Ñ¥½¸¡•¬Á…ÍÍ•¸Ñ¥½¹±¥¹Ğ(Ä¸Ü¸ÄÈ…•ÁÑÌ…±°İ½É­™±½İÌ¸½µÁ±•Ñ”±½…°¸ôÄ•á•ÕÑ¥½¸…¹É•…µ½¹±ä)…Õ‘¥Ğ¡•­•™½ÕÈ…Í•Ì°€ÄÈÍÑ…ÉÑÌ…¹€Ğà¥µ…”…ÉÉ…åÌİ¥Ñ ¹¼İ¥¹¹•È‰½Õ¹)¡¥Ğ¸Q¡”µ¥¹¥µÕ´µ½ÍĞÍ½±ÕÑ¥½¹ÌÉ•½Ù•È¸ôÄ¸ÀÀÄÀÔ´´Ä¸ÀÀÄĞÔ°)I”ôÄÔ¸äàÌÔ´´ÄØ¸ÀÄÀà…¹ÄôÀ¸ÔääØÄĞ´´À¸ÔääÜÄä¸!½İ•Ù•È°Ñ¡”‘•±¥‰•É…Ñ•±ä)•áÑ•¹‘•ÍÑ…ÉĞ¥¸‰½Ñ 8½¡½ÍĞôÄÀ…Í•Ì½¹Ù•É•Ñ¼„µÕ İ½ÉÍ”ÄôÄ‰½Õ¹‘…Éä)‰…Í¥¸ìÑ¡…ĞÍÑ…ÉĞ¥ÌÉ•Ñ…¥¹•É…Ñ¡•ÈÑ¡…¸É•Á½ÉÑ•…Ì…É••µ•¹Ğ¸Q¡•Í”…É”)1=0Á¥Á•±¥¹”½‰Í•ÉÙ…Ñ¥½¹Ì½¹±ä°¹½Ğ¥Ñ!ÕˆÍÕ•ÍÌ½È…¸…•ÁÑ…¹”‰…¹¸((ŒŒŒÕ¼…ÑÕ…°$ÍÁ±¥ĞÉ•ÍÕ±ĞìÕÀ™É½é•¸ƒŠP€ÈÀÈØ´Àä´ÀĞUQ()IÕ¸€¨¨ÌÌàÄäÌĞäàÔĞ¨¨…Ğ€ÜÀĞÄäÀÜÈÌÅ„ÈØÈäÉ˜áŒØØÍŒÉ‘˜àäá˜ÌÄäÈÄÜÕ„İ•€)•áÁ±¥¥Ñ±ä½µÁ±•Ñ•½™…¥±ÕÉ”¸Q¡”¸ôÄ©½ˆ½µÁ±•Ñ•½ÍÕ•ÍÌ…¹¥ÑÌÍÑÉ¥Ğ)…Õ‘¥Ğ¡•­•…±°™½ÕÈ…Í•Ì°€ÄÈÍÑ…ÉÑÌ…¹€Ğà…ÉÉ…åÌ¸Q¡”¸ôĞ©½ˆ™…¥±•)‰•™½É”…Õ‘¥Ğ…™Ñ•ÈÉ•½É‘¥¹œÍ¥àÍÑ…ÉÑÌèÑ¡”½µÁ…ĞÍÑ…ÉĞ™½Èµ½‘Õ±”…Ğ)8½¡½ÍĞôÄÀÉ•…¡•Ñ¡”Õ¹¡…¹•€ÄàÀµÍ•½¹ÁÉ½•ÍÌ±¥µ¥Ğ€¡É•ÑÕÉ¸½‘”€ÄÈĞ¤)…¹ÁÉ½‘Õ•¹¼‰•ÍĞµ™¥Ğ½µ½‘•°½É•Í¥‘Õ…°™¥±•Ì¸QÉÕÑ …¹•áÑ•¹‘•ÍÑ…ÉÑÌ™½È)Ñ¡…Ğ•á…ĞÍ•¹”½µÁ±•Ñ•¥¸€Ì´´ĞÍ•½¹‘Ì°…É••…Ğ¸ôĞ¸ÄÌÌØÄ°I”ôÄØ¸ÈÈÜ°)ÄôÀ¸ÔäØÄÔÄ…¹Á½¥¹Ğ™±Õàôä¸ääÜÈÔ°…¹¡…¹¼‰½Õ¹¡¥Ğ¸Q¡¥Ì‘½•Ì¹½Ğµ…­”)Õ¼½µÁ±•Ñ”½ÈÍÕ•ÍÍ™Õ°¸ÉÑ¥™…Ğ%Ì°i%@¡…Í¡•Ì…¹™¥ÑÑ•ÍÕµµ…É¥•Ì…É”)ÁÉ•Í•ÉÙ•¥¸ŒÕ½|ÌÌàÄäÌĞäàÔĞ¹©Í½¹€ìÑ¡”™…¥±•…ÉÑ¥™…ĞÉ•µ…¥¹Ì…ÕÑ¡½É¥Ñ…Ñ¥Ù”¸()=™™¥¥…°%µ™¥Ğ€Ä¸äÍ½±Ù•È‘½Õµ•¹Ñ…Ñ¥½¸İ…ÌÉ•¡•­•‰•™½É”É•ÍÁ½¹‘¥¹œ¸ÕÀ)¥Ì„Í•Á…É…Ñ”‰½Õ¹‘•½ÁÑ¥µ¥é•ÈµÁ…Ñ ‘¥…¹½ÍÑ¥ŒèÉ•Á±…ä½¹±äÑ¡”‘•±…É•¸ôĞ°)8½¡½ÍĞôÄÀ½µÁ…ĞÍÑ…ÉĞ™½Èµ…Ñ¡•µ½‘Õ±•Ì½İ¥Ñ Ñ¡”¥‘•¹Ñ¥…°¥µ…”°)½‰©•Ñ¥Ù”°‰½Õ¹‘Ì°Í¥¹•AM°Ñ¡É•…½Õ¹Ğ…¹€ÄàÀµÍ•½¹…À¸½µÁ…É”%µ™¥ĞÌ)‘•™…Õ±Ğ1•Ù•¹‰•Éœ´µ5…ÉÅÕ…É‘Ğ……¥¹ÍĞ¥ÑÌµ…¥¹Ñ…¥¹•€´µ¹µ€9•±‘•È´µ5•…Í½±Ù•È°)É•½É‘¥¹œÑ¥µ•½ÕÑÌ…ÌÉ•ÍÕ±ÑÌ…¹É•½µÁÕÑ¥¹œÑ¡”½‰©•Ñ¥Ù”™½È™¥¹¥Ñ”½ÕÑÁÕÑÌ¸)Q¡¥Ì¥Ì¹½Ğ„Õ¼É•ÉÕ¸°É•½Ù•ÉäÑ½±•É…¹”½ÈÍÕ‰ÍÑ¥ÑÕÑ”Á…ÍÌ¸¥™™•É•¹Ñ¥…°)Ù½±ÕÑ¥½¸¥Ì‘•™•ÉÉ•‰•…ÕÍ”¥ÑÌÁ½ÁÕ±…Ñ¥½¸½ÍĞ¥Ìµ…Ñ•É¥…±±ä±…É•Èì¥Ğ)µ…ä‰”©ÕÍÑ¥™¥•½¹±ä…™Ñ•ÈÑ¡”‰½Õ¹‘•Á…Ñ¡Ì…É”É•Ù¥•İ•¸M•”)ÕA}AI=Q==0¹µ‘€¸¼¹½ĞÍÑ…ÉĞÑ¡”İÉ½¹œµAM™É•”µÍ¡…Á”…É´‰•™½É”…ÑÕ…°ÕÀ)…ÉÑ¥™…ÑÌ…É”…Õ‘¥Ñ•¸((ŒŒŒÕÀ…ÑÕ…°$…¹ÕÄ™É••é”ƒŠP€ÈÀÈØ´Àä´ÀĞUQ()IÕ¸€¨¨ÌÌàÈÌĞÀÔÜÌÌ¨¨…ĞˆÔØĞÑŒäÉ™„Å•™ŒÜÈÀÑÈØİ…‘ŒÀäàØÌÙ˜ĞÌİˆÉ€)•áÁ±¥¥Ñ±ä½µÁ±•Ñ•½ÍÕ•ÍÌ™½Èµ½‘Õ±•Ì…¹¸	½Ñ ÍÑÉ¥Ğ…Õ‘¥ÑÌİ•É”)É•ÉÕ¸½¸Ñ¡”‘½İ¹±½…‘•½É¥¥¹…°…ÉÑ¥™…ÑÌìi%@M!ÈÔØ…¹…ÉÑ¥™…Ğ%Ì…É”)É•½É‘•¥¸ŒÕÁ|ÌÌàÈÌĞÀÔÜÌÌ¹©Í½¹€¸5½‘Õ±”Ì14É•Á±…ä……¥¸É•…¡•Ñ¡”)Õ¹¡…¹•€ÄàÀµÍ•½¹…À…™Ñ•È€Ğäà±½•¥Ñ•É…Ñ¥½¹Ì¸9•±‘•È´µ5•…½µÁ±•Ñ•)¥¸€à¸ÈÄÍ•½¹‘Ì…Ğ¸ôÈ¸ÄÜÄ°I”ôä¸ĞÄĞ°ÄôÀ¸ØĞÈ…¹…¸MM€¨¨àä¸ÀĞÑ¥µ•Ì¨¨Ñ¡”)™¥¹¥Ñ”Õ¼Í½±ÕÑ¥½¸¸½Èµ½‘Õ±”°14½µÁ±•Ñ•¥¸€ÄÀ¸ÄÌÍ•½¹‘Ì…Ğ¸ôĞ¸ÈÈÜ°)I”ôÄØ¸ÄÌÀ°ÄôÀ¸Ôää°İ¡¥±”9•±‘•È´µ5•…½µÁ±•Ñ•¥¸€Ü¸àĞÍ•½¹‘Ì…Ğ¸ôÈ¸ĞĞØ°)I”ôä¸ÄÔĞ°ÄôÀ¸ØàÔ…¹…¸MM€¨¨ÌÈ¸ÄĞÑ¥µ•Ì¨¨İ½ÉÍ”¸9¼É•Á½ÉÑ•Í½±ÕÑ¥½¸¡¥Ğ)„‰½Õ¹¸%µ™¥ĞÌ™½Éµ…°µ½‘Õ±”µ14Õ¹•ÉÑ…¥¹Ñ¥•Ì…É”•áÑÉ•µ•±ä±…É”°İ¡¥ )¥ÌÉ•Ñ…¥¹•…Ì¥‘•¹Ñ¥™¥…‰¥±¥Ñä•Ù¥‘•¹”É…Ñ¡•ÈÑ¡…¸¥¹Ñ•ÉÁÉ•Ñ•…ÌÁÉ•¥Í¥½¸¸()ÕÀÑ¡•É•™½É”½¹™¥ÉµÌ„µ½‘Õ±”´…¹Í½±Ù•Èµ‘•Á•¹‘•¹Ğ±½…°µ‰…Í¥¸ÁÉ½‰±•´ì)…¸½ÁÑ¥µ¥é•ÈÍÕ•ÍÌ±…‰•°‘½•Ì¹½Ğ•ÍÑ…‰±¥Í É•½Ù•Éä¸	•™½É”…¹äAM)µ¥Íµ…Ñ °ÕÄ™É••é•ÌÑ¡”¡•­ÍÕ´µÁ¥¹¹•%µ™¥Ğ€´µ‘”µ±¡Í€±½‰…°Í½±Ù•Èİ¥Ñ )Ñİ¼‘•Ñ•Éµ¥¹¥ÍÑ¥ŒÍ••‘Ì½¸Ñ¡”•á…ĞÍ…µ”‘¥™™¥Õ±Ğ½¥¹ÁÕÑÌ°‰½Õ¹‘Ì°)½‰©•Ñ¥Ù”…¹€ÄàÀµÍ•½¹…À¸á¥ÍÑ¥¹œM¥Aäİ…Ì¹½ĞÍÕ‰ÍÑ¥ÑÕÑ•‰•…ÕÍ”)Ñ¡…Ğİ½Õ±¡…¹”Ñ¡”•¹¥¹”½½‰©•Ñ¥Ù”¥¹Ñ•É™…”°…¹Aå%µ™¥Ğİ½Õ±¹½Ğ…‘…¸)¥¹‘•Á•¹‘•¹Ğ•¹¥¹”¸Q¥µ•½ÕÑÌÉ•µ…¥¸É•ÍÕ±ÑÌì¹¼Á½ÍĞµ¡½Œ™¥Ğ‰…¹¥Ì…‘‘•¸)M•”ÕE}AI=Q==0¹µ‘€¸ÑÕ…°ÕÄ½ÕÑÁÕÑÌµÕÍĞ‰”É•Ù¥•İ•‰•™½É”ÁÉ½••‘¥¹œ¸((ŒŒŒÕÄ…ÑÕ…°$…¹ÕÈ™É••é”ƒŠP€ÈÀÈØ´Àä´ÀĞUQ()IÕ¸€¨¨ÌÌàÌÀØØÄØÔØ¨¨…Ğ)™˜ÌäÜÀÅ˜İ•ŒÕˆå˜ØäààÜÌÀØÑ‰àÕ‘„ÔÍ„ĞÄÜÔĞÑ€•áÁ±¥¥Ñ±ä½µÁ±•Ñ•½ÍÕ•ÍÌ™½È)‰½Ñ µ½‘Õ±•Ì¸Q¡”‘½İ¹±½…‘•…ÉÑ¥™…ÑÌ€¡%Ì€ääÈÄØàÜØÔä…¹€ääÈÄØàäÈää¤Á…ÍÍ•)Ñ¡•¥ÈÍÑÉ¥Ğ…Õ‘¥ÑÌ…¹Ñ¡•¥Èi%@¡…Í¡•Ì…É”É•½É‘•¥¸)ŒÕÅ|ÌÌàÌÀØØÄØÔØ¹©Í½¹€¸±°™½ÕÈµ1!LÁÉ½•ÍÍ•ÏŠQÑİ¼ÁÉ•‘•±…É•Í••‘Ì™½È)•… µ½‘Õ±—ŠQÉ•…¡•Ñ¡”Õ¹¡…¹•€ÄàÀµÍ•½¹…Àİ¥Ñ¡½ÕĞ½µÁ±•Ñ”™¥Ğ)ÁÉ½‘ÕÑÌ¸Q¡ÕÌÕÄ¥Ì„½µÁ±•Ñ”‘¥…¹½ÍÑ¥Œ•á•ÕÑ¥½¸‰ÕĞÁÉ½Ù¥‘•Ì¹¼™¥¹¥Ñ”)±½‰…°µÍ•…É Í½±ÕÑ¥½¸½È…É••µ•¹Ğ±…¥´¸Q¡”…À¥Ì¹½Ğ•áÁ…¹‘•¸()Õ¼´µÕÄ¹½Ü¡…É…Ñ•É¥é”Ñ¡”¹½µ¥¹…°µ…Ñ¡•µAMÁÉ½‰±•´…ÌÍÑ…ÉĞ´°Í½±Ù•È´)…¹µ½‘Õ±”µ‘•Á•¹‘•¹Ğè™¥¹¥Ñ”±½İ•Èµ½ÍĞ•áÑ•¹‘•µ¡½ÍĞÍ½±ÕÑ¥½¹Ì•á¥ÍĞ°‰ÕĞ)Ñ¡”½µÁ…Ğµ½‘Õ±”µ14Á…Ñ …¹…±°‰½Õ¹‘•Á½ÁÕ±…Ñ¥½¸Á…Ñ¡Ì™…¥°İ¥Ñ¡¥¸Ñ¡”)‘•±…É•É•Í½ÕÉ”•¹Ù•±½Á”¸Q¡¥Ì±¥µ¥Ñ…Ñ¥½¸¥ÌÍÕ™™¥¥•¹Ñ±ä•áÁ±¥¥ĞÑ¼…ÉÉä)™½Éİ…É…Ì…¸½‰Í•ÉÙ…‰±”ì¥Ğ¥Ì¹½Ğ½¹Ù•ÉÑ•¥¹Ñ¼„µ…Ñ¡•µAMÁ…ÍÌ¸()½±±½İ¥¹œi¡Õ…¹œ€˜M¡•¸ÌÁÕ‰±¥Í¡•ÁÉ•‘¥Ñ¥½¸Ñ¡…ĞAMµ¥Íµ…Ñ ¡…¹•Ì¡½ÍĞ)™±Õà…¹½¹•¹ÑÉ…Ñ¥½¸°ÕI}AI=Q==0¹µ‘€™É••é•ÌÑ¡”Í•Á…É…Ñ”İÉ½¹œµAM)™É•”µÍ¡…Á”‘¥…¹½ÍÑ¥Œ¸%Ğ•á¡…¹•Ì½AMÌ½¹±ä…Ğ¹½¥Í•±•ÍÌ8½¡½ÍĞôÄÀ°)É•ÕÍ•ÌÑ¡”•á…ĞÕ¼ÍÑ…ÉÑÌ°‰½Õ¹‘Ì°½‰©•Ñ¥Ù”…¹É•Í½ÕÉ”…À°…¹É•½É‘Ì)Ñ¥µ•½ÕÑÌ…¹‰½Õ¹‘…É¥•Ìİ¥Ñ¡½ÕĞÉ•ÅÕ¥É¥¹œ½¹Ù•É•¹”¸9½¥Í”É•µ…¥¹Ì…‰Í•¹Ğ¸)9¼É•½Ù•Éä‰…¹°É•¹‘•É•È¡…¹”½ÈÁ¡åÍ¥…°µAM±…¥´¥Ì¥¹ÑÉ½‘Õ•¸½±±½Ü)…Ñ”µŒµ…¸µ¥µ™¥ĞµİÉ½¹œµÁÍ˜µ™É•”µÍ¡…Á•€ìÉ•Ù¥•Ü¥ÑÌ…ÑÕ…°…ÉÑ¥™…ÑÌ‰•™½É”)¡½½Í¥¹œ„¹½¥Í”½Èµ½ÉÁ¡½±½ä…Ñ”¸((ŒŒŒÕÈ…ÑÕ…°$É•ÍÕ±Ğ…¹ÑÉ…¹Í¥Ñ¥½¸Ñ¼•İÍ¹…ÀƒŠP€ÈÀÈØ´Àä´ÀĞUQ()IÕ¸€¨¨ÌÌàĞÈÌĞÜÌÈà¨¨…Ğ)€å„äÉˆäÀàÔÑ‘…‘„ÄäĞÙŒäàØÀàå……ŒÄØÀÅ•Ù˜äàÉ€•áÁ±¥¥Ñ±ä½µÁ±•Ñ•½ÍÕ•ÍÌ™½È)‰½Ñ ¡½ÍĞµ¥¹‘•à©½‰Ì¸Q¡”½É¥¥¹…°‘½İ¹±½…‘•…ÉÑ¥™…ÑÌ€¡%Ì€ääÈÔØĞĞØäÜ…¹(ääÈÔÔÜÔÌàÈ¤Á…ÍÍ•Ñ¡•¥ÈÍÑÉ¥Ğ…Õ‘¥ÑÌìi%@M!ÈÔØ…¹…±°Í•±•Ñ•™¥ÑÌ…É”)É•½É‘•¥¸ŒÕÉ|ÌÌàĞÈÌĞÜÌÈà¹©Í½¹€¸É½ÍÌ€ÄÈ‘•±…É•ÍÑ…ÉÑÌ°Í¥à½µÁ±•Ñ•)İ¥Ñ ™¥¹¥Ñ”ÁÉ½‘ÕÑÌ…¹Í¥àÉ•…¡•Ñ¡”Õ¹¡…¹•€ÄàÀµÍ•½¹…À¸±°™½ÕÈ)µ¥¹¥µÕ´µ™¥¹¥Ñ”Í½±ÕÑ¥½¹Ì¡¥Ğ…Ğ±•…ÍĞ½¹”‰½Õ¹¸()Q¡”•™™•Ğ¥Ì‘¥É•Ñ¥½¹…°…¹…Ñ…ÍÑÉ½Á¡¥Œ™½Èµ½ÉÁ¡½±½äÉ•½Ù•Éä¸¥ÑÑ¥¹œ)µ½‘Õ±”µ‘…Ñ„İ¥Ñ µ½‘Õ±”ÌAM‘É½Ù”Ñ¡”Á½¥¹ĞµÍ½ÕÉ”™±ÕàÑ¼é•É¼…¹ÁÕĞ)…‰½ÕĞ€ÄÀ¸ÜÄØ€¡ÑÉÕ”¸ôÄ¤½È€ÄÀ¸àÄÄ€¡ÑÉÕ”¸ôĞ¤Ñ½Ñ…°™±Õà¥¹Ñ¼„ÍÕ‰Á¥á•°¡½ÍĞ)İ¥Ñ ¸ôÀ¸Ô…¹I”…‰½ÕĞ€À¸äÔÁ¥á•°¸%¸Ñ¡”É•Ù•ÉÍ”‘¥É•Ñ¥½¸Ñ¡”Í•±•Ñ•)¡½ÍÑÌ…±Í¼É•…¡•¸ôÀ¸Ô°İ¥Ñ ¡½ÍĞ™±Õà…‰½ÕĞ€À¸ääÈ…¹€À¸ØÜÌ…¹I”…‰½ÕĞ(È¸àà…¹€Ì¸ØĞÁ¥á•±Ì¸¥Ğ½µÁ±•Ñ¥½¸…¹±½İ•ÈMM‘¼¹½Ğµ…­”…¹ä½˜Ñ¡•Í”)‰½Õ¹‘…ÉäÍ½±ÕÑ¥½¹ÌÁ¡åÍ¥…°É•½Ù•Éä¸M¥¹••µÁ¥É¥…°İ¥¹ÌÉ•µ…¥¸)¹½¸µÁ¡½Ñ½¸µÉ•…‘ä¸()Q¡¥Ì±½Í•ÌÑ¡”½¹ÑÉ½±±•¹½¥Í•±•ÍÌi¡Õ…¹œ´µM¡•¸Í½Á”…Ì„‘½Õµ•¹Ñ•)™…¥±ÕÉ”½¹‘¥Ñ¥½¸¸‘‘¥¹œÑ…É•Ğ¹½¥Í”İ½Õ±½¹™½Õ¹„µ¥Íµ…Ñ Á…Ñ¡½±½ä)…±É•…‘äÁÉ•Í•¹Ğİ¥Ñ¡½ÕĞ¹½¥Í”°Í¼¥Ğ¥Ì¹½ĞÑ¡”¹•áĞ•áÁ•É¥µ•¹Ğ¸½±±½İ¥¹œ)Ñ¡”±¥Ñ•É…ÑÕÉ”½Í½™Ñİ…É”µ™¥ÉÍĞÉ•Ù¥•Ü°Ù„¥¹ÍÑ•…™É••é•ÌÍÑÉ½A¡½Ğ€À¸Äà¸À(¡Ñ…œ½µµ¥ĞˆÈÁŒäáˆÑ…‰„ÑˆäÜÀàäÌàØÄÁ”ØÅ…•ØÁ˜ÈÀÔØÈÁ€¤…ÌÑ¡”µ…¥¹Ñ…¥¹•°)½Á•¸µÍ½ÕÉ”É½ÍÌµ™¥ÑÑ•È…¹‘¥‘…Ñ”ÕÍ•‰ä•İÍ¹…À•Ğ…°¸1%P°Aå%µ™¥Ğ…¹)A•ÑÉ½¥Ğİ•É”½¹Í¥‘•É•‰ÕĞ‘¼¹½Ğ½™™•ÈÑ¡”Í…µ”½µ‰¥¹…Ñ¥½¸½˜¥¹‘•Á•¹‘•¹Ğ)•¹¥¹”°Í½ÕÉ”¥¹ÍÁ•Ñ…‰¥±¥Ñä…¹‘¥É•Ğ•İÍ¹…ÀÁÉ½Ù•¹…¹”¸Ù„™¥ÉÍĞ¡•­Ì)¥¹ÍÑ…±±…Ñ¥½¸°Í¥¹•µÍ…µÁ±”ÁÉ•Í•ÉÙ…Ñ¥½¸…¹Ñ¡”ØÀ¸Äà…á¥Ì½¹Ù•¹Ñ¥½¸ì¥Ğ¥Ì)¹½Ğå•Ğ„™¥ÑÑ¥¹œ½ÈÉ•½Ù•Éä±…¥´¸M•”‰•¹¡µ…É­Ì½‘•İÍ¹…Á|ÈÀÈÔ½Ù}AI=Q==0¹µ‘€¸