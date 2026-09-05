# C6b: matched-PSF noiseless common-scene AstroPhot/Imfit diagnostic

Frozen 2026-09-04 UTC after C6a run `33849387267` completed/success and its signed-PSF convention artifact was audited. C6b is a diagnostic comparison, not a production acceptance test.

## Scientific question

On the exact clean C5o `n=1` matched-PSF scenes for which the archived Imfit 1.9.0 shard completed cleanly, does pinned AstroPhot 0.18.0 recover a comparable host+nucleus solution, or do renderer/parameterization/optimizer differences move the inferred morphology even before PSF mismatch or noise is introduced?

This stage isolates fitting implementation from PSF-construction mismatch. It must not introduce target noise, a wrong PSF, the unresolved C5o `n=4` optimizer path, or a new recovery tolerance.

## Frozen inputs

Reuse artifact `agn-imfit-free-shape-n1` from C5o workflow run `33819349854`, artifact id `9917787955`, SHA-256 `4d168eb8f26c7be0b2906cd659c12d99ae327b4ef3f2aabfb19422e35094d74b`.

Use exactly four archived scenes:

- module A, AGN/host = 1;
- module A, AGN/host = 10;
- module B, AGN/host = 1;
- module B, AGN/host = 10.

All have host truth `n=1`, `Re=16` pixels, `q=0.6`, physical PA 45 degrees, host total flux 1, fixed coincident host/nucleus center, zero background and zero noise. The exact signed module PSF is matched to each scene and negative samples are preserved.

C5o's clean n=1 Imfit winners are archived rather than rerun. The C5o workflow as a whole failed because the separate n=4 shard timed out; that does not invalidate the explicit n=1 job success and artifact used here.

## AstroPhot environment and parameterization

- AstroPhot `0.18.0`, source tag commit `b20c98b4acba4b9708938610e61aced60f205620`;
- CPU PyTorch `2.14.0+cpu`, Python 3.12;
- 201 x 201 `TargetImage`, unit variance, one arcsec/pixel numerical scale, `crpix=(100,100)`;
- `sersic galaxy model` + `point model` inside a `group model`;
- centers fixed at tangent-plane `(0,0)`;
- same C5o physical shape limits where the parameterization permits: `0.5<n<6`, `0.5<Re<60`, `0.15<q<1`;
- point flux constrained nonnegative with the same numerical ceiling `1e6`;
- AstroPhot PA is its native cyclic East-of-North angle on `(0,pi)`. The C5o Imfit interval `[-180,180]` is therefore not copied numerically; physical equivalence modulo 180 degrees is audited instead;
- AstroPhot uses `Ie`, not total host flux, as the Sérsic amplitude. Initial desired host total flux is mapped analytically to `Ie`; no false claim of an Imfit-equivalent host-amplitude ceiling is made.

The empirical PSF is supplied with its archived signed sum. It is not clipped and is not manually renormalized. Input PSF sum and rendered component sums are recorded because native normalization semantics are part of this cross-code diagnostic.

## Coordinate/convention prefit audit

Before optimization, render the truth morphology at AstroPhot PA = 45 degrees and PA = 135 degrees for every case. Sum the four truth-state SSE values for each orientation and choose the lower-SSE mapping only as a coordinate-convention audit fixed by the data geometry:

- if 45 degrees wins: `PA_astrophot = (-PA_imfit) mod 180`;
- if 135 degrees wins: `PA_astrophot = PA_imfit mod 180`.

Both candidate truth-state renderings and SSE values are preserved. This is not a fitted recovery degree of freedom and creates no post-hoc acceptance band. The exact 0-degree displaced start is represented by a fixed `1e-10` radian interior offset because AstroPhot's cyclic PA endpoints are non-inclusive; this numerical representability offset is recorded.

## Starts and objective

Reuse the three C5o starts without changing morphology or flux intent:

- truth: `q=.6, n=1, Re=16, host flux=1, point fraction=1`;
- compact: `q=.8, n=2, Re=8, host flux=.5, point fraction=.8`;
- extended: `q=.3, n=5, Re=30, host flux=1.5, point fraction=1.2`.

Use AstroPhot LM with its pinned implementation, `max_iter=100` and `relative_tolerance=1e-5`. The objective is the same full-stamp unit-weight Gaussian least-squares problem. Optimizer success, immobility, maximum-iteration exit, singular covariance warnings and bound proximity are recorded as observables; none are converted into an artificial pass by changing limits or tolerances.

## Required outputs

For every case and start, record runtime, optimizer message/loss history, fitted `PA,q,n,Re,Ie`, point parameter flux, rendered host and point sums, recomputed pixel SSE, residual L1/data L1, bound proximity, and complete data/model/residual/host/point arrays. Record SHA-256 hashes of all seven C5o input FITS files.

Winner selection is the minimum finite recomputed SSE per case, independent of the optimizer's success label. Compare each AstroPhot winner to the archived Imfit C5o winner in `n`, `Re`, `q`, physically mapped PA, point parameter, rendered component fluxes and SSE. No recovery band is declared in C6b.

## Execution/audit rule

C6b execution is complete only if all 12 attempts are recorded, both PA truth-state convention renders are finite for all four cases, at least one finite fit exists per case, winner selection is reproducible from saved metrics, input hashes are complete, and saved residual algebra closes against the archived data arrays. A scientific disagreement, bound approach or optimizer non-success remains a result, not a CI reason to loosen the experiment.

C6b does not establish photon readiness, wrong-PSF robustness, noisy recovery, literal Dewsnap reproduction, survey readiness or production acceptance. Its next decision is whether a clean common-scene baseline exists before C6c tests PSF construction/mismatch.