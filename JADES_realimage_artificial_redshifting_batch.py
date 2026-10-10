#!/usr/bin/env python3
# JADES real-image artificial redshifting: standalone Python equivalent.
# Generated directly from JADES_realimage_artificial_redshifting_batch.ipynb.
# NOTEBOOK_ENGINE_CHECKSUM_32: 8cc09d94
#
# Edit the SINGLE USER SETTINGS section below, or change the root path
# in that section for your machine. No import-time mosaics are loaded.

# ================================================================
# NOTEBOOK ENGINE CELL 4
# ================================================================
# INTERNAL - DO NOT EDIT FOR NORMAL USE
from __future__ import annotations

import csv
import gc
import hashlib
import itertools
import json
import math
import os
import platform
import re
import sys
import traceback
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.ndimage import binary_dilation, map_coordinates, shift as ndi_shift, zoom
from scipy.signal import fftconvolve
from scipy.integrate import trapezoid

from astropy.io import fits
from astropy.table import Table
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_scales, proj_plane_pixel_area
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.cosmology import Planck18, FlatLambdaCDM


# ================================================================
# NOTEBOOK ENGINE CELL 6
# ================================================================
# =====================================================================
# USER SETTINGS - EDIT ONLY THIS CELL
# =====================================================================

# ---------- HANDOFF RUN CONTROL ----------
# Start with metadata-only preflight. Set BATCH when all required files pass.
RUN_MODE = "PREFLIGHT_ONLY"   # "PREFLIGHT_ONLY" or "BATCH"
PREFLIGHT_SAMPLE_ROWS = 5    # only a few small source cutouts for identity/WCS checks
PREFLIGHT_CHECK_SPECTRAL_SUPPORT = True

# ---------- INPUT SAMPLE ----------
# CSV, ECSV, or FITS table. One row per source galaxy.
# Change only this root for your machine; the defaults below match the
# minimal GOODS-S jw011800-deep23 JADES DR5 download set.
JADES_DATA_ROOT = Path("/path/to/JADES_DR5_test")  # change only this base directory
INPUT_CATALOG_PATH = str(JADES_DATA_ROOT / "catalogs" /
    "hlsp_jades_jwst_nircam_goods-s_photometry_v5.0_catalog.fits")
INPUT_CATALOG_HDU = None
# "JADES_DR5": join SIZE+PHOTOZ_KRON (or PHOTOZ) internally by ID;
# "TABLE": ordinary CSV/ECSV/FITS table with ID/RA/Dec/redshift columns.
CATALOG_FORMAT = "JADES_DR5"
JADES_REDSHIFT_HDU = "PHOTOZ_KRON"  # use PHOTOZ for aperture photo-z
JADES_REDSHIFT_COL = "z_a"         # alternatives: z500, z_peak, z_ml
JADES_REQUIRE_GOOD_FLAGS = False  # legacy name: if True, require positive WHT in ALL configured source bands
# Optional sample constraints applied before loading image cutouts:
OBJECT_IDS = []             # empty => all objects
SOURCE_Z_RANGE = [0.65, 1.25]  # pilot z range for F115W/F150W/F200W->F444W z=5; None=all
AUTO_SELECT_TARGET_FOOTPRINT = True  # select galaxies in F444W-A subregion for pilot
FOOTPRINT_EDGE_MARGIN_ARCSEC = 5.0
# For science sample, set AUTO_SELECT_TARGET_FOOTPRINT=False if a fixed
# input list already contains objects whose source and target WCS are valid.

# In JADES_DR5 mode these are output column names produced by the adapter.
ID_COL = "ID"
RA_COL = "RA"          # degrees
DEC_COL = "DEC"        # degrees
Z_COL = "z_source"

# If a path below contains placeholders such as {region}, list those
# catalog columns here. Example: PATH_TEMPLATE_COLUMNS = ["region"]
PATH_TEMPLATE_COLUMNS = []

# ---------- SOURCE / NATIVE REAL IMAGES ----------
# Add every source band that may be used for pixel-SED interpolation.
# For JADES DR5, use the exact full-field or subregion products and PSFs
# that correspond to your sample. Do not copy example filenames blindly.
#
# err_kind:
#   "STDDEV"   -> ERR/RMS image
#   "VARIANCE" -> variance image
#   "IVAR"     -> inverse variance image
#
# A local throughput file should contain wavelength + throughput columns.
# If throughput_file is None, SVO is used and cached.
SOURCE_BANDS = {
    band: {
        "sci_path": str(JADES_DATA_ROOT / "mosaics" /
            f"hlsp_jades_jwst_nircam_jw011800-deep23_{band.lower()}_v5.0_drz.fits"),
        "err_path": "SAME_AS_SCI",
        "seg_path": str(JADES_DATA_ROOT / "mosaics" /
            "hlsp_jades_jwst_nircam_goods-s_segmentation_v5.0_drz.fits"),
        "psf_path": str(JADES_DATA_ROOT / "psfs" /
            f"hlsp_jades_jwst_nircam_jw011800-deep23_{band.lower()}_v5.0_mpsf.fits"),
        "sci_ext": "SCI", "err_ext": "ERR", "seg_ext": "AUTO", "psf_ext": "AUTO",
        "expected_min_hdus": 6, # DR5 DRZ expected PRIMARY,SCI,ERR,EXP,WHT,NIM
        "err_kind": "STDDEV",
        "psf_pixel_scale_arcsec": None,   # set only if PSF FITS lacks scale
        "throughput_file": None,
        "throughput_wavelength_unit": "um",
        "svo_id": f"JWST/NIRCam.{band}",
    }
    for band in ("F115W", "F150W", "F200W")
}

# ---------- TARGET / BACKGROUND PRODUCTS ----------
# One entry for every target filter used in TARGET_PLAN.
TARGET_PRODUCTS = {
    "F444W": {
        "sci_path": str(JADES_DATA_ROOT / "mosaics" /
            "hlsp_jades_jwst_nircam_jw011800-deep23_f444wa_v5.0_drz.fits"),
        "err_path": "SAME_AS_SCI",
        "seg_path": str(JADES_DATA_ROOT / "mosaics" /
            "hlsp_jades_jwst_nircam_goods-s_segmentation_v5.0_drz.fits"),
        "psf_path": str(JADES_DATA_ROOT / "psfs" /
            "hlsp_jades_jwst_nircam_jw011800-deep23_f444wa_v5.0_mpsf.fits"),
        "sci_ext": "SCI", "err_ext": "ERR", "seg_ext": "AUTO", "psf_ext": "AUTO",
        "expected_min_hdus": 6, # DR5 DRZ expected PRIMARY,SCI,ERR,EXP,WHT,NIM
        "err_kind": "STDDEV",
        "psf_pixel_scale_arcsec": None,
        "throughput_file": None,
        "throughput_wavelength_unit": "um",
        "svo_id": "JWST/NIRCam.F444W",
    },
}

# Pilot source redshifts are individual PHOTOZ_KRON measurements; only target
# z and filter are fixed. Add other target cases in this cell if desired.
TARGET_PLAN = [{"z": 5.0, "filter": "F444W"}]

# ---------- CUTOUT / SOURCE ISOLATION ----------
SOURCE_CUTOUT_ARCSEC = 6.0
TARGET_CUTOUT_ARCSEC = 6.0
SOURCE_MASK_DILATION_PIX = 2
SOURCE_LABEL_SEARCH_RADIUS_PIX = 4
REQUIRE_SOURCE_SEGMENTATION = True

# ---------- INJECTION POSITIONS ----------
# "CATALOG": use two input-table columns.
# "AUTO_BLANK": deterministic blank-sky search in the target segmentation map.
INJECTION_MODE = "AUTO_BLANK"
INJECTION_RA_COL = "injection_ra"
INJECTION_DEC_COL = "injection_dec"

# For AUTO_BLANK, None means use the target mosaic WCS center.
AUTO_BLANK_CENTER_RA_DEG = None
AUTO_BLANK_CENTER_DEC_DEG = None
AUTO_BLANK_SEARCH_SIZE_ARCSEC = 40.0
AUTO_BLANK_EXCLUSION_RADIUS_ARCSEC = 1.2
AUTO_BLANK_EDGE_MARGIN_ARCSEC = 3.5

# ---------- THROUGHPUT / PIXEL SED ----------
THROUGHPUT_CACHE_DIR = "./jades_throughput_cache"
THROUGHPUT_SUPPORT_FRACTION = 0.01
MAX_SED_CONDITION_NUMBER = 1.0e5

# ---------- PSF TRANSFORMATION ----------
# Empirical Fourier/Wiener matching. The code never intentionally sharpens.
PSF_WIENER_REGULARIZATION = 1.0e-3
PSF_MATCH_L1_MAX = 0.15
PSF_WIDTH_TOLERANCE = 0.03

# ---------- NOISE ----------
# The real target background is NEVER redrawn.
# Source ERR is propagated through the same linear operator with streaming MC.
PROPAGATE_SOURCE_ERR = True
SOURCE_NOISE_MC_DRAWS = 12
FLUX_CONSERVATION_TOLERANCE = 0.12
SOURCE_ERR_SCALE = 1.0
TARGET_ERR_SCALE = 1.0
RANDOM_SEED = 20261010

# ---------- JADES-STYLE REFIT ----------
RUN_NATIVE_REFIT = True  # obtain native reference morphology at matched wavelength
REFIT_MODE = "NUTS"      # "NUTS" for science, "MAP" for a quick software test
PYSERSIC_WARMUP = 1000
PYSERSIC_SAMPLES = 250
PYSERSIC_CHAINS = 1
PYSERSIC_N_MIN = 0.65
PYSERSIC_N_MAX = 8.0
PYSERSIC_ELLIP_MAX = 0.9
FIT_MASK_DILATION_PIX = 4
MAX_FIT_IMAGE_PIX = 161  # center crop before PySersic; reduces JAX RAM use
MAX_FIT_PSF_LOST_SIGNED_FLUX = 0.03

# The published JADES morphology fitting uses sky_type="none". JADES mosaics
# are already background corrected, so leave this False unless your exact
# target product has a documented residual scalar sky that must be removed.
SUBTRACT_LOCAL_TARGET_BACKGROUND = False

# Optional: copy native/reference morphology from the input catalog so the
# batch summary can report recovered-minus-reference changes. Leave a value
# as None when that quantity is unavailable.
REFERENCE_MORPHOLOGY_COLUMNS = {
    "n": None,
    "re_arcsec": None,
    "q": None,
    "pa_rad": None,
}

# ---------- COSMOLOGY ----------
COSMOLOGY_CONFIG = {"name": "Planck18"}
# Alternative:
# COSMOLOGY_CONFIG = {"name": "FlatLambdaCDM", "H0": 70.0, "Om0": 0.3}

# ---------- OUTPUT / RESUME ----------
OUTPUT_DIR = "./JADES_realimage_artificial_redshifting"
SAVE_INTERMEDIATE_FITS = True
SAVE_DIAGNOSTIC_PNG = True
RESUME = True
FORCE_RERUN_CASES = []   # list of exact case IDs
MAX_CASES = 5             # change to None to run full selected sample

# =====================================================================


# ================================================================
# NOTEBOOK ENGINE CELL 8
# ================================================================
# INTERNAL - DO NOT EDIT FOR NORMAL USE

class PipelineFailure(RuntimeError):
    def __init__(self, code, message, terminal=True):
        super().__init__(f"[{code}] {message}")
        self.code = str(code)
        self.terminal = bool(terminal)

@dataclass
class Cutout:
    data: np.ndarray
    wcs: WCS
    header: fits.Header
    pixel_scale_arcsec: float
    pixel_area_sr: float
    bunit: str
    bbox: tuple
    full_shape: tuple
    path: str
    ext: object

@dataclass
class ThroughputCurve:
    band: str
    wavelength_um: np.ndarray
    throughput: np.ndarray
    provenance: str

@dataclass
class PSFInfo:
    array: np.ndarray
    pixel_scale_arcsec: float
    rms_radius_arcsec: float
    provenance: str

def _jsonable(x):
    if isinstance(x, (str, int, float, bool)) or x is None:
        return x
    if isinstance(x, Path):
        return str(x)
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)):
        return [_jsonable(v) for v in x]
    return str(x)

def atomic_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)

def append_log(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(str(text).rstrip() + "\n")

def sanitize_case_id(x):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(x))

def resolve_template(value, row, extra=None):
    if value is None:
        return None
    if value == "SAME_AS_SCI":
        return value
    mapping = {c: row[c] for c in PATH_TEMPLATE_COLUMNS if c in row.index}
    if extra:
        mapping.update(extra)
    try:
        return str(value).format(**mapping)
    except KeyError as exc:
        raise PipelineFailure("PATH_TEMPLATE_COLUMN_MISSING",
                              f"Missing template value {exc} for path {value!r}")

