# Benchmark Data Registry

This registry records external datasets used for scientific verification. Third-party data are **not** copied into this repository unless redistribution is clearly allowed and there is a strong reason to vendor a small immutable file. Prefer reproducible retrieval from a pinned upstream version plus checksums.

Every benchmark dataset entry must record: scientific reference, upstream location, immutable version/commit or archival identifier, license/usage terms, exact files used, expected units/metadata, retrieval procedure, and a local checksum manifest generated after download.

## BDATA-001 — Zhuang & Shen JWST/NIRCam PSF and mock-AGN products

**Science reference**

M.-Y. Zhuang & Y. Shen, *Characterization of JWST NIRCam PSFs and Implications for AGN+Host Image Decomposition*, ApJ 962, 139; arXiv:2304.13776.

**Upstream repository**

`https://github.com/mingyangzhuang/JWST-NIRCam-Data-Product`

**Pinned upstream commit**

`0a55283e973e2dc055ab807e29a04d89733fee48`

Commit message: `Update with new broader and narrower PSF models`.

**License**

The upstream GitHub repository declares an MIT license. Scientific use must still cite the associated paper and preserve upstream attribution.

**Repository contents verified at the pinned commit**

- `CEERS_PSF/PSF_statistics.ipac`
- empirical CEERS PSF FITS files split by pointing/filter/module, including F115W, F150W, F200W, F277W and other bands;
- `mock_AGN_results/Info.ipac`;
- `mock_AGN_results/mock_AGN_input_values.ipac`;
- fiducial, broader-PSF and narrower-PSF recovery tables for multiple NIRCam filters;
- center-not-tied recovery tables for the fiducial PSF experiment.

The upstream `mock_AGN_results/Info.ipac` gives the benchmark PSF FWHMs (mas):

| Filter | Fiducial | Broader | Narrower |
| --- | ---: | ---: | ---: |
| F070W | 64.8 | 66.5 | 62.0 |
| F115W | 60.5 | 62.0 | 59.1 |
| F150W | 64.7 | 64.7 | 63.3 |
| F200W | 75.0 | 76.0 | 74.2 |
| F277W | 119 | 120 | 118 |
| F356W | 138 | 139 | 137 |
| F444W | 160 | 162 | 160 |

These values are properties of the authors' benchmark products. They must **not** be interpreted as universal NIRCam PSF values.

**Retrieval policy**

Gate C should add a retrieval script that downloads only the files required for a selected benchmark from the pinned commit. The script must:

1. refuse an unpinned `main` URL;
2. place downloads under an ignored external-data directory;
3. compute SHA-256 checksums after retrieval;
4. record file sizes and upstream Git blob SHAs where available;
5. never silently replace an existing file with a different checksum.

The large mock tables should not be committed to our Git repository.

## BDATA-002 — CEERS public JWST/NIRCam imaging for survey-transfer validation

**Purpose**

A public real-survey dataset for generic Level-1 mosaic injection and, where calibrated individual exposures can be retrieved, a controlled Level-1 versus Level-2 comparison before the COSMOS-Web-specific validation.

**Required products**

- selected NIRCam science mosaic(s), including WCS and calibrated units;
- corresponding weight/error/context information where available;
- selected calibrated individual exposures for the same footprint if an L2 comparison is performed;
- exact JWST pipeline version / CRDS context when available from headers or archive metadata;
- filter, detector/module, exposure and dither metadata.

**Status**

Registry entry established; exact archival product identifiers and immutable download manifest are still to be frozen. Do not download arbitrary 'latest' products into a benchmark without first recording the public release/version.

## BDATA-003 — COSMOS-Web NIRCam products

**Purpose**

First science-specific Level-1 validation and passive-spiral demonstration, using the same 30-mas imaging environment relevant to the COSMOS-Web morphology work.

**Required products before execution**

- exact 30-mas mosaics for the selected filters/tiles;
- empirical/survey PSFs or the exact PSF-construction inputs used by the target morphology workflow;
- segmentation maps;
- uncertainty/weight/context maps where available;
- complete WCS and calibration headers;
- survey release/version and, for JWST-calibrated products, recoverable CRDS/pipeline provenance where possible.

**Status**

Methodological requirement defined. Exact file inventory is intentionally deferred until Gates B and the controlled Gate-C benchmarks are stable, so that only scientifically necessary products are requested and archived.

## Registry rules

- A benchmark result is invalid if the external-data version cannot be reconstructed later.
- URLs alone are not provenance; immutable commit/archive identifiers and checksums are required.
- Large third-party products remain outside git history.
- Any transformed/cropped benchmark derivative must record the parent checksum and the transformation configuration.
- If an upstream dataset changes or is corrected, create a new registry version rather than silently replacing the previous benchmark.
