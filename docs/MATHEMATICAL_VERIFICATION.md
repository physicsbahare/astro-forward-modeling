# Mathematical Verification Note v0.1

**Status:** pre-implementation scientific design. This is not production code and does not define a public package API yet.

## Purpose

The future framework will forward-model an astrophysical source through cosmological propagation, wavelength-dependent morphology, instrument response, PSF, detector/survey effects, source injection, and the user's measurement pipeline. Its scientific output is not merely a simulated image but a **transfer function** between source/observation truth and recovered measurements.

This note freezes the physical conventions that must be correct before production implementation begins and records the numerical experiments used to select later acceptance thresholds.

---

## 1. Cosmological spectral and surface-brightness conventions

We use emitted/rest-frame and observed-frame quantities with subscripts `e` and `o`.

Redshift:

\[
\nu_e=(1+z)\nu_o,
\qquad
\lambda_o=(1+z)\lambda_e.
\]

For a standard FLRW luminosity and angular-diameter distance pair,

\[
D_L=(1+z)^2D_A.
\]

For total spectral luminosity density and observed spectral flux density:

\[
F_{\nu,o}(\nu_o)
=\frac{(1+z)L_{\nu,e}[(1+z)\nu_o]}{4\pi D_L^2},
\]

\[
F_{\lambda,o}(\lambda_o)
=\frac{L_{\lambda,e}[\lambda_o/(1+z)]}{4\pi D_L^2(1+z)}.
\]

For specific intensity, Liouville invariance gives

\[
I_{\nu,o}(\nu_o)=\frac{I_{\nu,e}[(1+z)\nu_o]}{(1+z)^3},
\]

or equivalently

\[
I_{\lambda,o}(\lambda_o)=\frac{I_{\lambda,e}[\lambda_o/(1+z)]}{(1+z)^5}.
\]

After integrating over the corresponding redshifted spectral interval,

\[
I_{\rm bol,o}=\frac{I_{\rm bol,e}}{(1+z)^4},
\]

i.e. Tolman surface-brightness dimming.

### Design consequence: no separate forward K-correction multiplier

A K-correction is a derived relation between observed and rest-frame band measurements. In a forward model that already has an SED or spatial-spectral scene, the physically correct operation is to redshift the spectrum and integrate it through the target throughput. Applying a second K-correction factor would risk double counting.

The framework may *report* a conventional K-correction as a diagnostic, but it will not use one as an additional image multiplier.

Primary references:

- Hogg, D. W. 1999, *Distance measures in cosmology*, arXiv:astro-ph/9905116.
- Hogg et al. 2002, *The K correction*, arXiv:astro-ph/0210394.
- Barden, Jahnke & Haeussler 2008, FERENGI, arXiv:0812.1022.

---

## 2. Angular transformation

For fixed proper transverse size \(R\),

\[
\theta(z)=\frac{R}{D_A(z)}.
\]

For input and output pixel angular scales \(p_i,p_o\), the number of pixels spanning the same physical feature transforms as

\[
\frac{N_o}{N_i}
=\frac{D_A(z_i)}{D_A(z_o)}\frac{p_i}{p_o}.
\]

The future code should preferably render a latent physical scene directly into target angular pixel footprints rather than chaining geometric image interpolation steps.

---

## 3. Canonical source scene

The most general separable representation we plan to support is

\[
I_{\nu,e}(\mathbf r,\nu)
=\sum_{k=1}^{K} M_k(\mathbf r)S_k(\nu),
\]

where \(M_k\) is a spatial component/coefficient map and \(S_k\) is a spectral basis component.

This contains as special cases:

- one global SED (\(K=1\));
- bulge + disk;
- host + point-source AGN;
- continuum + spatial emission-line maps;
- a high-dimensional approximation to FERENGI-style local/pixel SEDs;
- externally supplied spectral cubes, which can bypass broadband reconstruction.

A point source is represented as a spatial delta component before convolution by the observation operator.

This representation is motivated by resolved SED reconstruction and modern astronomical scene modeling, while the exact integrated framework is our engineering design rather than a claim from one paper.

---

## 4. Photon-counting observation operator

For a photon-counting detector, an expected pixel signal should be derived from the spectral scene rather than from an arbitrary post-hoc image scaling. Schematically,

\[
\mu_p = t_{\rm exp}
\int d\lambda\,A_{\rm eff}(\lambda)\frac{\lambda}{hc}
\int_{\Omega_p} d\Omega\,
R_p(\boldsymbol\theta,\lambda)
\left[P_\lambda * I_{\lambda,o}\right](\boldsymbol\theta),
\]

