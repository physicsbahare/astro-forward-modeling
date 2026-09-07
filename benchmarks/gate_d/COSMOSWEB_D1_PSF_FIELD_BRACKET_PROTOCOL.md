# COSMOS-Web Gate D1n-a — STPSF detector-field bracket protocol

## Purpose

D1m removed the AB=26 target-bound hits but retained two catastrophic interior morphology failures. Before changing the scene model, segmentation, target bounds, optimizer, or injection noise model, D1n-a asks a narrower question: **how much can the declared ideal STPSF change across physically valid detector-field positions under the exact spectral/pixel assumptions already used by Gate D?**

This is a PSF-sensitivity diagnostic, not a literal reconstruction of the effective COSMOS-Web mosaic PSF. A drizzled mosaic may combine multiple exposures, detector locations, orientations, resampling phases, and temporal wavefront states, so mosaic `(x,y)` is not mapped to a single NIRCam detector coordinate here.

## Literature/software basis frozen before implementation

STPSF supports detector-position-dependent JWST wavefront/PSF calculation, including field-dependent aberration terms. Photutils ePSF methods model the net pixel-convolved PSF and subpixel phase, but an empirical ePSF requires a suitable stellar sample and is not automatic ground truth. Therefore the smallest first diagnostic is an STPSF field bracket; empirical/effective-PSF construction is deferred until this bracket is measured and the real cutout's stellar support is audited.

## Frozen inputs

- Reuse the successful D1d injection `summary.json` from run `33949290838` only to recover the exact PSF configuration and target pixel scale.
- Reuse STPSF `2.2.0` and the exact checksummed reference-data archive already frozen by Gate D.
- Preserve the D1d filter, detector, spectral weighting, output extension, FOV, oversampling, and 0.03 arcsec target scale.
- Preserve the original D1d detector position as the `baseline` condition.

## Detector-field bracket

In addition to the baseline coordinate, calculate four interior detector positions:

- `(256, 256)`
- `(1792, 256)`
- `(256, 1792)`
- `(1792, 1792)`

These are deliberately interior bracket points, not inferred local positions for the mosaic. They avoid edge-specific coordinate ambiguity while sampling a broad detector field. No bracket point is selected after seeing morphology-recovery results.

## Measurements

For each bracket PSF, normalize total flux to unity and record:

- native STPSF and resampled shapes/pixel scales;
- centroid relative to the normalized array center;
- second-moment major/minor sigma and position angle;
- enclosed-flux radii at 50% and 80%;
- normalized image L1 distance from the baseline after center-padding both images to a common shape;
- normalized cross-correlation with the baseline.

No numerical acceptance threshold is defined. The output is descriptive evidence used to decide whether a subsequent minimal recovery rerun is scientifically warranted.

## Scientific invariants

D1n-a performs **no source injection or recovery**. It therefore cannot rescue or discard D1m failures and cannot claim improved morphology. It changes no target/nuisance bounds, convergence settings, segmentation threshold, support radius, ERR/WHT data, background/noise model, Tolman factor, or acceptance criterion. It constructs no matching/deconvolution kernel and performs no PSF sharpening.

If the field bracket shows material shape variation, the next experiment may rerun only the two known AB=26 catastrophic interior cases plus frozen good controls under explicitly labelled matched/mismatched PSF conditions. If the bracket is negligible, PSF field dependence alone is deprioritized and the next diagnostic should audit effective-PSF/scene/background structure instead. That decision must be based on the machine-readable D1n-a result, not workflow status.