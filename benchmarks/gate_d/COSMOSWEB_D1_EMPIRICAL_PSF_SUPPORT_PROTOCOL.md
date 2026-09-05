# Gate D1n-b — empirical point-source / effective-PSF support audit

## Purpose

D1n-a showed that the ideal STPSF F444W shape changes across the frozen NIRCam detector-field bracket, but only modestly. D1n-b asks a different question: **does the literal frozen COSMOS-Web F444W mosaic cutout contain enough compact, isolated, high-S/N point-source-like support to diagnose the local/effective mosaic PSF, and if so how different is that support from the single declared STPSF used by D1d–D1m?**

This is a support audit, not a morphology-recovery experiment. Compact detections are not asserted to be stars unless independently identified, and no empirical stack/ePSF is promoted to survey ground truth.

## Literature/software check before implementation

Photutils' current ePSF guidance follows Anderson & King-style empirical ePSF construction and explicitly recommends bright, isolated stars; it also warns that a robust ePSF generally benefits from a reasonably large sample (often several hundred) and that source quality normally requires visual vetting. Therefore this 512x512 cutout is audited for empirical support **before** any `EPSFBuilder` model is attempted.

STScI's NIRCam PSF documentation distinguishes single-exposure PSFs from resampled (`i2d`) PSFs and reports that resampling slightly broadens/smears the PSF. For F444W, the published context values are approximately EE50/EE80 = 0.085/0.276 arcsec for empirical single-exposure data and 0.113/0.291 arcsec for simulated resampled data. These values are context, not acceptance bands.

## Frozen design

1. Input is the exact checksummed 512x512 COSMOS-Web DR1 F444W 30-mas real cutout already used by Gate D.
2. SCI/ERR/WHT are read only and never modified.
3. Detect compact candidates with maintained `photutils.detection.DAOStarFinder`, using:
   - FWHM = 0.145 arcsec / 0.03 arcsec pix^-1;
   - threshold = 8 robust background MAD-sigma;
   - DAOStarFinder's maintained shape screening.
4. The support subset additionally requires:
   - central-pixel significance `(SCI - global background)/ERR >= 10`;
   - distance to the nearest detected candidate >= 3 detector-FWHM values;
   - enough edge clearance for a 31x31 stamp.
   These are source-quality/sample-definition settings, not morphology-recovery acceptance thresholds.
5. For each selected candidate:
   - use a 31x31 native-mosaic stamp;
   - estimate local background from an 11–15 pixel annulus;
   - retain signed background-subtracted pixels in diagnostics;
   - estimate centroid from non-negative support and interpolate the stamp to a common center with cubic `scipy.ndimage.shift`;
   - calculate positive-support second moments and EE50/EE80 while separately recording negative residual fraction.
6. Compare every selected stamp to the exact declared D1d STPSF on a common 31x31 support using normalized L1 and normalized cross-correlation.
7. If at least three candidates survive, create a **positive-flux normalized median stack** only as a diagnostic image and compare it to the declared STPSF. This is not `EPSFBuilder`, not a calibrated ePSF, and not a truth PSF.
8. Do **not** run `EPSFBuilder` in this 512x512 audit. Whether the sample is adequate for a robust ePSF is itself the result; Photutils guidance makes clear that forcing an ePSF from a small/unvetted set can be noisy or incomplete.
9. Record all detections and all selected-support diagnostics. No post-hoc acceptance band is introduced.
10. No source injection, target fitting, segmentation tuning, Tolman factor, noise addition, or PSF sharpening is performed.

## Interpretation

- A useful compact-source sample with coherent widths/EE profiles that differ from the declared STPSF would motivate a larger-mosaic empirical/effective-PSF experiment before any PSF-sensitive recovery rerun.
- Too few clean candidates is also a valid scientific result: it means this cutout cannot independently establish an empirical ePSF and we must not pretend otherwise.
- Agreement with the declared STPSF would reduce, but not eliminate, concern about the effective mosaic PSF because source classification, drizzle history, exposure mixtures and wavelength/SED dependence remain.
