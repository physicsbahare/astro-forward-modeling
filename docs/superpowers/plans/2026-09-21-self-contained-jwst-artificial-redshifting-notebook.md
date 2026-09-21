# Self-Contained JWST Artificial-Redshifting Notebook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver one portable, self-contained notebook that runs a scientifically defensible JWST artificial-redshifting experiment from a single user-settings cell.

**Architecture:** `JWST_artificial_redshifting_general.ipynb` contains every custom data adapter, PSF/noise diagnostic, Lenstronomy renderer, Galight recovery wrapper, checkpoint function, plotting routine, and batch runner in internal cells. Optional Markdown documents only explain the notebook and field adaptation; no project-local Python module is imported at runtime. A configuration normalization function produces explicitly distinct native/source and target/background datasets, so convenience reuse cannot silently cross PSFs or uncertainty maps.

**Tech Stack:** Python 3.10+, NumPy, SciPy, Astropy, Matplotlib, Photutils, Lenstronomy, Galight, nbformat, nbclient/Jupyter.

**Spec:** `docs/superpowers/specs/2026-09-21-jwst-artificial-redshifting-notebook-design.md`

## Global Constraints

- The public deliverable is `JWST_artificial_redshifting_general.ipynb`; it imports no custom local `.py` module.
- Use the validated Lenstronomy ImageModel/Galight convention; do not use the deprecated analytic Sersic renderer.
- Preserve `native/input -> native-clean -> target-clean -> target-real -> recovery` and distinguish the latter two comparisons.
- Native/source and target/background SCI, ERR, segmentation, PSF, filter, and WCS are separate internal concepts.
- Default real injection is deterministic and must not add a second sky, read-noise, or correlated-background realization.
- Source Poisson mode requires physically valid count/exposure metadata; MJy/sr alone is insufficient.
- Never clip signed PSF wings; report them instead.
- Batch checkpoints are atomic, receipt-bearing, duplicate-free, and use `OK`, `WARNING`, `TERMINAL_ERROR`, and `RETRYABLE_ERROR` semantics.
- Do not include private paths, COSMOS tile conventions, GOLD403 IDs/columns, fixed filters, fixed redshift, or fixed pixel scale.
- Do not touch the paused GOLD403 production process or its data while implementing this deliverable.

## Review Focus

- A target mosaic with a different WCS or pixel scale must use target coordinates/PSF/ERR, never source products; Task 2 tests this normalized configuration.
- A lone source-filter flux whose wavelength does not support the target rest wavelength must terminate before rendering; Task 3 tests this failure.
- Missing segmentation must produce a protected-source, robust-patch warning rather than call all pixels blank sky; Task 3 tests this fallback.
- A malformed/incomplete batch checkpoint must retry, whereas terminal scientific input failures must remain skipped on resume; Task 4 tests both paths.
- A fresh notebook kernel with `DEMO_MODE=True` must write results without project imports or prior variables; Task 5 executes it with nbclient.

---

### Task 1: Freeze the public contract and notebook skeleton

**Files:**
- Modify: `docs/superpowers/specs/2026-09-21-jwst-artificial-redshifting-notebook-design.md`
- Create: `JWST_artificial_redshifting_general.ipynb`
- Create: `README_JWST_artificial_redshifting.md`
- Create: `requirements-jwst-artificial-redshifting.txt`
- Create: `docs/JWST_FIELD_ADAPTATION_CHECKLIST.md`
- Create: `docs/JWST_ARTIFICIAL_REDSHIFTING_METHOD_AND_LIMITATIONS.md`

**Interfaces:**
- Consumes: the approved spec.
- Produces: the one-cell public settings surface and a notebook whose all later functions live in `# INTERNAL - DO NOT EDIT FOR NORMAL USE` cells.

- [x] **Step 1: Write a notebook contract assertion cell before implementation**

```python
assert "passive_disk_forward_model" not in NOTEBOOK_SOURCE
assert "/home/bahareh" not in NOTEBOOK_SOURCE
assert "SOURCE_SCI_PATH" in NOTEBOOK_SOURCE
assert "TARGET_SCI_PATH" in NOTEBOOK_SOURCE
```

- [x] **Step 2: Run the assertion against the skeleton and verify it fails before settings and source separation exist**

