# GOLD403 Restartable Clean-Sweep Design

## Purpose

Make the validated clean native-clean -> z=3-clean sweep safe to resume after
a notebook, kernel, or process failure without rerunning valid successful
objects or losing failures.

## Boundary

This change wraps the existing validated notebook integration functions. It
does not change the Lenstronomy/Galight renderer, fitting settings, PSF
treatment, sample definition, or scientific tolerance. It is for future runs;
the in-flight notebook run remains an immutable execution record.

## Design

`run_clean_identifiability_sweep` will accept a run directory and maintain an
atomic aggregate CSV checkpoint after every object. It will maintain a JSON
provenance receipt and append-only run log. On startup it validates completed
rows, skips valid IDs, retains `ERROR` rows, and allows `force_ids` to replace
only explicitly requested IDs. The return frame is deterministic and has one
row per requested object.

The runner will capture fit diagnostics already exposed by the validated
helpers, including chi-square and a conservative parameter-bound proximity
flag when fit-result bounds can be inspected. If a bound cannot be inspected,
the field is null rather than inferred.

## Verification

Static tests will exercise atomic write, resume/skip, forced rerun, malformed
checkpoint rejection, error-row retention, and provenance creation using
injected lightweight runners. The science-environment integration remains a
separate gated computation after the current sweep receipt is validated.
