# Isolated TOY B/T identifiability — numerical experiment (2026-10-23)

> **NOT A COSMOS-WEB RESULT. NOT A PRODUCTION CALIBRATION.**
> Git branch: `experiment/toy-bt-identifiability-20261023`; directory: `isolated_experiments/2026-10-23_toy_bt_identifiability/`.
> **Nothing was changed in GOLD91/GOLD403 run directories or science results.** The core literature backlog was audited separately on `main`.

## Question and relationship to the science gates

Can two sources with disk Sérsic n=1 + bulge Sérsic n=4 become observationally indistinguishable when their characteristic radii are comparable to or smaller than the PSF, even when the fitting program receives the **true geometry**? What happens when the assumed PSF width is wrong?

This is a **simple linear-amplitude, fixed-geometry toy**. It does NOT diagnose the real pipeline's open free-structure, Lenstronomy supersampling, neighbor-fitting or input-versus-fit rendering gates. Consult [real gate protocol](https://github.com/physicsbahare/astro-forward-modeling/blob/research/gold403-gates-20261011/docs/GOLD403_GATE_RESOLUTION_PROTOCOL_2026-10-11.md) on the existing science branch and [main roadmap](../../docs/PASSIVE_DISK_END_TO_END_ROADMAP_2026-10-19.md). The real numerical receipts supersede this exploratory result.

## Inputs and execution

- All data generated in memory; **no local COSMOS-Web cutouts, catalogs or PSFEx kernels** needed.
- Circular, center-point pixel-sampled n=1 and n=4 Sérsic profiles, normalized within a 64×64 stamp; Gaussian PSF FWHM=2 px; positive amplitudes fitted with linear least squares followed by nonnegative least squares when needed.
- For each of 3 geometries (well resolved, marginal, unresolved), simulate 2 matched-filter template S/N values (30 and 100), 4 true B/T values (0.25, 0.45, 0.55, 0.75), and 400 independent Gaussian-noise realizations per cell. Add 2 PSF-mismatch cells for 26 total cells (10,400 mock noise realizations).
- Frozen random generator seed: **20261023**. No astrophysical source size/PSF scale is inferred from these pixel values.
- Executed with Python, NumPy and SciPy, without external survey datasets; reran from the same seed and verified an **identical output CSV hash**.

### Selected numerical results (fixed true shape and correctly assumed PSF)

Here `wrong class` means fitted B/T crosses 0.5 (disk: <0.5, non-disk: ≥0.5); **not** an observational completeness or contamination fraction.

| Geometry (R_disk,R_bulge in pixels) | S/N | True B/T | Template cosine | Normalized matrix condition | Robust B/T scatter | Wrong-class mock fraction |
|---|---:|---:|---:|---:|---:|---:|
| well resolved (4,1) | 30 | 0.45 | 0.8281 | 3.3 | 0.062 | 0.245 |
| well resolved (4,1) | 100 | 0.45 | 0.8281 | 3.3 | 0.017 | 0.003 |
| marginal (1.4,0.45) | 30 | 0.45 | 0.9855 | 11.7 | 0.192 | 0.413 |
| marginal (1.4,0.45) | 100 | 0.45 | 0.9855 | 11.7 | 0.059 | 0.230 |
| unresolved (0.5,0.15) | 30 | 0.45 | 0.9990 | 44.2 | 0.500 | 0.438 |
| unresolved (0.5,0.15) | 100 | 0.45 | 0.9990 | 44.2 | 0.207 | 0.463 |

Robust scatter = half of (84th minus 16th percentile); fractions are finite Monte Carlo estimates with 400 trials per cell, and should not be reported with spurious precision. Even with nominal S/N=100, an unresolved bulge+disk decomposition can be extremely unstable. **No threshold** on condition number, radius, or cosine is recommended for GOLD403 based on this toy.

### PSF-mismatch diagnostic

Same **well-resolved** truth (PSF FWHM=2 px, true B/T=0.45) at template S/N=100, but fit assumes FWHM 1.8 or 2.2 px.

| Fit FWHM | Median recovered B/T minus 0.45 | Wrong-class mock fraction |
|---|---:|---:|
| 1.8 px | -0.053 | 0.000 |
| 2.2 px | +0.058 | 0.685 |

The direction/magnitude depend strongly on the chosen shapes and pixel sampling. This shows why PSF fidelity must be audited before interpreting recovered light fractions; it is **not** a quantitative uncertainty budget for COSMOS-Web.

## What PASSED and what did NOT

- PASS: generated images are finite and normalized; fitted B/T is in [0,1]; deterministic second run gives bit-identical CSV; 26 designed simulation cells execute.
- NOT TESTED: Galight/Lenstronomy, spatially dependent/signed PSFEx, JWST finite-pixel/ePSF response, correct Sérsic flux-integral convention, nonlinear free n/Re/q/center fitting, source shot noise, realistic backgrounds or neighbors, SFHs, surface-brightness profiles, or disk-observability at z=3.
- NOT PASSED: GOLD403 B/T identifiability, recovered-class confusion, mass/redshift population completeness. Historic GOLD91/403 products remain **unchanged and scientifically conditional**.
- IMPORTANT: fixing the true shapes makes this an *optimistic* identifiability baseline; the real nonlinear task can be harder. The stamp-integral toy normalization is not used to revise the science pipeline's analytic-total-flux convention.

## Reproduce

```bash
python -m pip install numpy scipy
python isolated_experiments/2026-10-23_toy_bt_identifiability/synthetic_bt_identifiability.py --out toy_bt_run
```

Outputs: `toy_results.csv` (all 26 cells) and `manifest.json`, locally in the new output directory. Do **not** point `--out` at any GOLD403/GOLD91 `Results/` directory.

**Integrity of this run:** source script SHA256 `07e1bae0b06141a94ae3aaff382bacb36bf08df6d82c1803dacfbdf2ef587968`; CSV SHA256 `0b180e9591a89cf1fde9e6e1799c53b70b10e1a9135422f4cd3e87593e613516`. Hashes were measured from the isolated execution in this chat and reproducibility check. Different dependency versions may change low-level floating-point output.

## Recommended next steps (when local data available)

1. **Do not rerun production yet.** Review the real free-fit identifiability and renderer issues in `research/gold403-gates-20261011`; retain all failures.
2. Validate the toy diagnostic notion of template overlap using real signed, spatially varying PSFEx kernels and exact Lenstronomy image-model convention, without changing fit truth or source normalization. These require local PSF files and the user environment.
3. Extend to genuinely free structural B/T fits, multiple starts, convergence diagnostics and model-mismatch/neighbor/sky tests. Predeclare a held-out assessment grid and negative controls (non-disk→disk).
4. Estimate both measurability and true-to-measured confusion as functions of S/N, sizes/PSF, B/T, n, wavelength and context, then determine an empirically supported identifiability policy. Keep detected, measurable, and correctly disk-classified denominators distinct.
5. Later separately test multiwavelength fits (IMFIT-MW) and optional spiral-feature injection/recovery (JADES-inspired), not in the same experiment.
