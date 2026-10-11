# COSMOS-Web passive disks: recovered methods and supported results

Research checkpoint: 2026-10-11 (Asia/Taipei). **Partial scientific completion.**
The supported sample/recovery products are complete at this checkpoint; final
corrected GOLD403 production and population calibration remain scientifically
conditional. This report is not a claim that the whole project has passed its
publication gates.

## Verified research state

GitHub was fetched before implementation. Only `main` was advertised; the
recovery branch starts at `fa744a6`. Local `main` had been at `588882c`, twelve
commits behind the corrected two-branch methods. The unrelated edited general
notebook remains untouched and excluded from the methods commit. Relevant
historical commits, receipts, scope/R3 decisions and source helpers were read.
JADES was not used as COSMOS-Web evidence.

The historical 806-case F444W E0/E1J CSV is complete: **786 OK, 20 preserved
ERROR rows**. The 418-row pause receipt is historical. No checkpointed production
case was forced or rerun. Historical n and joint classifications came from
single-Sérsic fits to B+D truth and are not final catalog-n transfer science.
Historical B/T is not reused across changed interpolated truth without identity
checks. The corrected GOLD91 generating notebook was recovered in Downloads,
its bytes archived, and its functions reused rather than replacing Galight.

## Structural and physical conventions

Keep published selection → mapped/interpolated truth → native-clean → z=3-clean
→ z=3-real stages distinct. The mapping is an explicit sample-definition layer
within the published-to-native step. Wavelength-interpolated GOLD91 does not yet
have a complete matching native-clean baseline; no redshift-only bias is claimed
from its clean-to-real comparison. n uses single-Sérsic truth/recovery, and B/T
uses n=1 disk plus n=4 bulge truth/recovery. A joint disk is n<2.5 AND B/T<0.5
only after both measurements pass their independent quality rules.

Exact Lenstronomy rendering, major-axis radii, supersampling=2, the adopted
angular-diameter-distance ratio and observer-frame Fν luminosity-distance
transfer are retained. No second Tolman dimming, PSF sharpening, or intrinsic
luminosity evolution is introduced. E0 remains primary; E1J is only sensitivity.
GalSim DES_PSFEx is evaluated at position+1, drawn with `no_pixel`, normalized
by signed flux and retains negative wings. Deterministic source images are added
to existing SCI; real ERR and segmentation are retained; no second sky noise is
added and original SCI/ERR/WHT products are not modified.

## GOLD91 recovery diagnosis

Saved-table validation reproduces **91 parent, 90 valid interpolated models,
73 input disks, 90 clean and real successful fits, 56 measurable real results**.
Of the 73 input disks, 45 are measurable and remain disk classified; 28 are
unmeasurable (27 low S/N, one high-S/N quality failure). This is 45/73 conditional
measurable disk retention, not source detection completeness. The eight apparent
non-disk→disk changes remain recovery outcomes. Median real-minus-clean n is
−0.1641, with conditional bootstrap 95% interval [−0.2185,−0.1156]; median B/T
change is −0.08844, with interval [−0.13897,−0.03692]. These describe this selected
sample and do not establish physical evolution or a calibrated estimator.

Two new seeds in the original context plus one deterministic next valid
same-tile context were run for each disputed object: **24/24 fits OK**, with
per-case JSON checkpoints, pickles, source/context arrays and model/residual
figures. IDs **119834 and 215914 cross B/T=0.5 between contexts**. ID215914
recovers approximately 0.372 in two original-context fits and 0.574 in the
independent context, despite input B/T=0.661. The other six retain downward
recovery bias in these trials. Fixed-shape controls generally do not reproduce
the free-fit shifts; component size/shape freedom and real context matter.
This is evidence of recovery bias/sensitivity, not intrinsic morphology change.
Three trials cannot identify a population confusion matrix or establish all
component posterior uncertainties. All eight retain an explicit uncalibrated
robustness flag; no post-hoc class threshold is introduced.

The stored aperture-S/N estimator includes the underlying context aperture
flux. For ID732291, source-only aperture S/N is about 19.47 while the saved
scene-aperture value is 23.97. This illustrates why the existing S/N-qualified
measurability count is not an independently validated detection efficiency.
No revised S/N threshold was used to improve retention.

## Renderer issues found and bounded repair

The old wavelength renderer sets component weights after separately normalizing
their finite stamp sums. Galight reports integrated-to-infinity Sérsic flux.
Using the original rendered truth, the actual integrated B/T minus the requested
B/T has median **0.004868**, range
**[-0.007712,0.046716]**.
This convention mismatch is smaller than the major real-image shifts and is
not their sole explanation. Set component amplitudes from Lenstronomy
`LightModel.total_flux` and use one common image normalization. The small helper
has two meaningful regression tests (including invalid-input subcases), exact
amplitude closure for 90 models to <1e-14, and three independent perturbed-start
clean Galight recoveries with |ΔB/T| = 0.00386, 0.00060, 0.01331.
All three pass the inherited 0.10 pilot tolerance. This does not calibrate
real-context uncertainty for all 403 objects.

An independent reconstruction of the original inverse-coordinate Galight grid
matches all eight diagnostic source images to relative error
2.8e-16. The initial requested-radius
normalization diagnostic is superseded by `normalization_diagnostics_with_truth_flags.csv`
for original-run claims. The original builder clips requested radii for IDs
**164952, 283184, 666469**. They are retained with rendered/requested size fields
and a `REQUESTED_TRUTH_RADIUS_CLIPPED` flag. The targeted diagnostic Jy conversion
differs from the original rounded arcseconds/radian conversion by 1.879 ppm;
the exact original conversion is used when reproducing saved spectral fluxes.

