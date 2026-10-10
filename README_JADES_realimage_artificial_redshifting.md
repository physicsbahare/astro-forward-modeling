# JADES real-image artificial redshifting

This notebook is the group-facing, batch-capable real-image version of the JWST artificial-redshifting workflow.

**Main file:** `JADES_realimage_artificial_redshifting_batch.ipynb`

The science path is:

real multi-band source pixels → source-band PSF homogenization → throughput-aware pixel SED interpolation → cosmological surface-brightness and angular rescaling → source-PSF to target-PSF transformation → injection into a real target mosaic → propagated uncertainty → JADES-style PySersic refit → recovered parameters.

It does **not** replace the real galaxy by an analytic Sérsic model before redshifting.

## What is based on JADES DR5

JADES DR5 contains the full NIRCam imaging in GOODS-S and GOODS-N, including co-reductions of many other programs. DR5 provides full-field mosaics and also subregion mosaics and PSFs. The DR5 NIRCam morphology catalog fits single-component Sérsic profiles independently in available wide bands with `pysersic`. The published fitting setup uses the image, uncertainty cutout, segmentation mask, and PSF, Gaussian loss, NUTS, one chain, 1000 warm-up steps, and 250 posterior samples.

Useful official links:
- JADES DR5 data page: https://jades-survey.github.io/scientists/data.html
- DR5 temporary data access: https://slate.ucsc.edu/~brant/jades-dr5/
- NIRCam imaging paper: https://arxiv.org/abs/2601.15954
- Photometric catalog paper: https://arxiv.org/abs/2601.15956
- Morphology paper: https://arxiv.org/abs/2601.15957
- PySersic docs: https://pysersic.readthedocs.io/

## First run

1. Create an environment with `requirements-jades-realimage-redshifting.txt`.
2. Open the notebook.
3. Edit **only** the cell titled `USER SETTINGS - EDIT ONLY THIS CELL`.
   The included starter settings are **specifically for the real GOODS-S DR5
   `jw011800-deep23` test pack**. On the user's Linux drive, the one required
   root path is:

   ```python
   JADES_DATA_ROOT = Path("/run/media/bahareh/My Passport/JADES_DR5_test")
   ```

   For a different machine, change that path, and (if different) the filter/
   subregion filenames in the **same settings cell**. For the first test,
   the notebook uses the real F115W, F150W and F200W source images, the
   F444W-A target SCI/ERR image, four matched mPSFs, and one full-field
   GOODS-S segmentation map. The pilot chooses up to 5 galaxies in the
   F444W-A footprint from a configurable source-redshift interval and
   transforms each galaxy independently to z=5. Set `MAX_CASES=None`,
   adjust `SOURCE_Z_RANGE` and `TARGET_PLAN` to process a larger sample.
   `expected_min_hdus=6` refuses incomplete DR5 DRZ downloads.

   **Actual audit details:** see `docs/JADES_DR5_LOCAL_AUDIT_2026-10-10.md`.

   The `SCI` extension selector intentionally skips the empty DR5 primary
   HDU that also carries `EXTNAME=SCI`. Source/target segmentation masks
   are sampled from their own WCS onto the science-cutout grid, one small
   cutout at a time, with nearest-neighbour label sampling. Neither a
   primary-HDU alias nor different full-field versus submosaic WCS can
   silently change galaxy identity.
   For the full DR5 photometric catalog, set:
   ```python
   CATALOG_FORMAT = "JADES_DR5"
   INPUT_CATALOG_PATH = "/path/to/hlsp_jades_jwst_nircam_goods-s_photometry_v5.0_catalog.fits"
   JADES_REDSHIFT_HDU = "PHOTOZ_KRON"  # or "PHOTOZ"
   JADES_REDSHIFT_COL = "z_a"         # or "z500", "z_peak", "z_ml"
   ID_COL, RA_COL, DEC_COL, Z_COL = "ID", "RA", "DEC", "z_source"
   ```
   JADES DR5 is a **multi-HDU FITS catalog**. The notebook joins `SIZE`
   (`ID`, `RA`, `DEC`) to `PHOTOZ_KRON` or `PHOTOZ`
   (`ID`, selected redshift) using `ID`, not table row alignment.
   It copies only these small fields rather than converting the entire
   several-GB FITS catalog into a DataFrame.
   For a custom/previously prepared CSV list, choose `CATALOG_FORMAT="TABLE"`
   and map its actual `ID_COL`, `RA_COL`, `DEC_COL`, and `Z_COL`.
