# JWST field-adaptation checklist

Complete this checklist before interpreting results from a new JADES,
COSMOS-Web, CEERS, PRIMER, or other JWST/NIRCam field.

- [ ] **Native versus target roles:** source SCI/ERR/PSF describe the native
  morphology; target SCI/ERR/PSF describe the injection background. They are
  deliberately distinct even when they are the same files.
- [ ] **Units:** inspect `BUNIT` and confirm the notebook's conversion is
  appropriate. MJy/sr needs WCS-derived pixel solid angle. Do not use an
  unknown count-rate unit as though it were Jy/pixel.
- [ ] **WCS and coordinates:** verify both mosaics have celestial WCS and that
  source and target/injection coordinates lie safely inside their images.
- [ ] **Pixel scale:** inspect the reported source and target scales; no 30 mas
  assumption is built in.
- [ ] **PSF:** provide the correct filter/position PSF for each role, check
  sampling and centroid diagnostics, and retain signed wings.
- [ ] **ERR meaning:** determine whether the supplied map is ERR/RMS, variance,
  inverse variance, or weight. A WHT map needs a documented conversion.
- [ ] **Correlated noise:** inspect empirical blank-sky RMS / supplied ERR. A
  warning is evidence to investigate, not permission for silent rescaling.
- [ ] **Source photon noise:** default deterministic injection adds no source
  Poisson realization. Enable it only with valid counts/exposure provenance;
  MJy/sr alone is not sufficient.
- [ ] **Segmentation:** provide a compatible segmentation map when possible.
  Without one, the notebook uses protected-source, sigma-clipped patches and
  records a warning rather than asserting unmasked pixels are blank.
- [ ] **Filter / throughput support:** declare source and target filters and
  bracket the required source-frame wavelength with photometry or an SED. Do
  not silently extrapolate.
- [ ] **Cosmology and evolution:** record the angular-size and Fnu distance
  factors separately from any explicit luminosity-evolution sensitivity.
- [ ] **Flux conservation:** require the clean-render flux check to pass.
- [ ] **Native-clean recovery:** verify Galight recovers the Lenstronomy native
  clean structural model before discussing redshift effects.
- [ ] **Target-clean recovery:** verify target-z clean recovery separately from
  target-z real-background recovery.
- [ ] **Crowding:** inspect segmentation/crowding warnings. The basic public
  fit masks segmented neighbors; field-specific joint-neighbor models require
  their own validation.
