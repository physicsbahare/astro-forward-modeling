# Portable JWST artificial redshifting notebook

The collaborator deliverable is [JWST_artificial_redshifting_general.ipynb](JWST_artificial_redshifting_general.ipynb). It is fully self-contained: all custom helpers are notebook cells, and it imports no project-local Python module.

## Quick start

1. Create an environment using `requirements-jwst-artificial-redshifting.txt`.
2. Open the notebook, leave `DEMO_MODE = True`, and choose **Run All**.
3. Set `DEMO_MODE = False`.
4. Edit only the **USER SETTINGS — EDIT ONLY THIS CELL** section.
5. Set native/source and target/background FITS products separately, then Run All.
6. Read the preflight panel and inspect the automatic `OUTPUT_DIR` receipt.

The source data determine native morphology. The target data supply the target
PSF, real SCI background, and uncertainty map for injection. They are never
silently interchangeable. `SAME_DATASET_BACKGROUND = True` is an explicit
convenience choice that copies source settings into a separate target role.

The normal PSF interface is one empirical `*_PSF_PATH` FITS image per role.
Advanced users can select `CALLABLE`, `PSFEX_CALLABLE`, or `WEBBPSF` in the
advanced settings. A PSFEx evaluator must be supplied by the user because its
position-coordinate convention is release-specific; the notebook will not
guess it. Every path is normalized and checked without clipping signed wings.
`WEBBPSF` is optional and requires `pip install webbpsf` in addition to the
listed base requirements.

For a generic JADES mosaic, use placeholders such as:

```python
SOURCE_SCI_PATH = '...'
SOURCE_ERR_PATH = '...'
SOURCE_PSF_PATH = '...'
SOURCE_FILTER = 'F200W'

TARGET_SCI_PATH = '...'
TARGET_ERR_PATH = '...'
TARGET_PSF_PATH = '...'
TARGET_FILTER = 'F444W'
```

Check the headers and release documentation of the exact JADES (or CEERS,
PRIMER, COSMOS-Web) files you use; this repository does not assume an ERR
extension, a tile layout, or a release-specific filename.
See [the generic JADES template](docs/JADES_CONFIG_TEMPLATE.md) for a
copy-and-edit settings block.

## Scientific interpretation

The notebook preserves four interpretable comparisons:

`native/input → native-clean → target-clean → target-real`

Use native-clean to target-clean for resolution/redshift effects, and
target-clean to target-real for observational/context degradation. Do not
attribute native/input to target-real differences entirely to redshift.

The default `REAL_BACKGROUND_DETERMINISTIC` mode adds a deterministic source
to the real target SCI mosaic, retains its observed noise, and does not draw a
second sky/read/correlated-noise realization. It does not add injected-source
Poisson noise. `REAL_BACKGROUND_SOURCE_POISSON` is deliberately refused unless
the user provides a physically valid count-rate conversion and exposure.

See [the field-adaptation checklist](docs/JWST_FIELD_ADAPTATION_CHECKLIST.md)
and [method/limitations](docs/JWST_ARTIFICIAL_REDSHIFTING_METHOD_AND_LIMITATIONS.md)
before interpreting a new field.