def load_catalog(path, hdu=None):
    """Read only essential catalog columns when using JADES DR5 multi-HDU FITS.

    The DR5 photometric catalog is not a flat table: SIZE holds sky coordinates,
    PHOTOZ/PHOTOZ_KRON holds z_a/z500/etc, and FLAG holds coverage flags.
    Never read the whole 6+GB catalog as a pandas DataFrame.
    """
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(p)
    fmt = str(CATALOG_FORMAT).upper()
    if fmt == "JADES_DR5":
        if p.suffix.lower() not in {".fits", ".fit", ".fz"}:
            raise PipelineFailure("CATALOG_TYPE_MISMATCH",
                                  "CATALOG_FORMAT='JADES_DR5' requires a DR5 FITS catalog.")
        with fits.open(p, memmap=True, lazy_load_hdus=True) as hdul:
            for ext in ("SIZE", JADES_REDSHIFT_HDU):
                if ext not in hdul:
                    raise PipelineFailure("CATALOG_HDU_MISSING", f"{ext} not found in {p}.")
            size = hdul["SIZE"].data
            zz = hdul[JADES_REDSHIFT_HDU].data
            for col in ("ID", "RA", "DEC"):
                if col not in size.dtype.names:
                    raise PipelineFailure("CATALOG_COL_MISSING", f"SIZE.{col} not found.")
            if "ID" not in zz.dtype.names or JADES_REDSHIFT_COL not in zz.dtype.names:
                raise PipelineFailure("CATALOG_COL_MISSING",
                                      f"{JADES_REDSHIFT_HDU}: requires ID and {JADES_REDSHIFT_COL}.")
            sky_df = pd.DataFrame({
                "ID": np.asarray(size["ID"], dtype=np.int64).copy(),
                "RA": np.asarray(size["RA"], float).copy(),
                "DEC": np.asarray(size["DEC"], float).copy(),
            })
            z_df = pd.DataFrame({
                "ID": np.asarray(zz["ID"], dtype=np.int64).copy(),
                "z_source": np.asarray(zz[JADES_REDSHIFT_COL], float).copy(),
            })
            # Validate one-to-one ID semantics (not merely equal row number).
            df = sky_df.merge(z_df, on="ID", how="inner", validate="one_to_one")
            if "FLAG" in hdul:
                ff = hdul["FLAG"].data
                if "ID" in ff.dtype.names:
                    quality = {"ID": np.asarray(ff["ID"], dtype=np.int64).copy()}
                    if "FLAG_BN" in ff.dtype.names:
                        quality["FLAG_BN"] = np.asarray(ff["FLAG_BN"], dtype=np.int32).copy()
                    for b in SOURCE_BANDS:
                        # DR5 *_FLAG columns are float-valued with pixel units,
                        # not boolean good/bad flags: preserve NaN and precision.
                        for suffix in ("_FLAG", "_WHT", "_TEXP"):
                            key = f"{b}{suffix}"
                            if key in ff.dtype.names:
                                quality[key] = np.asarray(ff[key], dtype=np.float64).copy()
                    df = df.merge(pd.DataFrame(quality), on="ID", how="left", validate="one_to_one")
            if JADES_REQUIRE_GOOD_FLAGS:
                # Legacy setting now means nonzero inverse-variance coverage,
                # never FLAG == 0 (the DR5 FLAG columns are pixel quantities).
                weight_cols = [f"{b}_WHT" for b in SOURCE_BANDS if f"{b}_WHT" in df]
                if weight_cols:
                    df = df.loc[np.isfinite(df[weight_cols]).all(axis=1) &
                                (df[weight_cols] > 0).all(axis=1)].copy()
        if PATH_TEMPLATE_COLUMNS:
            raise PipelineFailure("CATALOG_PATH_TEMPLATES",
                                  "For region-specific path templates use a prebuilt flat input table.")
    elif fmt == "TABLE":
        s = p.suffix.lower()
        if s in {".csv", ".txt"}:
            df = pd.read_csv(p)
        elif s == ".ecsv":
            df = Table.read(p, format="ascii.ecsv").to_pandas()
        elif s in {".fits", ".fit", ".fz"}:
            t = Table.read(p, hdu=hdu) if hdu is not None else Table.read(p)
            df = t.to_pandas()
        else:
            raise ValueError(f"Unsupported catalog format: {p.suffix}")
    else:
        raise ValueError(f"Unknown CATALOG_FORMAT={CATALOG_FORMAT!r}")
    required = [ID_COL, RA_COL, DEC_COL, Z_COL] + list(PATH_TEMPLATE_COLUMNS)
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Input catalog missing columns: {missing}")
    if df[ID_COL].duplicated().any():
        raise ValueError("Input IDs must be unique.")
    # Keep unsupported z values in batch receipts rather than silently select.
    return df

def get_cosmology():
    name = str(COSMOLOGY_CONFIG.get("name", "Planck18"))
    if name == "Planck18":
        return Planck18
    if name == "FlatLambdaCDM":
        return FlatLambdaCDM(H0=float(COSMOLOGY_CONFIG["H0"]),
                             Om0=float(COSMOLOGY_CONFIG["Om0"]))
    raise ValueError(f"Unsupported COSMOLOGY_CONFIG: {COSMOLOGY_CONFIG}")

COSMOLOGY = get_cosmology()

def _choose_hdu(hdul, ext, preferred=("SCI",)):
    """Select a real 2-D image, including when PRIMARY and ImageHDU share EXTNAME.

    Actual JADES DR5 submosaics have EXTNAME=SCI on both the empty primary
    and the 2-D science extension. hdul["SCI"] alone selects the wrong HDU.
    Inspect headers first to avoid loading a giant image into RAM.
    """
    def is_2d_image(h):
        return isinstance(h, (fits.PrimaryHDU, fits.ImageHDU, fits.CompImageHDU)) and (
            int(h.header.get("NAXIS", 0)) == 2
            and int(h.header.get("NAXIS1", 0)) > 0
            and int(h.header.get("NAXIS2", 0)) > 0
        )
    if isinstance(ext, str) and ext.isdecimal():
        ext = int(ext)
    if isinstance(ext, int):
        try:
            h = hdul[ext]
        except Exception as exc:
            raise PipelineFailure("HDU_NOT_FOUND", f"Index {ext} not found") from exc
        if not is_2d_image(h):
            raise PipelineFailure("HDU_NOT_IMAGE", f"Index {ext} is not a 2-D image HDU")
        return h
    wanted = [ext] if ext not in (None, "AUTO") else list(preferred)
    for name in wanted:
        for h in hdul:
            if str(h.header.get("EXTNAME", "")).upper() == str(name).upper() and is_2d_image(h):
                return h
    if ext not in (None, "AUTO"):
        raise PipelineFailure("HDU_NOT_FOUND", f"No 2-D image named {ext!r}")
    for h in hdul:
        if is_2d_image(h):
            return h
    raise PipelineFailure("NO_2D_HDU", "No usable 2-D image HDU found.")

def _pixel_geometry(header):
    w = WCS(header)
    if not w.has_celestial:
        raise PipelineFailure("NO_CELESTIAL_WCS", "Image has no celestial WCS.")
    scales = proj_plane_pixel_scales(w.celestial) * 3600.0
    scale = float(np.sqrt(abs(scales[0] * scales[1])))
    try:
        area_sr = float(abs(proj_plane_pixel_area(w.celestial)) * (np.pi / 180.0) ** 2)
    except Exception:
        area_sr = float((scale / 206265.0) ** 2)
    if not np.isfinite(scale) or scale <= 0 or not np.isfinite(area_sr) or area_sr <= 0:
        raise PipelineFailure("INVALID_PIXEL_SCALE", "Could not establish a valid pixel scale.")
    return w.celestial, scale, area_sr

def _to_mjy_sr(data, bunit, pixel_area_sr):
    unit = str(bunit or "").strip().lower().replace(" ", "")
    a = np.asarray(data, dtype=np.float32)
    if unit in {"mjy/sr", "mjypersteradian", "mjy/sr."}:
        return a
    if unit in {"jy/sr"}:
        return a / 1.0e6
    if unit in {"jy/pixel", "jy/pix"}:
        return a / float(pixel_area_sr) / 1.0e6
    if unit in {"mjy/pixel", "mjy/pix"}:
        return a * 1.0e-3 / float(pixel_area_sr) / 1.0e6
    if unit in {"ujy/pixel", "ujy/pix", "μjy/pixel", "μjy/pix"}:
        return a * 1.0e-6 / float(pixel_area_sr) / 1.0e6
    if unit in {"njy/pixel", "njy/pix"}:
        return a * 1.0e-9 / float(pixel_area_sr) / 1.0e6
    raise PipelineFailure("UNSUPPORTED_BUNIT",
                          f"Unsupported BUNIT={bunit!r}. Expected a declared surface-brightness or per-pixel flux unit.")

def _err_to_stddev(err, kind):
    k = str(kind).upper()
    e = np.asarray(err, dtype=np.float32)
    if k in {"STDDEV", "ERR", "RMS"}:
        out = e
    elif k == "VARIANCE":
        out = np.sqrt(np.where(e >= 0, e, np.nan))
    elif k in {"IVAR", "INVERSE_VARIANCE"}:
        out = np.where(e > 0, 1.0 / np.sqrt(e), np.nan)
    else:
        raise PipelineFailure("UNKNOWN_ERR_KIND",
                              f"err_kind={kind!r} is unsupported. WHT is not silently treated as ERR.")
    return out.astype(np.float32)

def mosaic_center_sky(path, ext):
    with fits.open(Path(path).expanduser(), memmap=True, lazy_load_hdus=True) as hdul:
        h = _choose_hdu(hdul, ext, ("SCI",))
        if h.data is None or np.ndim(h.data) != 2:
            raise PipelineFailure("NO_IMAGE", f"No 2-D science image in {path}")
        w, _, _ = _pixel_geometry(h.header)
        ny, nx = h.data.shape
        return w.pixel_to_world((nx - 1) / 2.0, (ny - 1) / 2.0)

def read_cutout(path, ext, ra_deg, dec_deg, size_arcsec, preferred=("SCI",), convert_sb=True):
    p = Path(path).expanduser()
    if not p.exists():
        raise PipelineFailure("FILE_NOT_FOUND", str(p), terminal=False)
    with fits.open(p, memmap=True, lazy_load_hdus=True) as hdul:
        hdu = _choose_hdu(hdul, ext, preferred)
        if hdu.data is None or np.ndim(hdu.data) != 2:
            raise PipelineFailure("NO_IMAGE", f"{p} extension {ext!r} is not a 2-D image.")
        w, pix, area = _pixel_geometry(hdu.header)
        sky = SkyCoord(float(ra_deg) * u.deg, float(dec_deg) * u.deg)
        x, y = w.world_to_pixel(sky)
        # Some Astropy WCS versions return length-one arrays for scalar SkyCoord.
        x, y = float(np.asarray(x).ravel()[0]), float(np.asarray(y).ravel()[0])
        if not np.isfinite(x) or not np.isfinite(y):
            raise PipelineFailure("COORD_OUTSIDE", f"Coordinate cannot be projected into {p}")
        # Nearest integer pixel radius avoids floating-WCS roundoff
        # expanding a nominally full-frame cutout by an extra pixel.
        half = max(2, int(round(0.5 * float(size_arcsec) / pix)))
        xc, yc = int(round(x)), int(round(y))
        ny, nx = hdu.data.shape
        x0, x1 = xc - half, xc + half + 1
        y0, y1 = yc - half, yc + half + 1
        if x0 < 0 or y0 < 0 or x1 > nx or y1 > ny:
            raise PipelineFailure("CUTOUT_OUTSIDE", f"Requested cutout reaches outside {p}")
        # Important: only this small slice is copied into RAM.
        arr = np.array(hdu.data[y0:y1, x0:x1], dtype=np.float32, copy=True)
        hdr = hdu.header.copy()
        cut_wcs = w.slice((slice(y0, y1), slice(x0, x1)))
        bunit = str(hdu.header.get("BUNIT", ""))
        if convert_sb:
            arr = _to_mjy_sr(arr, bunit, area)
            outunit = "MJy/sr"
        else:
            outunit = bunit
        return Cutout(arr, cut_wcs, hdr, pix, area, outunit,
                      (x0, x1, y0, y1), (ny, nx), str(p), ext)

def read_aux_cutout(path, ext, ra_deg, dec_deg, size_arcsec, preferred, sci_pixel_scale=None):
    return read_cutout(path, ext, ra_deg, dec_deg, size_arcsec, preferred=preferred, convert_sb=False)

def resolve_product(product, row, band):
    out = {}
    path_keys = {"sci_path", "err_path", "seg_path", "psf_path", "throughput_file"}
    for k, v in product.items():
        out[k] = resolve_template(v, row, {"filter": band.lower(), "FILTER": band}) if k in path_keys else v
    if out.get("err_path") == "SAME_AS_SCI":
        out["err_path"] = out["sci_path"]
    return out

