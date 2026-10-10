# JADES real-image artificial redshifting: group handoff

**Status: research handoff for independent JADES data testing, not a fully
validated science release.** The engine has passed synthetic FITS/WCS/PSF and
PySersic MAP/NUTS tests. Full end-to-end verification using the actual source
images, segmentation map, PSFs and target mosaic is still necessary.

## Three files to share

| File | Purpose |
| --- | --- |
| `JADES_realimage_artificial_redshifting_batch.ipynb` | Jupyter notebook; **edit only the USER SETTINGS code cell** |
| `JADES_realimage_artificial_redshifting_batch.py` | Same engine exported as a Python script; edit only USER SETTINGS |
| `README_JADES_realimage_artificial_redshifting.md` | These instructions |

There is also a repository-level `requirements-jades-realimage-redshifting.txt`
and automated synthetic tests. The notebook and script implement the same
functions rather than separate algorithms.

## Quick start

Install Python 3.11 and the packages specified in
`requirements-jades-realimage-redshifting.txt`:

```bash
python -m pip install -r requirements-jades-realimage-redshifting.txt
```

In the **single USER SETTINGS block**, start with:

```python
JADES_DATA_ROOT = Path("/path/to/JADES_DR5_test")
RUN_MODE = "PREFLIGHT_ONLY"
CATALOG_FORMAT = "JADES_DR5"
JADES_REDSHIFT_HDU = "PHOTOZ_KRON"
JADES_REDSHIFT_COL = "z_a"
SOURCE_Z_RANGE = [0.65, 1.25]  # illustration only; not a science sample cut
MAX_CASES = 5
TARGET_PLAN = [{"z": 5.0, "filter": "F444W"}]
```

**Important:** the `/path/to/...` value is a placeholder. Replace it with
the folder where the downloaded survey products are stored. For the original
Linux test drive, the root was
`/run/media/bahareh/My Passport/JADES_DR5_test`.

The supplied JADES DR5 **starter configuration** assumes the following
subfolders under that root:

```text
JADES_DR5_test/
  catalogs/
    hlsp_jades_jwst_nircam_goods-s_photometry_v5.0_catalog.fits
  mosaics/
    hlsp_jades_jwst_nircam_jw011800-deep23_f115w_v5.0_drz.fits
    hlsp_jades_jwst_nircam_jw011800-deep23_f150w_v5.0_drz.fits
    hlsp_jades_jwst_nircam_jw011800-deep23_f200w_v5.0_drz.fits
    hlsp_jades_jwst_nircam_jw011800-deep23_f444wa_v5.0_drz.fits
    hlsp_jades_jwst_nircam_goods-s_segmentation_v5.0_drz.fits
  psfs/
    hlsp_jades_jwst_nircam_jw011800-deep23_f115w_v5.0_mpsf.fits
    hlsp_jades_jwst_nircam_jw011800-deep23_f150w_v5.0_mpsf.fits
    hlsp_jades_jwst_nircam_jw011800-deep23_f200w_v5.0_mpsf.fits
    hlsp_jades_jwst_nircam_jw011800-deep23_f444wa_v5.0_mpsf.fits
```

Other subregions, filters, JADES releases or JWST surveys can be handled by
editing `SOURCE_BANDS`, `TARGET_PRODUCTS`, `TARGET_PLAN`, and their FITS
extensions in the **same USER SETTINGS block**. Do not assume the example
paths, segmentation label convention, PSF provenance or band coverage apply
unchanged outside the indicated DR5 subregion.

For a normal FITS catalog with your own selected objects instead of the
official multi-extension JADES catalog, set `CATALOG_FORMAT="TABLE"`,
point `INPUT_CATALOG_PATH` to your CSV/ECSV/FITS file, and set the four
column mappings `ID_COL`, `RA_COL`, `DEC_COL`, `Z_COL`.
Each source uses its **own** catalog redshift. `OBJECT_IDS` optionally
selects exact IDs; an empty list means all objects. `MAX_CASES=None`
removes the pilot limit and runs the selected batch.

## 1. Preflight before you run science

**Notebook:** Run All with `RUN_MODE="PREFLIGHT_ONLY"`.

**Python script:**

```bash
python JADES_realimage_artificial_redshifting_batch.py preflight
```

Preflight produces, under `OUTPUT_DIR`:

- `data_preflight.md`: readable `PASS/WARN/FAIL` report;
- `data_preflight.csv`: tabular issues;
- `data_preflight.json`: machine-readable summary.

The audit looks up the actual HDU structure and column names, confirms FITS
image dimensions and units, looks for incomplete downloads, checks WCS and
PSF metadata, checks segmentation and source IDs on a small number of pilot
objects, and attempts source-filter spectral coverage checks. FITS mosaic
pixels are never read into RAM wholesale.

**Do not ignore `FAIL` results.** If data are missing or incompatible, the
batch refuses to run. `WARN` results are not automatically fatal but
require scientific judgment. In particular, a missing/incomplete file, an
unknown PSF pixel scale, or a segmentation ID mismatch must be resolved rather
than bypassed.

A local example preflight may fail initially if only the catalog and
F115W/F150W have finished downloading. That is expected, and the report
should identify the missing F200W/F444W/segmentation/mPSF products.

## 2. Run the batch

When preflight is satisfactory:

**Notebook:** set `RUN_MODE="BATCH"`, then Run All.

**Python script:**

```bash
python JADES_realimage_artificial_redshifting_batch.py run
```

The script's `preflight`/`run` argument chooses a mode without changing
the engine. It still uses the USER SETTINGS block for all paths, filters,
redshifts, selection and numerical controls.

A separate case is run for each selected source galaxy and requested
target-redshift/filter combination. `MAX_CASES=5` is the safe default;
change it when ready. Existing successful receipts are reused on restart;
missing or incomplete downloads are retryable errors.

Outputs under `OUTPUT_DIR`:

- `frozen_settings.json` and `software_provenance.json`;
- `batch_summary.csv` with successes, unsupported cases and failures;
- `cases/<object>__z<target>__<filter>/result.json`;
- injected FITS images, combined RMS, intermediate stamps, fit masks,
  optional models and diagnostic plots.

## What the code does scientifically

It starts from **real observed multi-band source pixels** rather than a
smooth input Sérsic model:

1. Read small, WCS-aware source SCI/ERR cutouts and source segmentation.
2. Remove unrelated neighbours; preserve the source's non-Sérsic structure.
3. Homogenize source-band PSFs and perform throughput-aware pixel-SED
   interpolation at the wavelength matching the target band and redshift.
4. Apply angular-diameter-distance image resizing and cosmological
   `I_nu` dimming; **no intrinsic size/luminosity evolution**.
5. Match the redshifted source PSF to the target PSF using a
   degradation-only transfer kernel.
6. Inject the transformed real source into a real target mosaic.
7. Propagate source ERR estimates and combine them with target ERR (the
   real background noise is **not added a second time**).
8. Refit the native wavelength-matched image and target degraded image
   with PySersic, yielding recovered single-Sérsic morphology and
   differences from the native reference measurements.

PySersic `NUTS` with 1000 warmup/250 samples/one chain is the intended
science setting. `MAP` is available for a quick test. The known transformed
source support is used as the fit mask; this tests morphology recovery for
a known object, **not** JADES detection completeness.

## Known JADES DR5 specifics

The official GOODS-S photometric FITS catalog has separate table extensions.
The adapter joins `SIZE.ID` to `PHOTOZ_KRON.ID` (or `PHOTOZ.ID`)
by ID; it does not align rows by position. The position columns are
`SIZE.RA`, `SIZE.DEC`; the redshifts include `z_a`, `z_ml`,
`z_peak`, `z500` and `z_spec`. The default `z_a` is a **photometric**
redshift and must be interpreted with its uncertainty.

The actual DR5 submosaic SCI/ERR data use `MJy/sr` and approximately
`0.03 arcsec/pixel`. An empty PRIMARY can share `EXTNAME=SCI` with the
true SCI image extension: the reader selects the **2-D image**. Full-field
segmentation pixels are mapped onto submosaic cutouts via WCS with nearest
neighbour interpolation rather than assumed to share array indices.
Per-band `*_FLAG` FITS columns are not necessarily boolean flags; the
actual catalog uses float pixel quantities.

In the original local data audit the F200W download was still incomplete.
The starter configuration's `expected_min_hdus=6` check prevents silently
using a partial DR5 mosaic.

## Scientific audit: modeled effects are not automatically bias corrections

