# COSMOS-Web Gate D1n-j — causal tangent/orthogonal residual split result

## Immutable execution receipt

- source branch HEAD at execution: `07e4c65f19c132804447b931791077495058f136`
- workflow: `gate-d-cosmosweb-residual-tangent-split`
- workflow run: `34014380482`
- workflow conclusion: `success`
- artifact: `gate-d-cosmosweb-residual-tangent-split`
- artifact id: `9983458786`
- artifact digest: `sha256:d0d8e5aff07746c03c1d3df20e40d5c8f3f5a885478ddc381d99d90141e3b80a`

The workflow conclusion records execution success only. This receipt is derived from the immutable machine-readable `summary.json` in the artifact and records a scientific diagnostic outcome, not a production acceptance criterion.

**Receipt correction:** the first receipt commit (`9aad5d36e461741a2f721b7f63a5661e9146121c`) manually transcribed the five `(168,66)` `chi2` entries incorrectly. The table below corrects only those five fields directly from the immutable artifact. Git history preserves the superseded transcription; no fitted parameter, bound-hit status, execution status, or scientific interpretation changed.

## Frozen semantics

The run retained the exact D1m scene decomposition, target renderer, STPSF, ERR weighting, exact child mask, target bounds, `scipy.optimize.least_squares` TRF optimizer, linear loss, `x_scale=jac`, `max_nfev=500`, and the D1n-i finite-difference steps. The planar-background subspace was removed before the split. No regularization, Jacobian-column removal, added noise, source-shot noise, ERR/WHT modification, Tolman factor, PSF sharpening, altered bounds, or post-hoc acceptance threshold was used. Optimizer failures and target-bound hits were retained.

All 20 fits were finite and reported optimizer success. One target-bound hit occurred: the catastrophic near-source case at `(168,66)` in `orthogonal_only`, where the recovered Sérsic index reached the lower bound `n=0.3000000000000209`. This bound solution is part of the result.

## Split identities and local tangent power

The numerical split identities were satisfied to machine precision. Across the four positions, `max|tangent + orthogonal - background_residualized_full|` was `2.22e-16`–`4.44e-16`; the largest absolute residualized-Jacobian/orthogonal inner product was `2.16e-13`; and `original_full` reconstructed the literal D1d injected valid pixels to `<=6.94e-18` in image units.

| role | class / position | tangent power fraction | tangent condition number | tangent power | orthogonal power |
|---|---|---:|---:|---:|---:|
| catastrophic | near-source `(168,66)` | 0.0194647621 | 296.2623 | 94.0503 | 4737.7743 |
| catastrophic | isolated `(69,195)` | 0.0176640432 | 291.6142 | 52.0950 | 2897.1165 |
| control | near-source `(379,254)` | 0.00780169387 | 290.2817 | 21.3438 | 2714.4465 |
| control | isolated `(358,97)` | 0.00326204029 | 289.6915 | 9.38951 | 2869.0280 |

The catastrophic locations therefore retain the D1n-i distinction: only about 1.77–1.95% of background-residualized weighted residual power is locally target-tangent, but this fraction is about 2.5–5.4 times that of the matched controls. Conditioning remains similar across all four positions.

## Machine-readable recovery outcomes

Truth is `Re=0.18 arcsec`, `n=1`. `delta_mag` is recovered minus injected magnitude.

