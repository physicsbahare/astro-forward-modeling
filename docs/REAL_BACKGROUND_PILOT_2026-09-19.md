# GOLD403 corrected real-background pilot — 2026-09-19

The compact receipt is [GOLD403_real_background_pilot_2026-09-19.csv](../data/validation/GOLD403_real_background_pilot_2026-09-19.csv). Full local fit records, diagnostics, provenance, and plots remain in the local science-output receipt.

## Result

The restart-safe nine-case pilot passed technically: **9/9 OK**, no bound hits, and four recorded Galight fits per case (z=3-clean B+D/single and z=3-real B+D/single). The cases cover IDs 751217 (known B/T-non-identifiable), 514739 (identifiable n-boundary case), and 162363 (stable control), with F277W E0 and F444W E0/E1J.

- Exact Lenstronomy B+D truth was scaled radiometrically and deterministically added to the existing real SCI; the real ERR and segmentation arrays were retained. No independent sky/background or source-noise realization was added.
- Maximum fractional stamp-flux error was `2.22e-16`.
- Every injection centre had positive finite real ERR and context valid-ERR fractions were at least `0.999986`.
- Position-dependent signed PSFEx remained un-clipped. Context recovery explicitly modelled 0–2 segmented neighbours.
- Empirical S/N spans 14.6–217.1. The low-S/N F277W 162363 context becomes a clean-to-real n-classification flip; this is retained as contextual degradation rather than discarded.
- The F277W 751217 flip remains scientifically non-interpretable in B/T because the clean gate established that its native decomposition is non-identifiable. ID 514739 remains classification-stable in all pilot real contexts.

The appropriate real-context comparison is strictly **z=3 clean -> z=3 real**, not published catalog -> real injection.

## Gate decision

Gate 2 is **PASS** for the corrected renderer/context implementation. The production receipt must retain clean-to-real deltas, empirical S/N, ERR quality, neighbour/crowding metadata, fit convergence/bound hits, and the clean-gate B/T identifiability policy.
