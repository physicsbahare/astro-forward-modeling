# B9a — PyAutoGalaxy/PyAutoArray morphology convention preflight

Frozen before execution. This is the first half of the remaining Gate-B morphology extension. It is a **renderer / geometry / PSF-convolution convention diagnostic**, not yet a recovered-parameter benchmark and not a production dependency decision.

## Why this preflight exists

PyAutoGalaxy's current Sérsic implementation evaluates its light profile using an `eccentric_radii_grid_from` geometry, with the radius scaled by `sqrt(q)`, and its public coordinate convention is `(y,x)` with angle measured counter-clockwise from +x. A direct comparison against a renderer using the more common unscaled elliptical radius would therefore create a convention difference and falsely label it a numerical failure.

The independent benchmark must first make that geometry explicit, then compare the same analytic scene at pixel centres and after PSF convolution. Only once that is understood should B9b fit common images and compare recovered structural parameters.

## Frozen software

- Python 3.12;
- `autogalaxy==2026.8.14.1`;
- `autoarray==2026.8.14.1`;
- NumPy/SciPy dependency versions recorded by the workflow artifact;
- plain NumPy backend; JAX is not required for this controlled CPU preflight.

The selected release family was current and maintained in August 2026. The exact versions are pinned so later package releases cannot silently change geometry or convolution semantics inside this result.

## Frozen scenes

Use four 101 x 101 pixel-centre scenes with pixel scale 1 arbitrary angular unit:

1. circular `n=1`, `q=1`, angle 0 deg;
2. elliptical `n=1`, `q=0.6`, angle 37 deg;
3. circular `n=4`, `q=1`, angle 0 deg;
4. elliptical `n=4`, `q=0.6`, angle 37 deg.

All have centre `(0,0)`, effective radius 8 and intensity at `Re` = 0.03. PyAutoGalaxy is evaluated with `over_sample_size=1` so this test isolates pixel-centre profile semantics rather than sub-pixel quadrature.

The independent reference computes the same Sérsic law using SciPy's inverse regularized gamma function for `b_n` and the documented PyAutoGalaxy eccentric-radius geometry. It does not call PyAutoGalaxy geometry/profile helpers.

## PSF operator

Use a normalized, symmetric 9 x 9 Gaussian kernel with sigma 1.2 pixels. Build it explicitly as an `Array2D`, then use PyAutoArray `Convolver(..., use_fft=False)` so this preflight tests the maintained real-space path without FFT padding as a confounder. The independent reference uses SciPy `convolve2d` on the same kernel.

PyAutoGalaxy's unmasked convolution pads profile evaluation beyond the output image edge. Therefore convolved-image comparisons are reported both globally and on the central crop that excludes the four-pixel kernel radius. The crop comparison is the convention/operator diagnostic; edge differences remain recorded rather than suppressed.

## Recorded diagnostics

For every scene save the independent and PyAutoGalaxy raw and convolved arrays and record:

- total image sums;
- max absolute and L1-normalized raw-image differences;
- max absolute and L1-normalized convolved differences globally and in the interior crop;
- centroid `(y,x)` for both renderers;
- unweighted second central moments and moment-derived axis ratio/angle;
- exact package versions and configuration.

There is **no post-hoc morphology acceptance band** in B9a. Workflow success means pinned software installed, all declared scenes ran, outputs were finite, the kernel stayed normalized, and the read-only artifact audit reconstructed the stored metrics. Numerical differences are evidence for B9b design, not a reason to alter geometry, sampling or tolerances after the fact.
