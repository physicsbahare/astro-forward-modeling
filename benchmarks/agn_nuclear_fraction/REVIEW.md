# Gate C4 — AGN nuclear-fraction morphology contamination benchmark

**Status: IN PROGRESS — Stage-0 literature/control anchors frozen; no morphology result interpreted yet.**

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

**IN PROGRESS.** Only the Stage-0 anchors are frozen. No Stage-1 morphology result exists yet, so no PASS/FAIL decision is made.

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
