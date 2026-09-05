# Gate D1b preflight — remote acquisition of one real COSMOS-Web cutout

Frozen before inspecting the real cutout artifact.

## Purpose

Create the first compact real-survey SCI/ERR/WHT bundle directly from the public COSMOS-Web DR1 products so Gate D can proceed without waiting for a local workstation. This stage is **real-data acquisition/ingest only**. It is not yet an injection/recovery result and does not close Gate D.

## Frozen product and sky location

- Survey: COSMOS-Web DR1.
- Instrument/filter: JWST/NIRCam F444W.
- Mosaic sampling: 30 mas/pixel.
- Tile: A1.
- Public products: the separate `SCI`, `ERR`, and `WHT` files already frozen in D0.
- Cutout center: COSMOS2025 catalog object ID 4204, ICRS `(RA, Dec) = (149.8671500, 2.1294010) deg`, which is publicly identified as an A1 source. The center is therefore source-containing by construction rather than selected after looking for an unusually blank patch.
- Cutout size: 512 x 512 pixels = 15.36 x 15.36 arcsec at the declared 30 mas sampling.

The location is a reproducible anchor, not a claim that this one region is representative of all COSMOS-Web environments. Later Gate-D validation must span multiple contexts/tiles.

## Acquisition contract

1. Download each official gzip-compressed product sequentially; do not commit multi-GB mosaics to git.
2. Compute SHA-256 for each downloaded compressed source and record the exact URL and byte size.
3. Read header/WCS metadata to determine the common pixel section around the frozen sky position.
4. SCI is the authoritative sky-coordinate plane and must contain a valid celestial WCS. SCI, ERR, and WHT must have exactly matching image shape.
5. If an ancillary ERR/WHT standalone file contains a celestial WCS, its sky-to-pixel coordinate at the frozen center must agree with SCI to <=0.05 pixel; any mismatch remains a hard failure.
6. If an ancillary standalone file contains **no celestial WCS declaration at all**, do not fabricate an independent coordinate check. Its alignment may instead be accepted only from the conjunction of (a) exact shape agreement, (b) the official COSMOS-Web release semantics that SCI/ERR/WHT are individual planes of the same mosaic product, and (c) extraction of the exact same frozen integer pixel section. This provenance-based mode must be explicitly recorded in the manifest. A malformed/partial celestial WCS declaration remains a hard failure.
7. Extract the same strict 512-pixel image section with CFITSIO `fitscopy`. CFITSIO updates WCS keywords for an image subsection when those keywords exist.
8. For the compact benchmark bundle only, if an ancillary cutout lacks celestial WCS metadata, copy the SCI cutout celestial-WCS keywords into that ancillary extension and record `propagated-from-SCI-co-grid`; pixel values must remain unchanged. This is metadata propagation for a known co-grid ancillary plane, not a resampling operation.
9. Delete each multi-GB compressed source after its compact section and checksum have been produced, limiting runner disk use.
10. Package the compact sections into one FITS artifact with `SCI`, `ERR`, and `WHT` image extensions plus a JSON provenance/diagnostic manifest and a PNG SCI preview.
11. The workflow must not alter SCI pixels, synthesize background/noise, alter ERR/WHT pixel values, add source shot noise, convolve with any PSF, inject a source, or fit/recover morphology.

## Why the WCS rule was clarified after run 33933263708

Run `33933263708` downloaded the official SCI product and reached the official ERR product, then failed before any scientific measurement because Astropy reported zero celestial world inputs for the ERR header. The pre-run code had assumed every standalone ancillary plane duplicated a celestial WCS. That assumption is stronger than the data-product semantics require: COSMOS-Web publishes SCI, ERR, and WHT as separate planes of the same mosaic, while JWST ERR is an uncertainty array corresponding pixel-by-pixel to the science data. Astropy's `.celestial` interface correctly returns no celestial axes when none are declared. The correction therefore changes metadata handling, not any scientific tolerance: whenever ancillary WCS is present, the original <=0.05-pixel criterion is unchanged.

## Interpretation

A successful workflow demonstrates that a checksummed real COSMOS-Web cutout can be reproducibly acquired and ingested on GitHub Actions. It is **not scientific success of Gate D**. The next stage may design the first L1 injection/recovery only after the real artifact is inspected for finite coverage, weights, background structure, sources/crowding, and any masking/edge issues.
