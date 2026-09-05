# Gate D1l — limited simultaneous parametric-neighbour Sérsic diagnostic

## Purpose

D1k showed that splitting frozen >5-sigma parents into Photutils children does not
coherently improve both crowded AB=26 regimes. D1i already ruled out post-hoc support
growth as a monotonic solution. D1l therefore asks the next narrower question:

**Does allowing a small number of nearby contaminating sources to have genuinely free
parametric morphology remove the real-scene bias while the injected target model remains
unchanged?**

This is a pre-production diagnostic. It is not blind detection, not a catalog measurement
pipeline, not independent cross-code validation, and not literal COSMOS-Web source
reproduction.

## Literature/software check before implementation

The current COSMOS-Web morphology analysis (Yang et al. 2026, arXiv:2606.14869) uses
Galight/lenstronomy Sérsic fitting and, when contaminants are present, models contaminating
objects with additional Sérsic profiles; when many are present it models the three nearest
and masks the rest. GALFIT guidance and Peng et al. likewise recommend simultaneous
modelling of overlapping neighbours when masking alone is inadequate. SourceXtractor++
also supports joint model fitting of overlapping source groups.

Directly replacing the current target fit with Galight/lenstronomy, GALFIT, or
SourceXtractor++ would change multiple variables at once (renderer/conventions, optimizer
or objective, parameter transforms, and PSF handling). That would not isolate the specific
D1k failure. D1l therefore uses the smallest adapter: the already-verified D1e Sérsic
renderer is reused for nuisance neighbours while the target implementation is left
byte-for-byte unchanged. This is an identifiability/scene-modelling diagnostic, not a claim
that the in-repository renderer is ground truth.

References consulted before implementation:

- Yang et al. 2026, COSMOS-Web multi-wavelength morphology catalog, section 3.1.2.
- Galight: https://github.com/dartoon/galight
- lenstronomy Sérsic profile documentation:
  https://lenstronomy.readthedocs.io/en/latest/lenstronomy.LightModel.Profiles.html
- GALFIT rules of thumb: https://users.obs.carnegiescience.edu/peng/work/galfit/TOP10.html
- Peng et al. 2010 GALFIT technical paper:
  https://users.obs.carnegiescience.edu/peng/work/galfit/galfit3.pdf
- SourceXtractor++ model fitting:
  https://sourcextractorplusplus.readthedocs.io/

## Frozen design

1. Reuse D1k's exact pre-injection parent detection and Photutils deblending. There is no
   new threshold, contrast, support growth, or segmentation tuning.
2. The 65x65 target patch and the injected target are exactly those of D1e.
3. Candidate nuisance sources are deblended children whose frozen child footprint overlaps
   the target patch and whose flux-weighted child centroid lies inside the patch.
4. Rank candidates by Euclidean distance from the frozen child centroid to the injection
   position. Fit at most `MAX_NEIGHBOURS = 3`, matching the limited-neighbour strategy used
   in the COSMOS-Web morphology analysis.
5. Any additional overlapping deblended children are masked only on their **exact frozen
   child support**. No dilation/growth is applied. The number of masked pixels and whether
   the target-center pixel is masked are recorded.
6. Each selected nuisance source is one PSF-convolved Sérsic component. Its centroid is
   initialized from positive pre-injection child-core moments and may move only ±2 pixels
   around that seed. Its initial axis ratio and position angle come from the moment
   covariance; its initial `Re` is the Gaussian half-light equivalent
   `sqrt(2 ln 2) * sigma_major`; its initial `n=1`.
7. Nuisance-component free-parameter ranges are frozen before output:
   - amplitude ratio relative to the D1e AB=27.5 reference: `1e-4 .. 1e4`;
   - centroid correction around the child seed: `-2 .. +2` pixels per axis;
   - `Re = 1 .. 20` pixels;
   - `n = 0.3 .. 6`;
   - `q = 0.2 .. 1`;
   - `PA = -90 .. +90` degrees.
   These are nuisance bounds only. They do not alter target bounds.
8. Every nuisance Sérsic component is convolved with the **same declared STPSF** used for
   the injected target. This is a controlled PSF convention, not a claim that this STPSF is
   the literal effective COSMOS-Web PSF at each real source position.
9. The target uses exactly the D1e renderer, target bounds, STPSF, ERR weights, planar
   background, linear least-squares loss, and 65x65 patch. The optimizer remains SciPy TRF
   least squares with `x_scale="jac"`. Only the nuisance scene model is changed.
10. `max_nfev=500` is frozen before output. Exhaustion/failure is retained as a scientific
    outcome; it does not trigger looser bounds or acceptance.
11. SCI is the frozen D1d injected scene. ERR/WHT are not modified. No extra sky/background
    noise, source shot noise, or Tolman factor is added.
12. Record all target bound hits, nuisance bound hits, centroid excursions, optimizer
    status/messages, selected/masked child labels, masked pixels, recovered target
    magnitude/Re/n/q/centroid, and low-S/N failures.
13. AB=29 is retained as an intentional failure regime. It is not a target for parameter
    relaxation.

## Interpretation

Workflow success means only that this frozen experiment executed. Scientific improvement
would require a coherent improvement in the informative AB=26 near-source and intermediate
placements without degrading the relatively isolated controls. No numerical acceptance
band is created after seeing the result.

If D1l still fails, preserve that failure. Do not return to segmentation/support tuning and
do not loosen target constraints. The next decision should separate PSF realism from scene
model complexity and should be literature/software-reviewed before another implementation.
