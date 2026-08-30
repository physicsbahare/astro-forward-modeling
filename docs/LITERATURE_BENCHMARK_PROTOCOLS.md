# Gate C — Literature Reproduction Protocols

The purpose of Gate C is not to reproduce every published figure pixel-for-pixel. It is to show that the future framework reproduces the physical trends and controlled biases established by landmark artificial-redshifting and AGN-host studies when configured to match their assumptions.

Every benchmark must distinguish differences caused by input data, cosmology, filters, PSFs, software versions, measurement definitions, and intrinsic-evolution prescriptions.

## C1. FERENGI benchmark

Primary reference: Barden, Jahnke & Haeussler (2008).

Reproduce the logical operator sequence on a controlled multiband nearby galaxy or synthetic equivalent:

1. source multiband registration/PSF preparation;
2. spatially resolved spectral interpolation;
3. angular-size transformation;
4. cosmological spectral/surface-brightness transformation;
5. target bandpass integration;
6. source-to-target PSF transformation;
7. target pixel sampling;
8. realistic background/noise insertion.

Compare at minimum total flux, angular size, radial profile, color-gradient behavior, and normalized morphology residuals across target redshifts. Run an additional experiment with intrinsic luminosity evolution disabled so observational degradation is isolated.

## C2. DOPTERIAN / Paulino-Afonso benchmark

Primary reference: Paulino-Afonso et al. (2017), plus later DOPTERIAN-based work.

Reproduce the published style of angular rebinning, cosmological dimming, PSF transformation, Poisson noise and real-background insertion. The aim is to confirm that a modern implementation reproduces the direction and scale of structural degradation without inheriting legacy implementation assumptions blindly.

Record explicitly where the modern radiometric treatment differs from a simple hard-coded Tolman multiplier and show that the final observable agrees when conventions are matched.

## C3. Yu et al. (2023) DESI-to-JWST morphology benchmark

Primary reference: Yu et al. 2023, artificial redshifting from DESI to JWST CEERS.

Reproduce a representative subset of their redshift/resolution experiment, with target filter choice approximately rest-frame matched to their setup.

Required recovered quantities:

- Petrosian-like radius/resolvedness measure;
- half-light radius;
- concentration;
- asymmetry;
- axis ratio where practical;
- Sersic index if the fitting backend is available.

Key independent variable:

R / FWHM_PSF rather than redshift alone.

The benchmark passes only if we reproduce the published qualitative bias directions and the transition toward unreliable morphology in poorly resolved systems. Numerical thresholds will not be forced to match if the source sample or measurement implementation differs; discrepancies must be explained quantitatively.

## C4. AGN nuclear-contamination benchmark

Primary references: Pierce et al. (2010), Gabor et al. (2009), and related controlled AGN-host simulations.

Construct host-only truth images, add an unresolved nuclear component over a grid of target-band AGN fractions, then measure host morphology with and without nuclear subtraction/decomposition.

Suggested AGN fractions:

0, 0.01, 0.03, 0.05, 0.10, 0.20, 0.30, 0.50, 0.70, 0.90.

At minimum measure concentration, asymmetry, Gini/M20 where available, half-light radius, Sersic index, and recovered host flux. We should recover the established result that central-light-sensitive morphology becomes biased as unresolved nuclear contribution grows, with the exact transition depending on S/N, PSF and host structure.

## C5. Zhuang & Shen JWST PSF-mismatch benchmark

Primary reference: Zhuang & Shen (2023), NIRCam PSF characterization and AGN+host decomposition.

Generate PSF+Sersic mock systems with a known PSF, then recover them with controlled PSF mismatch families:

- width mismatch;
- core/wing mismatch;
- detector-position mismatch;
- source-SED/chromatic mismatch;
- empirical realization mismatch.

Sweep host-to-nucleus contrast, host size relative to PSF FWHM, Sersic index and S/N.

Track biases in:

- host flux;
- effective radius;
- Sersic index;
- axis ratio;
- AGN fraction;
- residual structure.

The benchmark should reproduce the reported direction that PSF mismatch can create systematic host-parameter errors that become more important than formal statistical errors at high S/N.

## C6. COSMOS-Web AGN-host stress case

Required design input: Vijarnwannaluk et al. (2025), ApJ 994, 265, DOI 10.3847/1538-4357/ae102a.

This is not intended as a literal reproduction of their full 690-object analysis. Instead it is a framework stress test ensuring that one experiment can simultaneously support:

- unresolved nuclear emission;
- extended host components;
- wavelength-dependent host morphology;
- field/epoch-dependent PSF handling;
- host-only morphology after nuclear decomposition;
- model comparison / measurement adapters;
- uncertainty propagation across PSF realizations.

## Benchmark data policy

Where original public benchmark data can be redistributed legally, store stable download scripts/checksums rather than large files in git. Where redistribution is restricted, store retrieval instructions and exact identifiers. Synthetic analogues should be retained in the repository because their truth is exactly known.

## Gate-C closure criterion

For every benchmark:

1. exact paper/method section recorded;
2. exact assumptions mapped to framework operators;
3. executable reproduction script/notebook;
4. machine-readable outputs;
5. quantitative comparison against the published trend;
6. discrepancy discussion;
7. pass/fail review before production defaults are frozen.