where

- \(A_{\rm eff}(\lambda)\) is effective collecting area, including the efficiencies declared by the instrument adapter;
- \(P_\lambda\) is the wavelength-dependent PSF;
- \(R_p\) is the pixel response/integration operator;
- \(\mu_p\) is the expected detector signal, normally in electrons before calibration.

The instrument API must prevent double counting if a supplied `effective_area` already includes throughput/QE.

---

## 5. Chromatic PSF and color gradients

The correct broadband operator is generally

\[
\int d\lambda\,T(\lambda)
\left[P(\lambda)*I(\lambda)\right],
\]

not

\[
P_{\rm generic} * \int d\lambda\,T(\lambda)I(\lambda).
\]

The two commute only under restrictive assumptions. A galaxy can have a red bulge, blue disk, emission-line regions, and an AGN with different spectra. A single effective PSF based on the *global* SED can preserve total flux and even selected low-order moments while still altering the normalized image morphology.

The standalone verification experiment in this repository constructs a red compact component and a blue extended component with a diffraction-like PSF width proportional to wavelength. At high wavelength sampling the one-global-PSF approximation differs from the wavelength-resolved image by about **3.1% in normalized L1 image distance**, even though integrated flux agrees and the second moment was deliberately matched. This is exactly why low-order agreement is not a sufficient chromatic-PSF validation metric.

Relevant references/tools:

- GalSim chromatic profiles and bandpass integration.
- STPSF polychromatic PSFs, source-spectrum weighting, detector-position dependence.
- Voigt et al. 2012 on galaxy color-gradient biases.
- Berlfein et al. 2025 / RomanChromaticPSF for modern survey-scale chromatic PSF work.

---

## 6. Spatial information and PSF matching

For direct degradation from source PSF \(P_s\) to broader target PSF \(P_t\), seek a kernel \(K\) satisfying

\[
P_t \simeq P_s*K.
\]

The unregularized Fourier relation

\[
\tilde K=\frac{\tilde P_t}{\tilde P_s}
\]

is unstable where the source optical transfer function (OTF) is small. We therefore plan regularized Fourier matching; current Photutils supports Wiener/Tikhonov matching of the form

\[
\tilde K =
\frac{\tilde P_t\tilde P_s^*}
{|\tilde P_s|^2+\lambda R(k)},
\]

with scalar or frequency-dependent penalties.

We will report at least:

\[
D=\sum |P_t-P_s*K|,
\]

an image-domain reconstruction metric analogous to Aniano et al. (2011), and

\[
W_- = \frac12\left(\sum |K|-\sum K\right),
\]

which quantifies negative kernel weight. We will also report OTF support, noise amplification, and encircled-energy residuals.

### Hard safety rule

Direct mode may degrade spatial information but may not create spatial frequencies unsupported by the input observation. A requested target observation that is intrinsically sharper than the information support of the source must fail or switch explicitly to a model-based latent reconstruction. Prior-dominated spatial scales must remain marked as such.

The analytic Gaussian test verifies the exact result

\[
\sigma_K=\sqrt{\sigma_t^2-\sigma_s^2}
\]

for \(\sigma_t>\sigma_s\), and deliberately fails for \(\sigma_t\leq\sigma_s\). The sampled 101-pixel reference achieves L1 PSF reconstruction error \(\sim8\times10^{-16}\), demonstrating that the independent test harness itself is not the limiting factor in this ideal case.

References:

- Aniano et al. 2011, PASP 123, 1218, DOI 10.1086/662219.
- Photutils PSF matching documentation.
- PyPHER/Boucaud et al. regularized PSF homogenization.
- Zhuang & Shen 2023, arXiv:2304.13776, for AGN-host sensitivity to PSF mismatch.

---

## 7. Resampling and pixel semantics

The future framework must distinguish explicitly between:

- surface brightness / specific intensity;
- integrated flux per pixel;
- expected detector counts per pixel.

The same numerical array cannot be reprojected correctly without knowing this semantic meaning.

For a latent continuous scene, the preferred operation is direct integration into target pixel footprints.

For transfer of an already-pixelized image, our independent reference distributes each input pixel according to exact geometric overlap under a piecewise-uniform assumption. This conserves total flux at machine precision but cannot recreate subpixel information already lost in the input.

