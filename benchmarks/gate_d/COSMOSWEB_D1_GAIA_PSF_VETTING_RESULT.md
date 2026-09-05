# COSMOS-Web Gate D1n-d — Gaia-vetted compact-source PSF support result

## Immutable execution receipt

Workflow: `gate-d-cosmosweb-gaia-psf-vetting`

Confirmed GitHub Actions run: `33996528969`

- status: `completed`
- conclusion: `success`
- head SHA: `d9d320b96c4b0bfa5752a5578c5dc2b432c8c6b7`
- artifact: `gate-d-cosmosweb-gaia-psf-vetting`
- artifact id: `9978225068`
- artifact SHA256: `fb54686d7e13ff1efa8809e8d008b0a3adab389bd2e2995b906f2e0a91459c0d`
- dedicated unit tests completed successfully before the catalog diagnostic.

This is an execution-success receipt, not evidence that the 512x512 cutout contains a usable empirical stellar PSF sample.

## Machine-readable scientific result

The archived `summary.json` from the successful workflow was inspected directly.

- Parent D1n-b support candidates: `14`.
- Gaia DR3 rows returned inside the frozen query footprint: `0`.
- Gaia-matched D1n-b candidates within the predeclared `0.15 arcsec` radius: `0/14`.
- Gaia-vetted median stack constructed: `false`.
- The match radius was not enlarged after inspection.
- D1n-b candidate selection was not changed.
- `EPSFBuilder` was not attempted.

Therefore the 512x512 real-mosaic cutout has **no independent Gaia stellar support** for calibrating or validating its effective PSF. The broader D1n-b stack of compact detections must remain an unvetted compact-source diagnostic and must not be promoted to an empirical/effective PSF.

The absence of Gaia rows is itself the scientific result of the frozen support test; it is not repaired by morphology-based relabelling or by loosening the association radius.

## Scientific interpretation

D1n-a showed only modest ideal-STPSF field-position variation. D1n-b showed that unvetted compact detections in the literal mosaic are much broader/less circular than the declared STPSF, but D1n-d demonstrates that the small cutout cannot independently establish that those detections are stars. D1n-c separately showed that background/residual structure is not a sufficient general explanation for the remaining catastrophic AB=26 D1m interior solutions.

A better next PSF diagnostic is therefore not to force an ePSF from this cutout. Zhuang, Li & Shen (2024, ApJ 962, 93; arXiv:2309.03266) publicly released COSMOS-Web NIRCam PSF models and found measurable temporal/spatial PSF variation, including F444W. Their pointing table places the current Gate-D sky position nearest the footprint of observation `OBS_084`, for which public F444W `global`, `broad`, and `narrow` PSF models are available. The next experiment should compare those published survey-specific empirical PSFs against the declared Gate-D STPSF before any morphology rerun.

No production framework implementation, PSF sharpening, source injection, target refit, noise addition, Tolman factor, segmentation change, bound change, convergence relaxation, or acceptance-band change is authorized by this result.
