# Gate D1d — first real-mosaic L1 injection operator

Frozen before inspecting any injection output.

## Purpose

Inject a controlled disk-like Sérsic source into the checksummed COSMOS-Web DR1 F444W 30 mas A1 cutout at positions selected *before injection* from the successful D1c real-context audit. This stage validates L1 injection arithmetic, photometric units, placement diversity, and plane-preservation semantics. It does **not** perform morphology recovery and does not close Gate D.

## Frozen real input

- Real-cutout run `33941326833`, artifact SHA-256 `764d542f2417810c904bce711455b3eb69c70cf388f97348cb857b056b2dd66d`.
- D1c run `33944133603` completed/success and measured 43 >5-sigma source-like islands with 3.1078% source-pixel occupancy.
- Nine placements are frozen in `COSMOSWEB_D1_INJECTION_MATRIX.json`: three each in near-source (2-5 px), intermediate (8-20 px), and relatively-isolated (>=30 px) regimes. No placement is changed after seeing injection or later recovery outcomes.

## Frozen source and PSF

- Exponential Sérsic (`n=1`), `Re=0.18 arcsec`, axis ratio `q=0.65`, PA=30 deg.
- Two flux regimes: AB=26 and AB=29. These are stress levels, not pass/fail thresholds. Low-S/N non-recovery in the later measurement stage must remain an observable.
- Declared PSF: pinned STPSF 2.2.0 + data 2.2.0, NIRCam/F444W, NRCA5 center, `OVERDIST`, oversample=2, with the explicitly recorded three-point in-band spectral weighting. This is a declared PSF approximation for the first L1 experiment, not an empirical reconstruction of the COSMOS-Web drizzled PSF and not literal survey reproduction.
- The oversampled STPSF image is flux-conservingly resampled to the mosaic pixel scale and renormalized. No PSF-matching/deconvolution operator is used, so no sharper-target convolution issue is invoked.

## Photometric and noise semantics

1. Read `BUNIT` and `PIXAR_SR` from the real SCI header; require `MJy/sr` and a positive finite pixel solid angle.
2. Convert AB total flux to Jy and then to the required sum in MJy/sr pixels using the actual `PIXAR_SR`.
3. Add the PSF-convolved source to SCI only. Do not regenerate or add sky/background.
4. Keep ERR and WHT unchanged. Source shot noise is intentionally **not** added in D1d; the resulting approximation must be quantified separately as required by Gate D.
5. Apply no Tolman dimming or redshift transformation in this injection stage. The source amplitude is already defined directly in observed-frame AB flux, so an additional cosmological dimming factor would double-count the radiometry.
6. Record requested and realized injected flux for every placement/magnitude. Flux mismatch is a hard software/numerical failure; no tolerance is to be widened post hoc.
7. Save all injected SCI scenes plus the untouched original SCI/ERR/WHT and machine-readable provenance so the subsequent recovery workflow can reproduce the exact inputs.

## Interpretation

A green D1d workflow means the real-mosaic injection operator executed reproducibly with the frozen semantics. It is **not** scientific morphology success. The next stage must run the chosen measurement pipeline on every frozen scene and retain low-S/N failures, bound hits, crowding failures, and optimizer failures as results rather than filtering them away.
