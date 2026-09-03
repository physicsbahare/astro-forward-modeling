# C5 — Zhuang & Shen PSF-mismatch verification

Status: IN PROGRESS. C5a width-only experiment frozen 2026-09-03 UTC.

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