Our Gaussian experiment shows this clearly. With a source Gaussian sampled at only about 1.05 pixels per sigma, exact-overlap transfer can conserve total flux perfectly while producing a normalized morphology L1 error of about 25%. As input sampling is refined to \(\gtrsim 15\) pixels per sigma in this controlled test, the L1 error falls below about 0.2% and second-moment error below 0.1% (depending on grid commensurability/subpixel phase).

This is not a universal astronomy threshold; it is evidence that **flux conservation alone is not evidence of morphology conservation**.

The future implementation will benchmark maintained reprojection tools such as `reproject_exact` and `reproject_adaptive`. `reproject` itself explicitly distinguishes surface-brightness preservation from flux-per-pixel semantics and warns that simple interpolation is not guaranteed to be photometrically accurate.

---

## 8. Source shot noise must be applied after optical redistribution

For a Poisson source blurred by a PSF, photon arrivals are assigned to detector pixels according to the optical probability distribution. Conditional on the expected detector image, pixel counts follow the detector-level Poisson process.

A common incorrect shortcut is:

1. draw a noisy source image before the PSF;
2. convolve the noisy image.

For a point source this creates strongly correlated output fluctuations. Our 30,000-realization test finds approximately:

- correct detector-level center variance / mean: **0.98** (consistent with Poisson unity);
- correct adjacent-pixel correlation: **-0.007** (consistent with zero);
- incorrect pre-PSF adjacent-pixel correlation: **~1.0**.

Thus noise ordering is a physical issue, not a software-style preference.

---

## 9. Real-image injection must not re-add the real sky noise

A reduced survey image already contains sky noise, correlated resampling noise, detector residuals, and unresolved backgrounds. Injecting a new independent realization of the same background would double the background variance in expectation. The standalone simulation gives a variance ratio of **1.996**, as expected for two independent equal-variance Gaussian backgrounds.

Therefore L1 mosaic injection will retain the observed background and add only the synthetic source signal plus whatever source-noise treatment is scientifically supported at that fidelity.

Exact post-drizzle source covariance generally requires exposure-level injection (L2), because the final mosaic alone does not contain all information needed to reproduce the original resampling process. JWST pipeline documentation explicitly states that science-image drizzle does not directly propagate the full variance through `cdriz`; output variance is approximated by resampling variance/error components separately.

---

## 10. Spectral support is an inverse-problem question, not a wavelength-overlap question

A target rest-frame band lying between input filters does not guarantee that its flux is data constrained. A useful linearized model is

\[
\mathbf y=\mathbf R\mathbf a+\boldsymbol\epsilon,
\]

where \(\mathbf a\) are spectral-basis amplitudes and \(\mathbf R\) is the input-filter response matrix.

For target response vector \(\mathbf r_t\),

\[
f_t=\mathbf r_t^T\mathbf a.
\]

The framework should therefore track a posterior predictive distribution

\[
p(f_t\mid\mathbf y,\text{spectral model}),
\]

rather than only a yes/no wavelength-coverage flag.

Our synthetic example deliberately places a narrow spectral feature inside the wavelength range of three broad input filters. A simple wavelength-envelope metric reports **100% target coverage**, yet the target-band posterior uncertainty remains about **14.6%**, the particular noisy realization is biased by about **23%**, and about **46%** of the variance reduction in the target direction is attributable to the weak regularizing prior by our diagnostic. This demonstrates why interpolation/extrapolation labels alone are insufficient.

This diagnostic is an engineering proposal of this project, not a universal definition from the literature.

---

## 11. AGN-host decomposition as a mandatory stress test

The framework core is science-neutral, but AGN hosts are an intentionally difficult validation case because an unresolved spectral component can dominate model systematics.

Two literature branches motivate this:

1. AGN contamination simulations show that adding unresolved nuclear light biases morphology/color measures.
2. JWST-specific PSF studies show that PSF mismatch systematically biases recovered host flux and concentration, with systematics exceeding formal errors in high-S/N regimes.

The 2025 COSMOS-Web paper by Vijarnwannaluk et al. (ApJ 994, 265; DOI 10.3847/1538-4357/ae102a), provided by the project owner as a key use case, measures rest-frame 1-micron morphology for 690 X-ray-selected AGN hosts and finds disks/bars/spiral-like residual substructure in addition to spheroidal components. This strengthens the requirement that the framework distinguish intrinsic host structure, nuclear point-source light, wavelength dependence, and PSF systematics.

---

## 12. Fidelity ladder

### L0 — controlled forward rendering

Cosmological propagation, spectral integration, PSF/pixel response, idealized/declared noise.

### L1 — survey-realistic mosaic injection

