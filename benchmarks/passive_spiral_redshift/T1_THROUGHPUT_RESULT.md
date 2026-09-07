# T1 throughput-aware interpolation sensitivity result

Status: LOCAL/ATTACHED-DATA RESULT. Not a GitHub Actions science run.

Inputs:
- COSMOS-Web ID 57977 A2 30-mas SCI cutouts used in R1.
- User-supplied official NIRCam Jan-2025 v7 throughput archive.
- Archive SHA256: `1aace14fbcfee640ba286102a97e1acfc80dd14796fa229aa33a479e89caceec`.

Throughput preflight:
- Recomputed pivots from the supplied curves: F115W=1.154078 um, F150W=1.500899 um, F277W=2.776230 um, F444W=4.401743 um, matching the STScI v7 values.

Models:
- R1: pivot-wavelength linear Fnu interpolation between F150W and F277W.
- T1-L: exact-throughput linear Fnu model constrained by F150W and F277W band averages.
- T1-Q: exact-throughput quadratic Fnu model constrained by PSF-homogenized F115W, F150W and F277W band averages.

Main result:
1. Exact throughput integration alone (T1-L) is effectively identical to R1 for morphology: normalized image differences are only about 0.0006–0.0023%, |delta q| < 5e-6, and flux ratios differ from unity by <0.02%.
2. Allowing spectral curvature with F115W+F150W+F277W (T1-Q) changes normalized morphology only mildly: positive-image differences 0.21–1.11%, |delta q| <= 0.0067, RMS-size changes <=0.48%, and |delta concentration| <=0.0018.
3. Flux normalization is more sensitive than morphology. T1-Q predicts about 3–13% higher signed flux than R1 depending on target redshift.
4. An independent smooth positive global SED fit to the catalog F115W/F150W/F277W photometry gives a similar 3–11% flux increase, supporting the conclusion that the flux effect is due to plausible SED curvature rather than image-shape instability.

Interpretation:
- For the morphology-only demonstration of ID 57977, the frozen R1 pivot-linear approximation is robust.
- For final completeness work, where detection/SNR matters, the 3–11% flux-normalization sensitivity should be propagated or replaced by a better SED-informed normalization.
- The user throughput curves enable exact bandpass integration, but throughput files alone do not uniquely determine the full per-pixel SED. A true FERENGI-style full solution would fit a spectral model/template per pixel (or a constrained spatial SED model) before integrating through the target bandpass.
- T1-Q uses negative F115W coefficients in some target cases, which is mathematically normal for quadratic interpolation but can amplify pixel noise; therefore T1-Q remains a sensitivity diagnostic, not the adopted production interpolation.

References:
- FERENGI (Barden, Jahnke & Haussler 2008): https://arxiv.org/abs/0812.1022
- STScI NIRCam filters / v7 throughput curves: https://jwst-docs.stsci.edu/jwst-near-infrared-camera/nircam-instrumentation/nircam-filters
- synphot photon-counting bandpass formulae: https://synphot.readthedocs.io/en/latest/synphot/formulae.html

No acceptance threshold was introduced after inspecting the result.
