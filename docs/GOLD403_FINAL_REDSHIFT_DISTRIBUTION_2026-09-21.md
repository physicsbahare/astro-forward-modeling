# Final GOLD403 redshift distribution — 2026-09-21

This is a lightweight catalog receipt, separate from the artificial-redshifting
production. It uses **only**
`Data/passive_disk_GOLD403_with_visual_flags.csv`: the final 403 unique-ID
GOLD403 catalog. The earlier 1,163/1,158 parent-candidate sample is neither
read nor used as a denominator.

## Result and predeclared choice rule

The most-populated fixed narrow bin is **0.75 <= z < 1.00 (Δz = 0.25),
N = 91**. Its median redshift is 0.8684 and its complete log-stellar-mass
distribution has median 9.872, with 16th--84th percentiles [9.597, 10.593].

The broad fixed-bin maximum is 0.50 <= z < 1.00 (Δz = 0.50), N = 170.

For an initial narrow-bin population analysis, the selected 0.75 <= z < 1.00
interval was chosen by a rule set before examining any morphology or
artificial-redshifting outcome: among Δz = 0.25 bins with N >= 20 and complete
or at least 90% stellar-mass coverage, select the highest N (then lower z if
tied). It has 100% mass coverage; no result-dependent optimization was used.

## Exact counts

| Fixed interval | N |
|---|---:|
| 0.00 <= z < 0.25 | 15 |
| 0.25 <= z < 0.50 | 57 |
| 0.50 <= z < 0.75 | 79 |
| 0.75 <= z < 1.00 | 91 |
| 1.00 <= z < 1.25 | 54 |
| 1.25 <= z < 1.50 | 27 |
| 1.50 <= z < 1.75 | 37 |
| 1.75 <= z < 2.00 | 17 |
| 2.00 <= z < 2.25 | 12 |
| 2.25 <= z < 2.50 | 4 |
| 2.50 <= z < 2.75 | 7 |
| 2.75 <= z < 3.00 | 3 |

For Δz = 0.50, the counts are 72, 170, 81, 54, 16, and 10 in the consecutive
intervals [0.00, 0.50), ..., [2.50, 3.00), respectively.

## Scope notes

- `logM` is complete for all 403 rows. No rest-frame luminosity column exists
  in this final catalog, so the saved tables use complete observed
  `mag_model_f444w` AB magnitude as a brightness diagnostic, not as a
  rest-frame luminosity or a completeness limit.
- Direct catalog fields `known_xray_agn` and `verified_xray_agn` are present
  for every row and both are false for all 403. Per-bin reported AGN count is
  consequently 0, but this is selection-censored and is not an estimate of
  the field AGN incidence.
- No documented per-object tracer-density estimate exists in the final catalog
  or current compact local products. A schema inventory finds `group_id` in a
  master catalog, but it is not a calibrated density measurement; environment
  density coverage is therefore reported as 0 rather than inferred from the
  selected objects.

## Reproduction and outputs

Run:

```bash
python scripts/analyze_final_gold403_redshift_distribution.py \
  --input /path/to/passive_disk_GOLD403_with_visual_flags.csv \
  --outdir /path/to/catalog_science_GOLD403/final_redshift_distribution
```

The validated local run is in
`Data/catalog_science_GOLD403/final_redshift_distribution_20260921/` and
contains the compact bin table, selected-bin membership table, provenance JSON,
interpretation, and four requested PNG diagnostics.
