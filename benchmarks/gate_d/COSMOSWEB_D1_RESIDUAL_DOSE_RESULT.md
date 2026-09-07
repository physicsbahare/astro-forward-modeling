# COSMOS-Web Gate D1n-h — residual-dose causal audit result

## Immutable execution receipt

Workflow: `gate-d-cosmosweb-residual-dose`

Confirmed GitHub Actions run: `34008699437`

- status: `completed`
- conclusion: `success`
- head SHA: `72a6fadda43d5d1c7bff626c870abb1160106714`
- artifact: `gate-d-cosmosweb-residual-dose`
- artifact id: `9981796648`
- artifact SHA256: `f37fcd49bfabedfa06249b43e6ecc7a71362dbc0e4fe2d2db60e4551784f053d`

The dedicated frozen-neighbour, multistart, and residual-dose tests, pinned STPSF-data download, frozen D1d artifact download, residual-dose audit, and artifact upload all completed successfully. Workflow success is not itself a claim of morphology recovery.

## Frozen experiment semantics

D1n-h keeps the exact four D1n-g AB=26 positions, D1m pre-injection neighbour scene, declared STPSF, ERR weighting, exact-support masks, target bounds, planar background, linear loss, TRF optimizer, `x_scale="jac"`, and `max_nfev=500`. It changes only the dose of the already-existing pre-injection residual:

`scene(alpha) = fitted_preinjection_scene + injected_target + alpha * preinjection_residual`

with `alpha = 0, 0.25, 0.5, 0.75, 1`.

`alpha=1` reconstructs the literal D1d injected real-mosaic patch. `alpha=0` and intermediate doses are synthetic diagnostic compositions and are not literal survey reproductions. No new noise is added, ERR/WHT are unchanged, no extra Tolman factor is applied, and no PSF sharpening or matching kernel is constructed.

## Machine-readable scientific result

The artifact contains 20/20 finite optimizer-successful fits and no target-bound hits. The two previously catastrophic positions show a strong, smooth dose response, whereas their matched controls remain much more stable.

### Near-source catastrophic position `(168, 66)`

- `alpha=0`: Δmag ≈ -0.0042, Re ≈ 0.1789 arcsec, n ≈ 0.987, centroid excursion ≈ 0.009 pix.
- `alpha=0.25`: Δmag ≈ -0.506, Re ≈ 0.3387 arcsec, n ≈ 1.827.
- `alpha=0.50`: Δmag ≈ -0.766, Re ≈ 0.4346 arcsec, n ≈ 2.087.
- `alpha=0.75`: Δmag ≈ -0.959, Re ≈ 0.4834 arcsec, n ≈ 2.194.
- `alpha=1`: Δmag ≈ -1.112, Re ≈ 0.5096 arcsec, n ≈ 2.314, reproducing the D1m catastrophic solution.

### Relatively isolated catastrophic position `(69, 195)`

- `alpha=0`: Δmag ≈ -0.0043, Re ≈ 0.1789 arcsec, n ≈ 0.987, centroid excursion ≈ 0.009 pix.
- `alpha=0.25`: Δmag ≈ -0.506, Re ≈ 0.4248 arcsec, n ≈ 1.636.
- `alpha=0.50`: Δmag ≈ -0.721, Re ≈ 0.4674 arcsec, n ≈ 2.478.
- `alpha=0.75`: Δmag ≈ -0.868, Re ≈ 0.5211 arcsec, n ≈ 2.912.
- `alpha=1`: Δmag ≈ -1.011, Re ≈ 0.6000 arcsec, n ≈ 3.106, centroid excursion ≈ 1.173 pix, reproducing the D1m catastrophic solution.

### Controls

The isolated control remains close to truth from `alpha=0` through `alpha=1`: Δmag changes only from about -0.004 to -0.021 mag and Re from about 0.179 to 0.189 arcsec. The near-source control moves more, but remains non-catastrophic: at `alpha=1`, Δmag ≈ +0.291 mag, Re ≈ 0.183 arcsec, n ≈ 1.424 and centroid excursion ≈ 0.465 pix.

Scalar residual power is not by itself sufficient to identify the failure. For example, the near-source control has a larger weighted pre-injection residual chi-square than the near-source catastrophic location, yet it does not undergo the same catastrophic morphology change.

## Scientific interpretation

D1n-h establishes causal sufficiency for the **location-specific pre-injection model residual** in the two catastrophic D1m cases: removing that residual restores the target almost exactly, and continuously restoring the same residual continuously drives the target toward the observed catastrophic solution. Combined with D1n-f and D1n-g, this rules against PSF-width mismatch alone and optimizer initialization/basin alone as explanations for these failures.

The remaining question is therefore not whether a residual exists, but **which spatial components of the residual are degenerate with the target Sérsic morphology**. A minimal next diagnostic should measure the ERR-weighted projection of each frozen residual onto the local target-model tangent space at the injected truth, after removing the free planar-background subspace. This is a diagnostic of model identifiability, not a new recovery method or a justification for changing bounds or acceptance criteria.

No production framework implementation is authorized by this result.
