# GOLD403 Restartable Sweep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a restart-safe wrapper for the validated GOLD403 clean sweep.

**Architecture:** Keep all scientific fitting in the existing helper and add
small persistence utilities plus a runner that calls it one object at a time.
Aggregate CSV updates use same-directory atomic replacement; JSON provenance
and an append-only log make partial progress inspectable.

**Tech Stack:** Python 3.11, pandas, pytest; Galight/Lenstronomy only through
the existing notebook integration functions.

**Spec:** `docs/superpowers/specs/2026-09-19-gold403-restartable-sweep-design.md`

## Global Constraints

- Do not alter validated rendering, PSF, fit, or tolerance conventions.
- Preserve `ERROR` rows and never silently drop failed IDs.
- Resume only rows that pass structural validation; forced IDs replace only
  their own prior row.
- Do not add local science data to Git.

## Review Focus

- Interrupted atomic writes must not leave an accepted malformed CSV.
- A valid `ERROR` row must be considered completed on resume.
- Forced IDs must not duplicate rows.
- Provenance must identify configuration and software, not just output paths.
- Missing bound information must stay unknown rather than become false.

### Task 1: Persistence primitives

**Files:**
- Create: `scripts/gold403_restartable_sweep.py`
- Create: `tests/test_gold403_restartable_sweep.py`

- [ ] Write failing tests for atomic CSV persistence and structural checkpoint validation.
- [ ] Run the focused tests and confirm expected failures.
- [ ] Implement the minimal persistence primitives.
- [ ] Run focused tests and confirm they pass.

### Task 2: Resume-aware sweep coordinator

**Files:**
- Modify: `scripts/gold403_restartable_sweep.py`
- Modify: `tests/test_gold403_restartable_sweep.py`

- [ ] Write failing tests for successful-row skip, `ERROR`-row skip, forced rerun, and provenance/log creation.
- [ ] Run focused tests and confirm expected failures.
- [ ] Implement the coordinator with injected object runner/ID selector.
- [ ] Run focused tests and confirm they pass.

### Task 3: Notebook integration and documentation

**Files:**
- Modify: `scripts/gold403_validation_notebook_cells.py`
- Modify: `docs/RUNBOOK.md`
- Modify: `docs/NEXT_GATES.md`
- Modify: `tests/test_gold403_validation_helpers.py`

- [ ] Write failing static integration tests for the new restart-safe entry point.
- [ ] Implement the thin notebook-facing integration without changing scientific functions.
- [ ] Run all applicable focused tests and the helper syntax check.
- [ ] Document usage, provenance, and restart behavior.
