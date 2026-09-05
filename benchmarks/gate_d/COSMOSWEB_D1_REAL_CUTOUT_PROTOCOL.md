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
3. Read only header/WCS metadata to determine the common pixel section around the frozen sky position.
4. SCI, ERR, and WHT must have matching image shape and their sky-to-pixel coordinates at the frozen center must agree with SCI to <=0.05 pixel. A mismatch is a hard failure.
5. Extract the same strict 512-pixel image section with CFITSIO `fitscopy`, allowing the source gzip stream to be decompressed without retaining a full uncompressed mosaic.
6. Delete each multi-GB compressed source after its compact section and checksum have been produced, limiting runner disk use.
7. Package the compact sections into one FITS artifact with `SCI`, `ERR`, and `WHT` image extensions plus a JSON provenance/diagnostic manifest and a PNG SCI preview.
8. The workflow must not alter SCI, synthesize background/noise, alter ERR/WHT, add source shot noise, convolve with any PSF, inject a source, or fit/recover morphology.

## Interpretation

A successful workflow demonstrates that a checksummed real COSMOS-Web cutout can be reproducibly acquired and ingested on GitHub Actions. It is **not scientific success of Gate D**. The next stage may design the first L1 injection/recovery only after the real artifact is inspected for finite coverage, weights, background structure, sources/crowding, and any masking/edge issues.