def read_segmentation_on_science_grid(path, ext, sci):
    """Extract segmentation labels on the SCI cutout WCS using nearest pixels.

    DR5 official segmentation is a full-field mosaic while SCI may be a
    subregion. WCS-aligned nearest-neighbour sampling is required before
    comparing labels. Read only the bounding rectangle of needed SEG pixels.
    """
    p = Path(path).expanduser()
    if not p.exists():
        raise PipelineFailure("SEG_FILE_NOT_FOUND", str(p), terminal=False)
    ny, nx = sci.data.shape
    yy, xx = np.indices((ny, nx), dtype=np.float64)
    ra, dec = sci.wcs.pixel_to_world_values(xx, yy)
    with fits.open(p, memmap=True, lazy_load_hdus=True) as hdul:
        h = _choose_hdu(hdul, ext, ("SEG", "SEGM", "SEGMENTATION"))
        seg_wcs, _, _ = _pixel_geometry(h.header)
        sx, sy = seg_wcs.world_to_pixel_values(ra, dec)
        sy_pix, sx_pix = np.rint(sy), np.rint(sx)
        full_ny, full_nx = int(h.header["NAXIS2"]), int(h.header["NAXIS1"])
        valid = (np.isfinite(sx_pix) & np.isfinite(sy_pix) &
                 (sx_pix >= 0) & (sx_pix < full_nx) &
                 (sy_pix >= 0) & (sy_pix < full_ny))
        # Small (<2%) losses only at the outer edge can arise when an
        # independently gridded segmentation image has a subpixel offset.
        # The source/injection center must always be covered.
        central = valid[max(0, ny//2-2):ny//2+3, max(0, nx//2-2):nx//2+3]
        if not np.all(central) or np.mean(valid) < 0.98:
            raise PipelineFailure("SEGMENTATION_COVERAGE_FAIL",
                                  f"{p} covers only {100*np.mean(valid):.2f}% of science cutout "
                                  "or lacks the central pixels.")
        ix = np.asarray(sx_pix[valid], dtype=np.int64)
        iy = np.asarray(sy_pix[valid], dtype=np.int64)
        x0, x1 = int(ix.min()), int(ix.max())+1
        y0, y1 = int(iy.min()), int(iy.max())+1
        sub = np.array(h.data[y0:y1, x0:x1], dtype=np.int64, copy=True)
        labels = np.full((ny, nx), -1, dtype=np.int64)
        labels[valid] = sub[iy-y0, ix-x0]
        return labels

_FITS_INTEGRITY_CACHE = {}

def validate_mosaic_file_integrity(path, expected_min_hdus=None):
    """Cheap structural integrity guard against using still-downloading FITS.

    Each downloaded image is examined once per size/mtime. No 2-D image is
    ever copied to RAM; HDU headers and fileinfo offsets are checked.
    """
    p = Path(path).expanduser()
    if not p.exists():
        raise PipelineFailure("FILE_NOT_FOUND", str(p), terminal=False)
    st = p.stat()
    key = (str(p.resolve()), st.st_size, st.st_mtime_ns, expected_min_hdus)
    if key in _FITS_INTEGRITY_CACHE:
        return
    with fits.open(p, memmap=True, lazy_load_hdus=True) as hdul:
        if expected_min_hdus is not None and len(hdul) < int(expected_min_hdus):
            raise PipelineFailure(
                "INCOMPLETE_FITS_DOWNLOAD",
                f"{p.name} contains {len(hdul)} readable HDUs; "
                f"the configured DR5 release expects at least {expected_min_hdus}. "
                "Finish the wget download and rerun the FITS audit.", terminal=False)
        for i in range(len(hdul)):
            info = hdul.fileinfo(i)
            if info is None:
                continue
            end = int(info.get("datLoc", 0) or 0) + int(info.get("datSpan", 0) or 0)
            if end > st.st_size:
                raise PipelineFailure(
                    "TRUNCATED_FITS_HDU",
                    f"{p.name}: HDU {i} extends to byte {end:,}, "
                    f"but file size is only {st.st_size:,}. Download is incomplete.", terminal=False)
    _FITS_INTEGRITY_CACHE[key] = True

def read_science_err_seg(product, row, band, ra, dec, size_arcsec):
    p = resolve_product(product, row, band)
    validate_mosaic_file_integrity(p["sci_path"], p.get("expected_min_hdus"))
    sci = read_cutout(p["sci_path"], p.get("sci_ext", "SCI"), ra, dec, size_arcsec, ("SCI",), True)
    err_raw = read_cutout(p["err_path"], p.get("err_ext", "ERR"), ra, dec, size_arcsec, ("ERR",), False)
    if not grids_coincident(sci, err_raw):
        raise PipelineFailure("ERR_GRID_MISMATCH",
                              f"{band}: SCI and ERR differ in WCS/grid. Reproject externally onto the SCI grid.")
    err_native = _err_to_stddev(err_raw.data, p.get("err_kind", "STDDEV"))
    err = _to_mjy_sr(err_native, err_raw.header.get("BUNIT", sci.header.get("BUNIT", "")),
                     err_raw.pixel_area_sr)
    seg = None
    if p.get("seg_path") not in {None, "", "..."}:
        seg = read_segmentation_on_science_grid(p["seg_path"], p.get("seg_ext", 0), sci)
    return sci, err.astype(np.float32), seg, p

def source_product_has_coverage(product, row, band, ra_deg, dec_deg):
    """Cheap per-object coverage check without loading a mosaic into RAM."""
    p = resolve_product(product, row, band)
    path = Path(p["sci_path"]).expanduser()
    if not path.exists():
        raise PipelineFailure("FILE_NOT_FOUND", str(path), terminal=False)
    with fits.open(path, memmap=True, lazy_load_hdus=True) as hdul:
        hdu = _choose_hdu(hdul, p.get("sci_ext", "SCI"), ("SCI",))
        if hdu.data is None or np.ndim(hdu.data) != 2:
            raise PipelineFailure("NO_IMAGE", f"{path}: no 2-D science image.")
        w, _, _ = _pixel_geometry(hdu.header)
        x, y = w.world_to_pixel(SkyCoord(float(ra_deg) * u.deg, float(dec_deg) * u.deg))
        x, y = float(np.asarray(x).ravel()[0]), float(np.asarray(y).ravel()[0])
        ny, nx = hdu.data.shape
        if not (np.isfinite(x) and np.isfinite(y) and 0 <= x < nx and 0 <= y < ny):
            return False
        # Read only one pixel. A non-finite center normally means no usable
        # coverage at the source position; another configured band may still work.
        v = hdu.data[int(round(y)), int(round(x))]
        return bool(np.isfinite(v))

def _to_um(wave, unit):
    a = np.asarray(wave, float)
    u0 = str(unit).lower()
    if u0 in {"um", "micron", "microns"}:
        return a
    if u0 in {"nm", "nanometer", "nanometers"}:
        return a / 1000.0
    if u0 in {"a", "aa", "angstrom", "angstroms"}:
        return a / 1.0e4
    raise ValueError(f"Unknown wavelength unit: {unit}")

def _clean_curve(band, lam, thr, provenance):
    lam = np.asarray(lam, float)
    thr = np.asarray(thr, float)
    ok = np.isfinite(lam) & np.isfinite(thr) & (lam > 0) & (thr >= 0)
    lam, thr = lam[ok], thr[ok]
    order = np.argsort(lam)
    lam, thr = lam[order], thr[order]
    lam_u, inv = np.unique(lam, return_inverse=True)
    if len(lam_u) != len(lam):
        sums = np.zeros(len(lam_u)); nums = np.zeros(len(lam_u))
        np.add.at(sums, inv, thr); np.add.at(nums, inv, 1)
        lam, thr = lam_u, sums / nums
    if len(lam) < 10 or trapezoid(thr, lam) <= 0:
        raise PipelineFailure("INVALID_THROUGHPUT", f"{band}: unusable throughput curve.")
    return ThroughputCurve(str(band), lam, thr, str(provenance))

def load_throughput(band, cfg):
    local = cfg.get("throughput_file")
    if local not in {None, "", "..."}:
        p = Path(local).expanduser()
        if not p.exists():
            raise PipelineFailure("THROUGHPUT_FILE_NOT_FOUND", str(p))
        arr = np.genfromtxt(p, comments="#")
        if arr.ndim != 2 or arr.shape[1] < 2:
            raise PipelineFailure("INVALID_THROUGHPUT", f"{p}: need at least 2 columns.")
        return _clean_curve(band, _to_um(arr[:, 0], cfg.get("throughput_wavelength_unit", "um")),
                            arr[:, 1], f"local:{p.resolve()}")
    svo_id = cfg.get("svo_id")
    if not svo_id:
        raise PipelineFailure("NO_THROUGHPUT", f"{band}: no local curve or SVO ID.")
    cache = Path(THROUGHPUT_CACHE_DIR)
    cache.mkdir(parents=True, exist_ok=True)
    cp = cache / (str(svo_id).replace("/", "_") + ".csv")
    if cp.exists():
        a = np.genfromtxt(cp, delimiter=",", names=True)
        return _clean_curve(band, a["wavelength_um"], a["throughput"], f"SVO-cache:{cp.resolve()}")
    try:
        from astroquery.svo_fps import SvoFps
        tab = SvoFps.get_transmission_data(svo_id)
    except Exception as exc:
        raise PipelineFailure("SVO_DOWNLOAD_FAILED",
                              f"{band}: SVO download failed; provide throughput_file or restore network access.", terminal=False) from exc
    wc = tab["Wavelength"]
    try:
        lam = wc.quantity.to_value(u.um)
    except Exception:
        lam = np.asarray(wc, float) / 1e4
    thr = np.asarray(tab["Transmission"], float)
    c = _clean_curve(band, lam, thr, f"SVO:{svo_id}")
    with cp.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["wavelength_um", "throughput"])
        w.writerows(zip(c.wavelength_um, c.throughput))
    return c

def pivot_um(c):
    l, t = c.wavelength_um, c.throughput
    return float(np.sqrt(trapezoid(t * l, l) / trapezoid(t / l, l)))

def mapped_curve(c, zs, zt):
    s = (1.0 + float(zs)) / (1.0 + float(zt))
    return ThroughputCurve(c.band + "_mapped", c.wavelength_um * s, c.throughput.copy(),
                           c.provenance + f"; map_factor={s:.12g}")

def significant_support(c):
    keep = c.throughput >= THROUGHPUT_SUPPORT_FRACTION * np.nanmax(c.throughput)
    if np.count_nonzero(keep) < 2:
        raise PipelineFailure("THROUGHPUT_SUPPORT_FAIL", c.band)
    x = c.wavelength_um[keep]
    return float(x.min()), float(x.max())

def band_moment(c, lam0, scale, power):
    l, t = c.wavelength_um, c.throughput
    w = t / l
    den = trapezoid(w, l)
    x = (l - lam0) / scale
    return float(trapezoid((x ** power) * w, l) / den)

def choose_sed_plan(source_curves, target_curve_mapped):
    ptarget = pivot_um(target_curve_mapped)
    slo, shi = significant_support(target_curve_mapped)
    piv = {b: pivot_um(c) for b, c in source_curves.items()}
    bands = sorted(piv, key=piv.get)
    combos = []
    for n in (3, 2):
        if len(bands) < n:
            continue
        for combo in itertools.combinations(bands, n):
            vals = [piv[b] for b in combo]
            if min(vals) <= slo and max(vals) >= shi:
                lam0 = ptarget
                scale = max(max(vals) - min(vals), 1e-6)
                M = np.array([[band_moment(source_curves[b], lam0, scale, k)
                               for k in range(n)] for b in combo], float)
                v = np.array([band_moment(target_curve_mapped, lam0, scale, k)
                              for k in range(n)], float)
                A = M.T
                cond = float(np.linalg.cond(A))
                if np.isfinite(cond):
                    try:
                        weights = np.linalg.solve(A, v)
                    except np.linalg.LinAlgError:
                        continue
                    score = cond * (1.0 + 0.01 * np.sum(np.abs(weights)))
                    combos.append((score, combo, weights, cond, lam0, scale))
        if combos:
            break
    if not combos:
        raise PipelineFailure(
            "SPECTRAL_SUPPORT_FAIL",
            f"Mapped target support {slo:.4f}-{shi:.4f} um is not bracketed by source-band pivots {piv}."
        )
    score, combo, weights, cond, lam0, scale = min(combos, key=lambda x: x[0])
    if cond > MAX_SED_CONDITION_NUMBER:
        raise PipelineFailure("SED_ILL_CONDITIONED",
                              f"Pixel-SED moment system condition number {cond:.3g} exceeds limit.")
    return {
        "bands": list(combo), "weights": np.asarray(weights, float),
        "condition_number": cond, "mapped_pivot_um": ptarget,
        "mapped_support_um": [slo, shi], "source_pivots_um": {b: piv[b] for b in combo},
        "basis_lam0_um": lam0, "basis_scale_um": scale,
        "sum_abs_weights": float(np.sum(np.abs(weights))),
    }

def _psf_scale_from_header(header):
    try:
        w, s, _ = _pixel_geometry(header)
        return s
    except Exception:
        for key in ("PIXSCALE", "PIXELSCL"):
            if key in header and float(header[key]) > 0:
                return float(header[key])
    return None

def _normalize_psf(a):
    x = np.asarray(a, dtype=np.float64)
    if x.ndim != 2 or not np.all(np.isfinite(x)):
        raise PipelineFailure("INVALID_PSF", "PSF must be a finite 2-D array.")
    s = float(np.sum(x))
    if not np.isfinite(s) or abs(s) < 1e-12:
        raise PipelineFailure("INVALID_PSF", "PSF signed sum is zero/non-finite.")
    return x / s

def _odd_center_crop_or_pad(a, shape):
    ty, tx = shape
    out = np.zeros((ty, tx), float)
    sy, sx = a.shape
    cy, cx = (sy - 1) / 2.0, (sx - 1) / 2.0
    oy, ox = (ty - 1) / 2.0, (tx - 1) / 2.0
    yy0 = max(0, int(math.floor(oy - cy)))
    xx0 = max(0, int(math.floor(ox - cx)))
    yy1 = min(ty, yy0 + sy)
    xx1 = min(tx, xx0 + sx)
    ay0 = max(0, int(math.floor(cy - oy)))
    ax0 = max(0, int(math.floor(cx - ox)))
    ay1 = ay0 + (yy1 - yy0); ax1 = ax0 + (xx1 - xx0)
    out[yy0:yy1, xx0:xx1] = a[ay0:ay1, ax0:ax1]
    return out

def _recentre_psf(a):
    x = _normalize_psf(a)
    pos = np.clip(x, 0, None)
    if pos.sum() <= 0:
        pos = np.abs(x)
    yy, xx = np.indices(x.shape, dtype=float)
    cx = float(np.sum(pos * xx) / np.sum(pos))
    cy = float(np.sum(pos * yy) / np.sum(pos))
    tx, ty = (x.shape[1] - 1) / 2.0, (x.shape[0] - 1) / 2.0
    return _normalize_psf(ndi_shift(x, (ty - cy, tx - cx), order=3, mode="constant", cval=0.0))

def psf_rms_radius_arcsec(a, pix):
    x = np.clip(np.asarray(a, float), 0, None)
    if x.sum() <= 0:
        x = np.abs(np.asarray(a, float))
    yy, xx = np.indices(x.shape, dtype=float)
    cx = np.sum(x * xx) / np.sum(x); cy = np.sum(x * yy) / np.sum(x)
    r2 = ((xx - cx) ** 2 + (yy - cy) ** 2) * float(pix) ** 2
    return float(np.sqrt(np.sum(x * r2) / np.sum(x)))

def read_psf(product_resolved, science_pixel_scale):
    p = Path(product_resolved["psf_path"]).expanduser()
    if not p.exists():
        raise PipelineFailure("PSF_FILE_NOT_FOUND", str(p), terminal=False)
    with fits.open(p, memmap=True, lazy_load_hdus=True) as hdul:
        h = _choose_hdu(hdul, product_resolved.get("psf_ext", 0), ("PSF", "SCI"))
        a = np.array(h.data, dtype=np.float64, copy=True)
        hdr = h.header.copy()
    ps = product_resolved.get("psf_pixel_scale_arcsec")
    if ps in {None, "", "..."}:
        ps = _psf_scale_from_header(hdr)
    if ps is None:
        raise PipelineFailure("PSF_SCALE_UNKNOWN",
                              f"{p}: PSF pixel scale not found; set psf_pixel_scale_arcsec in USER SETTINGS.")
    ps = float(ps)
    a = _recentre_psf(a)
    if abs(ps / science_pixel_scale - 1.0) > 1e-3:
        fac = ps / float(science_pixel_scale)
        a = zoom(a, fac, order=3, mode="constant", cval=0.0, prefilter=True)
        if a.shape[0] % 2 == 0:
            a = np.pad(a, ((0, 1), (0, 0)))
        if a.shape[1] % 2 == 0:
            a = np.pad(a, ((0, 0), (0, 1)))
        a = _recentre_psf(a)
        ps = float(science_pixel_scale)
    return PSFInfo(a, ps, psf_rms_radius_arcsec(a, ps), str(p))

def grids_coincident(a, b, tol_pix=0.10):
    """Compare WCS at center and four corners; never silently shift/rotate masks."""
    if a.data.shape != b.data.shape:
        return False
    ny, nx = a.data.shape
    for x, y in ((0, 0), (nx-1, 0), (0, ny-1),
                 (nx-1, ny-1), ((nx-1)/2, (ny-1)/2)):
        sky = a.wcs.pixel_to_world(float(x), float(y))
        xb, yb = b.wcs.world_to_pixel(sky)
        xb, yb = float(np.asarray(xb).ravel()[0]), float(np.asarray(yb).ravel()[0])
        if not np.isfinite(xb) or not np.isfinite(yb):
            return False
        if np.hypot(xb-x, yb-y) > tol_pix:
            return False
    return True

def same_source_grid(cutouts):
    vals = list(cutouts.values())
    ref = vals[0]
    return all(grids_coincident(ref, v) for v in vals[1:])

def fourier_matching_kernel(source_psf, target_psf):
    ny = max(source_psf.shape[0], target_psf.shape[0])
    nx = max(source_psf.shape[1], target_psf.shape[1])
    if ny % 2 == 0: ny += 1
    if nx % 2 == 0: nx += 1
    s = _normalize_psf(_odd_center_crop_or_pad(source_psf, (ny, nx)))
    t = _normalize_psf(_odd_center_crop_or_pad(target_psf, (ny, nx)))
    S = np.fft.fft2(np.fft.ifftshift(s))
    T = np.fft.fft2(np.fft.ifftshift(t))
    power = np.abs(S) ** 2
    lam = float(PSF_WIENER_REGULARIZATION) * max(float(power.max()), 1e-30)
    K = np.conj(S) * T / (power + lam)
    k = np.fft.fftshift(np.fft.ifft2(K).real)
    k = _normalize_psf(k)
    matched = _normalize_psf(fftconvolve(s, k, mode="same"))
    l1 = float(np.sum(np.abs(matched - t)) / max(np.sum(np.abs(t)), 1e-30))
    neg_fraction = float(np.sum(np.abs(k[k < 0])) / max(np.sum(np.abs(k)), 1e-30))
    return k, {"l1_residual": l1, "negative_kernel_fraction": neg_fraction}

def check_degradation_only(source_psf, target_psf, pix, label):
    rs = psf_rms_radius_arcsec(source_psf, pix)
    rt = psf_rms_radius_arcsec(target_psf, pix)
    if rt < rs * (1.0 - PSF_WIDTH_TOLERANCE):
        raise PipelineFailure("PSF_SHARPENING_REQUIRED",
                              f"{label}: target PSF RMS radius {rt:.5f} < source {rs:.5f} arcsec.")
    k, audit = fourier_matching_kernel(source_psf, target_psf)
    if audit["l1_residual"] > PSF_MATCH_L1_MAX:
        raise PipelineFailure("PSF_MATCH_FAIL",
                              f"{label}: empirical PSF match L1 residual={audit['l1_residual']:.3f}.")
    audit.update({"source_rms_radius_arcsec": rs, "target_rms_radius_arcsec": rt})
    return k, audit

def write_fits(path, data, wcs, bunit="MJy/sr"):
    hdr = wcs.to_header()
    hdr["BUNIT"] = bunit
    fits.PrimaryHDU(np.asarray(data, np.float32), header=hdr).writeto(path, overwrite=True)


# ================================================================
# NOTEBOOK ENGINE CELL 10
# ================================================================
# INTERNAL - DO NOT EDIT FOR NORMAL USE

def find_source_label(seg, radius_pix, expected_id=None):
    ny, nx = seg.shape
    cy, cx = (ny - 1) / 2.0, (nx - 1) / 2.0
    yy, xx = np.indices(seg.shape)
    r2 = (xx - cx) ** 2 + (yy - cy) ** 2
    labels = seg[(r2 <= float(radius_pix) ** 2) & (seg > 0)]
    if labels.size == 0:
        raise PipelineFailure("SOURCE_LABEL_NOT_FOUND", "No segmentation label found near source coordinate.")
    vals, counts = np.unique(labels, return_counts=True)
    if expected_id is not None:
        try:
            eid = int(expected_id)
            if eid in vals:
                return eid
        except (TypeError, ValueError):
            pass
    chosen = int(vals[np.argmax(counts)])
    if expected_id is not None:
        # DR5 segmentation labels are unique source IDs. Never transfer a
        # nearby contaminant just because it overlaps the search circle.
        raise PipelineFailure(
            "SOURCE_ID_SEGMENTATION_MISMATCH",
            f"Galaxy ID={expected_id} is absent from the central segmentation search; "
            f"nearest detected label={chosen}. Check image/segmentation release and WCS.")
    return chosen

def isolate_source(sci, err, seg, object_id=None):
    if seg is None:
        if REQUIRE_SOURCE_SEGMENTATION:
            raise PipelineFailure("SOURCE_SEG_REQUIRED",
                                  "Source segmentation is required by USER SETTINGS but was not supplied.")
        # Deliberately conservative fallback: central positive connected support.
        med = float(np.nanmedian(sci.data))
        sigma = float(np.nanmedian(np.abs(sci.data - med)) * 1.4826)
        mask = np.isfinite(sci.data) & (sci.data > med + 1.5 * sigma)
        warnings.warn("No source segmentation: threshold fallback is being used.")
    else:
        lab = find_source_label(seg, SOURCE_LABEL_SEARCH_RADIUS_PIX, expected_id=object_id)
        mask = seg == lab
        if SOURCE_MASK_DILATION_PIX > 0:
            mask = binary_dilation(mask, iterations=int(SOURCE_MASK_DILATION_PIX))
        # Never admit pixels explicitly assigned to another segmentation label.
        mask &= (seg == 0) | (seg == lab)
    if np.count_nonzero(mask) < 5:
        raise PipelineFailure("SOURCE_MASK_TOO_SMALL", "Transferable source mask has fewer than 5 pixels.")
    blank = (~mask) if seg is None else ((seg == 0) & (~mask))
    good_blank = blank & np.isfinite(sci.data)
    if np.count_nonzero(good_blank) < 20:
        raise PipelineFailure("NO_LOCAL_BACKGROUND", "Too few local blank pixels for source background estimate.")
    bg = float(np.nanmedian(sci.data[good_blank]))
    stamp = np.zeros_like(sci.data, dtype=np.float32)
    stamp[mask] = (sci.data[mask] - bg).astype(np.float32)
    e = np.zeros_like(err, dtype=np.float32)
    valid_err = mask & np.isfinite(err) & (err > 0)
    e[valid_err] = (err[valid_err] * float(SOURCE_ERR_SCALE)).astype(np.float32)
    empirical = float(np.nanmedian(np.abs((sci.data[good_blank] - bg))) * 1.4826)
    reported = float(np.nanmedian(err[good_blank])) if np.any(np.isfinite(err[good_blank])) else np.nan
    return stamp, e, mask, {
        "background_mjy_sr": bg,
        "blank_empirical_sigma_mjy_sr": empirical,
        "blank_median_err_mjy_sr": reported,
        "blank_empirical_over_err": empirical / reported if reported > 0 else np.nan,
    }

def homogenize_source_bands(stamps, errs, psfs):
    # Reference is the broadest empirical source PSF among selected bands.
    ref_band = max(psfs, key=lambda b: psfs[b].rms_radius_arcsec)
    ref = psfs[ref_band].array
    out = {}
    kernels = {}
    audits = {}
    for b in stamps:
        if b == ref_band:
            out[b] = stamps[b].astype(np.float32)
            kernels[b] = None
            audits[b] = {"reference": True, "l1_residual": 0.0}
        else:
            k, audit = check_degradation_only(psfs[b].array, ref,
                                              psfs[ref_band].pixel_scale_arcsec,
                                              f"source homogenization {b}->{ref_band}")
            out[b] = fftconvolve(stamps[b], k, mode="same").astype(np.float32)
            kernels[b] = k
            audits[b] = audit
    return out, kernels, ref_band, _normalize_psf(ref), audits

def combine_pixel_sed(homogenized, weights, bands):
    stack = np.stack([np.asarray(homogenized[b], np.float64) for b in bands], axis=0)
    w = np.asarray(weights, float)[:, None, None]
    return np.sum(w * stack, axis=0).astype(np.float32)

def resample_sb_to_target(image, source_pix, target_pix, angular_scale, target_shape):
    if angular_scale <= 0:
        raise PipelineFailure("INVALID_ANGULAR_SCALE", str(angular_scale))
    src = np.asarray(image, float)
    nyo, nxo = map(int, target_shape)
    cxi, cyi = (src.shape[1] - 1) / 2.0, (src.shape[0] - 1) / 2.0
    cxo, cyo = (nxo - 1) / 2.0, (nyo - 1) / 2.0
    yy, xx = np.indices((nyo, nxo), dtype=float)
    src_x = cxi + (xx - cxo) * float(target_pix) / (float(angular_scale) * float(source_pix))
    src_y = cyi + (yy - cyo) * float(target_pix) / (float(angular_scale) * float(source_pix))
    return map_coordinates(src, [src_y, src_x], order=1, mode="constant", cval=0.0,
                           prefilter=False).astype(np.float32)

def rescale_psf_to_target(source_psf, source_pix, target_pix, angular_scale, target_shape):
    p = resample_sb_to_target(source_psf, source_pix, target_pix, angular_scale, target_shape)
    return _recentre_psf(p)

def inu_redshift_factor(zs, zt):
    return float(((1.0 + float(zs)) / (1.0 + float(zt))) ** 3)

def angular_scale_factor(zs, zt):
    da_s = COSMOLOGY.angular_diameter_distance(float(zs)).value
    da_t = COSMOLOGY.angular_diameter_distance(float(zt)).value
    if not np.isfinite(da_s) or not np.isfinite(da_t) or da_s <= 0 or da_t <= 0:
        raise PipelineFailure("COSMOLOGY_FAIL", f"DA(source)={da_s}, DA(target)={da_t}")
    return float(da_s / da_t)

def _source_noise_sigma_mc(errs, hom_kernels, bands, weights, source_pix, target_pix,
                           angular_scale, target_shape, target_kernel, redshift_factor, seed):
    n_draw = int(SOURCE_NOISE_MC_DRAWS)
    if not PROPAGATE_SOURCE_ERR or n_draw < 2:
        return np.zeros(target_shape, np.float32), {"draws": 0}
    rng = np.random.default_rng(int(seed))
    mean = np.zeros(target_shape, np.float64)
    M2 = np.zeros(target_shape, np.float64)
    for j in range(n_draw):
        combined = np.zeros_like(next(iter(errs.values())), dtype=np.float64)
        for wi, b in zip(weights, bands):
            e = np.asarray(errs[b], float)
            noise = rng.normal(0.0, np.where(np.isfinite(e), e, 0.0))
            k = hom_kernels[b]
            if k is not None:
                noise = fftconvolve(noise, k, mode="same")
            combined += float(wi) * noise
        tr = resample_sb_to_target(combined, source_pix, target_pix, angular_scale, target_shape)
        tr *= float(redshift_factor)
        tr = fftconvolve(tr, target_kernel, mode="same")
        delta = tr - mean
        mean += delta / (j + 1)
        M2 += delta * (tr - mean)
    var = M2 / max(n_draw - 1, 1)
    return np.sqrt(np.maximum(var, 0)).astype(np.float32), {
        "draws": n_draw,
        "note": "Per-pixel ERR propagation through the linear transfer operator; drizzle covariance is not reconstructed."
    }

def transformed_support(mask, source_pix, target_pix, angular_scale, target_shape):
    m = resample_sb_to_target(mask.astype(float), source_pix, target_pix, angular_scale, target_shape)
    out = m > 0.05
    if FIT_MASK_DILATION_PIX > 0:
        out = binary_dilation(out, iterations=int(FIT_MASK_DILATION_PIX))
    return out


# ================================================================
# NOTEBOOK ENGINE CELL 12
# ================================================================
# INTERNAL - DO NOT EDIT FOR NORMAL USE

# Cache blank-sky candidate grids per target product, not per galaxy.
# A large batch should not reread the same full-field segmentation region
# and recompute its candidate mask for every injected source.
_BLANK_SKY_CACHE = {}

def _deterministic_index(case_id, n):
    h = hashlib.sha256((str(RANDOM_SEED) + "::" + str(case_id)).encode()).hexdigest()
    return int(h[:16], 16) % int(n)

def find_auto_blank(product, row, band, case_id):
    p = resolve_product(product, row, band)
    if p.get("seg_path") in {None, "", "..."}:
        raise PipelineFailure("TARGET_SEG_REQUIRED",
                              "AUTO_BLANK requires a target segmentation map.")
    if AUTO_BLANK_CENTER_RA_DEG is None or AUTO_BLANK_CENTER_DEC_DEG is None:
        center = mosaic_center_sky(p["sci_path"], p.get("sci_ext", "SCI"))
        cra, cdec = float(center.ra.deg), float(center.dec.deg)
    else:
        cra, cdec = float(AUTO_BLANK_CENTER_RA_DEG), float(AUTO_BLANK_CENTER_DEC_DEG)
    key = (p["seg_path"], str(p.get("seg_ext", "AUTO")),
           round(cra, 8), round(cdec, 8),
           float(AUTO_BLANK_SEARCH_SIZE_ARCSEC),
           float(AUTO_BLANK_EXCLUSION_RADIUS_ARCSEC),
           float(AUTO_BLANK_EDGE_MARGIN_ARCSEC))
    if key not in _BLANK_SKY_CACHE:
        search = read_aux_cutout(p["seg_path"], p.get("seg_ext", "AUTO"), cra, cdec,
                                 AUTO_BLANK_SEARCH_SIZE_ARCSEC,
                                 ("SEG", "SEGM", "SEGMENTATION"))
        seg = np.asarray(np.rint(search.data), dtype=np.int64)
        pix = search.pixel_scale_arcsec
        rad = int(math.ceil(float(AUTO_BLANK_EXCLUSION_RADIUS_ARCSEC) / pix))
        edge = int(math.ceil(float(AUTO_BLANK_EDGE_MARGIN_ARCSEC) / pix))
        candidates = []
        step = max(rad, 2)
        ny, nx = seg.shape
        for y in range(edge, ny - edge, step):
            for x in range(edge, nx - edge, step):
                y0, y1 = max(0, y-rad), min(ny, y+rad+1)
                x0, x1 = max(0, x-rad), min(nx, x+rad+1)
                if np.all(seg[y0:y1, x0:x1] == 0):
                    candidates.append((x, y))
        if not candidates:
            raise PipelineFailure("NO_BLANK_INJECTION_POSITION",
                                  "No blank target position found in configured AUTO_BLANK search region.")
        xx, yy = np.asarray(candidates, float).T
        ra, dec = search.wcs.pixel_to_world_values(xx, yy)
        _BLANK_SKY_CACHE[key] = np.column_stack((ra, dec))
    candidates_sky = _BLANK_SKY_CACHE[key]
    ra, dec = candidates_sky[_deterministic_index(case_id, len(candidates_sky))]
    return float(ra), float(dec), {
        "mode": "AUTO_BLANK", "n_candidates": len(candidates_sky),
        "search_center_deg": [cra, cdec], "blank_candidates_cached": True,
    }

def choose_injection_position(row, product, band, case_id):
    mode = str(INJECTION_MODE).upper()
    if mode == "CATALOG":
        if INJECTION_RA_COL not in row.index or INJECTION_DEC_COL not in row.index:
            raise PipelineFailure("INJECTION_COLUMNS_MISSING",
                                  f"Need {INJECTION_RA_COL!r}/{INJECTION_DEC_COL!r} in input table.")
        return float(row[INJECTION_RA_COL]), float(row[INJECTION_DEC_COL]), {"mode": "CATALOG"}
    if mode == "AUTO_BLANK":
        return find_auto_blank(product, row, band, case_id)
    raise ValueError(f"Unknown INJECTION_MODE={INJECTION_MODE!r}")

def validate_target_blank(seg, pix):
    if seg is None:
        return {"target_segmentation_checked": False}
    ny, nx = seg.shape
    yy, xx = np.indices(seg.shape)
    r = np.hypot(xx - (nx-1)/2.0, yy - (ny-1)/2.0) * pix
    bad = (r <= AUTO_BLANK_EXCLUSION_RADIUS_ARCSEC) & (seg != 0)
    if np.any(bad):
        raise PipelineFailure("INJECTION_NOT_BLANK",
                              "Target segmentation contains an object inside the protected injection radius.")
    return {"target_segmentation_checked": True}

def _posterior_stats(results):
    idata = results.idata
    out = {}
    for name in ("xc", "yc", "flux", "r_eff", "n", "ellip", "theta"):
        if name not in idata.posterior:
            continue
        a = np.asarray(idata.posterior[name], float).ravel()
        a = a[np.isfinite(a)]
        if a.size:
            q16, q50, q84 = np.quantile(a, [0.16, 0.50, 0.84])
            out[name] = {"q16": float(q16), "median": float(q50), "q84": float(q84),
                         "mean": float(np.mean(a)), "sd": float(np.std(a, ddof=1)) if a.size > 1 else 0.0}
    return out

def run_pysersic_fit(image, rms, psf, source_support, pixel_scale_arcsec, seed):
    try:
        import jax
        from jax.random import PRNGKey
        from pysersic.priors import SourceProperties
        from pysersic import FitSingle
        from pysersic.loss import gaussian_loss
    except Exception as exc:
        raise PipelineFailure("PYSERSIC_IMPORT_FAIL",
                              "PySersic/JAX could not be imported. Install the requirements file.") from exc

    # Center-crop all fit input arrays to bound JAX compile/memory costs.
    # Preserve a local patch around the known injection position.
    data = np.asarray(image, np.float64)
    sig = np.asarray(rms, np.float64)
    support = np.asarray(source_support, bool)
    fit_n = min(int(MAX_FIT_IMAGE_PIX), data.shape[0], data.shape[1])
    if fit_n % 2 == 0:
        fit_n -= 1
    if fit_n < 15:
        raise PipelineFailure("FIT_STAMP_TOO_SMALL", f"Fit image size {fit_n} is too small.")
    cy, cx = data.shape[0] // 2, data.shape[1] // 2
    y0, x0 = cy - fit_n // 2, cx - fit_n // 2
    sl = (slice(y0, y0 + fit_n), slice(x0, x0 + fit_n))
    data, sig, support = data[sl].copy(), sig[sl].copy(), support[sl].copy()

    psf_arr = _normalize_psf(psf)
    if psf_arr.shape[0] > fit_n or psf_arr.shape[1] > fit_n:
        # JADES Carreira et al. PSFs must be no larger than the fitting image.
        cropped = _odd_center_crop_or_pad(psf_arr, (fit_n, fit_n))
        retained = float(np.sum(cropped))
        if not np.isfinite(retained) or abs(1.0 - retained) > float(MAX_FIT_PSF_LOST_SIGNED_FLUX):
            raise PipelineFailure("FIT_PSF_TRUNCATED",
                                  f"PSF cannot be cropped to {fit_n} pixels; retained signed flux={retained:.5f}.")
        psf_arr = cropped
    psf0 = _normalize_psf(psf_arr).astype(np.float64)
    good = support & np.isfinite(data) & np.isfinite(sig) & (sig > 0)
    if np.count_nonzero(good) < 20:
        raise PipelineFailure("FIT_MASK_TOO_SMALL", "Fewer than 20 usable fit pixels.")
    if np.count_nonzero(good) > 0.80 * good.size:
        warnings.warn("Fit mask covers over 80% of cutout; check segmentation and source stamp.")
    bad_mask = ~good

    # JADES DR5 morphology fitting does not fit sky; subtract a local robust
    # residual level using pixels outside the source support before the fit.
    sky_pixels = (~support) & np.isfinite(data)
    if SUBTRACT_LOCAL_TARGET_BACKGROUND and np.count_nonzero(sky_pixels) >= 20:
        sky = float(np.nanmedian(data[sky_pixels]))
    else:
        sky = 0.0
    fit_data = data - sky

    props = SourceProperties(image=fit_data, mask=bad_mask)
    prior = props.generate_prior("sersic", sky_type="none")
    prior.set_uniform_prior("n", float(PYSERSIC_N_MIN), float(PYSERSIC_N_MAX))
    prior.set_uniform_prior("ellip", 0.0, float(PYSERSIC_ELLIP_MAX))
    prior.set_uniform_prior("theta", 0.0, 2.0 * np.pi)

    fitter = FitSingle(data=fit_data, rms=sig, psf=psf0, prior=prior,
                       mask=bad_mask, loss_func=gaussian_loss)

    mode = str(REFIT_MODE).upper()
    if mode == "NUTS":
        fitter.sample(rkey=PRNGKey(int(seed)),
                      num_samples=int(PYSERSIC_SAMPLES),
                      num_warmup=int(PYSERSIC_WARMUP),
                      num_chains=int(PYSERSIC_CHAINS),
                      return_model=True)
        res = fitter.sampling_results
        stats = _posterior_stats(res)
        summary = res.summary()
        model = None
        try:
            model = np.asarray(res.get_median_model(), float)
        except Exception:
            pass
        result = {
            "mode": "NUTS",
            "posterior": stats,
            "summary_records": summary.reset_index().rename(columns={"index": "parameter"}).to_dict("records"),
        }
        if "r_eff" in stats:
            result["recovered_re_pix"] = stats["r_eff"]["median"]
            result["recovered_re_arcsec"] = stats["r_eff"]["median"] * float(pixel_scale_arcsec)
        if "n" in stats:
            result["recovered_n"] = stats["n"]["median"]
        if "ellip" in stats:
            result["recovered_q"] = 1.0 - stats["ellip"]["median"]
        if "theta" in stats:
            result["recovered_pa_rad"] = stats["theta"]["median"]
        result["local_sky_subtracted_mjy_sr"] = sky
        return result, model

    if mode == "MAP":
        m = fitter.find_MAP(rkey=PRNGKey(int(seed)))
        result = {"mode": "MAP", "local_sky_subtracted_mjy_sr": sky}
        model = None
        for k, v in m.items():
            if k == "model":
                try:
                    model = np.asarray(v, float)
                except Exception:
                    pass
            else:
                # MAP parameter values are 0-dimensional JAX arrays; 
                # np.isscalar(jax.Array(...)) is False, so inspect ndim.
                try:
                    value = np.asarray(v)
                    if value.ndim == 0 and np.isfinite(value):
                        result[k] = float(value)
                except (TypeError, ValueError):
                    pass
        if "r_eff" in result:
            result["recovered_re_pix"] = result["r_eff"]
            result["recovered_re_arcsec"] = result["r_eff"] * float(pixel_scale_arcsec)
        if "n" in result:
            result["recovered_n"] = result["n"]
        if "ellip" in result:
            result["recovered_q"] = 1.0 - result["ellip"]
        if "theta" in result:
            result["recovered_pa_rad"] = result["theta"]
        return result, model

    raise ValueError(f"Unknown REFIT_MODE={REFIT_MODE!r}")


# ================================================================
# NOTEBOOK ENGINE CELL 14
# ================================================================
# INTERNAL - DO NOT EDIT FOR NORMAL USE

_CURVE_CACHE = {}

def curve_for(band, cfg):
    key = (band, str(cfg.get("throughput_file")), str(cfg.get("svo_id")))
    if key not in _CURVE_CACHE:
        _CURVE_CACHE[key] = load_throughput(band, cfg)
    return _CURVE_CACHE[key]

def prepare_case_source(row, zs, zt, target_band):
    target_cfg = TARGET_PRODUCTS[target_band]
    target_curve = curve_for(target_band, target_cfg)
    mapped = mapped_curve(target_curve, zs, zt)

    source_curves = {}
    no_coverage = []
    for b, cfg in SOURCE_BANDS.items():
        if source_product_has_coverage(cfg, row, b, float(row[RA_COL]), float(row[DEC_COL])):
            source_curves[b] = curve_for(b, cfg)
        else:
            no_coverage.append(b)
    if len(source_curves) < 2:
        raise PipelineFailure(
            "INSUFFICIENT_SOURCE_BAND_COVERAGE",
            f"Only {list(source_curves)} have usable source coverage; missing/no-coverage={no_coverage}."
        )
    plan = choose_sed_plan(source_curves, mapped)
    plan["configured_bands_without_source_coverage"] = no_coverage
    bands = plan["bands"]

    sci_cuts, errs, segs, resolved, psfs = {}, {}, {}, {}, {}
    stamps, stamp_errs, masks, bg_audits = {}, {}, {}, {}
    for b in bands:
        sci, err, seg, p = read_science_err_seg(SOURCE_BANDS[b], row, b,
                                                float(row[RA_COL]), float(row[DEC_COL]),
                                                SOURCE_CUTOUT_ARCSEC)
        sci_cuts[b], errs[b], segs[b], resolved[b] = sci, err, seg, p
        st, er, ma, audit = isolate_source(sci, err, seg, object_id=row[ID_COL])
        stamps[b], stamp_errs[b], masks[b], bg_audits[b] = st, er, ma, audit
        psfs[b] = read_psf(p, sci.pixel_scale_arcsec)

    if not same_source_grid(sci_cuts):
        raise PipelineFailure(
            "SOURCE_GRID_MISMATCH",
            "Selected source-band cutouts are not on a common registered grid. "
            "Use aligned JADES products/subregions; this notebook will not silently warp them."
        )

    # The source support is the union of independently identified source
    # pixels. Each band retains its own per-band segmentation masking so
    # unrelated neighbours from another band never become part of the source.
    master = np.zeros_like(next(iter(masks.values())), bool)
    for m in masks.values():
        master |= m
    for b in bands:
        stamps[b] = np.where(masks[b], stamps[b], 0).astype(np.float32)
        stamp_errs[b] = np.where(masks[b], stamp_errs[b], 0).astype(np.float32)

    hom, hom_kernels, ref_band, common_psf, psf_audits = homogenize_source_bands(
        stamps, stamp_errs, psfs
    )
    source_plane = combine_pixel_sed(hom, plan["weights"], bands)
    source_pix = sci_cuts[bands[0]].pixel_scale_arcsec

    return {
        "plan": plan, "bands": bands, "source_plane": source_plane,
        "source_pix": source_pix, "source_pixel_area_sr": sci_cuts[bands[0]].pixel_area_sr,
        "source_wcs": sci_cuts[bands[0]].wcs,
        "master_mask": master, "stamp_errs": stamp_errs,
        "hom_kernels": hom_kernels, "common_psf": common_psf,
        "common_psf_band": ref_band,
        "psf_homogenization": psf_audits, "source_backgrounds": bg_audits,
        "source_paths": {b: resolved[b] for b in bands},
    }

def _native_combined_rms(stamp_errs, hom_kernels, weights, bands):
    """Propagate independent-pixel variance through source PSF homogenization.

    The estimate does not reconstruct input drizzle/interpolation covariance.
    """
    ref = np.asarray(stamp_errs[bands[0]], float)
    total_var = np.zeros_like(ref)
    for wi, b in zip(weights, bands):
        sig2 = np.asarray(stamp_errs[b], float) ** 2
        ker = hom_kernels[b]
        if ker is not None:
            sig2 = fftconvolve(sig2, np.asarray(ker, float) ** 2, mode="same")
        total_var += float(wi) ** 2 * np.maximum(sig2, 0)
    return np.sqrt(np.maximum(total_var, 0)).astype(np.float32)

def _flux_transfer_audit(source_sb, target_sb, source_area_sr, target_area_sr, angular_factor, inu_factor):
    """Check signed total flux against the SB + angular-rescaling prediction."""
    f_source_jy = float(np.nansum(source_sb)) * 1e6 * float(source_area_sr)
    f_target_jy = float(np.nansum(target_sb)) * 1e6 * float(target_area_sr)
    expected = f_source_jy * float(inu_factor) * float(angular_factor)**2
    if not np.isfinite(expected) or not np.isfinite(f_target_jy) or abs(expected) < 1e-20:
        raise PipelineFailure("FLUX_NORMALIZATION_INVALID",
                              f"source={f_source_jy} Jy, target={f_target_jy} Jy, expected={expected} Jy")
    residual = float(abs(f_target_jy / expected - 1.0))
    if residual > float(FLUX_CONSERVATION_TOLERANCE):
        raise PipelineFailure("FLUX_CONSERVATION_FAIL",
                              f"Transformed source flux differs by {residual:.3g} relative from predicted "
                              f"cosmology-only total ({f_target_jy:.5g} vs {expected:.5g} Jy).")
    return {
        "source_integrated_fnu_jy": f_source_jy,
        "expected_target_fnu_jy": expected,
        "observed_target_source_only_fnu_jy": f_target_jy,
        "relative_signed_flux_residual": residual,
        "tolerance": float(FLUX_CONSERVATION_TOLERANCE),
    }

def seed_for(case_id, offset=0):
    h = hashlib.sha256((str(RANDOM_SEED) + "::" + str(case_id)).encode()).hexdigest()
    return (int(h[:8], 16) + int(offset)) % (2**31 - 1)

def save_diagnostic(case_dir, background, source_only, injected, rms, fit_support, model=None):
    if not SAVE_DIAGNOSTIC_PNG:
        return
    arrays = [background, source_only, injected, rms]
    titles = ["real target background", "redshifted source only", "injected", "combined RMS"]
    if model is not None:
        arrays += [model, injected - model]
        titles += ["PySersic model", "data - model"]
    n = len(arrays)
    fig, axes = plt.subplots(1, n, figsize=(4*n, 4))
    axes = np.atleast_1d(axes)
    for ax, a, title in zip(axes, arrays, titles):
        a = np.asarray(a, float)
        finite = a[np.isfinite(a)]
        if finite.size:
            lo, hi = np.nanpercentile(finite, [2, 98])
        else:
            lo, hi = 0, 1
        ax.imshow(a, origin="lower", vmin=lo, vmax=hi, cmap="gray")
        ax.set_title(title)
        ax.set_xticks([]); ax.set_yticks([])
    fig.tight_layout()
    fig.savefig(Path(case_dir) / "diagnostic.png", dpi=150)
    plt.close(fig)

def run_case(row, zt, target_band, case_id, case_dir):
    zs = float(row[Z_COL])
    if not np.isfinite(zs) or zs <= 0:
        raise PipelineFailure("INVALID_SOURCE_REDSHIFT", f"z_source={zs}")
    if float(zt) <= zs:
        raise PipelineFailure("TARGET_NOT_HIGHER",
                              f"z_target={zt} must be greater than z_source={zs}.")
    if target_band not in TARGET_PRODUCTS:
        raise PipelineFailure("TARGET_FILTER_NOT_CONFIGURED", target_band)

    source = prepare_case_source(row, zs, float(zt), target_band)
    target_product = TARGET_PRODUCTS[target_band]
    inj_ra, inj_dec, inj_audit = choose_injection_position(row, target_product,
                                                            target_band, case_id)
    target_sci, target_err, target_seg, target_resolved = read_science_err_seg(
        target_product, row, target_band, inj_ra, inj_dec, TARGET_CUTOUT_ARCSEC
    )
    blank_audit = validate_target_blank(target_seg, target_sci.pixel_scale_arcsec)
    target_psf = read_psf(target_resolved, target_sci.pixel_scale_arcsec)

    ang = angular_scale_factor(zs, float(zt))
    inu = inu_redshift_factor(zs, float(zt))
    target_shape = target_sci.data.shape
    transformed = resample_sb_to_target(source["source_plane"], source["source_pix"],
                                        target_sci.pixel_scale_arcsec, ang, target_shape)
    transformed *= inu

    # The source PSF is embedded in the real source pixels. It shrinks/grows
    # with the same angular transform, then is matched only by degradation to
    # the actual target PSF.
    rescaled_source_psf = rescale_psf_to_target(
        source["common_psf"], source["source_pix"], target_sci.pixel_scale_arcsec,
        ang, target_psf.array.shape
    )
    target_kernel, target_psf_audit = check_degradation_only(
        rescaled_source_psf, target_psf.array, target_sci.pixel_scale_arcsec,
        f"target match {target_band}"
    )
    source_only = fftconvolve(transformed, target_kernel, mode="same").astype(np.float32)
    flux_audit = _flux_transfer_audit(
        source["source_plane"], source_only,
        source["source_pixel_area_sr"], target_sci.pixel_area_sr,
        ang, inu
    )

    fit_support = transformed_support(source["master_mask"], source["source_pix"],
                                      target_sci.pixel_scale_arcsec, ang, target_shape)

    source_sigma, source_noise_audit = _source_noise_sigma_mc(
        source["stamp_errs"], source["hom_kernels"], source["bands"],
        source["plan"]["weights"], source["source_pix"], target_sci.pixel_scale_arcsec,
        ang, target_shape, target_kernel, inu, seed_for(case_id, 101)
    )

    terr = np.asarray(target_err, np.float32) * float(TARGET_ERR_SCALE)
    combined_rms = np.sqrt(np.maximum(terr, 0) ** 2 + np.maximum(source_sigma, 0) ** 2).astype(np.float32)
    injected = (np.asarray(target_sci.data, np.float32) + source_only).astype(np.float32)

    native_fit = None
    if RUN_NATIVE_REFIT:
        native_sig = _native_combined_rms(
            source["stamp_errs"], source["hom_kernels"],
            source["plan"]["weights"], source["bands"])
        # Outside segmented galaxy there is no transferred source pixel; all
        # fitting pixels must have a strictly positive noise estimate.
        positive_sigma = native_sig[np.isfinite(native_sig) & (native_sig > 0)]
        if positive_sigma.size == 0:
            raise PipelineFailure("NATIVE_ERR_EMPTY", "No valid source uncertainty for reference fit.")
        native_sig = np.where(native_sig > 0, native_sig, np.median(positive_sigma))
        native_fit, _ = run_pysersic_fit(
            source["source_plane"], native_sig, source["common_psf"], source["master_mask"],
            source["source_pix"], seed_for(case_id, 202)
        )
    fit_result, model = run_pysersic_fit(
        injected, combined_rms, target_psf.array, fit_support,
        target_sci.pixel_scale_arcsec, seed_for(case_id, 303)
    )
    if native_fit:
        diffs = {}
        for k in ("recovered_n", "recovered_re_arcsec", "recovered_q"):
            a, b = native_fit.get(k), fit_result.get(k)
            if a is not None and b is not None:
                diffs["delta_" + k.removeprefix("recovered_")] = float(b) - float(a)
        fit_result["difference_from_native_reference"] = diffs
    # PySersic fits a compact central stamp to reduce JAX RAM usage.
    # Put its model back onto the target cutout for WCS-safe FITS output.
    if model is not None and np.shape(model) != np.shape(injected):
        full_model = np.full_like(injected, np.nan, dtype=np.float32)
        mh, mw = np.shape(model)
        yi, xi = injected.shape[0] // 2 - mh // 2, injected.shape[1] // 2 - mw // 2
        full_model[yi:yi+mh, xi:xi+mw] = np.asarray(model, np.float32)
        model = full_model

    target_noise_med = float(np.nanmedian(terr[fit_support])) if np.any(fit_support) else np.nan
    source_noise_med = float(np.nanmedian(source_sigma[fit_support])) if np.any(fit_support) else np.nan

    receipt = {
        "status": "OK",
        "case_id": case_id,
        "object_id": _jsonable(row[ID_COL]),
        "z_source": zs, "z_target": float(zt), "target_filter": target_band,
        "source_real_pixels": True,
        "analytic_source_model_used": False,
        "intrinsic_size_evolution_applied": False,
        "intrinsic_luminosity_evolution_applied": False,
        "extra_tolman_factor_applied": False,
        "angular_scale_DA_source_over_DA_target": ang,
        "inu_redshift_factor": inu,
        "pixel_sed": _jsonable(source["plan"]),
        "source_psf_common_band": source["common_psf_band"],
        "source_psf_homogenization": _jsonable(source["psf_homogenization"]),
        "target_psf_match": _jsonable(target_psf_audit),
        "flux_conservation": _jsonable(flux_audit),
        "source_background_audit": _jsonable(source["source_backgrounds"]),
        "injection": {**inj_audit, **blank_audit, "ra_deg": inj_ra, "dec_deg": inj_dec},
        "noise": {
            "target_background_redrawn": False,
            "target_err_scale": float(TARGET_ERR_SCALE),
            "source_err_scale": float(SOURCE_ERR_SCALE),
            "source_err_propagation": source_noise_audit,
            "median_source_transferred_sigma_mjy_sr": source_noise_med,
            "median_target_err_mjy_sr": target_noise_med,
            "source_to_target_noise_ratio": source_noise_med / target_noise_med
                if np.isfinite(target_noise_med) and target_noise_med > 0 else np.nan,
            "exact_drizzle_covariance_reconstructed": False,
            "new_target_source_poisson_drawn": False,
        },
        "refit": fit_result,
        "native_wavelength_matched_reference_fit": native_fit,
        "reference_morphology": {
            key: (_jsonable(row[col]) if col is not None and col in row.index else None)
            for key, col in REFERENCE_MORPHOLOGY_COLUMNS.items()
        },
        "refit_mask_semantics": (
            "Known transferred source support is used as the PySersic source mask. "
            "This reproduces the JADES morphology-fitting stage but does not rerun "
            "the full custom multi-band JADES DR5 detection/deblending pipeline."
        ),
        "source_paths": _jsonable(source["source_paths"]),
        "target_paths": _jsonable(target_resolved),
        "target_pixel_scale_arcsec": target_sci.pixel_scale_arcsec,
    }

    case_dir = Path(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)

    if SAVE_INTERMEDIATE_FITS:
        write_fits(case_dir / "01_source_wavelength_matched_mjy_sr.fits",
                   source["source_plane"], source["source_wcs"])
        write_fits(case_dir / "02_target_source_only_mjy_sr.fits",
                   source_only, target_sci.wcs)
        write_fits(case_dir / "03_target_background_mjy_sr.fits",
                   target_sci.data, target_sci.wcs)
        write_fits(case_dir / "04_target_injected_mjy_sr.fits",
                   injected, target_sci.wcs)
        write_fits(case_dir / "05_combined_rms_mjy_sr.fits",
                   combined_rms, target_sci.wcs)
        write_fits(case_dir / "06_fit_support.fits",
                   fit_support.astype(np.float32), target_sci.wcs, bunit="dimensionless")
        if model is not None:
            write_fits(case_dir / "07_pysersic_model_mjy_sr.fits",
                       model, target_sci.wcs)

    save_diagnostic(case_dir, target_sci.data, source_only, injected,
                    combined_rms, fit_support, model)
    atomic_json(case_dir / "result.json", receipt)
    return receipt


# ================================================================
# NOTEBOOK ENGINE CELL 16
# ================================================================
# INTERNAL - DO NOT EDIT FOR NORMAL USE

def _footprint_mask(path, ext, ra_values, dec_values, margin_arcsec):
    """Fast catalog-level coverage test using only FITS headers and shape."""
    p = Path(path).expanduser()
    if not p.exists():
        raise PipelineFailure("FOOTPRINT_FILE_MISSING", str(p))
    with fits.open(p, memmap=True, lazy_load_hdus=True) as hdul:
        h = _choose_hdu(hdul, ext, ("SCI",))
        w, pix, _ = _pixel_geometry(h.header)
        ny, nx = h.data.shape
    # World-to-pixel is vectorized; no science image pixel array is loaded.
    x, y = w.world_to_pixel_values(np.asarray(ra_values, float),
                                   np.asarray(dec_values, float))
    margin = float(margin_arcsec) / pix
    return (np.isfinite(x) & np.isfinite(y) &
            (x >= margin) & (x < nx-margin) &
            (y >= margin) & (y < ny-margin))

def select_catalog_for_batch(df):
    """Apply only explicit object IDs, redshift limits, and target footprint."""
    rows = df.copy()
    if OBJECT_IDS:
        wanted = set(map(str, OBJECT_IDS))
        rows = rows.loc[rows[ID_COL].astype(str).isin(wanted)].copy()
    if SOURCE_Z_RANGE is not None:
        lo, hi = SOURCE_Z_RANGE
        z = pd.to_numeric(rows[Z_COL], errors="coerce")
        rows = rows.loc[(z >= float(lo)) & (z <= float(hi))].copy()
    if AUTO_SELECT_TARGET_FOOTPRINT:
        # The source's native coordinates must also be in the explicitly
        # chosen target survey footprint for this one-field validation mode.
        # This does not assert coverage in every source filter.
        keep = np.zeros(len(rows), dtype=bool)
        if PATH_TEMPLATE_COLUMNS:
            raise PipelineFailure("FOOTPRINT_PATH_TEMPLATE_UNSUPPORTED",
                                  "Use a preselected flat catalog for region-templated files.")
        for band in {str(t["filter"]).upper() for t in TARGET_PLAN}:
            prod = resolve_product(TARGET_PRODUCTS[band], rows.iloc[0], band) if len(rows) else None
            if prod is not None:
                keep |= _footprint_mask(prod["sci_path"], prod.get("sci_ext", "SCI"),
                                        rows[RA_COL].to_numpy(), rows[DEC_COL].to_numpy(),
                                        FOOTPRINT_EDGE_MARGIN_ARCSEC)
        rows = rows.loc[keep].copy()
    print(f"Catalog: {len(df)} rows; {len(rows)} selected before batch.")
    return rows

def current_settings_snapshot():
    return {
        "RUN_MODE": RUN_MODE,
        "PREFLIGHT_SAMPLE_ROWS": PREFLIGHT_SAMPLE_ROWS,
        "PREFLIGHT_CHECK_SPECTRAL_SUPPORT": PREFLIGHT_CHECK_SPECTRAL_SUPPORT,
        "INPUT_CATALOG_PATH": INPUT_CATALOG_PATH,
        "INPUT_CATALOG_HDU": INPUT_CATALOG_HDU,
        "CATALOG_FORMAT": CATALOG_FORMAT,
        "JADES_REDSHIFT_HDU": JADES_REDSHIFT_HDU,
        "JADES_REDSHIFT_COL": JADES_REDSHIFT_COL,
        "JADES_REQUIRE_GOOD_FLAGS": JADES_REQUIRE_GOOD_FLAGS,
        "OBJECT_IDS": OBJECT_IDS,
        "SOURCE_Z_RANGE": SOURCE_Z_RANGE,
        "AUTO_SELECT_TARGET_FOOTPRINT": AUTO_SELECT_TARGET_FOOTPRINT,
        "FOOTPRINT_EDGE_MARGIN_ARCSEC": FOOTPRINT_EDGE_MARGIN_ARCSEC,
        "ID_COL": ID_COL, "RA_COL": RA_COL, "DEC_COL": DEC_COL, "Z_COL": Z_COL,
        "PATH_TEMPLATE_COLUMNS": PATH_TEMPLATE_COLUMNS,
        "SOURCE_BANDS": SOURCE_BANDS,
        "TARGET_PRODUCTS": TARGET_PRODUCTS,
        "TARGET_PLAN": TARGET_PLAN,
        "SOURCE_CUTOUT_ARCSEC": SOURCE_CUTOUT_ARCSEC,
        "TARGET_CUTOUT_ARCSEC": TARGET_CUTOUT_ARCSEC,
        "SOURCE_MASK_DILATION_PIX": SOURCE_MASK_DILATION_PIX,
        "REQUIRE_SOURCE_SEGMENTATION": REQUIRE_SOURCE_SEGMENTATION,
        "INJECTION_MODE": INJECTION_MODE,
        "INJECTION_RA_COL": INJECTION_RA_COL,
        "INJECTION_DEC_COL": INJECTION_DEC_COL,
        "AUTO_BLANK_CENTER_RA_DEG": AUTO_BLANK_CENTER_RA_DEG,
        "AUTO_BLANK_CENTER_DEC_DEG": AUTO_BLANK_CENTER_DEC_DEG,
        "AUTO_BLANK_SEARCH_SIZE_ARCSEC": AUTO_BLANK_SEARCH_SIZE_ARCSEC,
        "THROUGHPUT_SUPPORT_FRACTION": THROUGHPUT_SUPPORT_FRACTION,
        "MAX_SED_CONDITION_NUMBER": MAX_SED_CONDITION_NUMBER,
        "PSF_WIENER_REGULARIZATION": PSF_WIENER_REGULARIZATION,
        "PSF_MATCH_L1_MAX": PSF_MATCH_L1_MAX,
        "PROPAGATE_SOURCE_ERR": PROPAGATE_SOURCE_ERR,
        "SOURCE_NOISE_MC_DRAWS": SOURCE_NOISE_MC_DRAWS,
        "FLUX_CONSERVATION_TOLERANCE": FLUX_CONSERVATION_TOLERANCE,
        "RUN_NATIVE_REFIT": RUN_NATIVE_REFIT,
        "REFIT_MODE": REFIT_MODE,
        "MAX_FIT_IMAGE_PIX": MAX_FIT_IMAGE_PIX,
        "MAX_FIT_PSF_LOST_SIGNED_FLUX": MAX_FIT_PSF_LOST_SIGNED_FLUX,
        "PYSERSIC_WARMUP": PYSERSIC_WARMUP,
        "PYSERSIC_SAMPLES": PYSERSIC_SAMPLES,
        "PYSERSIC_CHAINS": PYSERSIC_CHAINS,
        "SUBTRACT_LOCAL_TARGET_BACKGROUND": SUBTRACT_LOCAL_TARGET_BACKGROUND,
        "REFERENCE_MORPHOLOGY_COLUMNS": REFERENCE_MORPHOLOGY_COLUMNS,
        "COSMOLOGY_CONFIG": COSMOLOGY_CONFIG,
        "SAVE_INTERMEDIATE_FITS": SAVE_INTERMEDIATE_FITS,
        "RESUME": RESUME,
    }

def software_provenance():
    mods = ["numpy", "scipy", "pandas", "astropy", "photutils",
            "astroquery", "pysersic", "jax", "numpyro", "arviz"]
    vers = {}
    for m in mods:
        try:
            mod = __import__(m)
            vers[m] = getattr(mod, "__version__", "unknown")
        except Exception:
            vers[m] = "not-importable"
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "packages": vers,
    }

