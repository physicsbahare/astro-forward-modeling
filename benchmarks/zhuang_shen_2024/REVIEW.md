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
