# B9b — common-scene morphology recovery with PyAutoGalaxy renderer

Frozen before execution. B9b is a **recovered-parameter diagnostic**, not a production dependency decision and not a survey-reality validation.

## Question

After B9a established the current PyAutoGalaxy eccentric-radius, coordinate, angle and real-space PSF conventions, do an independent analytic Sérsic renderer and the maintained PyAutoGalaxy renderer recover the same structural parameters from the same noiseless scenes when the optimizer, starts, bounds, PSF and objective region are held fixed?

This isolates renderer/parameterization recovery. It deliberately does not test PyAutoFit search strategy, noise calibration, chromatic PSFs, detector effects, or real-survey backgrounds.

## Frozen software

- Python 3.12;
- `autogalaxy==2026.8.14.1`;
- `autoarray==2026.8.14.1`;
- SciPy version recorded in the artifact;
- `scipy.optimize.least_squares` used for both renderers.

## Frozen scenes

Use two independent-reference truth scenes on an 81 x 81 grid, pixel scale 1:

- `n=1`, `q=0.6`, angle 37 deg;
- `n=4`, `q=0.6`, angle 37 deg.

Both have centre `(y,x)=(0.35,-0.25)`, effective radius 8 and intensity at `Re=0.03`. The same normalized 9 x 9 Gaussian PSF with sigma 1.2 pixels used in B9a is applied.

Truth images are generated only by the independent analytic renderer with the documented PyAutoGalaxy eccentric radius

`r_ecc = sqrt(q) * sqrt(x_major^2 + y_minor^2/q^2)`

and zero-filled SciPy convolution.

## Objective region and edge semantics

B9a showed that the central convolved image agrees closely while the largest `n=4` discrepancy is associated with the image boundary because PyAutoGalaxy evaluates light outside the output image before convolution whereas `convolve2d(..., mode="same", boundary="fill")` uses zero-filled boundaries.

Therefore the optimization objective is frozen to the central crop excluding the four-pixel PSF radius. Full-frame residuals and sums are still saved. This is a predeclared removal of a known operator-boundary confounder, not a post-result tolerance change.

## Free parameters

Angle is fixed at 37 deg so B9b measures the requested structural quantities without adding a periodic-angle degeneracy. Free parameters are:

- centre y and x: `[-1.5, 1.5]` pixels;
- axis ratio q: `[0.25, 0.95]`;
- Sérsic index n: `[0.5, 6.0]`;
- effective radius Re: `[2.0, 20.0]` pixels;
- intensity at Re: `[0.003, 0.2]`.

Bounds are identical for both renderers and will not be widened after execution.

Three deterministic starts are frozen before results:

1. balanced: `(0,0,q=0.70,n=2.0,Re=7,Ie=0.025)`;
2. compact: `(0.60,-0.60,q=0.45,n=0.8,Re=4,Ie=0.060)`;
3. extended: `(-0.50,0.50,q=0.85,n=4.5,Re=13,Ie=0.012)`.

SciPy least-squares uses `max_nfev=120`, `ftol=xtol=gtol=1e-9`. These are optimizer controls, not morphology acceptance thresholds.

## Recorded diagnostics

For every renderer, scene and start record termination status/message, evaluations, initial and final interior SSE, full-frame SSE, fitted centre/q/n/Re/Ie, bound proximity and derived analytic total flux. Winner is minimum finite interior SSE, regardless of the optimizer's success flag.

Save data, PSF, and winner model/residual arrays. Compare each renderer's winner against truth and compare PyAutoGalaxy versus independent winners directly.

## Decision rule

There is no post-hoc recovery band. Workflow success means the frozen experiment and read-only audit completed with finite, internally consistent outputs. Convergence failures, boundary solutions, start dependence and renderer disagreement are scientific observables.

If B9b is complete and interpretable, the PyAutoGalaxy/PyAutoArray Gate-B morphology extension can be closed with a written explanation of any residual renderer differences. If not, diagnose the specific convention/numerical issue before any production implementation or acceptance freeze.