def existing_receipt(case_dir):
    p = Path(case_dir) / "result.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None

def should_run(case_id, old):
    if case_id in set(map(str, FORCE_RERUN_CASES)):
        return True
    if not RESUME or old is None:
        return True
    return str(old.get("status")) == "RETRYABLE_ERROR"


def run_preflight():
    """Survey-data preflight with explicit PASS/WARN/FAIL rows.

    Inspect FITS headers and small WCS-aligned cutouts only. Never open a
    full mosaic as a NumPy image. This is a data-compatibility audit, not a
    guarantee that artificial-redshifting science results are correct.
    """
    outdir = Path(OUTPUT_DIR)
    outdir.mkdir(parents=True, exist_ok=True)
    items = []
    def add(status, category, subject, detail):
        items.append(dict(status=str(status), category=str(category),
                          subject=str(subject), detail=str(detail)))
    df = None

    if not str(INPUT_CATALOG_PATH).strip() or not Path(INPUT_CATALOG_PATH).expanduser().exists():
        add("FAIL", "catalog", "INPUT_CATALOG_PATH",
            f"Missing input catalog: {INPUT_CATALOG_PATH}")
    else:
        try:
            df = load_catalog(INPUT_CATALOG_PATH, INPUT_CATALOG_HDU)
            add("PASS", "catalog", "structure_and_join",
                f"{len(df):,} objects; ID={ID_COL}; coordinates={RA_COL}/{DEC_COL}; z={Z_COL}")
            zvals = pd.to_numeric(df[Z_COL], errors="coerce").to_numpy(float)
            good = np.isfinite(zvals) & (zvals > 0)
            if np.any(good):
                add("PASS", "catalog", "redshift",
                    f"{np.count_nonzero(good):,}/{len(df):,} positive finite source redshifts")
            else:
                add("FAIL", "catalog", "redshift", "No usable positive source redshifts.")
            if JADES_REQUIRE_GOOD_FLAGS:
                add("WARN", "catalog", "JADES_REQUIRE_GOOD_FLAGS",
                    "This option requires positive WHT values; DR5 *_FLAG means pixel units, not boolean flags.")
            if len(df) and OBJECT_IDS:
                nselected = np.count_nonzero(df[ID_COL].astype(str).isin(set(map(str, OBJECT_IDS))))
                add("PASS" if nselected else "FAIL", "catalog", "OBJECT_IDS",
                    f"{nselected} specified IDs found in catalog.")
        except Exception as exc:
            add("FAIL", "catalog", "catalog_reader", f"{type(exc).__name__}: {exc}")
            df = None

    if not SOURCE_BANDS:
        add("FAIL", "configuration", "SOURCE_BANDS", "No source bands configured")
    if not TARGET_PLAN:
        add("FAIL", "configuration", "TARGET_PLAN", "At least one target redshift/filter is required")
    for item in TARGET_PLAN:
        band = str(item.get("filter","")).upper()
        try:
            zt = float(item["z"])
            if zt <= 0 or not np.isfinite(zt):
                raise ValueError("Target redshift must be finite and positive")
            add("PASS", "configuration", f"target:{band}", f"target z={zt}")
        except Exception as exc:
            add("FAIL", "configuration", f"target:{band}", f"Invalid target plan: {exc}")
        if band not in TARGET_PRODUCTS:
            add("FAIL", "configuration", f"TARGET_PRODUCTS.{band}", "Target filter lacks a target product configuration")

    # Resolve file templates from a catalog row if available. With a
    # region-templated path, warn explicitly if the row is unavailable.
    probe = df.iloc[0] if df is not None and len(df) else pd.Series(dtype=object)
    products = [("source", b, cfg) for b,cfg in SOURCE_BANDS.items()]
    products += [("target", b, cfg) for b,cfg in TARGET_PRODUCTS.items()]
    products_ok = {}
    for kind,band,cfg in products:
        key = f"{kind}:{band}"
        try:
            product = resolve_product(cfg, probe, band)
        except Exception as exc:
            add("FAIL", "path_template", key, str(exc))
            continue
        products_ok[key] = product
        scipath = product.get("sci_path")
        errpath = product.get("err_path")
        segpath = product.get("seg_path")
        psfpath = product.get("psf_path")
        if not scipath:
            add("FAIL", "path", f"{key}:SCI", "Missing sci_path")
            continue
        try:
            validate_mosaic_file_integrity(scipath, product.get("expected_min_hdus"))
            with fits.open(scipath, memmap=True, lazy_load_hdus=True) as h:
                sci_h = _choose_hdu(h, product.get("sci_ext","SCI"), ("SCI",))
                w,sci_pix,sci_area = _pixel_geometry(sci_h.header)
                sci_shape = (int(sci_h.header["NAXIS2"]),int(sci_h.header["NAXIS1"]))
                bunit=sci_h.header.get("BUNIT", "")
                _to_mjy_sr(np.ones((1,1),np.float32), bunit,sci_area)
                add("PASS","SCI",key,
                    f"HDU={h.index_of(sci_h)}; shape={sci_shape}; BUNIT={bunit}; scale={sci_pix:.6g} arcsec/pix; HDUs={len(h)}")
        except Exception as exc:
            add("FAIL","SCI",key,f"{type(exc).__name__}: {exc}")
            continue

        if not errpath:
            add("FAIL","ERR",key,"Missing err_path; ERR is needed for PySersic refit")
        else:
            try:
                validate_mosaic_file_integrity(errpath, product.get("expected_min_hdus") if errpath==scipath else None)
                with fits.open(errpath,memmap=True,lazy_load_hdus=True) as h:
                    hh=_choose_hdu(h,product.get("err_ext","ERR"),("ERR",))
                    ww,err_pix,err_area=_pixel_geometry(hh.header)
                    eunit=hh.header.get("BUNIT",bunit)
                    _to_mjy_sr(np.ones((1,1),np.float32),eunit,err_area)
                    eshape=(int(hh.header["NAXIS2"]),int(hh.header["NAXIS1"]))
                    if eshape!=sci_shape or abs(err_pix/sci_pix-1)>1e-3:
                        raise ValueError(f"SCI vs ERR pixel-grid shape/scale differ: {sci_shape} vs {eshape}")
                    add("PASS","ERR",key,
                        f"HDU={h.index_of(hh)}; unit={eunit}; shape={eshape}; kind={product.get('err_kind','STDDEV')}")
            except Exception as exc:
                add("FAIL","ERR",key,f"{type(exc).__name__}: {exc}")

        if not segpath:
            add("FAIL" if REQUIRE_SOURCE_SEGMENTATION or INJECTION_MODE=="AUTO_BLANK" else "WARN",
                "SEG",key,"Segmentation map missing; needed for source isolation/blank-sky search")
        elif not Path(segpath).expanduser().exists():
            add("FAIL","SEG",key,f"Segmentation file not found: {segpath}")
        else:
            try:
                with fits.open(segpath,memmap=True,lazy_load_hdus=True) as h:
                    hh=_choose_hdu(h,product.get("seg_ext","AUTO"),("SEG","SEGM","SEGMENTATION"))
                    segw,seg_pix,_=_pixel_geometry(hh.header)
                    add("PASS","SEG",key,
                        f"HDU={h.index_of(hh)}; pixel_scale={seg_pix:.6g} arcsec/pix. "
                        "Full-field segmentation is WCS-sampled onto the SCI grid for each cutout.")
            except Exception as exc:
                add("FAIL","SEG",key,f"{type(exc).__name__}: {exc}")

        if not psfpath or not Path(psfpath).expanduser().exists():
            add("FAIL","PSF",key,f"Matched PSF missing: {psfpath}")
        else:
            try:
                psf=read_psf(product,sci_pix)
                if not np.isfinite(psf.rms_radius_arcsec) or psf.rms_radius_arcsec <= 0:
                    raise ValueError("Invalid PSF RMS width")
                add("PASS","PSF",key,
                    f"normalized/resampled; RMS radius={psf.rms_radius_arcsec:.5g} arcsec; "
                    f"pixel_scale={psf.pixel_scale_arcsec:.5g}; {psf.provenance}")
            except Exception as exc:
                add("FAIL","PSF",key,f"{type(exc).__name__}: {exc}")

        curve_local=product.get("throughput_file")
        svo=product.get("svo_id")
        if curve_local and not Path(curve_local).expanduser().exists():
            add("FAIL","throughput",key,f"Local throughput file missing: {curve_local}")
        elif not curve_local and svo:
            cp=Path(THROUGHPUT_CACHE_DIR)/(str(svo).replace("/","_")+".csv")
            add("PASS" if cp.exists() else "WARN","throughput",key,
                f"SVO ID {svo}; " + ("cached locally" if cp.exists() else "requires network for first load"))
        elif not curve_local and not svo:
            add("FAIL","throughput",key,"Set throughput_file or svo_id in USER SETTINGS")
        else:
            add("PASS","throughput",key,f"Local curve: {curve_local}")

    # WCS/segmentation identity sanity on a few actual objects only; this can
    # expose wrong release/field and label conventions before a batch run.
    if df is not None and len(df)>0:
        trial=df
        if OBJECT_IDS:
            trial=trial.loc[trial[ID_COL].astype(str).isin(set(map(str, OBJECT_IDS)))]
        if SOURCE_Z_RANGE is not None:
            lo,hi=SOURCE_Z_RANGE
            zz=pd.to_numeric(trial[Z_COL],errors="coerce")
            trial=trial.loc[(zz>=lo)&(zz<=hi)]
        trial=trial.head(max(0,int(PREFLIGHT_SAMPLE_ROWS)))
        if len(trial)==0:
            add("WARN","sample","pilot", "No objects match pilot filters; choose valid IDs or redshift interval")
        else:
            for _,row in trial.iterrows():
                oid=row[ID_COL]
                ra,dec=float(row[RA_COL]),float(row[DEC_COL])
                covered=[]
                for b,cfg in SOURCE_BANDS.items():
                    key=f"source:{b}"
                    product=products_ok.get(key)
                    if product is None or not Path(product["sci_path"]).exists():
                        continue
                    try:
                        found=source_product_has_coverage(cfg,row,b,ra,dec)
                        if found:
                            covered.append(b)
                            if product.get("seg_path") and Path(product["seg_path"]).exists():
                                cut=read_cutout(product["sci_path"],product.get("sci_ext","SCI"),
                                                ra,dec,min(SOURCE_CUTOUT_ARCSEC,2.0),("SCI",),True)
                                labels=read_segmentation_on_science_grid(
                                    product["seg_path"],product.get("seg_ext","AUTO"),cut)
                                lab=find_source_label(labels,SOURCE_LABEL_SEARCH_RADIUS_PIX,
                                                      expected_id=oid)
                                add("PASS","sample_seg",f"ID={oid}:{b}",
                                    f"Source segmentation ID={lab}; WCS-matched small cutout")
                        else:
                            add("WARN","sample_coverage",f"ID={oid}:{b}","No finite source SCI at coordinate")
                    except Exception as exc:
                        add("WARN","sample_check",f"ID={oid}:{b}",
                            f"{type(exc).__name__}: {exc}. Check footprint/segmentation-label conventions.")
                if len(covered)<2:
                    add("WARN","sample_sed",f"ID={oid}",
                        f"Only {len(covered)} source filters cover this object: {covered}. "
                        "This object will not have adequate multi-band interpolation.")
                if PREFLIGHT_CHECK_SPECTRAL_SUPPORT and len(covered)>=2:
                    for target in TARGET_PLAN:
                        tb=str(target["filter"]).upper()
                        try:
                            zt=float(target["z"]);zs=float(row[Z_COL])
                            if zt<=zs:
                                continue
                            targetcfg=TARGET_PRODUCTS.get(tb)
                            if not targetcfg:
                                continue
                            src_curves={b:curve_for(b,SOURCE_BANDS[b]) for b in covered}
                            mapped=mapped_curve(curve_for(tb,targetcfg),zs,zt)
                            plan=choose_sed_plan(src_curves,mapped)
                            add("PASS","sample_sed",f"ID={oid}:z={zt}:{tb}",
                                f"Supported source filters {plan['bands']}; cond={plan['condition_number']:.3g}")
                        except Exception as exc:
                            add("WARN","sample_sed",f"ID={oid}:z={target.get('z')}:{tb}",
                                f"{type(exc).__name__}: {exc}")

    add("WARN","science","remaining_validation",
        "Preflight cannot prove PSF/noise accuracy, completeness, or recovered-parameter "
        "bias on real JADES galaxies. Inspect real-image outputs and compare to native fits.")

    report=pd.DataFrame(items,columns=["status","category","subject","detail"])
    report.to_csv(outdir/"data_preflight.csv",index=False)
    atomic_json(outdir/"data_preflight.json",{
        "summary":report.status.value_counts().to_dict(),
        "rows":items,
    })
    md=[
        "# JADES input data preflight",
        "",
        "This checks actual FITS metadata and a few cutouts. It does **not** establish scientific validation.",
        "",
        f"Result: {int((report.status=='PASS').sum())} PASS; "
        f"{int((report.status=='WARN').sum())} WARN; "
        f"{int((report.status=='FAIL').sum())} FAIL.",
        "",
        "| Status | Category | Subject | Detail |",
        "| --- | --- | --- | --- |",
    ]
    def esc(x):
        return str(x).replace("|","\\|").replace("\n"," ")
    for row in items:
        md.append("| " + " | ".join(esc(row[k]) for k in ("status","category","subject","detail")) + " |")
    (outdir/"data_preflight.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print("Preflight: ",report.status.value_counts().to_dict())
    print("Saved:",(outdir/"data_preflight.md").resolve())
    return report

def run_batch():
    out = Path(OUTPUT_DIR)
    out.mkdir(parents=True, exist_ok=True)
    atomic_json(out / "frozen_settings.json", current_settings_snapshot())
    atomic_json(out / "software_provenance.json", software_provenance())
    log = out / "run.log"

    df = select_catalog_for_batch(load_catalog(INPUT_CATALOG_PATH, INPUT_CATALOG_HDU))
    rows = []
    requested = []
    for _, row in df.iterrows():
        oid = sanitize_case_id(row[ID_COL])
        for item in TARGET_PLAN:
            zt = float(item["z"]); band = str(item["filter"]).upper()
            cid = f"{oid}__z{zt:g}__{band}"
            requested.append((row, zt, band, cid))
    if MAX_CASES is not None:
        requested = requested[:int(MAX_CASES)]

    append_log(log, f"Starting batch with {len(requested)} requested cases")

    for i, (row, zt, band, cid) in enumerate(requested, 1):
        cdir = out / "cases" / cid
        old = existing_receipt(cdir)
        if not should_run(cid, old):
            rows.append(old)
            print(f"[{i}/{len(requested)}] SKIP {cid}: {old.get('status')}")
            continue

        print(f"[{i}/{len(requested)}] RUN  {cid}")
        append_log(log, f"RUN {cid}")
        cdir.mkdir(parents=True, exist_ok=True)
        try:
            result = run_case(row, zt, band, cid, cdir)
            append_log(log, f"OK {cid}")
        except PipelineFailure as exc:
            result = {
                "status": "TERMINAL_ERROR" if exc.terminal else "RETRYABLE_ERROR",
                "case_id": cid, "object_id": _jsonable(row[ID_COL]),
                "z_source": _jsonable(row[Z_COL]), "z_target": zt,
                "target_filter": band, "failure_code": exc.code,
                "message": str(exc),
            }
            atomic_json(cdir / "result.json", result)
            append_log(log, f"{result['status']} {cid}: {exc}")
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            result = {
                "status": "RETRYABLE_ERROR",
                "case_id": cid, "object_id": _jsonable(row[ID_COL]),
                "z_source": _jsonable(row[Z_COL]), "z_target": zt,
                "target_filter": band, "failure_code": "UNEXPECTED_EXCEPTION",
                "message": repr(exc),
                "traceback": traceback.format_exc(limit=12),
            }
            atomic_json(cdir / "result.json", result)
            append_log(log, f"RETRYABLE_ERROR {cid}: {repr(exc)}")
        rows.append(result)

        # Release arrays and JAX caches between objects. This is intentional for
        # large-mosaic batch work.
        gc.collect()
        try:
            import jax
            jax.clear_caches()
        except Exception:
            pass

    summary_rows = []
    for r in rows:
        flat = {
            "case_id": r.get("case_id"), "status": r.get("status"),
            "object_id": r.get("object_id"), "z_source": r.get("z_source"),
            "z_target": r.get("z_target"), "target_filter": r.get("target_filter"),
            "failure_code": r.get("failure_code", ""),
            "message": r.get("message", ""),
        }
        fit = r.get("refit", {}) if isinstance(r, dict) else {}
        for k in ("recovered_n", "recovered_re_arcsec", "recovered_q", "recovered_pa_rad"):
            flat[k] = fit.get(k, np.nan) if isinstance(fit, dict) else np.nan
        ref = r.get("reference_morphology", {}) if isinstance(r, dict) else {}
        for key in ("n", "re_arcsec", "q", "pa_rad"):
            flat[f"reference_{key}"] = ref.get(key, np.nan) if isinstance(ref, dict) else np.nan
        pairs = [
            ("n", "recovered_n"),
            ("re_arcsec", "recovered_re_arcsec"),
            ("q", "recovered_q"),
            ("pa_rad", "recovered_pa_rad"),
        ]
        for key, rkey in pairs:
            rv, vv = flat.get(f"reference_{key}"), flat.get(rkey)
            try:
                flat[f"delta_{key}"] = (
                    float(vv) - float(rv)
                    if np.isfinite(float(vv)) and np.isfinite(float(rv))
                    else np.nan
                )
            except Exception:
                flat[f"delta_{key}"] = np.nan
        summary_rows.append(flat)

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(out / "batch_summary.csv", index=False)
    print("\nBatch status counts:")
    if "status" in summary.columns:
        print(summary["status"].value_counts(dropna=False))
    else:
        print("No catalog rows matched the configured sample/footprint; check USER SETTINGS.")
    print("\nSaved:", (out / "batch_summary.csv").resolve())
    return summary

# ===================================================================
# COMMAND-LINE ENTRY POINT
#   python JADES_realimage_artificial_redshifting_batch.py preflight
#   python JADES_realimage_artificial_redshifting_batch.py run
# ===================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="JADES DR5 real-image artificial redshifting; header-level data audit or full batch."
    )
    parser.add_argument("command", choices=["preflight", "run"], nargs="?",
                        default="preflight", help="preflight is safe and default")
    args = parser.parse_args()
    report = run_preflight()
    if args.command == "preflight":
        return 0 if not (report.status == "FAIL").any() else 2
    if (report.status == "FAIL").any():
        print("Blocking FITS/configuration failures found; see OUTPUT_DIR/data_preflight.md")
        return 2
    summary = run_batch()
    print(summary.head(20).to_string(index=False))
    return 0 if "status" not in summary.columns or (summary.status == "OK").all() else 1

if __name__ == "__main__":
    raise SystemExit(main())
