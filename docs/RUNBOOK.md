# GOLD403 Operational Runbook

Use this file when resuming the project after a gap.

## 1. Environment

The currently validated fitting stack used:

- Python 3.11
- galight 0.2.1
- lenstronomy 1.12.0

The local environment also uses NumPy/SciPy/Pandas/Astropy/GalSim.

Before rerunning old notebooks, print package versions into the log.

## 2. Local data configuration

Configure paths in the notebook. Do not hard-code machine-specific paths into library code.

Typical current roots:

```python
DATA_ROOT = Path("/home/bahareh/Desktop/Projects/Passive_Spiral/Data")
COSMOS_ROOT = Path("/home/bahareh/Desktop/Projects/Data_General/Cosmos_Web")
EXTERNAL_ROOT = Path("/run/media/bahareh/Seagate Hub")
MOSAIC_ROOT = EXTERNAL_ROOT / "NIRCam_mosaics"
```

Important products:

```
passive_disk_GOLD403_with_visual_flags.csv
real_cutouts_GOLD403_for_z3/
F814W_GOLD403/cutouts/
forward_z3_GOLD403_v1/
```

## 3. Preflight

Check:

- GOLD403 has 403 unique IDs.
- required catalog extensions align by object.
- source cutouts exist.
- target mosaics exist.
- SCI and ERR pairs exist.
- PSFEx files exist.
- target contexts pass the finite/ERR validity checks.

Do not start fits if the data inventory is incomplete.

## 4. PSF preflight

For NIRCam:

- evaluate PSFEx at actual position,
- x_image/y_image -> add +1 for PSFEx coordinates,
- GalSim DES_PSFEx,
- `drawImage(..., method="no_pixel")`,
- preserve signed wings,
- normalize by signed total.

Record:

- tile
- filter
- x/y
- PSF shape
- negative flux fraction
- normalization

Do not clip the PSF just because Lenstronomy warns about negative elements.

## 5. Required validation sequence

### 5.1 Exact single-Sersic closed loop

Generate truth with Lenstronomy and recover with Galight.

Expected diagnostic examples:

- 751217: n ~ 2.2546
- 322095: n ~ 1.4136
- 162363: n ~ 0.7743

The recovery should be essentially exact.

### 5.2 Perturbed-start convergence

Perturb Re, n, q, and centroid.

Use at least two PSO repeats for the diagnostic.

All three known examples should converge close to truth.

### 5.3 Exact B+D validation

Generate exact disk n=1 + bulge n=4 truth.

Fit:

- B+D
- single Sersic

Record:

- injected B/T
- recovered B/T
- disk Re
- bulge Re
- single-Sersic n
- classification

Do not interpret a good chi-square as proof that B/T is identifiable.

### 5.4 Native-clean baseline

For the same structural model, generate/fix at its native state and fit it before redshifting.

This is required because published single-Sersic and B+D fits can be mutually inconsistent.

### 5.5 z=3-clean baseline

Move the same clean model to z=3 and fit before adding any real background.

The difference native-clean -> z3-clean is the pure resolution/redshift term.

## 6. Current next run: clean 30-object sweep

Run the consolidated sweep code from:

`scripts/gold403_validation_notebook_cells.py`

Recommended workflow in Jupyter:

```python
%run -i scripts/gold403_validation_notebook_cells.py
```

Then call the clean-sweep function after the normal project setup/helper cells have been executed.

The sweep should include the known diagnostics:

- 751217
- 322095
- 162363

and span source redshift and predicted z3 disk size.

Review before proceeding:

- number of successful fits
- native B/T identifiable fraction
- z3 B/T identifiable fraction
- classification-flip fraction
- worst delta n cases
- dependence on component size in pixels

## 7. Real-background pilot

Only after clean-sweep review.

For each injection:

1. select a valid context,
2. generate target source with Lenstronomy-compatible renderer,
3. scale to E0/E1J flux,
4. inject into real SCI,
5. do not add independent background noise,
6. use real ERR,
7. fit single Sersic and B+D,
8. record neighbors/crowding/background,
9. compare against z3-clean baseline.

## 8. Production run

Do not go directly from three diagnostics to 403.

After the corrected pilot passes:

- freeze configuration,
- freeze output schema,
- run all 403,
- checkpoint CSV frequently,
- make the run restartable,
- preserve ERROR rows.

## 9. Suggested output table

At minimum:

```
id
z_source
morph_filter
target_filter
evolution
context_tile
context_id

published_n
published_re
published_q
published_bt

native_clean_n
native_clean_bt
z3_clean_n
z3_clean_bt
z3_real_n
z3_real_bt

native_disk_re_pix
native_bulge_re_pix
z3_disk_re_pix
z3_bulge_re_pix

bt_native_abs_error
bt_z3_abs_error
bt_native_identifiable
bt_z3_identifiable

catalog_disk
native_clean_disk
z3_clean_disk
z3_real_disk

snr_empirical
background_metric
crowding_metric
n_neighbours_modelled

single_chisq
bd_chisq
single_bound_hit
bd_bound_hit
status
error
software_versions
```

## 10. Interpretation rule

For science plots, never collapse all failure types into one "not recovered" category.

Distinguish:

- not detected / too low S/N
- fit failed
- fit hit bounds
- single-Sersic non-identifiable
- B+D non-identifiable
- classification changed despite identifiable fit

That separation is part of the result, not bookkeeping.