4. Start with a small list of objects and one target redshift.
   `OBJECT_IDS` (specific IDs), `SOURCE_Z_RANGE`, and
   `AUTO_SELECT_TARGET_FOOTPRINT` are optional **explicit** sample controls.
   The shipped **pilot settings** use `MAX_CASES=5`, `SOURCE_Z_RANGE=[0.65, 1.25]`
   and `AUTO_SELECT_TARGET_FOOTPRINT=True`, to avoid accidentally running
   a long calculation on the entire catalog. These controls are not
   astrophysical sample-selection criteria. Change them for science runs.
   The available source-band pivots must bracket the mapped **full target
   passband**; for example, F115W/F150W/F200W to F444W at z_target=5
   is not valid for every source redshift. The code refuses extrapolation.
5. Run All.
6. Check `batch_summary.csv` and the per-case JSON receipts before scaling up.

The notebook reads large FITS mosaics with memory mapping and copies only small cutouts into RAM. It processes one object-target case at a time and does not load a full JADES mosaic into memory.

## The one settings cell

### 1. Input catalog

The official DR5 GOODS-S photometric FITS catalog is here:
`https://slate.ucsc.edu/~brant/jades-dr5/GOODS-S/hlsp/catalogs/hlsp_jades_jwst_nircam_goods-s_photometry_v5.0_catalog.fits`.

**Column sources documented in Robertson et al. (2026, Appendix A):**

| DR5 HDU | Relevant columns | Use |
| --- | --- | --- |
| SIZE | ID, RA, DEC, A, B, FWHM | Positions and object geometry |
| PHOTOZ_KRON | ID, z_a, z500, z_peak, z_ml | Primary configurable source redshift |
| PHOTOZ | ID, z_a, z500, z_peak, z_ml | Aperture-based alternative photo-z |
| FLAG | ID, FLAG_BN, F115W_FLAG, F115W_WHT, F115W_TEXP, ... | Coverage and weighted-image diagnostics |

The notebook joins by ID. It does not assume row order or a nonexistent flat `z` column.
From the actual 10 Oct 2026 FITS audit, the per-band `*_FLAG` fields
have floating-point **pixel** units, and `*_WHT` fields have
inverse-variance units `(MJy/sr)^-2`. These are **not** boolean flags.
The optional legacy `JADES_REQUIRE_GOOD_FLAGS=True` setting therefore
requires positive `*_WHT` values, never `*_FLAG == 0`; leave it
False for heterogeneous-coverage samples. `z_spec`, `z500`,
`z_a`, `z_ml`, and `z_peak` exist in the actual PHOTOZ HDUs.
For scientific interpretation, remember that these are photometric redshift
estimates and may be uncertain; a vetted spectroscopic redshift input list
is preferable when available.

Reference: https://arxiv.org/html/2601.15956#A11


Set:
- `INPUT_CATALOG_PATH`
- `ID_COL`
- `RA_COL`
- `DEC_COL`
- `Z_COL`

The input can be CSV, ECSV, or FITS. There is one row per galaxy. Redshift is read separately for every row, so there is no fixed source redshift.

Paths may contain placeholders such as `{region}`. If you use path templates, add the corresponding column to `PATH_TEMPLATE_COLUMNS`.

### 2. Source bands

`SOURCE_BANDS` tells the notebook where the real source mosaics, ERR maps, segmentation map, PSF, and throughput are for each filter.

Example:

