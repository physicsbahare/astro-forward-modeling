# Gate D1n-g — frozen D1m optimizer-basin / objective-identifiability audit

## Purpose

D1m leaves two catastrophic AB=26 interior solutions despite frozen pre-injection neighbour models. D1n-c shows that no single audited residual/background statistic explains both. D1n-e establishes a real published-vs-STPSF shape difference, but D1n-f shows that this PSF mismatch alone produces only percent-level morphology biases on paired-difference data rather than D1m-like catastrophes.

D1n-g asks one narrower question: **are the catastrophic D1m rows primarily a local-optimizer basin problem, or does the unchanged real-scene D1m objective itself prefer a wrong morphology?**

`scipy.optimize.least_squares` is a local nonlinear least-squares solver: its documented objective is a local minimum subject to bounds. Galaxy-profile fitting guidance likewise treats initialization and unmodelled scene structure as important failure modes rather than reasons to widen constraints. D1n-g therefore changes only the initial target vector and never changes the objective, data, model, bounds, tolerance policy, or optimizer budget.

## Frozen sample

Four AB=26 positions are fixed before execution:

1. near-source index 0, (168,66): catastrophic D1m row, delta-mag about -1.112;
2. relatively-isolated index 1, (69,195): catastrophic D1m row, delta-mag about -1.011;
3. near-source index 1, (379,254): same-class well-recovered control, delta-mag about -0.035;
4. relatively-isolated index 0, (358,97): same-class well-recovered control, delta-mag about -0.012.

No row is dropped after seeing multistart results.

## Frozen starts

Each row uses the same D1m pre-injection fitted/frozen-neighbour scene and the same free planar background. Background initialization is always the D1m median residual seed. Five deterministic target starts are used:

- `d1m_default`: exact D1m target start (AB=27.5 reference amplitude, dx=dy=0, Re=5 pix, n=1.5, q=0.7, PA=0 deg);
- `disk_compact`: AB=27.5 reference amplitude, dx=dy=0, Re=3 pix, n=1.0, q=0.65, PA=30 deg;
- `disk_extended`: AB=27.5 reference amplitude, dx=dy=0, Re=10 pix, n=1.0, q=0.65, PA=30 deg;
- `high_n_extended`: AB=27.5 reference amplitude, dx=dy=0, Re=10 pix, n=3.5, q=0.8, PA=0 deg;
- `injection_truth_oracle`: exact known injected AB=26 target shape/amplitude (Re=6 pix, n=1, q=0.65, PA=30 deg, zero centroid). This start is explicitly injection-only and must never be interpreted as a deployable initialization rule.

All starts lie strictly inside the existing target bounds. No random restart or post-hoc start is permitted.

## Frozen fit semantics

- Reuse D1m's exact D1k/D1l detection/deblending, selected nuisance children, pre-injection nuisance fit on `SCI_ORIG`, exact-support masks, frozen nuisance Sérsic source, declared STPSF, ERR weighting, target renderer, planar background, and target bounds.
- Target optimizer remains `scipy.optimize.least_squares`, method `trf`, loss `linear`, `x_scale="jac"`, `max_nfev=500` for **every** start.
- Do not alter ftol/xtol/gtol defaults, target/nuisance bounds, masks, segmentation, support, PSF, ERR/WHT, or source model.
- Preserve optimizer failures, target-bound hits, nuisance-bound hits, centroid excursions, and all finite/non-finite rows.
- Record for every start: optimizer status/message, nfev, chi-square, reduced-chi-square proxy, recovered magnitude, Re, n, q, PA, dx/dy, centroid excursion and bound hits.
- For each location, rank finite successful starts by raw chi-square only for navigation. Do not create a new scientific acceptance band.
- Record delta-chi-square of each start relative to the lowest finite successful solution and whether the D1m default and injection-truth oracle converge to numerically similar or materially different basins. No threshold is retrospectively tuned; raw parameter distances and objective differences are the evidence.

## Interpretation

- If multiple starts, especially the explicit truth oracle, converge to a truth-like solution with **lower chi-square** than the D1m catastrophic solution, local basin dependence is a major contributor and a future measurement pipeline will need an initialization/global-search policy that is independently validated before production.
- If the catastrophic solution retains lower chi-square than truth-like starts under the identical objective, the problem is principally model/objective identifiability against the real scene rather than a mere optimizer-start failure.
- If different starts produce similarly good objectives but very different morphologies, that is direct evidence of practical non-identifiability and must remain a failure mode.
- Controls are equally important: widespread multistart instability in well-recovered controls would indicate a more general objective pathology.

This is an injection-only diagnostic. It is not a production multistart policy, not a relaxation of convergence criteria, and not authorization to begin framework implementation.
