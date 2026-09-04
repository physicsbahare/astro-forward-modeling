# Gate D1a — local COSMOS-Web real-mosaic ingest bridge

Frozen before inspecting any real-injection result.

## Purpose

The user already has COSMOS-Web DR1 locally. D1a therefore prepares a deterministic bridge from the exact local `SCI`, `ERR`, and `WHT` products into a compact, checksummed cutout bundle that can be used by the first real L1 injection/recovery experiment. CI validates only the interface on synthetic FITS fixtures; CI must not be described as real-survey evidence.

## Frozen input family

- COSMOS-Web DR1, JWST/NIRCam F444W, 30 mas, tile A1.
- Separate `SCI`, `ERR`, and `WHT` FITS products corresponding to the D0 provenance record.
- The local files may be `.fits` or externally gzip-compressed `.fits.gz` files. Astropy supports opening externally gzip-compressed FITS files, but such files may require full decompression during access; uncompressed local FITS is preferred for repeated cutout work.

## Cutout contract

1. The same sky position and square pixel size are applied to SCI/ERR/WHT.
2. The SCI WCS defines the sky-to-pixel placement. ERR/WHT must have the same image shape and an equivalent celestial WCS at the requested position; disagreement is a hard failure.
3. `Cutout2D(..., mode='strict')` is used so an edge-truncated postage stamp cannot silently enter the benchmark.
4. The output is one FITS file containing `SCI`, `ERR`, and `WHT` image extensions with the propagated cutout WCS, plus a JSON manifest.
5. The manifest records source paths, file sizes, source header identity/provenance fields when present, requested center/size, cutout bounds, finite-pixel fractions, and SHA-256 of the compact output. Multi-GB source files are not hashed by default because D0 already froze the remote product identity; optional full-file hashing can be done separately if needed.
6. D1a performs no source injection, no added background/noise, no source-shot-noise augmentation, no PSF manipulation, no segmentation selection, and no recovery. It only creates the real-data bridge.
7. The first scientific D1b placement must be chosen after examining real local context; it must not be restricted to an unusually blank/isolated region. Crowding/background/segmentation effects remain part of Gate D.

## CI semantics

The dedicated workflow creates tiny synthetic FITS fixtures solely to verify file discovery, WCS propagation, strict aligned cutouts, and manifest/checksum generation. A green workflow means the local-data bridge software path is ready. It does **not** mean Gate D scientific validation passed.
