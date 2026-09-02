# Gate C4 — AGN nuclear-fraction morphology contamination benchmark

**Status: IN PROGRESS — Stage 3b profile CI reviewed; Stage 3c paired source-shot-noise pilot frozen below.**

Primary anchor: Zhuang & Shen (2024), *Characterization of JWST NIRCam PSFs and Implications for AGN+Host Image Decomposition*, ApJ 962, 139, arXiv:2304.13776.

## Purpose

This gate isolates one question before any PSF-mismatch experiment: how strongly does an unresolved central source contaminate recovered host morphology as the AGN fraction increases, even when the PSF is perfectly known?

It is deliberately separate from the later Zhuang & Shen PSF-mismatch gate. Noise is also deferred until after the noiseless perfect-PSF diagnostic is understood.

## Frozen literature anchors

Zhuang & Shen generate mock AGN+host systems over a broad grid including AGN-to-host flux ratios from `0.1` to `10` in `0.2 dex` steps, host effective radii from `4` to `64` pixels in `0.3 dex` steps, Sérsic indices `0.5, 1, 1.5, 2, 3, 4, 6`, axis ratios `0.3, 0.6, 0.9`, and a fixed position angle of `45 deg`.

Their diagnostic figures repeatedly show the representative AGN-to-host ratios `0.1`, `1`, and `10`. Stage 1 therefore freezes exactly those three ratios rather than choosing new values after seeing benchmark behavior. They correspond to nuclear fractions `F_AGN/(F_AGN+F_host)` of `1/11`, `1/2`, and `10/11`.

For the first controlled sweep, the host scenes are also predeclared as a subset of the published grid:

- `Re = 16 pix`;
- Sérsic `n = 1` and `n = 4`;
- `q = 0.6`;
- PA `=45 deg`.

These values are diagnostic anchors, not production cuts.

## Planned Stage 1 — perfect-PSF, noiseless isolation

For each host scene and each of the three frozen AGN-to-host ratios, generate the same AGN+host image with a central unresolved source and a perfectly known PSF. Measure it two ways:

1. host-only single-Sérsic fit, which intentionally ignores the nuclear component and exposes morphology contamination;
2. explicit Sérsic+PSF decomposition using the same PSF that generated the image.

Record host flux, nuclear flux, host `Re`, host `n`, host `q`, convergence, and every parameter-bound hit. Do not widen a bound or introduce an acceptance band in response to the result.

The scientific comparison is the *difference between the two measurement models as nuclear fraction increases*. A successful explicit same-model decomposition is expected to be a numerical reference, not proof that real AGN-host decomposition is uniquely identifiable.

## Deferred effects

- target noise: separate later stage;
- PSF mismatch: separate Zhuang & Shen gate;
- cross-fitter/model non-uniqueness: Dewsnap et al. gate;
- sparse point-source/smooth-host alternative decomposition: Kawase et al. gate.

Keeping these effects separate is required so that a failure can be attributed to nuclear contamination, information loss, PSF mismatch, or model/fitter ambiguity rather than an uncontrolled mixture.

## Review decision

**IN PROGRESS.** Stage 1 establishes same-renderer recovery and host-only contamination, not quadrature convergence or gate closure. See the dated review below.

## Stage-1 implementation (2026-09-02)

Stage-0 run `33632426495` is explicitly `completed/success`. Its anchor JSON
was inspected in the job log (the same payload written to the artifact).

The separate `gate-c-agn-nuclear-fraction-noiseless` workflow implements the
planned six images and two measurement models per image. Historical anchor
outputs remain unchanged. Choices below are fixed before the first execution:

- Circular Gaussian PSF, FWHM=3 detector pixels, no noise. This is a controlled
  PSF choice, **not** a measured NIRCam PSF or literal survey reproduction.
- 129-square detector stamp, 4x detector-centered subpixel integration.
  Host convolution occurs on the fine grid, with padding for the full
  six-sigma Gaussian support before cropping. The point source uses the exact
  detector integral of the same continuous Gaussian. Sérsic amplitudes denote
  analytic infinite-plane total flux; finite-stamp flux is separately recorded
  and is never renormalized. Identical host rendering in truth and fitting
  isolates model mismatch but cannot validate quadrature convergence.
