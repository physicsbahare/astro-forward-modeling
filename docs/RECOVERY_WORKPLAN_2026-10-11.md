# Recovery workplan — 2026-10-11

User-authorized autonomous research; one master notebook; no original science
products replaced. Work branch starts at GitHub `fa744a6`. The unrelated local
general-notebook modification is preserved and excluded from commits.

- [x] Fetch all remote heads and inspect relevant methods/history. Only main is
  currently advertised; historical commits remain in the fetched repository.
- [x] Inspect frozen production receipts: actual CSV now has 806 rows. The
  418-row pause receipt is historical, not a resume instruction for new fitting.
- [x] Recover generating GOLD91 notebook in Downloads and existing parent export.
- [x] Reproduce finite-stamp versus integrated-flux B/T convention mismatch.
- [x] Test signed-PSF normalization repair with exact linear closed loops.
- [x] Diagnose high-priority B/T flips using reused Galight functions, independent
  starts, and an existing independent real context; checkpoint every result.
- [x] Audit original parent selection, row joins, photo-z/mass/SFR intervals,
  completeness, morphology eligibility and denominator coverage.
- [x] Produce only supported sample/recovery figures, tables and uncertainty
  intervals; freeze any remaining science gate rather than inventing corrections.
- [x] Append executed sections to the permanent master notebook, preserve its
  existing cells, and save manifests tied to input/code hashes.
- [x] Verify outputs; compact validated methods/receipts prepared for the recovery branch.
  Publication is recorded by the branch push receipt.

Design: reuse the validated Galight/Lenstronomy definitions; add a small local
audit adapter and figure calculations. No new fitting framework. Fixed-shape
linear solutions are diagnostic controls, not claims of free-parameter
identifiability. Pixel ERR errors do not establish independent-pixel statistics
in resampled mosaics. A single z=3 selected-sample transfer cannot calibrate a
full redshift/mass population selection function.
