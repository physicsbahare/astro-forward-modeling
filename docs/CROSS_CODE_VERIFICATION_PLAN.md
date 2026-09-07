# Gate B — Cross-code Verification Plan

**Purpose:** independently compare the pre-implementation reference equations and numerical operators against maintained astronomy packages before any production framework code is written.

This document defines *what must be compared*, not just which packages should be imported. Package versions, exact configuration, random seeds, and external calibration contexts must be stored with every result.

## General policy

For every comparison we will retain:

- package name and exact version/commit;
- Python and dependency versions;
- complete test inputs and units;
- reference implementation result;
- external-package result;
- absolute and relative residuals;
- diagnostic plots where spatial outputs are involved;
- whether disagreement is numerical, conventional, or physical;
- a written resolution for every discrepancy before the gate is closed.

A package is not treated as ground truth merely because it is widely used. Agreement is expected after translating conventions explicitly. Unexplained agreement is insufficient; unexplained disagreement blocks production implementation.

## B1. Astropy cosmology and units

Reference target: `astropy.cosmology` and `astropy.units`.

Tests:

1. Flat-LambdaCDM distance grid over z = 1e-5 to 20 for matched H0 and Om0.
2. `luminosity_distance(z)` against the independent quadrature implementation.
3. `angular_diameter_distance(z)` against the independent implementation.
4. Etherington distance duality: `D_L / ((1+z)^2 D_A)`.
5. proper kpc/arcsec conversions at representative redshifts.
6. unit conversion tests for frequency/wavelength spectral densities using `spectral_density` equivalencies.
7. explicit F_nu/F_lambda round trips at fixed wavelengths.

Current Astropy documentation provides `luminosity_distance` and `angular_diameter_distance` as the appropriate FLRW quantities; the verification must pin a stable release rather than development documentation.

Acceptance concept: residuals should be consistent with the numerical accuracy of the independent quadrature and floating-point arithmetic. Any systematic redshift trend is a blocker.

## B2. reproject exact/adaptive resampling

Reference targets: `reproject_exact` and `reproject_adaptive`.

Tests:

1. Constant surface-brightness field under scale/rotation/WCS changes.
2. Isolated Gaussian source in surface-brightness units.
3. Isolated Gaussian source in flux-per-pixel semantics.
4. extended exponential/Sersic-like source with subpixel phase sweeps.
5. strongly downsampled source to measure aliasing.
6. rotated non-square pixel footprints.
7. comparison of exact-overlap reference implementation against `reproject_exact`.
8. adaptive resampling with and without `conserve_flux`.

The maintained `reproject` documentation explicitly distinguishes its default surface-brightness interpretation from flux-per-pixel mode in adaptive resampling. The production API must therefore never infer these semantics from array values.

Outputs: integrated flux, centroid, second moments, half-light radius, normalized L1 image residual, peak residual, and footprint coverage.

## B3. Photutils PSF matching

Reference targets: current `photutils.psf_matching.make_wiener_kernel` and, for comparison, `make_kernel`.

Tests:

1. Gaussian source/target PSFs with analytic kernel truth.
2. Moffat PSFs.
3. diffraction-like/Airy PSFs with near-zero OTF regions.
4. deliberately noisy empirical-style PSFs.
5. impossible sharper-target requests.
6. regularization sweep.
7. optional Laplacian penalty sweep.

Metrics:

- kernel normalization;
- reconstruction error D = sum |P_t - P_s*K|;
- negative weight W_-;
- encircled-energy residuals;
- OTF residual/support;
- white-noise variance amplification sum(K^2);
- ringing amplitude.

Photutils 3.0 introduced `make_wiener_kernel`, which uses Wiener/Tikhonov regularization and supports a Laplacian penalty related to the PyPHER approach. We will compare conventions explicitly rather than assume identical parameter meanings.

## B4. GalSim chromatic rendering

Reference target: GalSim chromatic machinery.

Tests:

1. single separable Gaussian morphology x power-law SED;
2. two spatial components with different SED slopes;
3. continuum plus narrow emission line;
4. wavelength-dependent diffraction-like PSF;
5. target bandpasses with smooth and sharp features;
6. source position/subpixel phase sweeps;
7. wavelength quadrature convergence.

Our independent renderer and GalSim must be supplied the same spectral units, bandpass, collecting area/exposure convention, pixel scale, and wavelength-dependent profile. GalSim internally supports multiple SED units and converts spectral SEDs to photon units; the comparison must avoid hidden normalization differences.

Important numerical benchmark: GalSim's chromatic continuous integrator has its own wavelength-sampling behavior. We will compare convergence, not blindly adopt its default sample count.

## B5. STPSF polychromatic JWST PSFs

Reference target: STPSF.

Tests for NIRCam initially:

1. monochromatic PSFs at selected wavelengths;
2. flat photon spectrum versus controlled power-law spectra;
3. blue and red source spectra through the same broad filter;
4. detector-position dependence;
5. oversampled versus detector-sampled outputs;
6. optics-only versus detector-effects products;
7. encircled-energy and effective-width comparisons;
8. wavelength-sampling convergence.

STPSF weights polychromatic PSFs by the source spectrum and instrument response. Its detector-effect products can include charge diffusion and IPC/PPC. We must store metadata indicating which effects are already inside a PSF product so that the future renderer cannot apply them twice.

## B6. JWST pipeline calibration and drizzle round trips

Reference targets: current stable `jwst` pipeline plus an explicit CRDS context.

Tests:

1. synthetic NIRCam image in count-rate units through `photom` to calibrated units;
2. verify PHOTMJSR and pixel-area semantics from the actual PHOTOM reference context;
3. calibrated-unit round trip where mathematically defined;
4. simple exposure pair through `ResampleStep` with known WCS shifts;
5. pixfrac and kernel sweeps;
6. compare flux, centroid, covariance diagnostics, and output variance products;
7. record how `var_poisson`, `var_rnoise`, and `var_flat` are handled by the installed pipeline version.

The JWST pipeline uses drizzle for imaging resampling and current documentation exposes pixfrac, kernels, weights and variance reporting. PHOTOM reference files provide calibration metadata including pixel-area quantities. Because these products evolve, every validation artifact must record the package release and CRDS context.

## Reproducible environment strategy

The local analysis environment used to prepare this design does not currently contain Astropy, reproject, Photutils, GalSim, STPSF, or the JWST pipeline. Gate B should therefore run in an isolated reproducible environment, preferably CI plus a locally exportable lock/environment file.

We will use two dependency sets:

1. **stable benchmark environment** — pinned stable releases used for acceptance;
2. **upstream-watch environment** — periodically tests current releases/development compatibility but does not silently change validated scientific defaults.

## Gate-B closure criterion

Gate B closes only when every subsection has:

- executable comparison code;
- saved machine-readable results;
- documented package versions;
- an explanation for all residuals above numerical noise;
- agreed acceptance thresholds derived from convergence rather than guessed in advance.
