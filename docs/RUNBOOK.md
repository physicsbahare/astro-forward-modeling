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
EXTERNAL_ROOT = Path("/run/media/bahareh/My Passport")
MOSAIC_ROOT = EXTERNAL_ROOT / "NIRCam_mosaics"
```



### External-drive rename and frozen production

The active external drive is currently mounted at:

```
/run/media/bahareh/My Passport
```

The already-launched frozen production notebook may still contain the earlier mount name. Do not edit that frozen notebook merely to change the mount path, because its SHA256 is part of the production provenance and the restart-safe runner verifies configuration identity before resuming. For an in-progress frozen run, preserve the notebook bytes and provide a filesystem alias/symlink from the old mount path to the new drive if needed. New notebooks/configuration should use the current `My Passport` path.

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

### 5.4 Corrected native-clean two-branch baseline

Use two independent native-clean loops:

- single-Sersic truth -> single-Sersic recovery for n;
- B+D truth -> B+D recovery for B/T.

Do not fit a single-Sersic model to a B+D truth image and call the recovered n the catalog-n transfer.

### 5.5 Corrected z=3-clean two-branch baseline

Move each branch independently to z=3 and recover it with the matching model family.

Only after both branches pass their validity checks should the disk state be formed from n<2.5 and B/T<0.5.

Native-clean -> z3-clean is the pure resolution/redshift/PSF term.

## 6. Current next run: corrected GOLD91 clean gate

The active subset is the predeclared most-populated narrow redshift bin:

```
0.75 <= z < 1.00
N = 91
```

After the normal notebook setup/helper cells have been executed:

```python
%run -i scripts/gold403_validation_notebook_cells.py

gold91 = select_gold91_redshift_bin(gold)

gold91_result = run_corrected_two_branch_clean_subset(
    gold91,
    output_csv=(
        PROJECT
        / "Results/GOLD91_corrected_two_branch_clean.csv"
    ),
    target_filter="F444W",
    pso_repeats=2,
    total_flux=1.0e4,
    n_identify_tol=0.50,
    bt_identify_tol=0.10,
    diag_root=(
        PROJECT
        / "Results/GOLD91_corrected_two_branch_diagnostics"
    ),
)

summary = summarize_corrected_two_branch_clean(gold91_result)
```

The runner checkpoints after every object and preserves completed OK rows on restart.

For the clean gate, do not add BAGPIPES or E1J. The fixed high-S/N truth normalization is intentional because this stage isolates structural representation, resolution, and PSF effects rather than detectability.

Before interpreting native -> z=3 changes, also report the original-selection -> mapped-morphology-band stage separately.

For off-laptop execution, see `KAGGLE_GOLD91_RUN.md`.

## 7. Corrected real-background pilot

Only after GOLD91 corrected clean review.

Run **E0 first**. A per-galaxy BAGPIPES luminosity-evolution correction is not part of the active method. E1J is optional later as a brightness/S/N sensitivity branch.

For each branch-specific injection:

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

Do not jump directly from the 30-object pilot to corrected GOLD403.

Order:

1. corrected GOLD91 clean;
2. corrected GOLD91 real-background E0;
3. provenance check for whether historical B/T products can be reused;
4. only then scale the corrected branch logic to GOLD403.

Keep every long run restart-safe and checkpoint after each object. Preserve ERROR rows.

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
