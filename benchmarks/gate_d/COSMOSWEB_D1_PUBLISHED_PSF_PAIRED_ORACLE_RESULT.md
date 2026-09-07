# COSMOS-Web Gate D1n-f — published-PSF paired-difference oracle result

## Immutable execution receipt

Workflow: `gate-d-cosmosweb-published-psf-paired-oracle`

Confirmed GitHub Actions run: `34004810134`

- status: `completed`
- conclusion: `success`
- head SHA: `6c07e54568c3dcceaf8a7b7a14335c827e037978`
- artifact: `gate-d-cosmosweb-published-psf-paired-oracle`
- artifact id: `9980609647`
- artifact SHA256: `edce5c3389d467c535874cb0364a54ca3f57a6fc36a9479a9d384b6e57f626ff`
- dedicated test step: success

This receipt records execution and the inspected machine-readable artifact. It does not turn the published OBS_084 PSFs into literal DR1 mosaic truth.

## Frozen semantics

The two selected rows are the largest-|delta-mag| AB=26 failures from D1m: near-source index 0 at (168,66), D1m delta-mag about -1.112, and relatively-isolated index 1 at (69,195), D1m delta-mag about -1.011. D1n-f removes the real scene by using `injected - SCI_ORIG`, then recovers each target with the frozen STPSF control and with the checksum-pinned published COSMOS-Web OBS_084 broad/global/narrow F444W PSFs as intentionally crossed mismatch models.

Target bounds, ERR weighting, TRF/linear least-squares objective, `x_scale=jac`, and `max_nfev=500` are unchanged. No noise, Tolman factor, deconvolution, PSF sharpening, bound relaxation, or acceptance threshold is introduced. Signed values in the published PSFs are retained.

## Machine-readable scientific result

All 8 fits are finite, optimizer-successful, and free of target-bound hits.

The matched STPSF control recovers both targets essentially exactly (absolute delta-mag below 3e-9 mag; centroid excursion below 3e-8 pixel; Re=0.180000 arcsec and n=1 to numerical precision).

Using the materially broader published COSMOS-Web PSFs produces only small biases in this paired-difference oracle:

- near-source failure row: delta-mag = +0.0089 to +0.0119 mag, Re = 0.1760-0.1777 arcsec, n = 1.016-1.043, q = 0.610-0.619, centroid excursion = 0.014-0.027 pixel;
- isolated failure row: delta-mag = +0.0069 to +0.0105 mag, Re = 0.1761-0.1779 arcsec, n = 1.018-1.045, q = 0.610-0.619, centroid excursion = 0.014-0.030 pixel.

Thus the D1n-e PSF-shape difference is real, but **PSF mismatch of this measured magnitude by itself does not reproduce the catastrophic D1m AB=26 solutions**. In particular it does not generate order-unity flux bias, large Re inflation, target-bound hits, or large centroid excursions when real-scene contamination is removed.

This does not prove that the effective real-mosaic PSF is irrelevant: PSF mismatch can still interact with an imperfect scene model. It does rule out a simple explanation in which the published-vs-STPSF width difference alone is sufficient to create the two D1m catastrophes.

## Next diagnostic

The two catastrophic D1m solutions are interior optimizer solutions, while D1n-c did not identify a single residual/background statistic that explains both and D1n-f shows that PSF mismatch alone is insufficient. The next smallest causal diagnostic is therefore an **optimizer-basin / objective-identifiability multistart audit** on the frozen D1m real-scene objective.

D1n-g must keep the D1m scene decomposition, STPSF, masks, ERR weighting, target/nuisance bounds, loss, and `max_nfev=500` unchanged. It should run a small, predeclared set of deterministic target starts on the two catastrophic rows plus matched well-recovered controls. An injection-truth start is permitted only as an explicit oracle start, not as a production initialization. The diagnostic question is whether lower-chi-square, truth-like interior minima already exist under the unchanged D1m objective, or whether the real-scene objective itself prefers the catastrophic morphology.

No production framework implementation is authorized by D1n-f.
