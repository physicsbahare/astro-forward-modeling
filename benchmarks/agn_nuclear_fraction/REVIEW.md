# Gate C4 — AGN nuclear-fraction morphology contamination benchmark

**Status: IN PROGRESS — Stage 1 CI artifacts reviewed; Stage 2a sampling diagnostic frozen below.**

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