```python
SOURCE_BANDS = {
    "F150W": {
        "sci_path": "/data/jades/{region}/f150w.fits",
        "err_path": "SAME_AS_SCI",
        "seg_path": "/data/jades/{region}/segmentation.fits",
        "psf_path": "/data/jades/{region}/psf_f150w.fits",
        "sci_ext": "SCI",
        "err_ext": "ERR",
        "seg_ext": "AUTO",
        "psf_ext": "AUTO",
        "expected_min_hdus": 6,  # for DR5 DRZ mosaics
        "svo_id": "JWST/NIRCam.F150W",
        "throughput_file": None,
    },
}
```

Use the actual files from the JADES release you are working with. Do not assume filenames from an older release.

The source segmentation map is strongly recommended. It is used to isolate the target galaxy from neighbours and sky before redshifting. Pixels inside the retained source mask are kept with their signed values; negative residual pixels are not clipped.

### 3. Target products

`TARGET_PRODUCTS` contains the real target/background mosaics and target PSFs.

Example:

```python
TARGET_PRODUCTS = {
    "F444W": {
        "sci_path": "/data/jades/target_f444w.fits",
        "err_path": "SAME_AS_SCI",
        "seg_path": "/data/jades/target_segmentation.fits",
        "psf_path": "/data/jades/psf_f444w.fits",
        "sci_ext": "SCI",
        "err_ext": "ERR",
        "seg_ext": 0,
        "psf_ext": 0,
        "svo_id": "JWST/NIRCam.F444W",
        "throughput_file": None,
    },
}
```

JADES DR5 uses real mosaics with uncertainty products; the notebook never treats WHT as ERR unless you explicitly configure an uncertainty conversion. For the normal JADES case, use the released ERR image.

### 4. Target redshifts

Set `TARGET_PLAN`, for example:

```python
TARGET_PLAN = [
    {"z": 3.0, "filter": "F356W"},
    {"z": 5.0, "filter": "F444W"},
]
```

Every galaxy is processed independently. A case with `z_target <= z_source` is recorded as unsupported rather than silently run in the wrong direction.

There is no intrinsic size or luminosity evolution by default. The code still applies the required angular-diameter-distance scaling and cosmological specific-intensity dimming.

### 5. Injection position

Two modes are supported.

`INJECTION_MODE = "CATALOG"`:
provide `INJECTION_RA_COL` and `INJECTION_DEC_COL` in the input table.

`INJECTION_MODE = "AUTO_BLANK"`:
the notebook searches a small target segmentation cutout for a blank location and chooses one deterministically for each case. A target segmentation map is required for this mode.

### 6. Throughputs

The preferred order is:
1. a local throughput file in `throughput_file`, or
2. SVO through `svo_id`, cached locally.

The code maps the target response into the source observed frame and refuses spectral extrapolation. It uses two or three source bands and solves for throughput-integrated linear/quadratic pixel-SED weights. Unsupported cases remain in the summary with an explicit failure code.

### 7. Optional reference morphology

If the input list already contains native/reference structural measurements, set:

```python
REFERENCE_MORPHOLOGY_COLUMNS = {
    "n": "your_n_column",
    "re_arcsec": "your_re_arcsec_column",
    "q": "your_axis_ratio_column",
    "pa_rad": "your_pa_radian_column",
}
```

Any unavailable quantity can remain `None`. The batch summary then includes reference values and recovered-minus-reference deltas. This is optional and does not affect the image transfer.

### 8. Noise

The target sky/read/drizzle noise is already present in the real target SCI mosaic, so the notebook does **not** draw it again.

The source image already contains source-observation noise. The notebook propagates the supplied source ERR maps through the same linear transforms with a small Monte Carlo calculation and combines that propagated uncertainty with the target ERR map for the refit. This estimates per-pixel variance but does not reconstruct full drizzle covariance.

It does not manufacture target source-Poisson noise from MJy/sr. Exact source-shot noise would require detector/exposure-level count provenance.

### 8. Refit

The default refit is deliberately matched to the published JADES DR5 single-Sérsic morphology-fitting stage:
- PySersic
- single Sérsic
- Gaussian loss
- no fitted sky
- source-associated-pixel mask
- NUTS
- 1 chain
- 1000 warm-ups
- 250 samples
- n prior 0.65–8
- ellipticity prior 0–0.9

