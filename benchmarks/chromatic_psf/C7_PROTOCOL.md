# C7 protocol — source-SED / chromatic-PSF mismatch

Frozen before C7 results. This is an operator-level stress test, not a reproduction of a particular paper and not a production PSF implementation.

## Question

For a spatially resolved source with a color gradient, what changes if the physically correct wavelength-resolved image

`sum_k integral dλ w_k(λ) [M_k * P(λ)]`

is replaced by a band-integrated intrinsic image convolved once with a single broadband PSF built from the **global** source SED?

The distinction matters because STPSF explicitly models filter response together with point-source spectra, and its documentation recommends synphot/stsynphot for proper spectral response. Existing Gate A/B checks established chromatic non-commutativity and cross-code correctness; C7 now quantifies the practical morphology bias of the source-independent-PSF shortcut for a color-gradient scene.

## Frozen scene

- wavelength grid: 1–5 µm, 401 trapezoidal samples;
- smooth synthetic throughput, identical to the established analytic chromatic verification scene;
- photon weighting proportional to `F_lambda * throughput * lambda`;
- wavelength-dependent circular Gaussian PSF with `sigma_psf = 0.72 * lambda_um` pixels;
- extended blue component: Gaussian spatial sigma 7 px, SED proportional to `lambda^-1.8`;
- compact red component: Gaussian spatial sigma 1.7 px, SED proportional to `0.75 * lambda^1.25`;
- image shape 161×161, centered components, zero noise/background.

The **correct** image integrates each spatial component through the wavelength-dependent PSF before summing. The **shortcut** first integrates the intrinsic source over wavelength, constructs one broadband PSF from the summed/global SED as the actual weighted mixture of monochromatic PSFs, then convolves once. This deliberately avoids replacing the broadband PSF by a Gaussian moment approximation.

## Controls

Two controls are mandatory and are part of the result, not optional tolerances:

1. **same-SED control:** both spatial components use the same spectral shape. Then one global broadband PSF is mathematically valid and the two operators should agree to numerical precision.
2. **achromatic-PSF control:** retain the color gradient but hold the PSF fixed with wavelength. Then source SED cannot change the PSF and the operators should again agree to numerical precision.

If either control fails materially, diagnose the implementation before interpreting the color-gradient result.

## Diagnostics

Record total-flux difference, normalized image L1 difference, second-moment size difference, central enclosed-flux fractions at radii 3 and 10 px, the effective second-moment PSF widths for each component/global SED, and all source/model arrays. No morphology-recovery acceptance band is defined. The scientific output is the measured bias and its disappearance in the two controls.

This test must not introduce Tolman factors, redshift factors, noise, fitting, deconvolution, or production code.