## Wavelength and spectral transfer

The recovered strict branch-specific morphology interpolation reproduces all
90 saved GOLD91 n/B/T inputs to 1e-9. Across GOLD403 there are **395 supported
brackets**, of which **331 satisfy the mapped input disk rule**, and eight
unsupported IDs: 123813,191260,197518,197717,314177,393785,487778,751391.
All remain in the source-by-source checkpoint. This is a morphology mapping
result, not a redshift recovery rate.

All 90 saved scalar source-flux inputs were numerically reproduced. Applying
the existing full-throughput three-band quadratic Fν operator to those same
cleaned integrated fluxes gives median curved/scalar ratio
**1.0493**, with 16–84% range
**[1.0263,1.0831]** and individual ratios
0.9221–1.2159. All 90 have the declared spectral-anchor support; negative
coefficients are retained. This is an integrated-flux sensitivity test, not the
full spatially resolved R3 synthesis. The effective-wavelength brightness method
and frozen R3 policy must be reconciled and propagated to recovery before a
final corrected production calibration. No scalar result was silently relabeled
as full-throughput science.

## Native parent sample and observed fractions

The local released FITS file has 784,016 rows, matching the official
[COSMOS2025 release documentation](https://cosmos2025.iap.fr/catalog.html).
All working IDs align exactly. The prior 78,053-row clean parent membership and
physical/morphology columns reproduce from the FITS tables. Its original chosen
band columns were older than GOLD403; applying the already frozen rest-optical
prescription reconstructs **all 403 IDs exactly**. Parent eligibility preserves
type=0, warn=0, HSC-star-mask exclusion, abs(F444W model mag)<30, finite physical
parameters, 0<z<3 and 9.5≤logM<13, valid NUV/r/J colors, finite main-sequence
offset and no flagged Chandra AGN. Both morphological bands require S/N>20,
finite physical B/T, and the inherited valid n range.

There are **36,905 eligible catalog galaxies**, of which
**25,642 have usable paired-band morphology**; the remaining
**11,263** are preserved as
unknown morphology. For the measurable subset the three distinct observed
fractions are:

| estimand               |   k |     n |   fraction |   ci95_low |   ci95_high |
|:-----------------------|----:|------:|-----------:|-----------:|------------:|
| passive_disk_among_all | 403 | 25642 |    0.01572 |    0.01426 |     0.01731 |
| disk_among_passive     | 403 |  4047 |    0.09958 |    0.09073 |     0.10919 |
| passive_among_disks    | 403 | 15171 |    0.02656 |    0.02412 |     0.02924 |

The bins are frozen 0.5-wide redshift and 0.5-dex mass intervals; sparse/empty
rows remain explicit. Wilson 95% intervals quantify conditional finite counts,
not cosmic variance, morphology errors or completeness. Missing-morphology
bounds keep passive labels fixed and vary unknown disk membership; measured
labels are assumed correct for those bounds. They do not account for undetected
galaxies or misclassification. Definition sensitivity changes the selected count
to 506 for NUVrJ-only, 421 for Speagle+NUVrJ, and 238 for stricter n/B/T. These
are checks, not optimized cuts. The conditional mass/redshift figures are
supported descriptive catalog products, not corrected intrinsic trends.

## SFR–mass interpretation

The six redshift panels show every GOLD403 object, measurable passive non-disks,
and the NUVrJ non-quiescent parent density. The inherited empirical main sequence
and a [Speagle et al. (2014)](https://arxiv.org/abs/1405.2041) comparison use source
redshifts and original masses/SFRs. Catalog SFR fields are SED posterior summaries;
their interval endpoints are not explicit observational upper limits. Ninety-six
GOLD objects are below logSFR=−4 and are now visible. Twenty-five have lower
posterior intervals near the model-grid floor; they are flagged, not removed.
Deeply suppressed SFR values and narrow intervals at that floor are not precise
direct measurements. Offset summaries include counts, 16–84% scatter and
conditional median bootstrap intervals only for N≥5; censored-population medians
and intrinsic SFR trends are not claimed.

## Reproducibility and delivery

The single permanent entry point is `Codes/Passive_Spiral_MASTER.ipynb`, executed
top-to-bottom in `phd`. Existing notebook cells/bytes and all science outputs are
preserved. `input_manifest.json` guards raw H5, PSFs, catalogs, throughput curves
and methods before checkpoint reuse; use the master entry point for safe resume,
not the diagnostic adapter alone. `notebook_execution.json` records source-cell
hash and execution state. Per-case fits skip existing rows safely. Environment:
Python 3.11, Galight 0.2.1, Lenstronomy 1.12.0, NumPy 2.4.6, SciPy 1.17.1,
Pandas 2.3.3, Astropy 7.2.0, GalSim 2.8.5. Writable temporary Numba/Jupyter
cache directories resolve sandbox cache/socket restrictions; no scientific
dependencies or original FITS arrays were changed.

Current science products are in `science_products/`; `sample_analysis/`,
`sample_analysis_restopt/`, `sample_analysis_validated/` and `normalization_probe.csv`
are retained audit history and are superseded for final checkpoint presentation.
Use the CSV/FITS catalogs, PDF/PNG figures, caption file and gate report together.
No large images, parent datasets or notebook outputs are added to GitHub.