- Host center and PA are fixed to truth; background is exactly zero. This
  intentionally limited reference does not test free-center degeneracies.
- Re bounds [0.5,60] pixels, n [0.5,6], q [0.15,1], following the Yu diagnostic.
  Three common starts n=1,2.5,5 with Re=12 and q=0.75; no truth-dependent start.
- TRF least squares profiles the one or two nonnegative flux amplitudes using
  NNLS. No upper flux bound. Max 160 function evaluations; ftol/xtol=1e-10,
  gtol=1e-7. Winner is minimum residual cost, even if unsuccessful; every start
  and boundary flag is retained. No recovery acceptance interval is introduced.
- Outputs: config, metrics, all starts, summary, and truth/fitted image NPZs,
  plus software/commit provenance. The workflow only validates finite matrix
  completion, not closeness to truth or literature. Optimizer non-convergence
  remains in the output rather than being suppressed.

Only one push-triggered two-shard run is added (no duplicate PR trigger for
this diagnostic). The next decision is to review decomposition recovery,
residuals, and host-only contamination as nuclear fraction rises. A successful
CI run alone will not close this gate or justify skipping noise/PSF mismatch.

## Stage-1 CI review and Stage-2a freeze (2026-09-02)

GitHub explicitly confirmed run `33642676932` completed/success at commit
`a059cd4a3475ac1b36a84e60f750fa733e39dd7b`. Both jobs succeeded:
`100289447991` (n=1) and `100289447884` (n=4). Downloaded and inspected
artifacts `9852668703` and `9852845589`: configs, commit provenance, metrics,
all 36 starts, summaries and all six NPZ truth/prediction products. Historical
run `33642495377` also succeeded, but this review uses the replacement run.

All 36 starts report optimizer success. All 18 decomposition starts recover
the input parameters (largest observed absolute n error about 3.75e-7).
All six decomposition winners have no bound hits; fractional L1 image
residuals range from 4.11e-16 to 6.96e-12. All six host-only winners hit
bounds: both ratio=0.1 cases reach n=6; all ratio=1 and 10 cases reach
Re=0.5. Host-only fractional L1 residuals span 0.0924–0.4803. The smaller
relative residual at high nuclear fraction does not imply accurate morphology.
NPZ arrays are finite, truth components sum to data to floating-point accuracy,
and recalculated image residuals agree with metrics. No acceptance bands changed.

Decision: test sampling before target noise. A common 4x renderer can cancel
its own quadrature errors; the exact integrated point source does not share
the host's approximate pixel integration. Stage 2a freezes factors 4, 8, 16,
both existing n values and all three ratios, with every other scene/PSF setting
unchanged. Compare 4→8, 8→16 and 4→16; higher sampling is a reference, not
proven truth. Record host image L1 differences and finite-stamp flux, plus
nonnegative host/nuclear flux bias when the lower-sampled host template fits
the higher-sampled image with structural parameters fixed. Record normalized
two-template condition numbers, explicitly not full nonlinear identifiability.
Save config before computation, all nine rows per host and image arrays.
CI checks finite matrix completion only; no new scientific pass band.

Next decision after CI artifact review: determine whether remaining sampling
drift requires finer/independent rendering and nonlinear cross-sampling fits
before adding noise. No target-noise or PSF-mismatch stage is authorized by
same-renderer recovery alone. The Stage-2a push-triggered workflow is
`gate-c-agn-sampling`; resolve its run by the implementation commit and do
not launch a duplicate. Stage-1 files/results are preserved unchanged.

Implementation checks: nine targeted pytest tests passed locally; both local
Stage-2a matrices completed (18 rows). These are not CI results. Parameters
above were frozen before those executions. No scientific acceptance decision
is made from the local smoke runs.

## Stage-2a CI review and Stage-2b freeze (2026-09-02 UTC)

Run `33650581586`, commit `bb95563d95f5123c6d27eb988be055e362ac8799`,
explicitly completed/success, with jobs `100316256577` and `100316256985`.
Downloaded artifacts `9854597447` (n=1) and `9854598606` (n=4). Inspected
all 18 metric rows, matching summary/config JSON, commit provenance and all
26 image arrays. Recomputed residuals agree with the CSV; arrays are finite.
This stage has analytic NNLS flux solutions, not nonlinear starts.