By default the fitting mask for an injected source is the **known transferred source support**. This avoids fitting unrelated target-sky pixels and reproduces the morphology-fit stage, but it is not the same as rerunning the full JADES DR5 catalog detection/deblending procedure. JADES DR5 detection is a custom multi-band S/N-stack and deblending pipeline. If the science question is *detection completeness* rather than morphology recovery conditional on a known source, the full detection/deblending experiment must be run separately on an appropriate multi-band injection set.

JADES mosaics are already background corrected, so `SUBTRACT_LOCAL_TARGET_BACKGROUND=False` is the default. Change it only when the exact product has a documented residual scalar background.

For a quick software test you may set `REFIT_MODE = "MAP"`, but use `"NUTS"` for the science run. When `RUN_NATIVE_REFIT=True`, the same fitter measures the native
wavelength-matched image as a reference, so recovered `n`, `Re`, and `q`
differences are available alongside the target fit. Those reference
measurements are not an independent intrinsic ground truth.

The notebook fits a bounded central stamp (`MAX_FIT_IMAGE_PIX`) to avoid
compiling unnecessarily huge JAX models.

## Coverage behavior

JADES coverage is heterogeneous. Before selecting the pixel-SED source bands for each object, the notebook checks whether each configured source mosaic actually covers that object's coordinate. It then chooses a supported 2- or 3-band throughput interpolation from the bands available for that object. It does not assume that every galaxy has the same band coverage.

## Scientific safeguards

The notebook stops or records an explicit failure instead of silently doing the following:
- spectral extrapolation beyond available source-band support;
- PSF sharpening/deconvolution when the target observation would require it;
- using an unknown image unit as surface brightness;
- treating WHT as ERR without a declared conversion;
- redshifting the whole noisy source sky cutout as if it were part of the galaxy;
- drawing a second realization of the already-observed target background;
- assuming all catalog galaxies have the same source redshift;
- loading entire multi-GB mosaics into RAM;
- dropping failed objects from the batch summary.

## Outputs

Each case gets its own directory and JSON receipt. The batch root contains:
- `frozen_settings.json`
- `batch_summary.csv`
- `run.log`

Successful cases can save:
- source-band cutouts and masks;
- wavelength-matched real source stamp;
- transformed source-only target stamp;
- real target background cutout;
- injected image;
- combined RMS;
- fit mask;
- PySersic posterior summary;
- recovered Sérsic parameters;
- diagnostic figure.

The runner is restart-safe. Existing successful/terminal receipts are skipped on resume; retryable failures can be rerun.

## Important limitations

This is a mosaic-level artificial-redshifting experiment. It does not reconstruct the exact exposure-level JWST drizzle covariance or a new detector realization. Source-noise propagation uses the released ERR information and therefore cannot reproduce covariance absent from those products. A final paper should state this explicitly.

The PSF files must correspond to the actual JADES products/subregions being analyzed. Do not use one unrelated PSF for a large field simply because the filter name matches.


## Validation and status

The GitHub validation workflow runs:
- notebook JSON/Python syntax and one-settings-cell checks;
- a pinned API smoke test for PySersic;
- a synthetic FITS multi-HDU catalog reader / multi-band real-pixel forward model / PySersic MAP test under `tests/validate_jades_realimage_notebook.py`.

**A successful synthetic test does not mean the exact JADES DR5 mosaic/PSF
combination has been validated.** After downloading the selected source,
target, segmentation, and PSF files, inspect each extension, BUNIT, WCS,
PSF scale and sample footprint. In particular, JADES DR5 morphological
fitting chooses contributing-program mPSFs using the actual exposure
contribution, so a configured single program mPSF is a scientifically
explicit approximation when the local combined mosaic has multiple
substantial contributors (Carreira et al. 2026).

Official methodology references:
- JADES imaging: https://arxiv.org/html/2601.15954
- JADES photometric FITS schema: https://arxiv.org/html/2601.15956
- JADES morphology and mPSF choice: https://arxiv.org/abs/2601.15957
