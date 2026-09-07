# Passive Spiral / artificial-redshifting — paper-scope decision

Status: **FROZEN SCOPE DECISION — P6 IMPLEMENTATION DEFERRED**

This receipt narrows the Passive Spiral verification effort to the scientific question needed by the paper. It does not modify or invalidate any historical P1–P5 protocol/result, Gate-D result, tolerance, target bound, convergence requirement, or failure record.

## Scientific question retained

The artificial-redshifting work is needed to quantify whether an observed redshift trend in passive-spiral incidence could be biased by morphology loss caused by finite resolution, surface-brightness dimming, PSF convolution, sampling, survey noise/background, and crowding.

It is **not** intended to rebuild the COSMOS-Web/COSMOS2025 extraction stack or to create a new general-purpose deblender/morphology fitter.

## Survey products to reuse

The science analysis should preferentially use the released COSMOS-Web/COSMOS2025 catalog products for quantities already extracted by the survey team, including photometry, redshifts/physical parameters, segmentation/model products when available, and released structural/morphological measurements. The artificial-redshifting harness should calibrate recovery/completeness relative to the paper's actual passive-spiral selection rather than replace those catalog products.

## Verification evidence already sufficient

- **P1:** establishes the controlled artificial-redshifting/operator survival test for a known spiral feature and records resolution-driven attenuation without introducing a classification threshold.
- **P2/P3:** establish the key real-mosaic failure mode: structured real-scene contamination can dominate raw spiral-phase recovery while paired subtraction retains same-renderer identifiability.
- **P4:** fixed pre-injection masking gives only limited, heterogeneous improvement.
- **P5:** frozen Huber robust loss gives only limited, heterogeneous improvement and is not to be retuned.

Together these are sufficient to demonstrate that crowding/contamination is a genuine source of morphology incompleteness and that simple corrective operators are not universally reliable. That is the relevant paper-level conclusion. The failures must remain failures; no post-hoc threshold, mask, robust-loss parameter, or acceptance band is introduced.

## Work stopped for current paper scope

The frozen `P6_PROTOCOL.md` is preserved as a historical proposed diagnostic, but **P6 implementation/execution is deferred and is not a blocker for the Passive Spiral paper**. Do not continue P6/P7/... contamination-control cycling unless a future scientific decision demonstrates a distinct paper-critical failure mode that cannot be answered with released survey products or the existing P1–P5/Gate-D evidence.

Likewise, do not build a replacement source extractor, deblender, segmentation pipeline, or general morphology framework for this paper solely because the verification harness can do so.

## Work still required

The next Passive Spiral task should be a compact **catalog-aligned morphology-recovery/completeness experiment**:

1. freeze the actual passive-spiral science selection and the exact released catalog morphology quantities used by the paper;
2. define a representative low-redshift/input spiral sample with trustworthy morphology;
3. artificially redshift that sample through the already-verified forward operator without double Tolman dimming or PSF sharpening;
4. place/render into survey-realistic conditions without re-adding existing sky noise; real-mosaic injection modifies SCI only and leaves ERR/WHT unchanged;
5. remeasure only the morphology/classification quantities necessary to apply the paper's frozen selection, using released survey products/tools where they already provide the measurement;
6. report recovery/completeness and failure fraction versus redshift and the controlling observables (at minimum magnitude/SNR, angular size/resolvedness, and crowding/context);
7. propagate that completeness into the interpretation of the passive-spiral fraction versus redshift.

Low-S/N failures, bound hits, centroid excursions, optimizer failures, non-detections, morphology loss, and crowded failures are part of the completeness result and must not be removed to improve recovery.

## Exposure-level provenance boundary

Nothing in this scope decision changes D1o/D2. Literal exposure-level source-shot noise remains forbidden unless provenance establishes that the relevant pre-resample source/count/variance representation and historical resampling operator are defensible. Synthetic-equivalent real-mosaic injection remains distinct from literal survey reproduction.

## Stop rule

Once the catalog-aligned completeness surface is measured with pre-frozen selection and failure bookkeeping, further verification is justified only by a **new, non-redundant, paper-critical failure mode**. Improving a contaminated fit for its own sake is not such a failure mode.
