# T1 — NIRCam throughput-aware interpolation sensitivity

Status: **FROZEN LOCALLY BEFORE T1 IMAGE RESULTS**. This is an attached-data validation experiment, not a GitHub/CI result and not a replacement for R1.

## Question
Does replacing the R1 pivot-wavelength linear per-pixel interpolation with a NIRCam-throughput-aware spectral interpolation materially change the artificial-redshifted morphology of COSMOS2025 ID 57977?

## Inputs
- Same checksummed 30 mas A2 SCI cutouts for ID 57977 used by R1.
- NIRCam throughput archive supplied by the user: `nircam_throughputs_all.zip`.
- Use detector-averaged `mean_throughputs` curves for F115W, F150W, F277W and F444W from the Jan-2025 v7 archive (files are labelled May2024 mean system throughput inside the archive).
- Source redshift z=0.4304 and target grid z=[1,1.5,2,2.5,3].
- Same target bands as R1: F277W,F277W,F444W,F444W,F444W.

## Common image preparation
- Use catalog center x=132.701475, y=133.200736 (zero-based pixels).
- Estimate scalar background independently in each source band from 2.5<=r<3.5 arcsec.
- Keep r<=1.5 arcsec source stamp; retain negative residual pixels.
- Homogenize source images to the declared F277W PSF bracket 0.092 arcsec: F115W 0.040->0.092, F150W 0.050->0.092, F277W unchanged. No sharpening.

## Models compared
### R1 reference
Linear Fnu interpolation between the F150W and F277W images at the filter pivot wavelengths, exactly as frozen in R1.

### T1-L: throughput-aware linear spectrum
At each pixel assume Fnu(lambda)=a+b lambda. Determine a,b by requiring the photon-weighted band averages through the exact F150W and F277W mean system throughput curves to equal the two observed PSF-matched images. Then integrate that spectrum through the target filter throughput mapped back to the source-observed wavelength interval.

### T1-Q: throughput-aware quadratic spectrum
At each pixel assume Fnu(lambda)=a+b lambda+c lambda^2. Determine a,b,c by requiring the photon-weighted band averages through the exact F115W, F150W and F277W mean system throughput curves to equal the three PSF-matched source images. Then integrate through the mapped target throughput.

For photon-counting response, use normalized Fnu weights proportional to P(lambda)/lambda. The mapped target passband uses lambda_source=lambda_target*(1+z_source)/(1+z_target).

## Downstream transfer
After spectral synthesis, use the same R1 I_nu redshift factor, angular rescaling, 30 mas sampling and degradation-only target PSF matching. Add no noise and no background.

## Diagnostics
For each target redshift and both T1 models, compare to the R1 image using:
- normalized positive-image L1 difference;
- pixel Pearson correlation in the central source region;
- second-moment q;
- RMS angular size;
- concentration F(<0.3 arcsec)/F(<1.0 arcsec);
- summed signed and positive intensity ratios.

No post-hoc pass/fail threshold is defined. The result is a representation-sensitivity diagnostic only.