Run: `python -c "import json; n=json.load(open('JWST_artificial_redshifting_general.ipynb')); s='\\n'.join(''.join(c.get('source',[])) for c in n['cells']); assert 'SOURCE_SCI_PATH' in s and 'TARGET_SCI_PATH' in s"`

Expected: non-zero exit before the skeleton contains the required public settings.

- [x] **Step 3: Create the notebook skeleton and companion guidance**

```python
# USER SETTINGS - EDIT ONLY THIS CELL
DEMO_MODE = False; RUN_MODE = "SINGLE"
SOURCE_SCI_PATH = "..."; SOURCE_ERR_PATH = "..."; SOURCE_PSF_PATH = "..."
TARGET_SCI_PATH = "..."; TARGET_ERR_PATH = "..."; TARGET_PSF_PATH = "..."
PHOTOMETRY = {}; SED_PATH = None
```

Include sections 0--18, a non-mutating dependency check that prints `pip install ...`, an optional commented installation cell, Quick Start, JADES placeholders only, and the exact adaptation checklist topics in the spec.

- [x] **Step 4: Run the contract assertion and inspect the static notebook structure**

Run: `python -c "import json; n=json.load(open('JWST_artificial_redshifting_general.ipynb')); s='\\n'.join(''.join(c.get('source',[])) for c in n['cells']); assert 'SOURCE_SCI_PATH' in s and 'TARGET_SCI_PATH' in s and 'passive_disk_forward_model' not in s and '/home/bahareh' not in s"`

Expected: zero exit.

- [x] **Step 5: Commit the contract and skeleton**

```bash
git add JWST_artificial_redshifting_general.ipynb README_JWST_artificial_redshifting.md requirements-jwst-artificial-redshifting.txt docs/JWST_FIELD_ADAPTATION_CHECKLIST.md docs/JWST_ARTIFICIAL_REDSHIFTING_METHOD_AND_LIMITATIONS.md docs/superpowers/specs/2026-09-21-jwst-artificial-redshifting-notebook-design.md
git commit -m "feat: scaffold self-contained JWST redshifting notebook"
```

### Task 2: Implement configuration, FITS, PSF, and provenance helpers inside the notebook

**Files:**
- Modify: `JWST_artificial_redshifting_general.ipynb`

**Interfaces:**
- Produces: `normalize_config(user: dict) -> dict`, `load_dataset(role, config) -> Dataset`, `prepare_psf(role, config, dataset) -> PSFInfo`, `write_provenance(config, output_dir) -> Path`, and `PipelineFailure(status, code, message)`.
- Consumes: values from the one user-settings cell only.

- [x] **Step 1: Add a failing inline self-test for source/target isolation**

```python
cfg = normalize_config({"SAME_DATASET_BACKGROUND": False,
                        "SOURCE_ERR_PATH": "source_err.fits",
                        "TARGET_ERR_PATH": "target_err.fits"})
assert cfg["source"]["err_path"] == "source_err.fits"
assert cfg["target"]["err_path"] == "target_err.fits"
assert cfg["source"]["err_path"] != cfg["target"]["err_path"]
```

- [x] **Step 2: Execute the inline self-test before the normalization helper exists**

Run: execute the isolated notebook cell with `normalize_config` removed.

Expected: `NameError`.

- [x] **Step 3: Implement the minimal safe adapters**

```python
def normalize_config(user):
    # create distinct source and target dictionaries; copy only if explicit
    # validate required target products for real-background mode
    return normalized

def prepare_psf(role, config, dataset):
    # preserve signed pixels; normalize signed total; validate centroid/sampling
    return PSFInfo(array=psf, pixel_scale_arcsec=scale, has_negative_wings=flag)
```

Read FITS headers where possible, fail if units/WCS/uncertainty semantics are not understood, and persist a normalized immutable JSON plus versions. Recognize SCI and declared ERR/RMS/variance/weight kinds without guessing a WHT conversion.

- [x] **Step 4: Execute the source/target isolation, signed-PSF, and invalid-PSF self-tests**

Run: execute the notebook helper/self-test cells in a clean Python kernel.

Expected: distinct products remain distinct; signed PSF remains signed after normalization; all-NaN/zero-sum PSF raises `TERMINAL_ERROR`.

