# GOLD91 gate resolution and corrected GOLD403 continuation

Active local output: `Results/Project_Completion_20261011/corrected_GOLD403_reviewed_v1/`.
All earlier results, failed experiments and master notebook cells are preserved.
The historic 806-case run is complete and is not the corrected two-branch run.

## Verified changes

- Exact Lenstronomy structures are rendered independently of optimizer guesses.
  Requested radii and axis ratios are retained; bounds contain the truth.
  Single-Sérsic and n=1+n=4 truth/recovery families remain separate.
- Integrated B/T uses analytic component fluxes. **Assigned photometry now
  normalizes analytic total flux**, and finite-stamp loss remains in the image.
  The rejected finite-aperture convention could imply 37.6% excess total flux
  for an extended pilot model. Cleaned-scene anchors still have an uncalibrated
  aperture systematic; three homogeneous published B+D-total fallbacks are flagged.
- E0 spectral transfer uses the frozen full-throughput quadratic response operator.
  The narrowest positive three-band passband envelope must cover at least 99%
  of mapped photon response. Negative coefficients are recorded, not clipped.
  Same-filter/same-redshift identity and quadratic integration tests pass.
- Native-clean is a synthetic reference at native angular size, using the same
  mapped structure and source-position PSF of the nearest valid morphology band.
  It is not another measurement of the native galaxy. Target clean/real share
  structural truth and numerical settings. Cosmological transfer is applied once.
- Signed position-dependent PSFEx kernels remain unchanged. Original SCI/ERR/WHT
  products are read-only. No second mosaic-noise realization is added.
- Native SIMPLEX termination, physical ellipticity, B/D center prior, finite
  nonpenalty likelihood, positive target/neighbor flux and bounds are explicit
  checks. Convergence does not establish uniqueness or identifiability.
- Galight removes custom priors when dumping. `restore_saved_prior` restores
  the exact known prior; unknown historic priors are rejected. Six actual saved
  fits passed reload checks without refitting or overwriting their pickles.
- All 395 supported models have frozen contexts. Missing historical assignments
  for 324589 and 752394 use the deterministic first valid same-tile context.
  Context/PSF exceptions become ERROR receipts and existing failures are skipped.
- Raw dependencies include recovered source notebooks, compiled helper code,
  source/context CSVs, catalogs, image cubes, throughputs and PSFs. Numerical
  checkpoints have strict identities. Explicit inheritance verifies identical
  truth/PSF ASTs, raw hashes and geometry, and records original receipt hashes.

## Open gates and interpretation

The seven-object pilot completed 42 stages: 41 OK and one nonphysical component-flux
outcome. All native/clean point errors passed the predeclared accuracy checks.
This does not promote its original finite-aperture normalization into production.
Regular supersampling 2 failed a 29.9% shape test. Adaptive32/core6 passed 28 targeted
controls, but global controls revealed further failures. Expanding to32/core24
alone did not fix all cases; factor64/core24 is tested against128/core24 and
64/core36. The numerical tolerance remains 1e-3. No failed case is dropped.

Source 732291 has competing structures evaluated on one identical analytic-total
real image, ERR map, mask and PSF. After re-solving linear amplitudes, B/T spans
0.182–0.502; the solution above 0.5 lies delta-chi2=1.66 from the best saved
structure. The original current solution is inferior by delta-chi2=6.83.
Recovered-component tests subsequently reject all four bulges:32-versus128
relative image errors are52–95%, and64-versus128 errors are19–115%. The
fixed-grid delta-chi2 values therefore cannot support statistical identifiability
or class probabilities. This is a numerical failure, not a physical change.
An exploratory q/minor-size domain retains every supported truth and is being
tested with native optimizers and higher-grid checks; it is not yet production.
The conditional 10109 chain remains unconverged at its current checkpoint.
Fixed-truth linear controls recover B/T=0.554 and0.653 for10109 and215914
(truth0.511 and0.661), while free structural fits give0.376 for both.
Adding a sky constant shifts these fixed-truth estimates modestly and does not
explain the much larger nonlinear structural bias. These are controlled
diagnostics, not physical transformations or calibrated posterior probabilities.

All 395 quadratic spectra are positive across significant mapped target response.
Fourth-band holdout errors have median54.3% and84th percentile150.5%; this is
usually a remote-band extrapolation diagnostic, not a calibrated error at the
mapped wavelength. Flux-dependent recovery classifications remain model-conditional.
Scalar/full-throughput experiments measure sensitivity, not a calibrated correction.

Full corrected 403 production remains held until numerical controls and a
scientifically adequate B/T recovery/identifiability policy are established.
Eight unsupported morphology inputs remain explicit rows. The source catalog
records pending, failed and unknown states; unknown is never non-disk.

## Native completeness

The mass-to-light diagnostic uses F444W27.5, the faintest30%, and the95th percentile
of masses rescaled to that limit, separately for NUVrJ-quiescent and other sources.
New bins align exactly with the existing observed denominator tables. WHT quartiles
are relative-depth strata. The prescription follows the
[COSMOS-Web mass-function selection](https://arxiv.org/html/2511.05259v1#S2).
The magnitude benchmark is approximately80% detection; a95th-percentile M/L
curve is not95% detection completeness. Neither this diagnostic nor native
paired-band eligibility supplies detection or class-confusion weights.

Intrinsic fractions still require footprint/depth-aligned detection, native
morphology recovery for passive and star-forming parents, quiescence purity,
redshift/mass migrations and appropriate SFR censoring. Existing redshift/mass
fractions and SFR–mass summaries remain observed, conditional products.

## Completed input numerical milestone

All 1,580 controls now have passing settings: 1,487 use adaptive32/core6;
93 require adaptive64/core24. All 395 supported input models pass, with eight
unsupported morphology rows preserved. `validated_input_policy/` freezes
native/clean settings and copies clean settings exactly into real injection.
This closes input-rendering precision, not fitted-model identifiability.

The first exploratory domain-controlled732291 fit converges to B/T=0.1671
with bulge q=0.503 and radius0.0361arcsec. It agrees with factor128 to7.1e-5;
the target reference additionally passes factor256 and region-size checks.
A second initialization and neighbor checks remain pending, so no class is promoted.
The conditional legacy chain remains unconverged after6,000steps.

The bounded legacy chain has completed6,300stored steps (6,000postburn),
with tau_max348.69 and failed convergence. Its diagnostic quantiles and
class probability are not promoted. The original HDF5 chain and all errors
remain preserved. This is not a calibrated B/T-identifiability measurement.

## Final targeted checkpoint

Both domain-controlled starts converge (B/T0.1671 and0.1927), and both
pass actual-grid/factor128 comparison plus factor256/region checks. The
local numerical defect is repaired for this test. These point estimates remain
far below injected B/T0.5152; calibrated recovery and identifiability remain open.
This is not physical transformation. No full corrected403 run is launched
through this unresolved gate. Native population completeness remains uncalibrated.