| role / position | mode | delta_mag | Re [arcsec] | n | centroid excursion [pix] | chi2 | target bound hit | optimizer success |
|---|---|---:|---:|---:|---:|---:|---|---|
| catastrophic `(168,66)` | none | 2.21e-09 | 0.1800000 | 1.0000000 | 1.51e-08 | 1.20884e-10 | no | yes |
| catastrophic `(168,66)` | tangent_only | -0.604426 | 0.280269 | 1.492344 | 0.298612 | 1.63094 | no | yes |
| catastrophic `(168,66)` | orthogonal_only | +0.214044 | 0.159176 | 0.300000 | 0.093147 | 4723.82 | **yes** | yes |
| catastrophic `(168,66)` | background_residualized_full | -1.111934 | 0.509825 | 2.315127 | 0.484553 | 4708.25 | no | yes |
| catastrophic `(168,66)` | original_full | -1.111933 | 0.509825 | 2.315124 | 0.484552 | 4708.25 | no | yes |
| catastrophic `(69,195)` | none | 4.06e-11 | 0.1800000 | 1.0000000 | 2.20e-08 | 2.71464e-12 | no | yes |
| catastrophic `(69,195)` | tangent_only | -0.413928 | 0.277508 | 1.773024 | 1.068732 | 2.00866 | no | yes |
| catastrophic `(69,195)` | orthogonal_only | +0.005573 | 0.179331 | 0.983666 | 0.002282 | 2897.12 | no | yes |
| catastrophic `(69,195)` | background_residualized_full | -1.011339 | 0.599659 | 3.105607 | 1.172834 | 2879.02 | no | yes |
| catastrophic `(69,195)` | original_full | -1.011339 | 0.599659 | 3.105607 | 1.172834 | 2879.02 | no | yes |
| control `(379,254)` | none | -1.39e-08 | 0.1800000 | 1.0000000 | 4.79e-08 | 5.11050e-12 | no | yes |
| control `(379,254)` | tangent_only | -0.001680 | 0.183919 | 1.566489 | 0.569369 | 0.266279 | no | yes |
| control `(379,254)` | orthogonal_only | -0.003451 | 0.180317 | 1.018733 | 0.027156 | 2714.43 | no | yes |
| control `(379,254)` | background_residualized_full | -0.034759 | 0.188828 | 1.713284 | 0.635240 | 2714.14 | no | yes |
| control `(379,254)` | original_full | -0.034759 | 0.188828 | 1.713284 | 0.635240 | 2714.14 | no | yes |
| control `(358,97)` | none | -2.48e-09 | 0.1800000 | 1.0000000 | 1.14e-08 | 2.53208e-12 | no | yes |
| control `(358,97)` | tangent_only | -0.056423 | 0.200294 | 1.178445 | 0.459938 | 0.0665549 | no | yes |
| control `(358,97)` | orthogonal_only | +0.003073 | 0.179320 | 0.998533 | 0.030945 | 2869.01 | no | yes |
| control `(358,97)` | background_residualized_full | -0.012246 | 0.191034 | 1.060863 | 0.420963 | 2870.01 | no | yes |
| control `(358,97)` | original_full | -0.012246 | 0.191034 | 1.060863 | 0.420963 | 2870.01 | no | yes |

## Scientific interpretation

The small tangent-aligned component is **causally capable of producing a substantial bias** at both catastrophic positions: by itself it gives `delta_mag=-0.604` and `-0.414`, inflates `Re` from `0.18` to about `0.28 arcsec`, and changes `n` to about `1.49` and `1.77`. The matched controls do not show comparable magnitude/size collapse under `tangent_only`.

However, `tangent_only` does **not** reproduce the full catastrophes. The literal/full residual drives the two failures to `delta_mag=-1.112/-1.011`, `Re=0.510/0.600 arcsec`, and `n=2.32/3.11`. Conversely, `orthogonal_only` is nearly truth-like for the isolated catastrophe and produces a smaller, opposite-signed size/flux response in the near-source catastrophe, although that near-source orthogonal-only fit hits the lower `n` bound.

Therefore D1n-j supports a two-stage picture: the low-power tangent-aligned residual provides a failure-specific local drive, while the much larger nominally orthogonal residual is not independently catastrophic but participates in a strongly nonlinear combined response that amplifies the final morphology failure. This is stronger than a claim based only on tangent-power correlation, but it does not justify treating the tangent projection as a production correction or denoiser.

`background_residualized_full` and `original_full` are essentially identical at all four positions, so the component parallel to the fitted planar-background subspace is not responsible for the catastrophic recovery.

## Next diagnostic implication

The smallest remaining diagnostic on this failure mechanism is a frozen tangent×orthogonal response-surface/continuation experiment: vary only the scalar dose of the already-frozen tangent and orthogonal components while leaving the D1m renderer, masks, ERR, bounds and optimizer untouched. The purpose is to localize the nonlinear amplification and test whether the catastrophe appears only when an orthogonal dose is added to an already tangent-displaced solution. It must not introduce regularization, new starts, altered bounds, or any acceptance threshold.
