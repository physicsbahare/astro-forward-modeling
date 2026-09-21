# Self-Contained JWST Artificial-Redshifting Notebook Design

## Goal

Deliver one shareable file, `JWST_artificial_redshifting_general.ipynb`, that
an astronomy collaborator can run from a fresh kernel after editing a single
`# USER SETTINGS - EDIT ONLY THIS CELL` cell. It must not import project-local
Python modules, depend on private data, assume a specific JWST field, or carry
hidden GOLD403/COSMOS-Web defaults.

The notebook implements the validated structural experiment:

`native/input -> native-clean -> target-redshift clean -> target-redshift real background -> recovery`.

Truth construction and recovery use the Lenstronomy ImageModel / Galight
convention. The deprecated analytic Sersic renderer is prohibited.

## User experience

The notebook begins with a Quick Start:

1. Set `DEMO_MODE = True`, then Run All to validate the installation.
2. Set `DEMO_MODE = False`.
3. Edit only the separated native/source and target/background paths, filters,
   redshifts, RA/Dec, morphology mode, photometry/SED support, and output
   directory in the one user-settings cell.
4. Run All.
5. Read the preflight panel before interpreting structural results.
6. Find machine-readable results, plots, provenance, and logs in `OUTPUT_DIR`.

`RUN_MODE = "SINGLE"` is the default. `RUN_MODE = "BATCH"` is optional and
uses a catalog mapping configured only in the user settings cell.

## Notebook layout

0. Introduction and Quick Start
1. Optional dependency check/install guidance
2. Imports
3. **USER SETTINGS — EDIT ONLY THIS CELL**
4. Advanced settings — normally unchanged
5. Internal helpers — **DO NOT EDIT FOR NORMAL USE**
6. FITS/data inspection
7. PSF preparation and validation
8. Noise/ERR and correlated-noise validation
9. Native morphology input or native-first fit
10. Artificial-redshifting physics
11. Target-redshift clean model
12. Real-background injection
13. Galight/Lenstronomy recovery
14. Identifiability and quality diagnostics
15. Results and plots
16. Save outputs and provenance
17. Optional restart-safe batch mode
18. Limitations and interpretation

All custom dataclasses, functions, plotting code, checkpointing, and adapters
are defined in internal notebook cells. The notebook has no import from this
repository, `passive_disk_forward_model`, or any custom `.py` file.

## Configuration contract

Required normal single-object fields are deliberately split so the source
observation used to establish morphology can never be confused with the
target mosaic used for injection:

```python
DEMO_MODE = False
RUN_MODE = "SINGLE"

# OBJECT
RA = ...
DEC = ...
SOURCE_REDSHIFT = 1.0
TARGET_REDSHIFT = 3.0

# NATIVE SOURCE DATA
SOURCE_SCI_PATH = "..."
SOURCE_ERR_PATH = "..."
SOURCE_SEG_PATH = None
SOURCE_PSF_PATH = "..."
SOURCE_FILTER = "F200W"

# TARGET BACKGROUND DATA
SAME_DATASET_BACKGROUND = False
TARGET_SCI_PATH = "..."
TARGET_ERR_PATH = "..."
TARGET_SEG_PATH = None
TARGET_PSF_PATH = "..."
TARGET_FILTER = "F444W"

# PHOTOMETRY / SED SUPPORT FOR TARGET-FLUX PREDICTION
PHOTOMETRY = {}  # e.g. {"F150W": (fnu, fnu_err), "F200W": (...)}
SED_PATH = None

# OUTPUT
MORPHOLOGY_MODE = "FIT_NATIVE_FIRST"
OUTPUT_DIR = "./JWST_redshifting_output"
```

`SAME_DATASET_BACKGROUND = True` is an explicit convenience action which
copies declared source paths into separate target fields before input
validation. It does not merge the two concepts: native fitting always uses
the source dataset and real-background injection always uses the target
dataset. For `PARAMETRIC` morphology the source image, ERR, segmentation, and
PSF may be omitted only if supplied structural and flux inputs are
independently validated; target inputs remain required for real-background
mode.

The notebook infers WCS, pixel scale, image extent, SCI units, source pixel
location, FITS extension layout, and basic uncertainty-map semantics only when
validated from supplied products. It fails clearly rather than guessing when
units, WCS, uncertainty semantics, source location, wavelength support, or
PSF/science sampling cannot be established.

`PARAMETRIC` mode accepts a single Sersic model (`Re`, `n`, `q`, `PA`, flux)
and an optional explicitly specified B+D model. `FIT_NATIVE_FIRST` first fits
the observed source with Galight and uses that result for clean structural
input. Single-Sersic and B+D results remain distinct; B/T is never invented
from a single-Sersic fit.

## Data, unit, and SED rules

The data adapter supports FITS SCI, ERR/RMS, WHT only when the user declares
how it converts to an uncertainty map, optional segmentation, empirical PSF
FITS, WCS, target coordinate, filter, and optional exposure metadata.

