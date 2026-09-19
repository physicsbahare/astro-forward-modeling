# Gate D1c — real COSMOS-Web context audit

Frozen before any injection/recovery result is inspected.

## Purpose

Use the successfully acquired COSMOS-Web DR1 F444W 30 mas A1 real cutout to quantify whether the field has valid coverage and realistic nonblank context before choosing injection positions. This is still pre-injection evidence: workflow success is not scientific success, and this stage does not close Gate D.

## Input

The exact GitHub Actions artifact from real-cutout run `33941326833`, containing the checksummed 512x512 SCI/ERR/WHT bundle centered on COSMOS2025 ID 4204. The bundle SHA-256 is `764d542f2417810c904bce711455b3eb69c70cf388f97348cb857b056b2dd66d`.

## Frozen diagnostics

1. Require all SCI/ERR/WHT pixels finite and all ERR/WHT pixels strictly positive; failures remain observable hard failures.
2. Estimate a robust SCI background using the median and MAD after iterative 3-sigma clipping; no background is subtracted from the stored data.
3. Form a diagnostic significance image `(SCI - robust_background) / ERR` only for context characterization.
4. Define source-like diagnostic pixels as significance > 5. This is not a production segmentation threshold and is not used to hide difficult regions.
5. Label connected source-like islands with 8-connectivity; report island count, source-pixel occupancy, and distance-to-nearest-source distribution over the field.
6. Quantify ERR and WHT spatial variation by robust percentiles. Do not renormalize or alter either plane.
7. Produce deterministic candidate placement classes from the measured distance map: near-source (2-5 px), intermediate (8-20 px), and relatively isolated (>=30 px). These classes are diagnostic only; the next injection experiment must retain a spread of crowding regimes rather than choosing only the easiest class.

## Interpretation

A green workflow means the real cutout can be characterized reproducibly and has valid coverage. It does not mean morphology recovery is successful. The next scientific decision is whether the measured context is suitable for a first L1 injection matrix and, if so, to freeze placements across multiple crowding classes before running recovery.