Host fractional L1 changes for 4→8 and 8→16 are respectively 3.40e-5 and
8.53e-6 (n=1), and 5.27e-4 and 1.54e-4 (n=4). Thus refinement reduces
differences, but does not establish convergence to an independent reference.
For n=4 the 4→16 difference is 6.81e-4. Fixed-shape fitting with the 4x
template shifts host flux by +3.10e-4 and nuclear flux by +4.76e-4 in units
of the unit true host flux; at AGN/host=0.1 the latter is about 0.476% of
the true nucleus. These are observed numbers, not acceptance thresholds.
Normalized two-template condition numbers are about 1.48 (n=1) and 2.83
(n=4); these do not describe nonlinear structural or free-centroid degeneracy.

Decision: quantify nonlinear propagation before deciding a rendering setting
for the noise experiment. Stage 2b freezes the same six noiseless scenes,
reference factor=16, fitting factors=4 and 8, and decomposition only. Free
Re, n, q and NNLS fluxes; keep center/PA/background fixed. Reuse Stage-1
bounds, three starts, optimizer settings, max_nfev=160 and minimum-cost winner
without changes. Four CI shards (host n × fitting factor), 12 fits and 36
starts total. Save every start, boundary flag, config, reference/prediction/
residual image and source-commit/software provenance. CI checks completion
and finite costs, not recovery. No noise or PSF mismatch is introduced.

The higher-sampled reference is still not independently validated. Following
Stage-2b CI artifact review, use structural drift and start agreement to choose
the next independent-renderer comparison; do not declare 16x converged or
skip that comparison based solely on these fits. New workflow:
`gate-c-agn-cross-sampling`, resolved by its implementation commit. Preserve
both earlier stages; do not rerun or overwrite their historical records.

Local implementation checks: ten targeted tests passed. The n=4/factor=4
smoke shard completed three fits and nine starts; image residuals, data hashes
and output completeness were checked. This is local execution only, not
Stage-2b Actions success or a new scientific acceptance decision.

## Stage-2b CI review and Stage-2c freeze (2026-09-02 UTC)

Run `33656800320` explicitly completed/success at commit
`69985d03a886ba2d2941369196e770548a49118b`. All four jobs succeeded:
`100337252653`, `100337252888`, `100337252905`, `100337253078`.
Downloaded artifacts `9857050645`, `9857052938`, `9857074318`, `9857074576`.
Reviewed all 12 winners and 36 starts, checked CSV against summary/config JSON,
commit provenance and image hashes, and verified all 12 reference/prediction/
residual bundles are finite and reproduce the reported residuals.

All starts succeeded without bounds. For n=4, moving the fitting quadrature
from 4x to 8x reduces Re bias from approximately -0.05844% to -0.01100%,
delta_n from +0.001363 to +0.0003402, and delta_q from +0.0003117 to
+0.00006160. At ratio=0.1, nuclear flux bias decreases from +0.4160% to
+0.09687% of true nuclear flux. For n=1, delta_n decreases in magnitude
from -9.30e-5 to -1.86e-5. Maximum within-scene/start spread in fitted n
is approximately 3.73e-7. These are diagnostic observations, not acceptance
thresholds. No low-noise/global/free-center identifiability claim follows.

Decision: compare against a genuinely independent implementation now, rather
than infer truth from continued refinement of the same renderer. Stage 2c
pins GalSim 2.8.4 (already used by Gate B) and freezes two FFT settings:
coarse/fine folding_threshold=1e-4/1e-5, maxk_threshold=1e-5/1e-6,
kvalue_accuracy=xvalue_accuracy=1e-7/1e-8. All other GSParams retain the
pinned version defaults. No truncation or finite-stamp renormalization.
GalSim's area-preserving shear requires circular HLR=16*sqrt(0.6) to match
semi-major Re=16, with q=0.6 and beta=45 degrees. Use float64, 129-square,
scale=1, centered drawImage(method='fft') for a single pixel integration.

