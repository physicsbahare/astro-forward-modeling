#!/usr/bin/env python3
"""Acquire one compact real COSMOS-Web SCI/ERR/WHT cutout reproducibly."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from urllib.request import Request, urlopen

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
import astropy.units as u

BASE = "https://cosmos2025.iap.fr/data/nircam/extensions"
PRODUCTS = {
    ext.upper(): f"{BASE}/mosaic_nircam_f444w_COSMOS-Web_30mas_A1_v1.0_{ext}.fits.gz"
    for ext in ("sci", "err", "wht")
}
USER_AGENT = "astro-forward-modeling-gate-d1b/0.1"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def image_header(path: Path):
    """Return (HDU index, header) for the first 2-D image without loading pixels."""
    with fits.open(path, mode="readonly", memmap=False, lazy_load_hdus=True) as hdul:
        for i, hdu in enumerate(hdul):
            hdr = hdu.header
            if hdr.get("NAXIS") == 2 and hdr.get("NAXIS1", 0) > 0 and hdr.get("NAXIS2", 0) > 0:
                return i, hdr.copy()
    raise ValueError(f"no 2-D image HDU found in {path}")


def section_from_sci_header(header: fits.Header, ra: float, dec: float, size: int):
    center = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
    x, y = WCS(header).celestial.world_to_pixel(center)
    if not (np.isfinite(x) and np.isfinite(y)):
        raise ValueError("non-finite SCI WCS coordinate")
    ny, nx = int(header["NAXIS2"]), int(header["NAXIS1"])
    xlo0 = int(np.floor(x - size / 2.0))
    ylo0 = int(np.floor(y - size / 2.0))
    xhi0 = xlo0 + size - 1
    yhi0 = ylo0 + size - 1
    if xlo0 < 0 or ylo0 < 0 or xhi0 >= nx or yhi0 >= ny:
        raise ValueError("requested cutout crosses mosaic boundary")
    return {
        "shape_yx": [ny, nx],
        "sci_center_pixel_xy_zero_based": [float(x), float(y)],
        "bounds_zero_based_inclusive": [xlo0, xhi0, ylo0, yhi0],
        "cfitsio_section_one_based": [xlo0 + 1, xhi0 + 1, ylo0 + 1, yhi0 + 1],
    }


def verify_header_against_sci(name: str, header: fits.Header, sci_header: fits.Header,
                              ra: float, dec: float):
    shape = [int(header["NAXIS2"]), int(header["NAXIS1"])]
    sci_shape = [int(sci_header["NAXIS2"]), int(sci_header["NAXIS1"])]
    if shape != sci_shape:
        raise ValueError(f"{name} image shape {shape} differs from SCI {sci_shape}")
    center = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
    sx, sy = WCS(sci_header).celestial.world_to_pixel(center)
    x, y = WCS(header).celestial.world_to_pixel(center)
    if not (np.isfinite(x) and np.isfinite(y)):
        raise ValueError(f"non-finite WCS coordinate for {name}")
    if abs(x - sx) > 0.05 or abs(y - sy) > 0.05:
        raise ValueError(f"{name} WCS differs from SCI by >0.05 pixel")
    return [float(x), float(y)]


def download(url: str, dest: Path):
    subprocess.run([
        "curl", "-L", "--fail", "--retry", "4", "--retry-delay", "5",
        "--user-agent", USER_AGENT, "--output", str(dest), url,
    ], check=True)


def head_metadata(url: str):
    req = Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as r:
        return {
            "status": int(r.status),
            "content_length": r.headers.get("Content-Length"),
            "etag": r.headers.get("ETag"),
            "last_modified": r.headers.get("Last-Modified"),
            "accept_ranges": r.headers.get("Accept-Ranges"),
            "final_url": r.geturl(),
        }


def extract_section(src: Path, hdu_index: int, section: list[int], dest: Path):
    if shutil.which("fitscopy") is None:
        raise RuntimeError("CFITSIO fitscopy is required")
    x1, x2, y1, y2 = section
    spec = f"{src}[{hdu_index}][{x1}:{x2},{y1}:{y2}]"
    subprocess.run(["fitscopy", spec, str(dest)], check=True)


def package_cutouts(parts: dict[str, Path], out_fits: Path):
    arrays = {}
    headers = {}
    for name, path in parts.items():
        with fits.open(path, memmap=True) as hdul:
            hdu = next(h for h in hdul if getattr(h, "data", None) is not None and np.ndim(h.data) == 2)
            arrays[name] = np.array(hdu.data, copy=True)
            headers[name] = hdu.header.copy()
    shapes = {a.shape for a in arrays.values()}
    if len(shapes) != 1:
        raise ValueError(f"extracted SCI/ERR/WHT shapes differ: {shapes}")
    hdus = [fits.PrimaryHDU()]
    for name in ("SCI", "ERR", "WHT"):
        hdus.append(fits.ImageHDU(data=arrays[name], header=headers[name], name=name))
    fits.HDUList(hdus).writeto(out_fits, overwrite=True, checksum=True)
    return arrays, headers


def make_preview(sci: np.ndarray, out_png: Path):
    import matplotlib.pyplot as plt
    finite = sci[np.isfinite(sci)]
    if finite.size == 0:
        raise ValueError("SCI cutout has no finite pixels")
    lo, hi = np.nanpercentile(finite, [1.0, 99.5])
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        lo, hi = float(np.nanmin(finite)), float(np.nanmax(finite))
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(sci, origin="lower", vmin=lo, vmax=hi)
    ax.set_title("COSMOS-Web DR1 F444W 30 mas A1 — real SCI cutout")
    ax.set_xlabel("x [pixel]")
    ax.set_ylabel("y [pixel]")
    fig.tight_layout()
    fig.savefig(out_png, dpi=160)
    plt.close(fig)


def run(out: Path, ra: float, dec: float, size: int):
    out.mkdir(parents=True, exist_ok=True)
    work = out / "work"
    work.mkdir(exist_ok=True)
    remote_meta = {name: head_metadata(url) for name, url in PRODUCTS.items()}
    provenance = {}
    parts = {}

    # Download SCI first, freeze the section from its WCS, extract, then delete.
    sci_gz = work / "SCI.fits.gz"
    download(PRODUCTS["SCI"], sci_gz)
    sci_hdu, sci_header = image_header(sci_gz)
    section = section_from_sci_header(sci_header, ra, dec, size)
    provenance["SCI"] = {
        "url": PRODUCTS["SCI"], "remote_head": remote_meta["SCI"],
        "compressed_size_bytes": sci_gz.stat().st_size,
        "compressed_sha256": sha256(sci_gz), "source_image_hdu": sci_hdu,
        "center_pixel_xy_zero_based": section["sci_center_pixel_xy_zero_based"],
    }
    sci_part = work / "SCI_cutout.fits"
    extract_section(sci_gz, sci_hdu, section["cfitsio_section_one_based"], sci_part)
    parts["SCI"] = sci_part
    sci_gz.unlink()

    # ERR/WHT are each downloaded, verified against the frozen SCI geometry,
    # extracted using exactly the same section, and immediately deleted.
    for name in ("ERR", "WHT"):
        src = work / f"{name}.fits.gz"
        download(PRODUCTS[name], src)
        idx, hdr = image_header(src)
        center_xy = verify_header_against_sci(name, hdr, sci_header, ra, dec)
        provenance[name] = {
            "url": PRODUCTS[name], "remote_head": remote_meta[name],
            "compressed_size_bytes": src.stat().st_size,
            "compressed_sha256": sha256(src), "source_image_hdu": idx,
            "center_pixel_xy_zero_based": center_xy,
        }
        part = work / f"{name}_cutout.fits"
        extract_section(src, idx, section["cfitsio_section_one_based"], part)
        parts[name] = part
        src.unlink()

    bundle = out / "cosmosweb_f444w_30mas_A1_ID4204_real_cutout.fits"
    arrays, cut_headers = package_cutouts(parts, bundle)
    center = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
    cut_pix = {}
    for name, hdr in cut_headers.items():
        x, y = WCS(hdr).celestial.world_to_pixel(center)
        cut_pix[name] = [float(x), float(y)]
    sx, sy = cut_pix["SCI"]
    for name, (x, y) in cut_pix.items():
        if abs(x - sx) > 0.05 or abs(y - sy) > 0.05:
            raise ValueError(f"extracted {name} WCS differs from extracted SCI by >0.05 pixel")

    preview = out / "cosmosweb_f444w_30mas_A1_ID4204_preview.png"
    make_preview(arrays["SCI"], preview)
    diagnostics = {}
    for name, arr in arrays.items():
        finite = np.isfinite(arr)
        vals = arr[finite]
        diagnostics[name] = {
            "shape": list(arr.shape), "finite_fraction": float(finite.mean()),
            "min": float(np.nanmin(vals)) if vals.size else None,
            "median": float(np.nanmedian(vals)) if vals.size else None,
            "max": float(np.nanmax(vals)) if vals.size else None,
            "positive_fraction": float(np.mean(vals > 0)) if vals.size else None,
        }

    manifest = {
        "stage": "Gate D1b preflight: remote real-cutout acquisition",
        "claim": "real COSMOS-Web acquisition/ingest only; no injection or recovery performed",
        "survey": "COSMOS-Web DR1", "instrument": "JWST/NIRCam", "filter": "F444W",
        "pixel_scale_mas": 30, "tile": "A1",
        "catalog_anchor": {"catalog": "COSMOS2025", "id": 4204},
        "center_icrs_deg": {"ra": ra, "dec": dec}, "size_pixels": size,
        "section": section, "sources": provenance,
        "cutout_center_pixel_xy_zero_based": cut_pix, "diagnostics": diagnostics,
        "bundle": {"path": bundle.name, "sha256": sha256(bundle), "size_bytes": bundle.stat().st_size},
        "preview": preview.name,
        "injection_performed": False, "recovery_performed": False,
        "noise_added": False, "err_wht_modified": False, "psf_operation_performed": False,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    shutil.rmtree(work)
    return manifest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--ra", type=float, default=149.8671500)
    p.add_argument("--dec", type=float, default=2.1294010)
    p.add_argument("--size", type=int, default=512)
    a = p.parse_args()
    if a.size <= 0:
        p.error("--size must be positive")
    print(json.dumps(run(a.out, a.ra, a.dec, a.size), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