The notebook recognizes declared `MJy/sr` and converts surface brightness
using an explicit pixel solid angle from WCS/header or an explicit user
override. It stores source/injected flux and conversion provenance. Unknown
units are a critical preflight failure.

`SOURCE_FILTER` and `TARGET_FILTER` are independent. A source morphology
image alone is not claimed to predict target-filter flux. Target rest/source
wavelength is derived from the selected target filter and redshift. Fnu
redshift/distance scaling, SED interpolation/K-correction, and optional
luminosity evolution are independent receipt factors. The user supplies
bracketing `PHOTOMETRY`, a validated `SED_PATH`, or explicitly declares a
same-rest-wavelength case. Interpolation beyond supplied wavelength support is
a terminal preflight failure unless the user provides an explicit, labeled
extrapolation method.

## PSF contract

The basic paths read `SOURCE_PSF_PATH` and `TARGET_PSF_PATH` as independent
FITS images. The notebook checks finite pixels, shape, centroid,
signed-total normalization, science/PSF pixel scale, and negative wings for
each. It displays a diagnostic and never clips negative wings.

Advanced optional adapters support PSFEx, a callable, or WebbPSF. PSFEx has no
default coordinate convention; users must explicitly supply the evaluator and
coordinate transformation appropriate to their release.

## Noise contract

`NOISE_MODE = "REAL_BACKGROUND_DETERMINISTIC"` is the default:

- add a deterministic source model to existing observed SCI;
- retain real background, detector/read, and correlated mosaic noise;
- do not draw a second sky/background/read-noise realization;
- retain the provided uncertainty map; and
- report that injected-source photon noise was not generated.

The current GOLD403 workflow did not demonstrate general source-Poisson
negligibility. The notebook reports a background-dominance diagnostic only
when comparable variance information exists; it does not claim it otherwise.

`REAL_BACKGROUND_SOURCE_POISSON` is disabled unless the user provides a
physically valid injected-flux-to-count conversion, effective exposure/gain or
detector provenance, and declares whether the operation is exposure-level
exact or a labeled mosaic-level approximation. It adds only injected-source
photon variance/realization and updates ERR consistently. MJy/sr alone is
insufficient and yields an actionable failure.

`SYNTHETIC_BACKGROUND` is separate, requires an explicit noise model, and
never pretends to be a real-mosaic injection.

Real-mosaic preflight samples blank unsegmented apertures/patches, reports
empirical RMS / supplied-ERR scatter, saves a plot and JSON receipt, warns for
material disagreement, and rescales ERR only when explicitly enabled. If no
segmentation map is supplied it masks the protected source region and uses
sigma-clipped robust patches; it reports a WARNING that external segmentation
was unavailable and does not label all remaining pixels blank sky.

## Preflight and quality states

The notebook prints PASS/WARNING/FAIL for readable FITS, WCS, pixel scale,
units, valid ERR/RMS, segmentation compatibility, PSF, source position,
wavelength support, finite cosmology, flux conservation, clean
render/recovery, real-background accounting, empirical noise, and absence of
a second background realization. Critical FAIL stops expensive fitting.

Results retain `OK`, `WARNING`, `TERMINAL_ERROR`, or `RETRYABLE_ERROR`;
failure codes; optimizer
convergence; bound hits; residual/chi-square metrics; finite-parameter checks;
native and target-clean B/T recovery; B/T physical-validity/identifiability;
and classification states. A nonphysical B+D total flux yields undefined B/T,
never an imputed disk class.

## Batch contract

Batch mode uses catalog columns specified in user settings. It writes an
immutable normalized configuration, manifest, package versions, append-only
log, atomic per-case JSON receipt, and optional diagnostics. Resume validates
schema/unique IDs and skips `OK`, `WARNING`, and `TERMINAL_ERROR` rows by
default; it retries `RETRYABLE_ERROR` rows and incomplete checkpoints.
`FORCE_RERUN_IDS` permits selected cases of any status. Examples of terminal
errors are unsupported wavelength support, missing required input, and
scientifically unusable source support. Optimizer crashes, interruptions, and
temporary numerical failures are retryable. The runner never rewrites valid
rows or creates duplicate case IDs.

## Validation and release gates

The notebook starts with a non-mutating environment check that names missing
packages and prints an exact install command; any install cell is visibly
optional. It must run from a fresh kernel without private local files in demo
mode. Tests cover Sersic truth recovery, flux conservation, invalid path,
missing ERR, invalid PSF, insufficient wavelength support, segmentation-free
noise fallback, double-background noise prevention, output receipt creation,
restart-safe batch behavior, and re-execution after a kernel restart.

One GOLD403 validation object is a secondary regression exercise only when
production is paused or complete. It uses documented tolerances and is never a
runtime dependency of the public notebook.

## Supporting files and non-goals

The notebook is the only required deliverable. Optional files are a README,
requirements file, methodology/limitations note, field-adaptation checklist,
and JADES placeholder configuration. It does not reproduce exact
exposure-level drizzle covariance from a final mosaic, infer detector
calibration, manufacture Poisson noise from surface-brightness units, provide
a universal B/T threshold, or transfer COSMOS-specific conventions to another
field.