- [x] **Step 5: Commit configuration and adapters**

```bash
git add JWST_artificial_redshifting_general.ipynb
git commit -m "feat: add portable source-target data and PSF adapters"
```

### Task 3: Implement physical rendering, photometry support, noise audit, and single-object pipeline

**Files:**
- Modify: `JWST_artificial_redshifting_general.ipynb`

**Interfaces:**
- Produces: `validate_wavelength_support(config) -> FluxPlan`, `preflight(config) -> list[Check]`, `run_single(config) -> dict`, `show_results(result)`, and `save_results(result)`.
- Consumes: Task 2 dataset/PSF objects and `PHOTOMETRY`/`SED_PATH` values.

- [x] **Step 1: Add failing inline tests for no extrapolation and no duplicate background noise**

```python
with pytest.raises(PipelineFailure, match="UNSUPPORTED_WAVELENGTH"):
    validate_wavelength_support(one_filter_not_matching_target_config)
result = inject_real_background(target_sci, model, target_err,
                                noise_mode="REAL_BACKGROUND_DETERMINISTIC")
assert np.array_equal(result["err"], target_err)
assert result["background_noise_draws"] == 0
```

- [x] **Step 2: Execute those tests before their functions exist**

Run: execute the inline test cell before implementation.

Expected: `NameError`.

- [x] **Step 3: Implement the validated scientific chain with clear receipts**

```python
def run_single(config):
    # native input -> native-clean -> target-clean -> target-real -> recovery
    # Lenstronomy ImageModel renders all structural truth.
    # Galight recovers native/target structural parameters.
    return result
```

Use `D_A` scaling and matched-rest-wavelength Fnu scaling
`((1+z_t)/(1+z_s)) * (D_L(z_s)/D_L(z_t))**2`; record SED, luminosity-evolution,
and flux-conservation factors separately. Fit native morphology in
`FIT_NATIVE_FIRST`, accept validated user truth in `PARAMETRIC`, and keep
single-Sersic and B+D/B-T outputs separate. Implement robust source-masked,
sigma-clipped patch sampling when segmentation is absent. Default to
deterministic real-background injection; source-Poisson requires explicitly
valid count/exposure conversion and never derives it from MJy/sr. Preflight
prints every required PASS/WARNING/FAIL and stops on critical failures.

- [x] **Step 4: Run unit-level inline tests**

Run: execute the wavelength, deterministic-noise, missing-segmentation,
flux-conservation, and preflight tests in a fresh kernel.

Expected: unsupported SED is terminal, missing segmentation is warning,
deterministic injection preserves ERR, flux ratio is finite, and every result
has native-clean/target-clean/target-real receipts.

- [x] **Step 5: Commit the single-object scientific path**

```bash
git add JWST_artificial_redshifting_general.ipynb
git commit -m "feat: add validated self-contained redshifting workflow"
```

### Task 4: Implement restart-safe optional batch execution inside the notebook

**Files:**
- Modify: `JWST_artificial_redshifting_general.ipynb`

**Interfaces:**
- Produces: `atomic_write_json`, `load_valid_checkpoints`, `case_should_run`, and `run_batch(config) -> pandas.DataFrame`.
- Consumes: `run_single`, `PipelineFailure`, and normalized immutable configuration.

- [x] **Step 1: Add a failing status/resume self-test**

```python
assert case_should_run({"status": "OK"}, force_ids=set()) is False
assert case_should_run({"status": "TERMINAL_ERROR"}, force_ids=set()) is False
assert case_should_run({"status": "RETRYABLE_ERROR"}, force_ids=set()) is True
assert case_should_run({"status": "OK"}, force_ids={"42"}) is True
```

- [x] **Step 2: Run the status test before batch helpers exist**

Run: execute the test cell before implementation.

Expected: `NameError`.

- [x] **Step 3: Implement atomic, idempotent receipts**

```python
def atomic_write_json(path, row):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(row, indent=2, sort_keys=True))
    os.replace(tmp, path)

def case_should_run(existing, force_ids):
    return existing is None or existing["status"] == "RETRYABLE_ERROR" or existing["case_id"] in force_ids
```

