# Generic JADES/NIRCam configuration template

Copy these values into the notebook’s one **USER SETTINGS — EDIT ONLY THIS
CELL** section. The placeholders are intentional: inspect the specific JADES
release headers and documentation rather than assuming filenames, extensions,
or ERR semantics.

```python
DEMO_MODE = False
RUN_MODE = 'SINGLE'

RA = ...
DEC = ...
SOURCE_REDSHIFT = ...
TARGET_REDSHIFT = ...

SOURCE_SCI_PATH = '...'
SOURCE_ERR_PATH = '...'
SOURCE_SEG_PATH = None
SOURCE_PSF_PATH = '...'
SOURCE_FILTER = 'F200W'

SAME_DATASET_BACKGROUND = False
TARGET_SCI_PATH = '...'
TARGET_ERR_PATH = '...'
TARGET_SEG_PATH = None
TARGET_PSF_PATH = '...'
TARGET_FILTER = 'F444W'

PHOTOMETRY = {
    # 'F150W': (Fnu_Jy, Fnu_error_Jy),
    # 'F200W': (Fnu_Jy, Fnu_error_Jy),
    # 'F277W': (Fnu_Jy, Fnu_error_Jy),
}
SED_PATH = None
MORPHOLOGY_MODE = 'FIT_NATIVE_FIRST'
OUTPUT_DIR = './JADES_redshifting_output'
```

Before Run All, confirm that the supplied uncertainty product is actually an
ERR/RMS map. For variance, inverse variance, or a weight map, set the
corresponding advanced uncertainty kind and document any required conversion.
The notebook preflight will stop if it cannot establish WCS, units, PSF
sampling, wavelength support, or valid target uncertainty semantics.