Compare both GalSim host images and local 4/8/16x host images; separately
compare the GalSim Gaussian point image to the analytic detector integral.
Keep the analytic point template in generated AGN scenes and fitting so this
isolates host-rendering differences, not an introduced PSF mismatch. Fit the
fine-GalSim host plus each of the original three nuclear ratios using the 8x
local fitter, with all Stage-1 bounds/starts/budget unchanged. Two host shards,
six fits and 18 starts. Save renderer metrics/images, all fit starts, config,
predictions/residuals and provenance. Neither GalSim nor its fine setting is
declared exact truth. CI checks finite completion; new profile/PSF algebra
tests check conventions, not morphology recovery. Their numerical criteria
are fixed in tests before first execution and must not be relaxed to pass.

Sources checked before implementation:
https://galsim-developers.github.io/GalSim/_build/html/gal.html and
https://galsim-developers.github.io/GalSim/_build/html/gsobject.html
(Sersic radius semantics, area-preserving shear, and FFT pixel integration).
Next: review GalSim refinement against cross-code differences, structural
bias and all starts before choosing whether a noise experiment is justified
or more numerical validation is required. This does not close the separate
PyAutoGalaxy, Dewsnap or other roadmap gates. Workflow: `gate-c-agn-galsim`;
resolve the run by its implementation commit without duplicate dispatches.

Local implementation validation: all 12 targeted tests passed with GalSim
2.8.4 installed, including independent profile normalization/ellipse checks
and the Gaussian pixel-integral check. The full n=4 smoke shard completed
three fits/nine starts, with output hashes and residual images checked.
These local checks are not Stage-2c CI success. The optional GalSim test module
skips only when GalSim is absent from the base suite; the dedicated workflow
installs the exact pin and the experiment itself requires and checks it.

## Stage-2c CI review and Stage-3a freeze (2026-09-02 UTC)

Run `33661985266` explicitly completed/success at commit
`94fc982e17b248b0227230554d6b47c5e1d40de8`, jobs `100354463534` and
`100354463644`. Downloaded artifacts `9859083212` (n=4), `9859077660`
(n=1). Reviewed six winners, all 18 starts, ten renderer metric rows,
config/summary JSON, provenance, both renderer image bundles and all six
fit image bundles. CSV/JSON values agree; arrays are finite; reference sums,
data hashes and recalculated residual metrics agree. All starts succeeded
without bounds; largest within-case n spread is approximately 3.73e-7.

GalSim coarse→fine host L1 drift is 5.84e-10 (n=1), 1.23e-7 (n=4),
well below local-8x versus fine-GalSim differences of 1.14e-5 and 2.11e-4.
Local-16x differences fall to 2.85e-6 and 5.77e-5 respectively. This is
independent evidence of decreasing discretization error for these scenes,
not a universal convergence tolerance. With 8x fitting, n=4 Re bias is
-0.01458%, delta_n=+0.0004627, delta_q=+0.00008205; at ratio=0.1 nuclear
flux bias is +0.1345%. The analytic Gaussian nucleus is common to truth and
fit; the GalSim point comparison was separate (fine L1 error 7.01e-7).
No physical PSF mismatch was introduced. Historical numerical floors remain.

Decision: proceed to a limited background-noise pilot, not close this gate.
Independent rendering now provides a measured noiseless baseline against
which noise-induced structural variation can be compared. Freeze host-only
known-template SNRs 100, 20 and 5: pixel sigma = ||unit GalSim host||_2/SNR.
This SNR is not marginalized over the nucleus/structure and is not aperture
SNR. Use spatially constant, zero-mean independent Gaussian background noise,
three seeds 20260903/20260904/20260905, PCG64 with SeedSequence([seed,n]).
Share each unit noise realization across the three ratios and SNRs for paired
comparisons; these paired cases are not independent ensemble replicates.
No Poisson/source-shot noise, resampling covariance, centroid freedom, PA
freedom, fitted sky or PSF mismatch. Each is a distinct later question.

Keep the same GalSim 2.8.4 fine host and analytic nuclear reference, 8x
decomposition fitter, all six scenes, three starts, bounds, termination
tolerances, max_nfev=160 and minimum-cost winner. Six host×SNR shards,
max two concurrent, 54 fits/162 starts total. Persist every start, convergence
and boundary flag, noise/data hashes, pixel sigma, chi-square, noiseless-model
discrepancy and all reference/noise/prediction/residual arrays. Also record
the host-renderer L2 discrepancy divided by sigma to compare numerical and
noise scales. CI checks finite completion, never closeness to truth. Three
realizations per case are a pilot, not calibrated uncertainties or reliable
failure rates. Config is written before generation/fitting; no recovery bands.

