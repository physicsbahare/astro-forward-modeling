# COSMOS-Web Gate D1n-e — published empirical-PSF bracket result

## Immutable execution receipt

Workflow: `gate-d-cosmosweb-published-empirical-psf`

Corrected confirmed GitHub Actions run: `34000460810`

- status: `completed`
- conclusion: `success`
- head SHA: `4d48945d584b052a83e03d38cdb29ef87b6384f3`
- artifact: `gate-d-cosmosweb-published-empirical-psf`
- artifact id: `9979333973`
- artifact SHA256: `9b636de5add233bcd76bc359ffa8f0b7ecd133b60a98d48095c66774cd7fc3a6`

The preceding run `34000069448` also completed at the workflow level but used the wrong fallback pixel scale for the released PSF products and is therefore preserved only as a superseded software/convention run, not as scientific evidence. The corrected run uses the public release-note convention of 15 mas/pixel for the 2x-oversampled published PSF arrays.

Workflow success is an execution/provenance statement, not a claim that any one observation-level published PSF is the literal DR1 mosaic effective PSF.

## Corrected machine-readable result

The corrected artifact `summary.json` was inspected directly.

Frozen STPSF comparator:

- EE50 = `0.08844` arcsec
- EE80 = `0.25617` arcsec
- moment axis ratio = `0.8588`

Published OBS_084 F444W PSFs, resampled from the documented 15 mas grid to the 30 mas comparison grid:

- **broad**: EE50=`0.10482` arcsec, EE80=`0.25920` arcsec, axis ratio=`0.9006`, L1 to STPSF=`0.26744`, cross-correlation=`0.99357`.
- **global**: EE50=`0.10452` arcsec, EE80=`0.25682` arcsec, axis ratio=`0.8535`, L1 to STPSF=`0.22498`, cross-correlation=`0.99703`.
- **narrow**: EE50=`0.10554` arcsec, EE80=`0.25839` arcsec, axis ratio=`0.8411`, L1 to STPSF=`0.23272`, cross-correlation=`0.99714`.

The published models also differ among themselves: normalized L1 is `0.08192` for broad/global, `0.12576` for broad/narrow, and `0.05169` for global/narrow. All signed negative-pixel diagnostics were preserved; no clipping, deconvolution or PSF-matching/sharpening kernel was introduced in D1n-e.

## Scientific interpretation

The dominant difference is in the core: the published observation-level models have EE50 near `0.105` arcsec, about 18–19% larger than the declared STPSF comparator, while EE80 remains close to `0.257` arcsec. The image-level L1 differences of roughly 0.22–0.27 are materially larger than the earlier ideal-STPSF detector-position bracket, so PSF shape is still a scientifically credible contributor to morphology sensitivity.

This does **not** establish that the published OBS_084 PSFs are the correct DR1 mosaic effective PSF. They are external observation-level empirical models and the final mosaic mixes exposures and resampling. The result therefore justifies a crossed-PSF sensitivity oracle, not replacement of the Gate-D PSF and not a post-hoc morphology rescue.

## Next diagnostic

The next experiment is D1n-f: use the exact paired-difference target signal from only the two pre-existing catastrophic AB=26 D1m rows and recover it with the frozen STPSF control plus the three published OBS_084 PSFs. The published PSFs are intentionally treated as mismatched recovery models against the known STPSF-injected truth. This removes the real scene and asks whether PSF mismatch of the observed magnitude can by itself generate comparable flux/size/Sersic/centroid failures.

No target bounds, optimizer convergence requirements, ERR weights or acceptance criteria are changed. Signed values in the published PSF products are preserved rather than clipped, and no sharpening/deconvolution kernel is constructed.
