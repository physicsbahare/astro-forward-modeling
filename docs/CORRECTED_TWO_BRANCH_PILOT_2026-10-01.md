# Corrected two-branch GOLD403 pilot — 2026-10-01

## Why this correction was needed

The earlier production rendered an exact B+D truth image and recovered both B/T and a single-Sersic n from that same B+D image. That is valid for the B/T branch, but it is not a closed-loop test of the catalog single-Sersic n: a single-Sersic fit to a two-component B+D image is a different parameterization.

The corrected structural transfer therefore keeps two independent branches:

1. **n branch:** catalog single-Sersic model -> single-Sersic truth -> single-Sersic recovery
2. **B/T branch:** catalog B+D model -> B+D truth -> B+D recovery

A disk classification is constructed only after both branch measurements are valid:

```
disk = (single_sersic_n < 2.5) and (B/T < 0.5)
```

Native-clean failures are representation/recovery failures and must not be counted as redshift-induced morphology loss.

## Pilot design

The corrective pilot contains 30 objects:

- 15 objects that the earlier B+D -> single-Sersic pathway labeled representation-unstable;
- 15 matched representation-stable controls.

Matching used source redshift, stellar mass, forward-input single-Sersic n, and forward-input B/T.

The pilot ran four clean fits per object:

- native single-Sersic branch;
- native B+D branch;
- z=3-clean single-Sersic branch;
- z=3-clean B+D branch.

The native recovery gates were frozen at:

- |delta n| <= 0.50
- |delta B/T| <= 0.10

The pilot gate required at least 90% of successful cases to pass the n, B/T, and joint native gates.

## Result

All 30 objects completed successfully.

| Quantity | Result |
|---|---:|
| Successful cases | 30 / 30 |
| Native n pass fraction | 1.000 |
| Native B/T pass fraction | 1.000 |
| Joint native pass fraction | 1.000 |
| Median native |delta n| | 8.65e-4 |
| Median native |delta B/T| | 8.76e-3 |
| Pilot gate | **PASS** |

The objects previously labeled representation-unstable recover at least as well as the matched controls under the corrected branch definition:

| Pilot group | N | median native |delta n| | median native |delta B/T| | native valid fraction |
|---|---:|---:|---:|---:|
| Matched stable controls | 15 | 1.28e-3 | 6.97e-3 | 1.000 |
| Previously representation-unstable | 15 | 5.12e-4 | 8.89e-3 | 1.000 |

This directly demonstrates that the earlier large native n offsets were caused by comparing different structural representations, not by a generic Galight failure.

## Classification result in the pilot

Using the corrected two-branch measurements:

- 28/30 are valid native-clean disks;
- 2/30 lie just across the B/T=0.5 boundary in the recovered native B+D fit;
- the same 28/30 are disks at z=3-clean;
- **0/30 cases change disk class between corrected native-clean and z=3-clean**.

The two native non-disks are boundary cases rather than catastrophic failures:

- ID 289242: input B/T = 0.4961, recovered native B/T = 0.5014;
- ID 463518: input B/T = 0.49985, recovered native B/T = 0.5087.

They remain non-disks at z=3-clean, so they are not redshift-induced losses.

## Consequence for the historical 806-case run

The completed 403 x 2 (E0/E1J) production is retained as important pipeline/provenance history, but its **single-Sersic n and combined disk-classification products are not final science products**, because the n values were recovered from B+D truth images.

The historical B+D branch is not automatically discarded. Its B/T fits used exact Lenstronomy B+D truth and can potentially be reused after a provenance/configuration match confirms that the context, PSF, truth model, and fitting configuration are identical to the corrected B/T branch.

Therefore the efficient correction path is:

1. preserve the historical B+D products;
2. rerun the single-Sersic branch with single-Sersic truth;
3. combine n and B/T only after branch-specific validity checks.

## GOLD91 next gate

For the next science-facing run, use the predeclared most-populated narrow redshift bin:

```
0.75 <= z < 1.00
N = 91
```

This is the GOLD91 bin already frozen in `GOLD403_FINAL_REDSHIFT_DISTRIBUTION_2026-09-21.md`.

A band audit of these 91 objects gives:

- original selection band F115W: 91/91;
- forward morphology band changes for 90/91 objects;
- mapped forward bands: F150W for 82, F277W for 8, one invalid;
- among 90 valid forward-band measurements, 88 remain disk-like and 2 are non-disks.

Thus the band mapping must still be reported as a separate morphological K-correction/sample-definition stage, but it does not dominate the GOLD91 classification count.

## Luminosity policy

For the clean native -> z=3 structural gate, no per-galaxy luminosity-evolution correction is required. A fixed high-S/N normalization is appropriate because this stage measures representation, resolution, and PSF effects.

For the later real-background observability stage:

- **E0 remains the primary branch**: cosmological/radiometric transfer with no intrinsic luminosity evolution;
- no BAGPIPES per-galaxy backward luminosity correction is adopted;
- E1J may be retained only as an optional brightness/S/N sensitivity test, not as the primary result.

## Machine-readable receipts

- `data/validation/GOLD403_two_branch_pilot_receipt_2026-10-01.json`
- `data/validation/GOLD403_two_branch_group_summary_2026-10-01.csv`
- `data/validation/GOLD403_two_branch_pilot_results_2026-10-01.csv`