Next: inspect all noise outputs against the Stage-2c noiseless baseline. Ask
whether structural scatter/bounds/start disagreement are dominated by lost
information, and whether a larger predeclared ensemble or separate source-shot
noise/free-center experiment is needed. Do not interpret successful execution
as scientific acceptance or quietly discard low-SNR outcomes. Workflow:
`gate-c-agn-noise-pilot`; resolve run by implementation commit, no duplicate
dispatch. Stage-2c and earlier records remain unchanged.

Implementation checks: fourteen targeted tests passed locally with the pinned
GalSim installed. The first three low-SNR smoke fits (n=1, SNR=5, seed
20260903) completed; noise hashes, additive-noise construction, residuals and
chi-square were checked from the saved arrays. A nuclear-flux zero-bound hit
was retained. These are local checks only, not Stage-3a Actions results.

## Stage-3a CI review and Stage-3b freeze (2026-09-02 UTC)

Run `33668364723` explicitly completed/success, commit
`46c7af879cb0c27432c2a34352b37dcada9d1be3`. All six jobs succeeded:
`100375560131`, `100375560432`, `100375560450`, `100375560565`,
`100375560623`, `100375560664`. Downloaded and reviewed all six artifacts:
`9861533515`, `9861542096`, `9861952745`, `9862155519`, `9862258463`,
`9862653168`. All 54 winners/162 starts and 54 image bundles inspected;
CSV/summary/config consistency, source commit, image/noise hashes, finite
arrays, additive noise, residuals and chi-square reconstruction verified.

All 162 starts report success, but 16/54 winners hit at least one bound:
none at SNR=100; three at SNR=20 (n=4); thirteen at SNR=5 (seven n=1,
six n=4). These counts are paired pilot outcomes, NOT independent failure
probabilities. At n=4, Re/true Re spans 0.823–1.119 at SNR=100 and
0.489–1.277 at SNR=20; at SNR=5 it reaches 0.254. Maximum within-case
n start spread is approximately 0.00624. Numerical host discrepancy divided
by sigma is at most 0.0979 (n=4,SNR=100), falling with SNR, supporting
noise/information loss rather than the measured rendering floor as the
dominant effect; this alone does not prove a global optimum was found.

With a shared exact point template, constant variance and paired additive
noise, increasing true nuclear flux simply translates the fitted nuclear
amplitude when its nonnegativity boundary is inactive. Thus near-identical
structural estimates across ratios here are expected, not evidence that
nuclear brightness never matters. Shot noise/PSF mismatch break this setup.

Decision: inspect the likelihood shape before enlarging the noise ensemble
or introducing another physical effect. Stage 3b uses the ACTUAL archived
Stage-3a images, not regenerated noise and not reruns of its unrestricted
fits. Select all n=4, ratio=1 cases (all three SNRs and all three seeds),
representing an interior-amplitude comparison without choosing only extreme
outcomes. Freeze n-grid [0.5,1,2,3,4,5,6]. At each fixed n optimize Re,q
and NNLS fluxes, with three Re starts [4,12,36], q start=0.75. Keep Re/q
bounds and all optimizer tolerances/max_nfev=160 unchanged. The new starts
probe nuisance optima; they do not overwrite original fits or enlarge bounds.
Fixed grid endpoints are not counted as optimized n-bound hits.

Three SNR shards, at most two concurrently; 63 grid winners and 189 starts.
Download source artifacts by run ID, verify commit and exact data hashes,
retain original winner/chi-square in source_record.json, and save all grid
starts and prediction/residual arrays. Report RAW delta chi-square relative
to the archived unrestricted winner, including negative values. A lower
grid cost would motivate an optimizer diagnosis, not silent replacement.
Do not attach confidence levels or asymptotic acceptance bands to this coarse
grid, especially with boundaries and three noise realizations. CI validates
complete finite output only. Next: decide whether profiles support weak
constraints versus missed minima before selecting further noise/PSF work.
Workflow `gate-c-agn-n-profile`; resolve by implementation commit, no duplicates.

