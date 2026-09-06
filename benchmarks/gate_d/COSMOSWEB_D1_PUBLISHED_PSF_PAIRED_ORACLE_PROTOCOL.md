# Gate D1n-f — published-PSF paired-difference mismatch oracle

## Purpose

D1n-e established a material core-shape difference between the single declared Gate-D STPSF and public COSMOS-Web OBS_084 F444W empirical PSF models, but those public PSFs are observation-level models rather than literal DR1 mosaic truth. D1m still contains two catastrophic interior AB=26 failures. Before changing any real-scene fit, D1n-f asks the narrower causal question:

**Can a PSF mismatch of the size represented by the published COSMOS-Web models, by itself, produce morphology biases comparable to the two catastrophic D1m rows when crowding/background are exactly removed?**

This is a crossed-PSF stress test, not a correction and not a PSF-selection procedure.

## Literature / software basis

Zhuang & Shen's NIRCam PSF characterization shows that PSF mismatch can bias recovered host flux, concentration/size and centroids, with broader and narrower PSFs producing different structural biases. Zhuang, Li & Shen's COSMOS-Web release provides observation-specific global/broad/narrow empirical PSFs and documents temporal/spatial variation. These results motivate measuring the exact effect for the Gate-D truth parameters instead of assuming the general literature magnitude applies.

The published arrays contain small signed negative components after empirical construction/background treatment. D1n-f preserves those signed values and normalizes by signed sum for the crossed model; it does not clip them into a different PSF. This is deliberately a diagnostic linear-response model, not a claim that negative empirical pixels are physical photon probabilities.

## Frozen subset

Only the two AB=26 D1m rows with the largest pre-existing absolute magnitude errors are used:

1. `near_source_2_5`, index 0, `(x,y)=(168,66)`, D1m Delta-mag about `-1.112`.
2. `relatively_isolated_ge30`, index 1, `(x,y)=(69,195)`, D1m Delta-mag about `-1.011`.

The subset is frozen from the already-inspected D1m result before D1n-f is executed. No rows are added or removed after seeing D1n-f.

## Frozen inputs and models

1. Exact D1d artifact from successful run `33949290838` supplies `SCI_ORIG`, ERR and the original STPSF-injected AB=26 images.
2. The paired-difference data are exactly `injected - SCI_ORIG`, so the real mosaic scene/background/crowding cancel. No new source, sky or detector noise is added.
3. Recovery PSFs are:
   - the exact frozen Gate-D STPSF control;
   - `OBS_084_F444W_broad_PSF.fits`;
   - `OBS_084_F444W_global_PSF.fits`;
   - `OBS_084_F444W_narrow_PSF.fits`.
4. Published files are checksum-pinned to the exact source bytes inspected in corrected D1n-e. Their documented source grid is 15 mas/pixel; comparison/recovery grid is 30 mas/pixel.
5. Published PSF signed values are preserved and normalized by signed sum. No negative clipping, recentring, deconvolution, Wiener operation, matching kernel or sharpening kernel is allowed.

## Frozen recovery

1. Use the inherited Gate-D Sersic source renderer geometry and the same target parameterization.
2. Keep the D1m target bounds exactly unchanged: centroid +/-2 pix, Re 1..20 pix, n 0.3..6, q 0.2..1, PA -90..90 deg, positive amplitude.
3. Keep the D1m target optimizer: `scipy.optimize.least_squares`, TRF, linear loss, `x_scale="jac"`, `max_nfev=500`.
4. Keep the literal ERR patch as the weighting map; ERR/WHT are not modified.
5. Retain free planar background terms exactly as in the inherited target parameterization even though the paired difference should be near zero background. This avoids changing the objective dimensionality between the STPSF control and crossed models.
6. Record optimizer status/message, nfev, bound hits, recovered magnitude, Delta-mag, Re, n, q, PA, centroid excursion, chi-square proxy and finite-solution state for all 2 positions x 4 PSFs = 8 rows.
7. Preserve optimizer failures, boundary solutions and morphology loss. No retry with relaxed bounds, alternate starting points or looser convergence is allowed.
8. No numerical acceptance band is introduced after seeing the result.

## Interpretation

- The STPSF-control paired-difference rows should reproduce the known numerical identifiability control; if they do not, D1n-f is a software/convention failure and no scientific conclusion is drawn.
- If crossed published PSFs alone create errors comparable to the catastrophic D1m rows, PSF mismatch remains capable of explaining a substantial part of the failure magnitude and a later minimal real-scene sensitivity test is justified.
- If crossed-PSF paired-difference biases remain modest compared with the catastrophic D1m failures, then PSF mismatch of this bracket is insufficient by itself and scene/model identifiability remains the stronger explanation.

Because the injected truth is STPSF-convolved, the published PSFs are intentionally *wrong* recovery models in D1n-f. Improvement under a published PSF would not prove that PSF is more correct for COSMOS-Web, and no PSF is selected based on fit quality.
