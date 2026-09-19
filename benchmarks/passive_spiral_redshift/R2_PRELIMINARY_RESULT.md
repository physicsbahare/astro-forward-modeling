# R2 preliminary real-context stress result

Status: **LOCAL/ATTACHED-DATA PRELIMINARY RESULT — NOT GITHUB ACTIONS AND NOT FINAL COMPLETENESS**

The R1 redshifted disk control (ID 57977) was injected into three pre-frozen locations of the literal COSMOS-Web A2 SCI background supplied by the ID 39749 cutout. Existing sky/background structure was left untouched and no additional stochastic noise was added.

## Summary

| context | max abs delta q | max abs delta concentration | flux-ratio range | max centroid offset [arcsec] |
|---|---:|---:|---:|---:|
| isolated | 0.094868 | 0.018533 | 0.925--0.999 | 0.0185 |
| intermediate | 0.207299 | 0.062732 | 1.007--1.068 | 0.0128 |
| near-source | 0.291604 | 0.386367 | 1.306--2.622 | 0.4660 |

The `isolated` placement is intentionally a nearly empty patch of the real A2 background. It is the low-crowding control. In that control, the recovered q changes by only +0.002 at z=1 and by +0.095 at z=3, while the concentration change remains below about 0.019 and the centroid offset below 0.019 arcsec.

The intermediate placement becomes progressively rounder and lower-concentration toward high redshift. The near-source placement becomes contamination dominated: at z=3, source-only q=0.585 becomes 0.877, concentration falls from 0.618 to 0.232, signed aperture flux is 2.62 times the injected-source value, and the centroid moves by 0.466 arcsec.

## Interpretation

For this one real disk-like source, the artificial-redshifting transfer operator itself remains coherent, while real-scene context increasingly controls the measured morphology as the source becomes fainter/smaller. This is a paper-relevant failure mode rather than a reason to tune a deblender.

This is **not yet a completeness fraction** because there is one input galaxy, three context placements, and a descriptive fixed-aperture proxy rather than the final frozen paper morphology selection. The next paper-facing step is to repeat the unchanged operator on several visually clean passive disks and more pre-frozen real contexts, then estimate a small pilot recovery/completeness surface versus redshift and context without inventing a post-hoc threshold.
