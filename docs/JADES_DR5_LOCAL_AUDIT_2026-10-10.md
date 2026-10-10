# JADES DR5 GOODS-S real-file audit: 2026-10-10

This is a condensed review of the user-supplied `JADES_DR5_audit.json`
and `JADES_DR5_audit.md`, generated locally with Astropy 7.2.0.
**It records observed FITS metadata only. It is not proof that every
download was complete or that final science products are validated.**

## FITS catalog — confirmed

- File: `hlsp_jades_jwst_nircam_goods-s_photometry_v5.0_catalog.fits`
- Local size during audit: **6,174,754,560 bytes (5.7507 GiB)**.
- **13 HDUs:** PRIMARY, FILTERS, FLAG, SIZE, CIRC, CIRC_BSUB,
  CIRC_CONV, CIRC_BSUB_CONV, KRON, KRON_CONV, MIRI, PHOTOZ, PHOTOZ_KRON.
- SIZE, FLAG, PHOTOZ and PHOTOZ_KRON each report **304,366 rows**.
- **SIZE:** `ID` (J, 32-bit integer), `RA`/`DEC` (degrees),
  `A`/`B`/`FWHM` (arcsec), `THETA` (degrees), `GINI`.
- **PHOTOZ / PHOTOZ_KRON:** `ID` (K, 64-bit integer),
  `z_spec`, `z_a`, `z_ml`, `z_peak`, `z500`,
  `l68`, `u68`, `l95`, `u95`, `nfilt`.
- **FLAG:** `ID` (K), `FLAG_BN` (J), per-band `F115W_FLAG`
  (D; units **pix**), `F115W_WHT` (D; **(MJy/sr)^-2**),
  `F115W_TEXP` (D; seconds), similarly for other bands.
- Therefore, join **by ID with explicit integer normalization**;
  do not depend on row order or integer width.
- Flag columns expressed in pixels are not binary quality switches.
- `z_a` is photometric, not necessarily independently spectroscopic
  (though `z_spec` is present). Scientists should decide whether its
  uncertainty is appropriate for each analysis.

## Real NIRCam submosaic FITS — confirmed as observed

For `jw011800-deep23`:

| Band | Size at audit (bytes) | HDUs reported | Status |
|---|---:|---:|---|
| F115W | 4,284,040,320 | 6 | Structural audit OK |
| F150W | 4,284,040,320 | 6 | Structural audit OK |
| F200W | 3,383,927,907 | 5 | **Possibly downloading/truncated; re-audit after wget finishes** |

For the completed F115W and F150W mosaics:

- HDU 0: empty PRIMARY **also labeled `EXTNAME=SCI`**.
- HDU 1: 2-D `SCI`; HDU 2: `ERR`; HDU 3: `EXP`;
  HDU 4: `WHT`; HDU 5: `NIM`.
- SCI and ERR images: **15,300 × 14,000**; `BUNIT='MJy/sr'`.
- Geometric scale: **0.029994759 arcsec/pixel**.
- Audited SCI and ERR WCS centers, corners and scale are identical.
- Header `BUNIT` is present on EXP/WHT/NIM too; **do not treat
  those data as surface brightness or as ERR**.
- The FITS reader must find the **actual two-dimensional SCI image**
  instead of the empty primary with the same EXTNAME.

The first four F200W image HDUs are readable in the audit, but the
fifth/final one and the file-size discrepancy mean it is **not yet
confirmed complete**. The notebook now supports an expected-minimum
HDU guard for these DR5 six-HDU DRZ products.

## Not covered by this audit

The following are still needed before a real end-to-end result can be
accepted:

1. Completed **F200W** file, and re-audit all remaining requested mosaics.
2. The **F444W-A** target SCI/ERR mosaic, on the correct field footprint.
3. Full GOODS-S DR5 **segmentation map** with usable WCS and source IDs.
4. Matched **mPSFs for F115W, F150W, F200W, F444W-A**, including pixel
   sampling and normalization checks.
5. Per-object coverage, source-segmentation identity, source-band
   registration and full-bandpass interpolation support.
6. PSF transformation checks, target-background placement, source
   flux conservation and uncertainty/refit validation on multiple
   **actual** galaxies.

CI with small **synthetic** FITS images exercises the code, but does not
replace these real-data checks. Correlated drizzle-noise covariance and
exposure-level Poisson realizations cannot be reconstructed exactly
from the available final mosaics alone.

## Corresponding notebook updates

- Real JADES DR5 duplicate-SCI-HDU selection.
- Lightweight `SIZE` + `PHOTOZ_KRON` / `PHOTOZ` joins on ID.
- Preserve float per-band FLAG and WHT diagnostics.
- WCS-aware nearest-neighbor alignment of full-field segmentation
  cutouts to science submosaics, with unknown pixels marked -1.
- Integrity check for still-downloading FITS products.
- One-cell `JADES_DATA_ROOT` starter configuration for the minimal
  F115W/F150W/F200W to F444W-A `z=5` pilot.

**Source of facts:** locally generated uploaded audit files; not a claim
of direct access to the user's mounted external drive.
