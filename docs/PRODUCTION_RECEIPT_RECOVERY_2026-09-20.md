# GOLD403 production receipt recovery — 2026-09-20

The restart-safe F444W E0/E1J production receipt was paused after the first
142 cases to investigate two strict-JSON serialization failures. The source
rendering, real-SCI injection, real ERR use, signed position-dependent PSFEx,
and Galight fitting path were unchanged.

## Root cause and correction

Cases 78 (ID 144050, E0) and 113 (ID 244474, E0) completed their fits but had
non-positive total real-background B+D model flux. Their recovered B/T and
clean-to-real B/T difference are therefore undefined (`NaN`); this is a
nonphysical B+D decomposition, not a finite B/T measurement. Strict JSON
rightly refused to serialize `NaN`, but the old runner lost the completed
per-case metadata while recording the generic exception.

The corrected runner now:

- writes the full per-case row atomically;
- records `status=ERROR` and `NONFINITE_OUTPUT_FIELDS`;
- leaves undefined B/T-derived fields blank;
- clears the derived real disk class and clean-to-real class-flip flag; and
- retains finite single-Sersic, chi-square, S/N, neighbour, context, native,
  and clean-stage diagnostics.

It does not coerce undefined B/T to zero, does not assign a morphology class,
and does not alter the frozen scientific configuration.

## Controlled validation

The two affected cases were rerun independently with identical frozen truth,
context/PSF, bounds, two-repeat PSO convention, and deterministic case seed.
Both reproduced the same scientific failure state and generated complete,
strict-JSON-safe receipt rows. The compact receipt is
`data/validation/GOLD403_production_nonphysical_bt_receipt_2026-09-20.csv`.

The restart utility also gained a `--stop-after-forced` control. It prevents a
diagnostic rerun from advancing into later incomplete production cases.

## Resume decision

The checkpoint contained 142 unique readable rows: 140 `OK`, the two
structured nonphysical-B/T `ERROR` rows above, no duplicates, and no malformed
rows. Cases 143–806 remain pending. Resume normally without forcing case IDs;
the runner skips all 142 existing rows, including the preserved ERROR rows.
