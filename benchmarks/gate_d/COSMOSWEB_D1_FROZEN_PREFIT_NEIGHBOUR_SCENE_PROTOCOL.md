# Gate D1m — pre-injection fitted, frozen-neighbour scene diagnostic

## Purpose

D1l was the first Gate-D neighbour treatment to improve the median AB=26 recovery in both crowded placement classes, but important failures remain: two of three near-source AB=26 targets still hit target bounds, nuisance components can hit bounds, and an isolated AB=26 case has a catastrophic interior solution. D1m asks one narrower identifiability question:

**How much of the remaining injected-target bias is caused by target–neighbour parameter competition, as opposed to inadequacy of the parametric scene model itself?**

This is a diagnostic control that uses information available only because this is an injection experiment: the real pre-injection `SCI_ORIG`. It is not a production measurement method, not blind detection, not independent cross-code validation, and not literal reproduction of real COSMOS-Web source morphology.

## Literature/software check before implementation

Established profile-fitting practice supports explicit modelling of overlapping neighbours rather than assuming that masking alone removes contamination. Peng et al. (2010) report that simultaneous fitting of overlapping/nearby objects with multiple components can recover simulated parameters more accurately than fitting a target singly while masking neighbours. SourceXtractor++ supports fitting mixtures of models to clumps of overlapping objects and explicitly notes that model fitting requires accurate PSF models. The current COSMOS-Web morphology analysis (Yang et al. 2026, arXiv:2606.14869) likewise models contaminating sources with additional Sérsic components and limits the modelled set when many contaminants are present.

D1m does not replace the verified in-repository target fitter with GALFIT, SourceXtractor++, Galight, or lenstronomy because that would change renderer, objective/optimizer conventions, parameter transforms, and PSF handling simultaneously. Instead it makes the smallest controlled change to D1l: nuisance components are fitted on the pre-injection scene and then frozen before the injected target is recovered.

References consulted before implementation:

- Peng et al. 2010, GALFIT 3 technical paper and GALFIT guidance.
- SourceXtractor++ model-fitting documentation.
- Yang et al. 2026, COSMOS-Web multi-wavelength morphology catalog, section 3.1.2.

## Frozen design

1. Reuse D1k/D1l's exact pre-injection parent detection and Photutils deblending. No detection threshold, `n_levels`, `contrast`, `n_pixels`, support radius, dilation, or segmentation rule changes.
2. Reuse D1l's exact candidate selection: deblended children whose frozen support overlaps the 65x65 target patch and whose pre-injection positive-core centroid lies inside it; rank by distance to the injection position and fit at most `MAX_NEIGHBOURS = 3`.
3. Remaining children are masked only on their exact frozen child support, with no growth.
4. For each of the nine frozen injection positions, fit the selected nuisance scene **once on `SCI_ORIG`**, before any injected source is present. The same prefit result is then reused for both AB=26 and AB=29 at that location.
5. The prefit nuisance model is exactly D1l's single PSF-convolved Sérsic component per selected child, with exactly the same declared STPSF, moment seeds, parameterisation, and nuisance bounds:
   - amplitude ratio `1e-4 .. 1e4` relative to the D1e AB=27.5 reference;
   - centroid correction `-2 .. +2` pixels around the frozen child seed;
   - `Re = 1 .. 20` pixels;
   - `n = 0.3 .. 6`;
   - `q = 0.2 .. 1`;
   - `PA = -90 .. +90` degrees.
6. The pre-injection scene fit includes a free planar background (`b0 + bx*x + by*y`) with the same normalized patch coordinates used by D1e. It is nuisance-only: there is no injected-target component in this stage.
7. Prefit optimizer: `scipy.optimize.least_squares`, TRF, linear loss, `x_scale="jac"`, `max_nfev=500`. Prefit failures and nuisance-bound hits are retained. There is no retry with changed bounds or segmentation.
8. If the prefit returns a finite nuisance solution, freeze all nuisance Sérsic parameters at that solution. The prefit background is **not** frozen; background remains free in the subsequent target fit exactly as in D1e/D1l.
9. Recover each injected target with the frozen neighbour source image added to the model. The target retains exactly the D1e/D1l renderer, declared STPSF, ERR weighting, planar background, linear loss, parameterisation, and target bounds. Target `max_nfev=500` is kept equal to D1l for direct comparison; target bounds are not changed.
10. If a prefit is non-finite or cannot be executed because too few valid pixels remain, preserve that as a failure and do not fabricate/fallback a neighbour solution. The corresponding injected-target rows are reported as not recovered by D1m.
11. SCI is still the frozen D1d injection product. ERR/WHT are unchanged. No additional sky/background noise, source shot noise, Tolman factor, or PSF sharpening is introduced.
12. Record per-position prefit optimizer status/message, nfev, chi-square proxy, selected child labels, nuisance parameters and nuisance bound hits; per injected target record target optimizer status, target bound hits, recovered magnitude, Re, n, q, PA, centroid, valid fraction, and whether the frozen prefit was reused across brightness levels.
13. AB=29 remains an intentional low-information failure regime. It is not a target for looser bounds, criteria, or rescue logic.

## Interpretation

Workflow success means only that the frozen control executed. The comparison is D1m versus D1l at identical injection locations and brightnesses, with the paired-difference recovery retained as the numerical identifiability oracle.

- If freezing a scientifically adequate pre-injection neighbour fit materially removes crowded AB=26 failures, target–neighbour parameter competition is an important contributor.
- If the remaining failures persist despite freezing, scene-model inadequacy, PSF mismatch, background structure, or undetected/unmodelled contaminants remain implicated.
- If the neighbour prefit itself is poor or bound-limited, that is evidence about scene-model inadequacy and is not to be hidden by changing nuisance bounds post hoc.

No numerical acceptance band is introduced after seeing D1m results.