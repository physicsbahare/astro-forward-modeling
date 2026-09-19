# Representative clean identifiability/resolution sweep

The restart-safe clean sweep completed all **31** frozen IDs: 31 `OK`, zero ERROR rows, zero parameter-bound hits, and four recorded Galight fits per object (native B+D/single and z=3 B+D/single). The checkpoint CSV, run log, selection manifest, and provenance agreed exactly.

The compact receipt is [GOLD403_clean_sweep_31_2026-09-19.csv](../data/validation/GOLD403_clean_sweep_31_2026-09-19.csv). Full local tables, fit metadata, plot, and provenance remain with the science output and are not placed in Git.

| Outcome | Count |
| --- | ---: |
| Native and z=3 B/T identifiable | 30/31 |
| Stable native-to-z=3 classification | 29/31 |
| Identifiable resolution-boundary classification flip | 1/31 (514739) |
| B/T non-identifiable/classification unusable | 1/31 (751217) |
| Fit failures / bound-hit objects | 0 / 0 |

751217 is the sole B/T outlier: native |ΔB/T|=0.1246 and z=3 |ΔB/T|=0.3090, compared with next-largest values 0.0287 and 0.0297. Its z=3 disk/bulge $R_e$/PSF values are 0.0866/0.0168; the next sampled disk value is 0.4585. Fixed-input PSO repeats already showed multiple low-χ² solutions for this object. The sweep confirms that this is a structural non-identifiability regime, but the gap in sampled resolution means it cannot establish a general hard component-size exclusion threshold.

The existing 0.10 recovery-error flag is therefore retained as a high-confidence *operational* B/T non-identifiability flag for this configuration, now supported by an observed separation rather than adopted blindly. Continuous errors and resolution diagnostics remain mandatory. A z=3 B/T may be physically interpreted only if the native-clean baseline is identifiable as well. Good χ²/bounds remain convergence diagnostics, not identifiability proof.

514739 crosses the single-Sersic classification boundary through a resolution effect (native n=2.636 to z=3 n=2.452) while B/T remains identifiable. This has a distinct `IDENTIFIABLE_RESOLUTION_FLIP` status and must not be counted as fit failure or B/T non-identifiability.

Seven objects have |published n − native-clean n| > 0.5, which reinforces the required comparison chain: published → native clean is representation mismatch; native clean → z=3 clean is the resolution/redshift term. The clean gate is complete at representative-sweep scope. The next gate is the small corrected real-background E0/E1J pilot, compared against z=3-clean rather than the catalog.
