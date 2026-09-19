# Gate D0 — COSMOS-Web DR1 real-mosaic access/provenance preflight

Frozen before any real-survey injection result is inspected.

## Purpose

Gate D must test the real survey transfer function rather than another synthetic-only benchmark. The immediate prerequisite is to freeze the exact public COSMOS-Web DR1 product family and L1 injection semantics without silently downloading multi-GB mosaics in CI.

This D0 preflight is **not** a real-source injection and does not close any Gate-D checkbox. It only proves that the declared real products are reachable and records remote provenance validators before a compact, checksummed cutout is archived for D1.

## Frozen public product

- survey/release: COSMOS-Web DR1;
- instrument/filter: JWST/NIRCam F444W;
- pixel scale: 30 mas;
- tile: A1;
- product family: separate `SCI`, `ERR`, and `WHT` extensions published by the COSMOS-Web team;
- public naming convention: `mosaic_nircam_f444w_COSMOS-Web_30mas_A1_v1.0_{sci,err,wht}.fits.gz`;
- base host: `https://cosmos2025.iap.fr/data/nircam/extensions/`.

The COSMOS-Web DR1 documentation states that 30-mas individual `SCI` extensions are typically 1.2–1.7 GB compressed. D0 therefore performs metadata-only HTTP requests and deliberately does not download a tile.

## L1 injection semantics frozen for D1

1. Inject the source model into the real `SCI` cutout only. The observed mosaic already contains real sky/background/noise; no second sky realization is added.
2. Preserve the original WCS exactly and inject in detector/mosaic pixel coordinates derived from that WCS.
3. Preserve the original `ERR` and `WHT` products for the baseline L1 test. Any source-shot-noise augmentation must be a separately declared approximation and compared against the unmodified baseline; it must not be hidden inside the injection step.
4. Use a declared empirical or otherwise provenance-tracked PSF appropriate to the filter/location. A sharper target may not be produced by pure convolution.
5. Record the pre-injection segmentation/context around the placement and do not choose only blank, isolated regions. Crowding/background/segmentation interactions are part of Gate D.
6. Recovery must be measured by the chosen measurement pipeline, not by comparing injected pixels alone.
7. Failures, blends, centroid excursions, segmentation changes, non-detections, and morphology loss are observables. No post-hoc acceptance-band widening is allowed.

## D0 output

For each of SCI/ERR/WHT record URL, HTTP status, content type, content length when available, ETag, Last-Modified, Accept-Ranges, and retrieval timestamp. A D0 process pass means only that the three declared endpoints answered a metadata request consistently enough to proceed with compact-cutout acquisition.

## Decision after D0

D1 should archive a small real 30-mas F444W cutout plus matching ERR/WHT and WCS metadata with checksums. The cutout should include nontrivial real background/crowding rather than a hand-selected empty patch. Only then should the first actual injection/recovery workflow run.