The notebook provides a **mosaic-level forward model and single-Sérsic
recovery experiment**, not a fully calibrated morphology-bias/completeness
correction. Before claiming any scientific bias correction, the group must
measure and validate the corresponding effects on actual JADES data.

| Effect | Current implementation | What is not yet validated or implemented |
| --- | --- | --- |
| Rest-frame bandpass / morphological K-correction | Throughput-weighted pixel SED interpolation, strict no-extrapolation | Color-gradient / emission-line substructure errors; interpolation truth comparison |
| Cosmological dimming and angular geometry | One `I_nu` redshift factor and `D_A` scaling | Real-data flux/aperture residuals across redshift and profile shapes |
| Spatial resampling | Bilinear intensity sampling plus a flux-audit tolerance | Exact pixel-area integration / aliasing-bias calibration, especially for compact sources |
| PSF | Common-source PSF and degradation-only target matching | Local effective PSF variability, model mPSF mismatch, recovered-profile bias versus resolvedness |
| Real noise | Observed target SCI background, source ERR transfer and combined per-pixel RMS | Full correlated-drizzle covariance, independent realizations, reliable source shot-noise exposure replay |
| Crowding / blending | Source segmentation isolation and injection into nominally blank real backgrounds | Multiple preselected crowding contexts and full neighbour deblending under the science pipeline |
| Fitting | Native and target PySersic single-Sérsic parameters | Robust posterior/convergence/bound-hit quality flags, and parity with a GALFIT/statmorph/nonparametric science pipeline |
| Morphology metrics | Recovered single-Sérsic `n`, `Re`, `q`, PA | CAS, Gini-M20, concentration, asymmetry, bars, multi-component B/T, or visual labels |
| Completeness / recovery selection | Keeps supported and failed cases, runs an input sample | Rerunning actual detection+deblending, false negatives, matched-population recovery surfaces or calibrated bias-correction functions |
| Source redshift uncertainty | Uses individual catalog `z_a` or another configured redshift estimate | Marginalization over photo-z PDFs or propagation of redshift uncertainty |

**Scientifically important:** a pipeline that reproduces a degraded image is
not equivalent to the Yu et al. (2023) bias-correction experiment, which
measures parameter-dependent systematic trends and uncertainty functions
across a galaxy sample. If the group's science uses CAS, Gini-M20 or another
nonparametric morphology estimator, they must **run the exact same science
measurement pipeline on the simulated and comparison images**. PySersic
alone is not a drop-in substitute for that analysis.

Before publication-quality results:
1. Run the preflight on the exact files and inspect its report.
2. Perform real-data tests on multiple sources spanning size, magnitude,
   profile shape, source redshift and crowding, with flux/PSF/fit diagnostics.
3. Validate the selected detection/segmentation and morphology pipeline in
   the target field, retaining failures and nondetections.
4. Quantify `delta`-parameter distributions and recovery/completeness
   versus target redshift, resolution (size/FWHM), S/N and crowding;
   distinguish physical changes from measurement effects.
5. Disclose missing drizzle covariance and exposure-level Poisson modeling
   rather than labeling these as fully corrected.

**Delivery decision:** suitable to share as a **research handoff / testing
version with known limitations**, not as a validated end-to-end
survey-wide bias correction.

## Validation status and scientific limits

**Passed:** automated synthetic FITS/WCS, segmentation, pixel processing,
PSF/flux accounting, PySersic MAP/NUTS and native-reference fitting.

**Not yet established:** success on the exact real JADES SCI/ERR, full
segmentation map and matched local mPSFs for the group's full galaxy list;
correctness of the real-data PSF residuals and selection effects; independent
recovery-bias calibration, noise covariance and completeness.

A preflight pass does not replace a real-image end-to-end test. The released
mosaic ERR maps do not encode complete drizzle covariance or detector-level
Poisson provenance. The pipeline is **mosaic-level** and does not claim to
reproduce the complete JADES detection and deblending workflow.

## References

- JADES DR5 data: https://jades-survey.github.io/scientists/data.html
- JADES DR5 NIRCam imaging: https://arxiv.org/abs/2601.15954
- JADES DR5 photometric catalog: https://arxiv.org/abs/2601.15956
- JADES DR5 morphology: https://arxiv.org/abs/2601.15957
- PySersic documentation: https://pysersic.readthedocs.io/
