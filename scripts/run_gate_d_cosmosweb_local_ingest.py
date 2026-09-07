#!/usr/bin/env python3
"""Create an aligned SCI/ERR/WHT cutout bundle from local COSMOS-Web mosaics."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.nddata import Cutout2D
from astropy.wcs import WCS
import astropy.units as u


def _image_hdu(path: Path):
    hdul = fits.open(path, mode="readonly", memmap=not str(path).endswith(".gz"))
    for i, hdu in enumerate(hdul):
        if getattr(hdu, "data", None) is not None and np.ndim(hdu.data) == 2:
            return hdul, i, hdu
    hdul.close()
    raise ValueError(f"no 2D image HDU found in {path}")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _header_identity(header):
    keys = ["TELESCOP", "INSTRUME", "FILTER", "PUPIL", "BUNIT", "DATE", "FILENAME"]
    return {k: header[k] for k in keys if k in header}


def build_cutout(sci_path: Path, err_path: Path, wht_path: Path, ra: float, dec: float,
                 size: int, out_fits: Path, out_json: Path):
    paths = {"SCI": sci_path, "ERR": err_path, "WHT": wht_path}
    opened = {}
    try:
        for name, path in paths.items():
            if not path.exists():
                raise FileNotFoundError(path)
            opened[name] = _image_hdu(path)
        shape = opened["SCI"][2].data.shape
        if any(opened[k][2].data.shape != shape for k in ("ERR", "WHT")):
            raise ValueError("SCI/ERR/WHT image shapes differ")
        center = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
        sci_wcs = WCS(opened["SCI"][2].header).celestial
        x_ref, y_ref = sci_wcs.world_to_pixel(center)
        cutouts = {}; origins = {}
        for name in ("SCI", "ERR", "WHT"):
            hdu = opened[name][2]; wcs = WCS(hdu.header).celestial
            x, y = wcs.world_to_pixel(center)
            if not (np.isfinite(x) and np.isfinite(y)):
                raise ValueError(f"non-finite WCS position for {name}")
            if abs(x - x_ref) > 0.05 or abs(y - y_ref) > 0.05:
                raise ValueError(f"{name} WCS disagrees with SCI by >0.05 pixel")
            c = Cutout2D(hdu.data, center, (size, size), wcs=wcs, mode="strict", copy=True)
            cutouts[name] = c; origins[name] = [int(c.origin_original[0]), int(c.origin_original[1])]
        out_fits.parent.mkdir(parents=True, exist_ok=True)
        hdus = [fits.PrimaryHDU()]
        for name in ("SCI", "ERR", "WHT"):
            hdr = cutouts[name].wcs.to_header(relax=True)
            for k, v in _header_identity(opened[name][2].header).items():
                if k not in hdr: hdr[k] = v
            hdus.append(fits.ImageHDU(data=np.asarray(cutouts[name].data), header=hdr, name=name))
        fits.HDUList(hdus).writeto(out_fits, overwrite=True, checksum=True)
        manifest = {
            "claim": "real-data ingest/cutout only; no injection or recovery performed",
            "survey": "COSMOS-Web DR1", "instrument": "JWST/NIRCam", "filter": "F444W",
            "pixel_scale_mas": 30, "tile": "A1",
            "center_icrs_deg": {"ra": ra, "dec": dec}, "size_pixels": size,
            "source_shape": list(shape), "cutout_origins_xy": origins,
            "sources": {k: {"path": str(paths[k].resolve()), "size_bytes": paths[k].stat().st_size,
                            "header_identity": _header_identity(opened[k][2].header)} for k in paths},
            "finite_fraction": {k: float(np.isfinite(cutouts[k].data).mean()) for k in cutouts},
            "output_fits": str(out_fits.resolve()), "output_sha256": _sha256(out_fits),
            "injection_performed": False, "recovery_performed": False,
        }
        out_json.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        return manifest
    finally:
        for hdul, _, _ in opened.values(): hdul.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sci", type=Path, required=True); p.add_argument("--err", type=Path, required=True)
    p.add_argument("--wht", type=Path, required=True); p.add_argument("--ra", type=float, required=True)
    p.add_argument("--dec", type=float, required=True); p.add_argument("--size", type=int, default=512)
    p.add_argument("--out-fits", type=Path, required=True); p.add_argument("--out-json", type=Path, required=True)
    a = p.parse_args()
    if a.size <= 0: p.error("--size must be positive")
    build_cutout(a.sci, a.err, a.wht, a.ra, a.dec, a.size, a.out_fits, a.out_json)

if __name__ == "__main__": main()
