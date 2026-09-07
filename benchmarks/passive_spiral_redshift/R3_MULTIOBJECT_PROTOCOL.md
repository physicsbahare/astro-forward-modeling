# Passive-disk R3 — multi-object real-context recovery pilot protocol

Status: **FROZEN BEFORE MULTI-OBJECT INPUT INGESTION / NO R3 RESULT YET**

This protocol is the next paper-facing step after the real single-object R1 transfer pilot and R2 real-context stress test. It does not change the artificial-redshifting operator, does not resume P6/P7 contamination fitting, and does not define a post-hoc spiral-recovery threshold.

## Scientific question

Across several visually secure passive-disk controls, how strongly do redshift and real COSMOS-Web scene context alter the morphology quantities that will later enter the passive-spiral completeness calculation?

R3 is a **multi-object recovery pilot**, not yet the final passive-spiral completeness measurement. A completeness fraction may be reported only after the actual paper passive-spiral selection/classification rule is frozen independently of the R3 outcomes.

## Input sample boundary

Use only objects already present in the existing passive-disk / visual-calibration project. Do not create a new B/T, Sérsic-index, color, or morphology cut for R3.

Eligible R3 controls must satisfy all of the following before their redshifted images are inspected:

1. belong to the existing visually labelled calibration/development sample;
2. have a secure visual disk-like label suitable as a morphology-survival control (the existing `smooth_disk_S0` class is allowed; ambiguous/spheroid/irregular-merger controls are not promoted into the secure-disk set);
3. have usable source redshift and catalog coordinates;
4. have literal COSMOS-Web 30-mas SCI cutouts in the source bands required to bracket every requested source wavelength;
5. have common-grid WCS across those source bands, or otherwise be explicitly flagged for a separately justified registration step rather than silently forced into alignment;
6. pass the same no-extrapolation and no-PSF-sharpening rules as R1.

ID 57977 remains the primary anchor and is not counted as an independent new object. ID 39749 remains the pre-frozen context stress source; its own morphology may be analysed later as a source only if its source-band context can be separated without changing the frozen operator.

The first R3 batch should be small enough for manual audit (target approximately 5--10 secure passive disks), spanning more than one source-redshift/size/axis-ratio regime where the existing visual-development sample permits it. Selection is made from pre-redshifting catalog/visual information only, never from which objects give the cleanest recovery.

## Required immutable input manifest

Before rendering, freeze one row per source containing at minimum:

- COSMOS2025 ID;
- source redshift;
- RA/Dec;
- COSMOS-Web tile;
- inherited visual label;
- source-band cutout filenames and SHA-256 values;
- pixel scale and `BUNIT`;
- source-band WCS equality/registration status;
- catalog magnitude/SNR quantities used later for interpretation;
- catalog size/resolvedness quantity used later for interpretation;
- catalog crowding/context quantity if one is already available from released products.

If a required binary cutout is unavailable, keep the object in the manifest as `INPUT_MISSING` rather than replacing it after inspecting other objects' results.

## Frozen redshift grid and observed bands

Use the same development grid as R1:

`z_target = [1.0, 1.5, 2.0, 2.5, 3.0]`

Use the same rest-frame-1-micron pivot-band mapping:

- z=1.0 -> F277W
- z=1.5 -> F277W
- z=2.0 -> F444W
- z=2.5 -> F444W
- z=3.0 -> F444W

For every object/target pair, compute the required source observed wavelength from the target pivot wavelength and source redshift. Rendering is allowed only when this wavelength is bracketed by available source bands. Unsupported cases are recorded as `SPECTRAL_SUPPORT_FAIL`; no extrapolation is introduced to fill the matrix.

## Transfer operator

R3 reuses the frozen R1 semantics unchanged:

- source images remain in calibrated `I_nu` / MJy sr^-1 semantics;
- source-band interpolation is performed only after degradation to a common supported source-resolution bracket;
- one and only one redshift specific-intensity factor `[(1+z_source)/(1+z_target)]^3` is applied at corresponding emitted wavelength;
- angular rescaling uses the repository `FlatLCDMReference(H0=70, Om0=0.3)` convention;
- target grid remains 0.03 arcsec/pixel;
- target PSF matching is degradation-only;
- any case requiring sharpening is preserved as `PSF_SHARPENING_REQUIRED_UNSUPPORTED`;
- no intrinsic luminosity/size evolution is added in this pilot;
- no extra Tolman `(1+z)^-4` factor is applied.

R3 must use the same minimal verification implementation unless an object exposes a genuinely new operator failure. Do not tune the transfer operator per object.

## Real-survey context

For each supported rendered source, measure at least the following scene classes using **pre-injection** information only:

1. `isolated`: a low-crowding real-mosaic placement with no obvious bright neighbour inside the measurement region;
2. `intermediate`: real structured background / weak-neighbour context;
3. `near-source`: a deliberately crowded placement where neighbour contamination is scientifically relevant.

Context locations must be frozen before source injection. The same context coordinates should be reused across the relevant target bands where the WCS permits a literal same-sky comparison; otherwise the mapping/provenance must be recorded explicitly.

Injection changes SCI only. Existing real background noise is not regenerated. ERR/WHT are not modified in this pilot. No literal source-shot-noise realization is added because D1o/D2 provenance has not established a defensible exposure-level source/count/covariance replay.

## Measurements and failure bookkeeping

Until the paper's actual passive-spiral selection is frozen, R3 records descriptive recovery quantities rather than declaring recovered/not-recovered spirals.

For every supported source x target-redshift x context cell, record at minimum:

- source ID, z_source, z_target, target band and context class;
- spectral-support / PSF-support state;
- transferred source-only axis-ratio proxy and real-context recovered axis-ratio proxy;
- transferred source-only concentration proxy and recovered concentration proxy;
- signed aperture-flux recovery ratio;
- centroid offset from the known injection position;
- source magnitude/SNR, angular size/resolvedness, and inherited crowding/context covariates where available;
- non-finite / failed / contaminated states without deletion.

Keep low-S/N failures, morphology loss, centroid excursions, non-detections, unsupported spectral cases, and crowded failures in the output table. Do not replace them with successful alternative placements.

## R3 figures

Produce two descriptive paper-facing products before any completeness threshold is introduced:

1. a FERENGI-style image matrix showing the same source across redshift columns and transfer-only/isolated/intermediate/crowded rows for representative objects;
2. population plots of `delta q`, `delta concentration`, flux-recovery ratio, and centroid offset versus redshift, with objects retained individually and context class shown explicitly.

A recovery/completeness surface is a later layer: it may be computed only after the paper's morphology/classification decision rule is frozen independently of these distributions.

## Morphology-selection boundary

R3 deliberately does **not** invent a new q, concentration, B/T, Sérsic-n, or visual threshold for passive spirals. The final experiment must attach the artificial-redshifting outputs to the paper's actual passive-spiral selector/classifier. The forward operator is morphology-agnostic so that a later confirmed-spiral subset can replace the passive-disk controls without changing the physics transformation.

## Stop / decision rule

After the first 5--10-object R3 batch is complete:

- if the operator remains coherent and the dominant changes are redshift/context dependent, freeze the paper's actual morphology-selection rule and compute the first completeness surface;
- if a new object exposes a genuinely new spectral/PSF/operator failure not already covered by R1/P1--P5/Gate-D, isolate that one failure with the smallest diagnostic;
- do not resume nuisance/deblending optimisation merely because crowded cells fail.

R3 cannot execute until additional pre-selected real passive-disk source cutouts and their immutable manifest are available. That missing binary input is a data boundary, not a reason to alter the method.