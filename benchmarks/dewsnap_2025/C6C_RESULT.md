# C6c result receipt — AstroPhot crossed empirical-PSF diagnostic

**Workflow run:** `33899519613`  
**Conclusion:** `completed / success`  
**Artifact:** `dewsnap-astrophot-psf-mismatch-c6c`, id `9947142920`, digest `sha256:99dee3561c1ba79a4cdd2eec5b8abdd47ca8c1db11eaf6e166931fe5f29a13f0`

This workflow success means the frozen crossed-PSF diagnostic completed and its artifact passed the read-only audit. It is **not** a morphology-recovery success.

## Frozen scope

- clean C5o `n=1`, AGN/host = 10 scenes only;
- A-data fitted with B-PSF and B-data fitted with A-PSF;
- AstroPhot `0.18.0`, PyTorch `2.14.0+cpu`;
- three predeclared starts per direction, six attempts total;
- no noise, no background, no clipping of signed PSF samples;
- unchanged shape bounds `0.5 <= n <= 6`, `0.5 <= Re <= 60`, `0.15 <= q <= 1`;
- unchanged point-flux bound `0 <= flux <= 1e6`;
- winner = minimum finite recomputed pixel SSE, regardless of optimizer message;
- no post-hoc recovery band.

## Results

All six attempts were finite. Two winners were selected.

### Truth A / fit PSF B

- AstroPhot winner start: `compact`
- optimizer message: `fail. Maximum iterations`
- `n = 6.0` — upper-bound hit
- `Re = 8.823596561560102`
- `q = 0.6828313493320098`
- point flux `8.481814705347524`
- SSE `0.02024922516490358`
- residual L1 / data L1 `0.37812394756956463`

Archived Imfit C5r winner for the same direction had `n=0.5`, `Re=0.955328`, `q=0.625221`, point flux `0`, SSE `0.009967161338144924`, with both `n` and point flux on bounds. AstroPhot/Imfit SSE ratio is `2.0315939993274297`.

### Truth B / fit PSF A

- AstroPhot winner start: `compact`
- optimizer message: `fail. Maximum iterations`
- `n = 0.5` — lower-bound hit
- `Re = 1.8264383665230906`
- `q = 0.26510273263127326`
- point flux `8.539475576272237`
- SSE `0.021444904921709085`
- residual L1 / data L1 `0.34155686758717896`

Archived Imfit C5r winner had `n=0.5`, `Re=2.88493`, `q=0.386991`, point flux `9.25014`, SSE `0.021938287641884054`, with `n` on its bound. AstroPhot/Imfit SSE ratio is `0.9775104270566216`.

## Scientific decision

Crossed empirical PSFs destroy clean morphology recovery in both independent fitters, but the failure mode is fitter- and direction-dependent. One direction sends AstroPhot to the opposite Sérsic-index boundary from Imfit, while the other direction agrees on the lower boundary but not on recovered size/axis ratio. Both AstroPhot winners exhausted the predeclared LM iteration budget and both hit an `n` bound.

Therefore C6 closes as evidence that PSF-construction mismatch and fitter/renderer behavior interact. Noise must not be added to this already non-identifiable condition. The next non-redundant verification target is the pinned PyAutoGalaxy/PyAutoArray morphology cross-code extension, beginning with an explicit renderer/geometry/convolution convention preflight before any recovered-parameter comparison.