Implementation checks: nine targeted local tests passed. The first five
completed SNR=5 profile-grid cells were checked for saved residual consistency
and raw delta-chi-square bookkeeping against the archived winner. This is a
partial local smoke check, not a completed Stage-3b experiment or CI success.

## Stage-3b CI review and Stage-3c freeze (2026-09-02 UTC)

Run `33674620167` explicitly completed/success at commit
`0869377df252ea81e4506b87d427a27c7e070ac7`; jobs `100396200031`,
`100396200145`, `100396200349` all succeeded. Downloaded artifacts
`9865650468`, `9864063887`, `9864035067`. Reviewed all 63 grid winners,
189 starts and 63 image bundles. CSV agrees with summary, configs agree,
commit/data hashes match, arrays are finite, and reconstructed residual sums
agree for both new and original predictions. No start failures; seven
SNR=5 winners hit nuisance bounds (fixed n endpoints are not counted).

At SNR=5 the full n-grid chi-square spans are approximately 0.958, 0.983
and 1.681 for seeds 20260903/4/5. At SNR=100 the spans are approximately
401, 380 and 309. This strongly supports weak constraints at low SNR, not
an assertion that every global optimum was proved. The lowest signed delta
against the archived winner is approximately -2.5e-7 (SNR=5, seed20260903,
n=6); it is retained as numerical optimizer disagreement. Maximum within-node
start chi-square spread is 1.64e-6. No confidence level is inferred from
these coarse grids, and no post-hoc tolerance is used to certify minima.

Decision: introduce source shot noise as a separate paired experiment, while
keeping perfect PSF and fixed center/PA/sky. Stage 3c selects n=4, all original
ratios 0.1/1/10, all SNR=100/20/5 shards and all three original seeds.
Use actual archived Stage-3a truth/background images, checking commit and data
hashes. Set analytic total host count to 10,000 electrons (a controlled scale,
not a survey exposure), with nuclear total 10,000 times the ratio. Draw Poisson
counts per pixel from 10,000 times the noiseless host+nucleus; divide by
10,000 and subtract the noiseless image to obtain zero-mean source noise.
Do not renormalize the stamp or clip negative intensities; invalid intensities
must fail explicitly. PCG64 SeedSequence([seed,4,ratio_index,310]), ratio_index
0/1/2. Shot draws are shared across SNR shards, not across ratios; background
is the original paired draw. No double-counted background or resampling.

Two arms per scene: archived background-only image and that same image plus
source noise. BOTH use identical fixed oracle variance sigma_bg^2 + I_true/10000.
Whiten data and both model templates and reuse the unchanged TRF/NNLS fitter,
three starts, bounds, max_nfev=160 and tolerances. This is approximate weighted
least squares, NOT exact Poisson-Gaussian maximum likelihood. Oracle weights
use unavailable true intensity and are not an operational fitting prescription.
For the background-only arm these weights deliberately differ from its actual
variance: that arm is a matched-estimator control, not a calibrated chi-square
test. Thus compare the two new arms to isolate shot noise; do not attribute
differences from the old unweighted pilot solely to the added noise.

Three SNR shards, maximum two concurrent, 54 winners/162 starts total. Retain
all failures/bounds, paired hashes, counts, variance maps, truth/background/
shot/data/prediction/residual arrays and weighted residual sums. Whitened L1
diagnostics are explicitly named. CI checks finite completion only. Three
paired seeds and n=4 are a pilot, not failure probabilities or generality to
n=1. PSF mismatch, free center and practical variance estimation remain open.
Next: inspect paired structural/flux shifts and bounds versus nuclear ratio,
then decide whether practical weights or a broader noise ensemble is required
before the separate PSF-mismatch gate. Workflow `gate-c-agn-shot-noise`,
resolved by implementation commit; do not duplicate an active run.

Implementation checks: nine targeted local tests passed. The first paired
SNR=100, ratio=0.1, seed20260903 fits completed; count/noise construction,
identical oracle weights, source/data hashes, residuals and weighted sums
were verified from saved arrays. This partial local smoke is not Stage-3c
CI success or a new scientific acceptance result.
