# Reference Map

This file records methodological sources shaping the verification and future design. **It is not a checklist of papers that must each be reproduced in full.** A source becomes a benchmark only when it contributes a distinct scientific operator, failure mode, maintained independent implementation, or survey-reality check. When several papers probe the same phenomenon, the project should use the smallest controlled set that spans the non-redundant claims.

## Cosmological radiometry and K-corrections

- Hogg (1999), *Distance measures in cosmology*.
- Hogg et al. (2002), *The K correction*.

These define conventions/reference equations; they do not require paper-level image reproduction.

## Artificial redshifting and morphology bias

- Barden, Jahnke & Haeussler (2008), FERENGI.
- Paulino-Afonso et al. (2017), DOPTERIAN/FERENGI-style degradation and structural recovery.
- Yu et al. (2023), DESI-to-JWST morphology-bias/resolvedness tests.
- Ferrari et al. (2017/2018), redshift effects on morphometric classification.
- Salvador et al. (2024), DOPTERIAN-based degradation analysis.

The completed FERENGI, Paulino-Afonso, and Yu benchmarks already cover the main non-redundant artificial-redshift, pixel-integration/identifiability, and resolvedness/morphology-loss questions. Ferrari/Salvador remain supporting references unless a later gap requires a specific additional observable.

## Morphological K-corrections / chromatic structure

- Kuchinski et al. (2001), UV/optical morphology and artificial redshifting.
- Voigt et al. (2012), galaxy colour-gradient biases.
- GalSim chromatic-object implementation and documentation.
- Berlfein et al. (2026), chromatic PSF effects in Roman simulations.

The required project-level test is an explicit source-SED/chromatic-PSF mismatch on a color-gradient scene, not reproduction of every weak-lensing result.

## PSF matching and PSF systematics

- Aniano et al. (2011), common-resolution convolution kernels.
- Boucaud et al. / PyPHER, regularized PSF homogenization.
- Photutils PSF-matching implementation/documentation.
- Zhuang & Shen (2023), JWST/NIRCam PSFs and AGN-host decomposition.
- Zhuang, Li & Shen (2023), COSMOS-Web NIRCam PSF models and AGN hosts.
- Dewsnap, Barmby & Gallagher (2025/2026), JWST AGN-host decomposition across PSF constructions and fitters.

The unique required claims here are PSF-mismatch sensitivity, PSF provenance/construction dependence, and independent-fitter morphology ambiguity. Exact reproduction of every source catalog or survey statistic is unnecessary for the framework.

## AGN-host morphology / decomposition stress cases

- Pierce et al. (2010), AGN contamination of colour/morphology.
- Gabor et al. (2009), AGN host morphology in COSMOS.
- Vijarnwannaluk et al. (2025), JWST morphology of X-ray-selected AGN hosts.
- Kawase, Shibuya & Matsuda (2026), smooth-host + sparse-point-source decomposition with a point-source-balance constraint.

The nuclear-fraction contamination stress test is already complete. Kawase is retained as a conditional method-validation target because its decomposition constraint is genuinely different; a minimal controlled comparison should decide whether it adds production value before any implementation commitment.

## Source injection / survey transfer functions

- HSC SynPipe synthetic-source injection work.
- DES Balrog transfer-function and full-survey injection work.
- Bottrell et al., RealSim.

These motivate Gate D's required real-mosaic/exposure injection architecture. Here the important target is an actual survey-level injection/recovery experiment, not paper-by-paper reproduction.

## Resampling / coaddition / calibration

- Fruchter & Hook (2002), Drizzle.
- Astropy-affiliated `reproject` exact/adaptive/interpolation implementations.
- JWST Calibration Pipeline `resample` documentation.
- JWST Calibration Pipeline `photom`/PHOTOM reference documentation.

## Instrument PSF / rendering infrastructure

- STPSF documentation and pinned data products.
- GalSim chromatic profiles, SEDs, bandpasses, wavelength-dependent profiles, and correlated noise.
- PyAutoGalaxy/PyAutoArray maintained morphology/PSF-convolution stack as an independent Gate-B extension.

## Spatial-spectral reconstruction

- Blanton & Roweis (2007), kcorrect/template-basis methodology.
- scarlet/scarlet2 scene modeling.
- piXedfit spatially resolved multi-band SED preparation and PSF matching.

These are design references. They become production dependencies only if later architecture/testing shows that a specific implementation is needed.

## High-redshift attenuation

- Inoue et al. (2014), analytic intergalactic attenuation model.

## Synthetic observations from physical simulations

Recent simulation-to-survey work remains useful for future validation of physically generated latent scenes, but it is not currently a blocking gate.

---

### Evidence and dependency policy

The public package must record exact versions/provenance of scientific software that actually participates in a forward model or validation result. Reference literature and verification-only packages are not automatically production dependencies. Web documentation is mutable; release validation should pin versions and, where possible, DOI-tagged releases or immutable source commits.