Real reduced image, empirical or position-dependent PSF, real background/crowding, survey measurement pipeline. Source covariance after the historical coadd may be approximate and must be flagged.

### L2 — exposure-level injection

Inject into individual exposures and run the normal survey reduction/coaddition. This is the preferred route when selection-function or covariance fidelity matters.

### L3 — raw/detector-level simulation

Detector history/nonlinearity/persistence/cosmic rays/etc. Instrument-specific and intentionally beyond initial v1 scope.

The Balrog and HSC SynPipe literature strongly motivates keeping L1 and L2 separate rather than pretending a coadd-only injection captures every selection effect.

---

## 13. Calibration is distinct from detector physics

The instrument adapter must separate:

1. physical response from incident radiation to expected detector signal;
2. survey/pipeline calibration from detector units into public science-image units.

For JWST NIRCam imaging, the pipeline `PHOTOM` reference includes `PHOTMJSR` (MJy/sr per DN/s), and the reference file carries `PIXAR_SR`/`PIXAR_A2` average pixel areas. These are calibration conventions, not substitutes for the underlying forward photon model.

JWST simulations must record the CRDS calibration context/version used when reproducing calibrated products.

---

## 14. What is physically frozen vs. numerically unfrozen

### Frozen physical conventions

- distance duality and angular-size use of \(D_A\)/\(D_L\);
- canonical spectral specific-intensity scene;
- no duplicate forward K-correction multiplier;
- wavelength-resolved PSF inside the band integration;
- explicit flux/surface-brightness/count semantics;
- source shot noise after optical redistribution;
- no duplicate sky noise in real-image injection;
- no silent super-resolution;
- spectral support based on predictive information, not wavelength overlap alone;
- explicit separation between intrinsic truth, observation truth, and recovered quantities.

### Deliberately not yet universal constants

- PSF regularization strength;
- acceptance thresholds for `D`, `W_-`, OTF support, and ringing;
- number/placement of wavelength quadrature points;
- universal morphology tolerance under resampling;
- criteria for declaring a spectral prediction too prior dominated.

These must be chosen from convergence tests and application-specific validation rather than guessed.

---

## 15. Current standalone numerical results

The independent test suite currently verifies:

- distance duality to floating-point precision in its flat-LCDM reference;
- bolometric consistency of the \(F_\nu\) relation to \(\sim10^{-16}\) on the finest grid;
- \(F_\lambda\) bolometric consistency to \(\sim1.4\times10^{-9}\), limited by the independent numerical quadrature path used here;
- photon-rate agreement between frequency and wavelength representations to \(\sim1.6\times10^{-12}\);
- Tolman integral scaling to floating-point precision for the constructed corresponding grids;
- exact sampled Gaussian PSF broadening to \(<10^{-15}\) reconstruction error in the reference case;
- machine-precision flux conservation under exact overlap transfer;
- explicit morphology error from finite input sampling despite exact flux conservation;
- non-equivalence of a global PSF and wavelength-resolved component rendering;
- correct vs. incorrect source-shot-noise covariance behavior;
- failure of wavelength-coverage-only spectral support diagnostics.

Run:

```bash
python run_verification.py
pytest -q
```

The numerical CSV/JSON outputs are written under `results/` and diagnostic figures under `figures/`.

---

## 16. External implementation references to benchmark later

- FERENGI / Barden et al. 2008 — artificial redshifting baseline.
- Paulino-Afonso et al. 2017 — Python translation of the FERENGI core and structural-redshift experiments.
- Yu et al. 2023 — DESI to JWST/CEERS morphology bias and resolvedness dependence.
- Aniano et al. 2011 — PSF-matching diagnostics and common-resolution kernels.
- Photutils — maintained PSF matching / Wiener regularization.
- GalSim — chromatic astronomical image rendering.
- STPSF — JWST/Roman polychromatic and field-dependent PSFs.
- `reproject` — explicit astronomical reprojection semantics and exact/adaptive methods.
- Balrog DES Y3/Y6 — survey transfer function via synthetic-source injection.
- HSC SynPipe — single-visit injection through reduction/measurement.
- Zhuang & Shen 2023 — JWST NIRCam PSF mismatch in AGN-host recovery.
- Pierce et al. 2010 and earlier AGN-host simulations — nuclear contamination of morphology measures.
- Vijarnwannaluk et al. 2025 — COSMOS-Web AGN morphology stress case supplied by the project owner.

The formal bibliography is maintained in `docs/REFERENCES.md`.
