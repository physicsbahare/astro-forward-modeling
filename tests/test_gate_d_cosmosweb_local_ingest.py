import importlib.util
from pathlib import Path
import numpy as np
import pytest
astropy = pytest.importorskip("astropy")
from astropy.io import fits
from astropy.wcs import WCS

SCRIPT = Path(__file__).parents[1] / "scripts" / "run_gate_d_cosmosweb_local_ingest.py"
spec = importlib.util.spec_from_file_location("gate_d_local_ingest", SCRIPT)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


def make_image(path, value):
    w = WCS(naxis=2); w.wcs.crpix = [50.5, 50.5]; w.wcs.cdelt = [-0.03/3600, 0.03/3600]
    w.wcs.crval = [150.0, 2.0]; w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    h = w.to_header(); h["TELESCOP"] = "JWST"; h["INSTRUME"] = "NIRCAM"; h["FILTER"] = "F444W"
    fits.PrimaryHDU(np.full((100, 100), value, dtype=np.float32), header=h).writeto(path)


def test_aligned_cutout_and_manifest(tmp_path):
    paths = {k: tmp_path/f"{k.lower()}.fits" for k in ("SCI","ERR","WHT")}
    for i, k in enumerate(("SCI","ERR","WHT"), 1): make_image(paths[k], i)
    out = tmp_path/"cutout.fits"; js = tmp_path/"manifest.json"
    m = mod.build_cutout(paths["SCI"], paths["ERR"], paths["WHT"], 150.0, 2.0, 32, out, js)
    assert out.exists() and js.exists() and len(m["output_sha256"]) == 64
    assert m["injection_performed"] is False and m["recovery_performed"] is False
    with fits.open(out) as hdul:
        assert hdul["SCI"].data.shape == (32,32)
        assert np.all(hdul["SCI"].data == 1) and np.all(hdul["ERR"].data == 2) and np.all(hdul["WHT"].data == 3)
        assert WCS(hdul["SCI"].header).celestial.pixel_n_dim == 2


def test_mismatched_shape_fails(tmp_path):
    make_image(tmp_path/"sci.fits", 1); make_image(tmp_path/"err.fits", 2); make_image(tmp_path/"wht.fits", 3)
    with fits.open(tmp_path/"wht.fits", mode="update") as h: h[0].data = h[0].data[:-1]
    with pytest.raises(ValueError, match="shapes differ"):
        mod.build_cutout(tmp_path/"sci.fits", tmp_path/"err.fits", tmp_path/"wht.fits", 150, 2, 16, tmp_path/"o.fits", tmp_path/"o.json")