Write a manifest, frozen config, software provenance, append-only log, one
receipt per case, and a merged summary with unique case IDs. Classify invalid
inputs and unsupported wavelengths as terminal; interruptions and optimizer
exceptions as retryable. Preserve already valid receipts and prevent a second
row for an existing valid case.

- [x] **Step 4: Run batch resume self-tests with temporary output**

Run: execute three cases twice: one `OK`, one `TERMINAL_ERROR`, and one
`RETRYABLE_ERROR`; then repeat with `FORCE_RERUN_IDS={"ok_case"}`.

Expected: only retryable runs on normal resume, forced OK reruns once with
supersession provenance, summary has one current row per case, and all JSON
receipts parse.

- [x] **Step 5: Commit restart-safe batch mode**

```bash
git add JWST_artificial_redshifting_general.ipynb
git commit -m "feat: add restart-safe batch receipts to public notebook"
```

### Task 5: Execute release validation and publish compact evidence

**Files:**
- Modify: `JWST_artificial_redshifting_general.ipynb`
- Create: `data/validation/jwst_artificial_redshifting_notebook_demo_receipt.json`
- Create: `data/validation/jwst_artificial_redshifting_notebook_negative_tests.json`
- Create: `data/validation/jwst_artificial_redshifting_gold403_regression_receipt.json`
- Modify: `README_JWST_artificial_redshifting.md`
- Modify: `docs/JWST_ARTIFICIAL_REDSHIFTING_METHOD_AND_LIMITATIONS.md`

**Interfaces:**
- Consumes: all notebook execution cells.
- Produces: reproducible self-contained execution evidence and documented limits.

- [x] **Step 1: Create a fresh-kernel demo execution test**

```python
client = NotebookClient(nb, timeout=900, kernel_name="python3")
client.execute(cwd=tempdir)
assert (Path(tempdir) / "JWST_redshifting_demo_output" / "result.json").exists()
```

- [x] **Step 2: Run it before final demo wiring and verify an expected failure**

Run: `jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=900 JWST_artificial_redshifting_general.ipynb --output /tmp/jwst-demo-pre.ipynb`

Expected: non-zero before demo rendering/recovery/output wiring exists.

- [x] **Step 3: Complete demo, tests, and documentation**

Build demo FITS/PSF in its output directory with Lenstronomy, run the known
truth render/recovery sequence, write all plots/JSON/CSV/provenance there,
and add a test mode for invalid path, missing ERR, invalid PSF, unsupported
wavelength, and no double background noise. Run a documented one-object
GOLD403 regression only while production remains paused or completed, using
private paths only in the external validation invocation and never in the
published notebook.

- [x] **Step 4: Execute release gates and record exact results**

Run: `jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=900 JWST_artificial_redshifting_general.ipynb --output /tmp/JWST_artificial_redshifting_general.executed.ipynb`

Expected: fresh-kernel demo succeeds; every output is under demo `OUTPUT_DIR`;
static scan finds no private path/module; negative tests yield actionable
statuses; the external GOLD403 comparison is within its documented tolerance
or is recorded as a release blocker.

- [x] **Step 5: Commit, verify, and push the validated release**

```bash
git add JWST_artificial_redshifting_general.ipynb README_JWST_artificial_redshifting.md requirements-jwst-artificial-redshifting.txt docs/JWST_FIELD_ADAPTATION_CHECKLIST.md docs/JWST_ARTIFICIAL_REDSHIFTING_METHOD_AND_LIMITATIONS.md data/validation/jwst_artificial_redshifting_*
git commit -m "feat: release portable JWST artificial redshifting notebook"
git push origin main
```

## Self-review

Spec coverage is complete: Tasks 1--2 implement the one-file UX, separated
source/target products, package guidance, inputs, PSF, provenance, and public
documentation; Task 3 implements cosmology, Fnu/SED, validated rendering,
noise and quality diagnostics; Task 4 implements the requested status and
resume behavior; Task 5 covers fresh-kernel, negative, and external GOLD403
regression gates. No production process is modified by any task. The five
review-focus failure modes are pinned to Tasks 2--5. The interface names in
later tasks are defined by the producer tasks. A scan for `TODO`, `TBD`, and
`implement later` finds no placeholders.
