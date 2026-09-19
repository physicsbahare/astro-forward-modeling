# R3 spectral-synthesis method amendment — throughput-aware curved SED

Status: **FROZEN BEFORE R3 EXECUTION**. This amendment supersedes only the spectral-interpolation subsection of `R3_MULTIOBJECT_PROTOCOL.md`; all other R3 guardrails remain unchanged.

## Decision
All new passive-disk/passive-spiral forward-model science runs must use the supplied official NIRCam Jan-2025 v7 mean-system throughput curves directly. Pivot-wavelength linear interpolation remains a historical R1 reference only and is not the default science renderer.

For the current source-redshift regime, use the PSF-homogenized F115W, F150W and F277W source images to constrain a quadratic `F_nu(lambda)` model independently at every pixel. The three observed band averages are treated as exact photon-counting bandpass constraints with normalized weights proportional to `P(lambda)/lambda`. For each target redshift and target filter, map the target throughput into the source-observed wavelength frame by `(1+z_source)/(1+z_target)` and integrate the curved spectral model through the full mapped throughput.

This is the minimum curved, full-throughput method justified by the available spatially resolved three-band data. It is closer to the FERENGI pixel-SED principle than the R1 pivot interpolation, while remaining explicit and auditable.

## Why the method is promoted
T1 showed that the R1 approximation is already very stable for the bright ID 57977 morphology, but spectral curvature changes flux normalization by several to about ten percent. Completeness and detection depend directly on flux/SNR, and the effect can be more consequential for smaller/fainter sources. Therefore the final completeness pipeline must not rely on the bright-anchor result to assume the pivot approximation is harmless for all objects.

## Throughput provenance
Required files are the user's official NIRCam Jan-2025 v7 mean-system throughput curves from `nircam_throughputs_all.zip` (individual files are internally labelled May2024).

- archive SHA256: `1aace14fbcfee640ba286102a97e1acfc80dd14796fa229aa33a479e89caceec`
- F115W SHA256: `0ed11483342bb380928a1ac5a912706983dadaa6bc8d16b406522b19de4cded6`
- F150W SHA256: `d13a549b8f3df2848ecaa8072a0cd296c76322114e971a2c4aa682c95d39e5a0`
- F277W SHA256: `8980999603464cf59ad6cea7f31c83ff8553f131d8b6d32b8e4dac81d7ebcfec`
- F444W SHA256: `97c148048ed0239b417c494c4cb5663c6d108f2197cee4f650aa0bfec87c3aa1`

The recomputed pivot wavelengths remain F115W=1.154078, F150W=1.500899, F277W=2.776230 and F444W=4.401743 micron.

## Failure and uncertainty policy
The curved interpolation is not allowed to silently fall back to the old two-band pivot method. Missing required source bands, ill-conditioned spectral systems, unsupported mapped wavelengths, or non-finite weights remain explicit failures. Negative interpolation coefficients are recorded because they can amplify pixel noise; they are not clipped post hoc.

The downstream R3 rules are unchanged: one redshift `I_nu` factor only, no second Tolman dimming, no PSF sharpening, no re-noising of real backgrounds, no source-shot replay without provenance, and failures remain in the output.

## Literature basis
FERENGI (Barden, Jahnke & Haussler 2008) explicitly models spectral change by fitting/interpolating an SED on a pixel-by-pixel basis before creating images in the target instrument/filter. The present three-band quadratic model is a constrained JWST/NIRCam implementation of that principle using the actual supplied filter throughput curves; it is not claimed to reconstruct spectral features unconstrained by the available bands.
