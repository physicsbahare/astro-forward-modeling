# Controlled z=3 recovery diagnostic

This recovery gate was run after the interrupted clean sweep produced a materially different z=3 result for ID 751217. The source notebook was not changed. Each result has an independent local JSON receipt containing the frozen truth-image and PSF hashes, selected context, starts, bounds, Galight/Lenstronomy versions, and requested NumPy/Python seed.

The compact version-controlled receipt is [GOLD403_controlled_z3_recovery_2026-09-19.csv](../data/validation/GOLD403_controlled_z3_recovery_2026-09-19.csv).

| ID | repeats | z=3 single-n range | z=3 B/T range | class result | bounds |
| --- | ---: | ---: | ---: | --- | --- |
| 751217 | 5 | 1.8156–4.1848 | 0.1333–0.7669 | 1 disk, 4 non-disk | one lower-size hit |
| 322095 | 2 | 1.4310–1.4348 | 0.3033–0.3055 | disk in both | none |
| 162363 | 2 | 1.0504–1.0508 | 0.0097–0.0138 | disk in both | none |

All nine fits were `OK`, finite, and unique. The 751217 runs held truth construction, context/target PSF, bounds, and initial parameters fixed; only the requested PSO seed varied. Their similarly low reduced chi-squares nevertheless yield incompatible B/T and classifications. This establishes z=3 structural non-identifiability for that compact case, rather than a deterministic pipeline discrepancy. The earlier validated `n=8.7976`, `B/T=0.0924` is an additional optimizer-accessible solution, not a privileged physical value.

322095 and 162363 reproduce stable n and classification. The small B/T changes relative to the prior receipt do not affect their interpretation. This gate therefore supports keeping B/T and classification identifiability as explicit fields, but it does not justify a final numeric warning threshold: the representative 31-object clean sweep is required for that decision.
