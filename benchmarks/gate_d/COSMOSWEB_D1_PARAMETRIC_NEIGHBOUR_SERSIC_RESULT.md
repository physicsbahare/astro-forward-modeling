# COSMOS-Web Gate D1l — limited simultaneous parametric-neighbour Sérsic result

## Immutable execution receipt

Workflow: `gate-d-cosmosweb-parametric-neighbour-sersic`

Confirmed GitHub Actions run: `33972836456`

- status: `completed`
- conclusion: `success`
- head SHA: `01788287aa257fca71fced3c9999c972df0e16ca`
- artifact: `gate-d-cosmosweb-parametric-neighbour-sersic`
- artifact SHA256: `4110591e19a20e6b6209a4e8b2164f015f34a9fd923a384bffcdbd871cdb8516`
- tests in the job: `10 passed`

This is an execution-success receipt, not a claim that the morphology experiment scientifically succeeded.

## Frozen experiment semantics

D1l reuses the D1k frozen real-scene parent detection/deblending. At most the three nearest already-detected child components are represented by free PSF-convolved Sérsic nuisance models; remaining detected children are masked only on their exact frozen support. The injected target uses the same renderer, PSF declaration, ERR weighting, loss, parameterisation, and target bounds as the prior Gate-D recovery experiments. No segmentation threshold/support-radius tuning was performed. SCI alone contains the injection; ERR/WHT are unchanged; no extra sky/background noise, source shot noise, or extra Tolman factor is added.

The injected sources are synthetic sources placed into literal real COSMOS-Web DR1 F444W mosaic context. The declared STPSF is not claimed to reproduce the exact effective survey PSF, and this diagnostic is not blind detection or independent cross-code validation.

## Aggregate result

- experiments: 18
- finite/optimizer-successful target fits: 18/18
- target-bound-hit fits: 10/18
- AB=26 target-bound-hit fits: 2/9
- AB=29 target-bound-hit fits: 8/9
- fits using at least one parametric neighbour: 12/18
- fits with at least one nuisance-neighbour bound hit: 4/18

Thus the reduction from D1k's 13/18 target-bound-hit fits to 10/18 is real, but workflow success alone is not interpreted as scientific success.

## AB=26 recovery by placement class

Truth: AB=26, Re=0.18 arcsec, n=1, q=0.65, zero centroid offset.

### Intermediate

Three recovered targets:

- Δmag = -0.114, -0.218, +0.293 mag
- Re = 0.218, 0.223, 0.134 arcsec
- n = 0.638, 0.943, 0.427
- q = 0.559, 0.639, 0.679
- centroid excursion = 0.742, 1.114, 0.602 pix
- target bound hits: 0/3

Medians:

- median Δmag ≈ -0.114 mag
- median Re ≈ 0.218 arcsec
- median n ≈ 0.638
- median q ≈ 0.639
- median centroid excursion ≈ 0.742 pix

Compared with D1k (median Δmag ≈ -0.43 mag, Re ≈ 0.321 arcsec), D1l is a substantial improvement in the intermediate AB=26 regime.

### Near-source

Three recovered targets:

- Δmag = -1.473, +0.293, -0.345 mag
- Re = 0.600, 0.183, 0.186 arcsec
- n = 2.103, 1.427, 0.300
- q = 0.753, 0.558, 0.918
- centroid excursion = 1.199, 0.465, 2.828 pix
- target bound hits: 2/3

Medians:

- median Δmag ≈ -0.345 mag
- median Re ≈ 0.186 arcsec
- median n ≈ 1.427
- median q ≈ 0.753
- median centroid excursion ≈ 1.199 pix

Compared with D1k (median Δmag ≈ -1.26 mag, Re ≈ 0.378 arcsec), the median near-source AB=26 recovery also improves substantially. However, one near-source fit remains catastrophically bright/large and two of three still hit target bounds. This failure topology is retained as evidence rather than removed.

### Relatively isolated

Three recovered targets:

- Δmag = -0.012, -1.011, +0.123 mag
- Re = 0.191, 0.600, 0.164 arcsec
- n = 1.061, 3.106, 0.630
- q = 0.621, 0.824, 0.591
- centroid excursion = 0.421, 1.173, 0.899 pix
- target bound hits: 0/3

Medians:

- median Δmag ≈ -0.012 mag
- median Re ≈ 0.191 arcsec
- median n ≈ 1.061
- median q ≈ 0.621
- median centroid excursion ≈ 0.899 pix

The isolated median remains close to truth, and D1l does not introduce parametric neighbour components in the isolated patches (`n_neighbour_models=0`). One isolated AB=26 case is nevertheless a severe non-bound-hit morphology/flux failure (Δmag ≈ -1.01 mag, Re ≈ 0.600 arcsec, n ≈ 3.11). This is scientifically important: absence of a parameter-bound hit is not sufficient evidence of correct recovery.

## AB=29 regime

AB=29 remains intentionally below practical independent-pixel information content (nominal independent-pixel S/N about 0.33–0.37). Eight of nine AB=29 targets hit at least one target bound. The single no-target-bound-hit case is an isolated placement and still has strongly biased shape parameters. D1l therefore does not rescue the AB=29 morphology regime, and no criterion/bound relaxation is justified.

## Scientific interpretation

D1l is the first neighbour-treatment diagnostic in this sequence that improves the median AB=26 recovery in both crowded classes simultaneously while leaving the isolated modelling path unchanged. This supports the conclusion that free neighbour morphology / simultaneous scene modelling matters, rather than simple support growth, masking, or empirical-template amplitude fitting alone.

The result is not a global solution. Near-source failures remain, nuisance models themselves can hit bounds, and an isolated non-bound-hit catastrophe demonstrates that optimizer success and interior parameters do not guarantee correct morphology.

The next experiment should therefore be the smallest diagnostic that separates **scene-model inadequacy** from **target–neighbour parameter competition**, not another post-hoc segmentation-threshold/support-radius change. A scientifically useful next control is a two-stage scene-model diagnostic: fit the neighbour Sérsic scene on the original pre-injection SCI, freeze that neighbour scene, then recover the injected target with the target model/bounds unchanged. This uses the injection benchmark's known pre-injection scene as a diagnostic control, not as a production method. It should be protocol-frozen before execution and compared directly to D1l and the exact paired-difference oracle.

This direction is consistent with established simultaneous-neighbour profile-fitting practice (e.g. GALFIT/GALAPAGOS) and with COSMOS2025's grouping and simultaneous fitting in SourceXtractor++/SE++, while remaining a narrower identifiability diagnostic rather than a new production pipeline.
