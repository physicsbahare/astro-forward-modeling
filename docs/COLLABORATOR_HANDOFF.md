# Collaborator handoff — passive-disk forward modeling

This note is the compact entry point for collaborators adapting the COSMOS-Web pipeline to another JWST field such as JADES or SMILES.

## Scientific structure to preserve

Do not derive both morphology diagnostics from one synthetic representation.

Use two independent branches:

- **single-Sersic branch** for n;
- **bulge+disk branch** for B/T.

At each stage, combine the two only after each branch passes its own validity/QC checks.

The disk criterion currently used by the project is:

```
n < 2.5 and B/T < 0.5
```

## Active code

The main reusable integration helpers are in:

```
scripts/gold403_validation_notebook_cells.py
```

The 2026-10-01 update adds the corrected two-branch clean recovery API and a restart-safe subset runner.

The real-context machinery is documented by:

```
scripts/run_gold403_real_background_pilot.py
docs/PASSIVE_DISK_Z3_METHOD.md
docs/CORRECTED_TWO_BRANCH_PILOT_2026-10-01.md
```

The old real-background runner used an exact B+D truth source and fitted both single-Sersic and B+D models to that same source. Its B/T branch remains useful, but its single-Sersic n branch must not be used as the final single-Sersic transfer measurement.

## Survey-specific pieces to replace for JADES/SMILES

A collaborator should keep the structural logic but replace the COSMOS-Web-specific adapters:

- source/target image inventory;
- WCS lookup;
- PSF model/evaluation;
- real SCI/ERR/weight products;
- segmentation/deblending products;
- context-selection logic;
- photometric flux transfer and filter curves.

The source rendering and recovery logic should remain survey-independent where possible.

## Luminosity

Use the no-intrinsic-evolution E0 branch as the primary observational-transfer baseline.

Do not use the current BAGPIPES experiment as a per-galaxy physical backward-luminosity correction. The inferred z=3 luminosity was too dependent on the assumed SFH family.

A simple brightening branch may be retained only as a transparent S/N sensitivity test.

## Data note

Large COSMOS-Web mosaics and local catalog/cutout products are intentionally not committed to this repository. A collaborator needs their own survey data bundle and should configure paths outside the library code.
