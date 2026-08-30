# Reference Map

This list records the methodological sources currently shaping the pre-implementation design. It is intentionally broader than the citations that will eventually appear in a software paper.

## Cosmological radiometry and K-corrections

- Hogg, D. W. (1999), **Distance measures in cosmology**, arXiv:astro-ph/9905116.
- Hogg, D. W. et al. (2002), **The K correction**, arXiv:astro-ph/0210394.

## Artificial redshifting and morphology bias

- Barden, M., Jahnke, K., & Haeussler, B. (2008), **FERENGI: Full and Efficient Redshifting of Ensembles of Nearby Galaxy Images**, arXiv:0812.1022.
- Paulino-Afonso, A. et al. (2017), **The structural and size evolution of star-forming galaxies over the last 11 Gyr**, MNRAS 465, 2717. Includes a Python translation of the FERENGI core and generalized luminosity evolution treatment. DOI: 10.1093/mnras/stw2939.
- Yu, S.-Y. et al. (2023), **Redshifting galaxies from DESI to JWST CEERS: Correction of biases and uncertainties in quantifying morphology**, arXiv:2307.04753.
- Ferrari, F. et al. (2017/2018), **The impact of redshift on galaxy morphometric classification: case studies for SDSS, DES, LSST and HST with Morfometryka**, MNRAS 473, 2701.
- Salvador et al. (2024), **The debiased morphological transformations of galaxies since z ~ 3 in CANDELS** (DOPTERIAN-based degradation analysis).

## Morphological K-corrections / chromatic structure

- Kuchinski et al. (2001), UV/optical morphology and artificial redshifting work.
- Voigt, L. M. et al. (2012), **The impact of galaxy colour gradients on cosmic shear measurement**.
- GalSim documentation and chromatic-object implementation.
- Berlfein et al. (2025), **Chromatic Effects on the PSF and Shear Measurement for the Roman Space Telescope High-Latitude Wide Area Survey**; companion public RomanChromaticPSF repository.

## PSF matching and PSF systematics

- Aniano, G., Draine, B. T., Gordon, K. D., & Sandstrom, K. (2011), **Common-resolution convolution kernels for space- and ground-based telescopes**, PASP 123, 1218. DOI: 10.1086/662219.
- Boucaud et al. / PyPHER — regularized PSF homogenization.
- Photutils `psf_matching` documentation, including Wiener/Tikhonov regularization.
- Zhuang, M.-Y. & Shen, Y. (2023), **Characterization of JWST NIRCam PSFs and Implications for AGN+Host Image Decomposition**, arXiv:2304.13776.
- Zhuang, Li & Shen (2023), **AGNs and Host Galaxies in COSMOS-Web. I. NIRCam Images, PSF Models and Initial Results**, arXiv:2309.03266.

## AGN-host morphology stress cases

- Pierce et al. (2010), **The effects of an active galactic nucleus on host galaxy colour and morphology measurements**, MNRAS 405, 718.
- Gabor et al. (2009), **Active Galactic Nucleus Host Galaxy Morphologies in COSMOS**, ApJ 691, 705.
- Vijarnwannaluk, B. et al. (2025), **The Stellar Morphology and Size of X-Ray-selected Active Galactic Nucleus Host Galaxies Revealed by JWST**, ApJ 994, 265. DOI: 10.3847/1538-4357/ae102a. This is the paper supplied by the project owner as a required design input.

## Source injection / survey transfer functions

- Huang et al. (2018), HSC **SynPipe** synthetic-source injection and pipeline characterization.
- Suchyta et al. / Everett et al. / DES Balrog work, especially **Dark Energy Survey Year 3 Results: Measuring the Survey Transfer Function with Balrog**, ApJS, DOI: 10.3847/1538-4365/ac26c1.
- Anbajagane et al. (2025), **Dark Energy Survey Year 6 Results: Synthetic-source Injection Across the Full Survey Using Balrog**, Open Journal of Astrophysics 8, DOI: 10.33232/001c.138627.
- Bottrell et al., **RealSim**, public code for realistic insertion/degradation of galaxy images into survey imaging.

## Resampling / coaddition / calibration

- Fruchter & Hook (2002), **Drizzle: A Method for the Linear Reconstruction of Undersampled Images**, PASP.
- Astropy-affiliated `reproject` documentation: exact-overlap, adaptive anti-aliased, and interpolation algorithms; explicit distinction between surface-brightness and flux-per-pixel semantics.
- JWST Calibration Pipeline `resample` documentation: drizzle, weights, and approximate variance propagation.
- JWST Calibration Pipeline `photom` and PHOTOM reference documentation: PHOTMJSR and pixel-area metadata.

## Instrument PSF / rendering infrastructure

- STPSF documentation: source-spectrum-weighted polychromatic PSFs, wavelength sampling, detector-position dependence, oversampling, detector-effect products.
- GalSim documentation: chromatic profiles, SEDs, bandpasses, wavelength-dependent profiles, correlated noise.

## Spatial-spectral reconstruction

- Blanton & Roweis (2007), **K-corrections and filter transformations in the ultraviolet, optical, and near-infrared**, kcorrect/template basis methodology.
- Melchior et al., scarlet / scarlet2 scene modeling.
- piXedfit documentation and papers for spatially resolved multi-band SED preparation, PSF matching, and adaptive pixel binning.

## High-redshift attenuation

- Inoue et al. (2014), analytic intergalactic attenuation model, MNRAS 442, 1805, arXiv:1402.0677.

## Synthetic observations from physical simulations

- Recent TNG50-to-JWST forward-modeling work generating dust-aware synthetic JWST observations with survey depth/resolution matching; relevant for later validation of physically generated latent scenes.

---

### Documentation sources to pin by version in the future public package

The public package must store or cite exact versions of: Astropy, Photutils, reproject, GalSim, STPSF, JWST Calibration Pipeline/CRDS context, and any survey-specific measurement software. Web documentation is mutable; release validation should pin versions and, where possible, DOI-tagged software releases.
