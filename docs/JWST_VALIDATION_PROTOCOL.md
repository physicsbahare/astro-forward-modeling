# JWST/STPSF Validation Protocol Before Production Coding

This protocol closes the JWST-specific part of Gate B and prepares Gate D. It is intentionally separate from the future public instrument adapter.

## 1. STPSF reference-data reproducibility

STPSF requires external telescope/instrument reference data in addition to the Python package. Current STPSF installation documentation supports versioned data bundles and a `STPSF_PATH` override. For scientific reproducibility we do **not** rely on an unversioned `LATEST` dataset in acceptance tests.

The current reproducibility lock is:

- STPSF software: `2.2.0`;
- STPSF data: `2.2.0`;
- version-specific upstream archive URL: `https://stsci.box.com/shared/static/mjst9j056ibf2uph4gxy8qxmi89tjzwk.gz`;
- archive SHA-256: `bbdfbe7c5aa7ee7fdb60efed13720ba3e0619c976b77aa0d63941dd59a4b6a98`.

The first CI run with this exact bundle passed all four initial NIRCam semantic tests. The checksum is now verified before extraction in every subsequent run.

Every benchmark must record:

- STPSF package version;
- exact STPSF data-bundle version/checksum;
- instrument, detector, filter and detector position;
- telescope state/OPD configuration where applicable;
- source spectrum used for polychromatic weighting;
- output extension used (`OVERSAMP`, `DET_SAMP`, `OVERDIST`, or `DET_DIST`);
- oversampling and field-of-view settings.

## 2. Separate optical PSF from detector-coupled PSF

Current STPSF documentation distinguishes ideal optical products from products with distortion and detector charge-redistribution effects. In particular, `OVERDIST` includes distortion and continuous charge diffusion, while `DET_DIST` also applies detector-sampled IPC/PPC by default for relevant JWST instruments.

Therefore the future PSF object must expose machine-readable flags such as:

- `includes_pixel_sampling`;
- `includes_geometric_distortion`;
- `includes_charge_diffusion`;
- `includes_ipc_ppc`.

A renderer that is also configured to simulate one of these effects must reject double application.

The executable Gate-B suite now verifies that the four documented STPSF products exist, that detector-effect toggling changes the detector PSF in the expected broadening direction, and that their integrated flux scales remain mutually consistent for a compact well-contained test PSF.

## 3. Required NIRCam PSF tests

For each of F115W, F150W, F277W and F444W initially:

1. monochromatic wavelength sweep across the band;
2. three controlled spectra (blue power law, flat photon spectrum, red power law);
3. a narrow emission-line perturbation on a continuum;
4. several detector positions spanning center/corners where supported;
5. optics-only versus detector-effects-enabled output;
6. oversampling convergence;
7. wavelength-sampling convergence;
8. encircled-energy radii, centroid, second moments and normalized image residuals;
9. comparison of a global-source-spectrum PSF against component-specific chromatic rendering for a two-color galaxy;
10. repeat with an unresolved AGN spectrum plus host spectrum.

The initial CI suite already covers a controlled F444W blue-versus-red photon distribution and a center-versus-corner field-dependence check. The broader filter grid, convergence study and component-specific chromatic tests remain to be run before numerical defaults are frozen.

The objective is not to declare STPSF 'correct by definition'. The objective is to understand exactly which operator it supplies to our framework and what effects remain external.

## 4. JWST pipeline/CRDS calibration tests

Use a pinned stable `jwst` pipeline release and an explicit CRDS context. Current JWST pipeline documentation states that CRDS selects dataset-specific reference files and that a specific `CRDS_CONTEXT` can be fixed for reproducibility.

For NIRCam imaging:

1. construct or use a small calibration-valid test data model with known count rate;
2. run the photometric calibration step with an explicit reference context;
3. record the exact PHOTOM reference file;
4. verify the `PHOTMJSR` conversion numerically;
5. verify `PIXAR_SR`/`PIXAR_A2` semantics and surface-brightness ↔ pixel-flux conversions;
6. ensure variance/error products are transformed in the same calibration convention as the SCI array;
7. save the full calibration metadata needed to reproduce the conversion later.

This is the next active JWST sub-gate after the STPSF checks.

## 5. Drizzle/resampling test

Using the pinned JWST pipeline, create a small pair/set of synthetic exposures with known sky positions and expected source fluxes. Run the real `ResampleStep` across a grid of:

- `pixfrac`;
- supported kernels;
- output pixel scale;
- subpixel dithers;
- source size relative to input sampling.

Measure:

- integrated flux;
- centroid;
- second moments/half-light radius;
- effective PSF;
- pixel covariance/noise power spectrum;
- `ERR`, `VAR_POISSON`, `VAR_RNOISE`, and `VAR_FLAT` behavior;
- context/coverage image behavior.

JWST 3.0.0 documentation exposes `pixfrac`, kernel, output pixel scale and error/variance reporting controls. The purpose of the benchmark is to quantify, not assume, the distinction between L1 mosaic injection and L2 exposure-level injection.

## 6. COSMOS-Web adapter-specific validation

Before a COSMOS-Web science analysis, compare simulated NIRCam products against the actual COSMOS-Web conventions used by the morphology catalog:

- 30 mas mosaics;
- actual filter-specific/survey PSFs or PSF grids;
- segmentation maps;
- local background and weight/RMS information;
- the same source detection and morphology measurement path where available.

The first COSMOS-Web validation should contain at least three truth families:

1. smooth extended galaxies;
2. galaxies with low-surface-brightness spiral/bar/clump structure;
3. host + unresolved AGN systems.

For each family, sweep source S/N, size/PSF ratio, subpixel phase, crowding and local depth.

## 7. Closure criterion

The JWST part of Gate B/D closes only when:

- versioned STPSF and CRDS inputs are frozen and checksum/provenance recorded;
- detector-effect inclusion is unambiguous and double counting is tested to fail;
- chromatic PSF behavior is cross-checked against an independent renderer;
- calibration round trips are understood quantitatively;
- drizzle covariance/measurement changes are characterized;
- L1-vs-L2 limitations are stated numerically rather than qualitatively.

No JWST-specific production defaults should be committed before these tests are complete.
