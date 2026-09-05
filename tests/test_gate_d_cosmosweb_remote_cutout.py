import importlib.util
from pathlib import Path

import numpy as np
import pytest
astropy = pytest.importorskip("astropy")
from astropy.io import fits
from astropy.wcs import WCS

SCRIPT = Path(__file__).parents[1] / "scripts" / "run_gate_d_cosmosweb_remote_cutout.py"
spec = importlib.util.spec_from_file_location("gate_d_remote_cutout", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def header(nx=1000, ny=900, dx=0.0):
    w = WCS(naxis=2)
    w.wcs.crpix = [500.5 + dx, 450.5]
    w.wcs.cdelt = [-0.03/3600, 0.03/3600]
    w.wcs.crval = [149.86715, 2.129401]
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    h = w.to_header()
    h["NAXIS"] = 2; h["NAXIS1"] = nx; h["NAXIS2"] = ny
    return h


def test_section_is_strict_and_exact_size():
    h = header()
    s = mod.section_from_sci_header(h, 149.86715, 2.129401, 512)
    x1, x2, y1, y2 = s["cfitsio_section_one_based"]
    assert x2 - x1 + 1 == 512
    assert y2 - y1 + 1 == 512
    assert min(s["bounds_zero_based_inclusive"]) >= 0


def test_err_wht_geometry_match_and_mismatch():
    sci = header()
    xy = mod.verify_header_against_sci("ERR", header(dx=0.02), sci, 149.86715, 2.129401)
    assert len(xy) == 2
    with pytest.raises(ValueError, match=">0.05 pixel"):
        mod.verify_header_against_sci("WHT", header(dx=0.2), sci, 149.86715, 2.129401)


def test_shape_mismatch_fails():
    with pytest.raises(ValueError, match="shape"):
        mod.verify_header_against_sci("ERR", header(nx=999), header(), 149.86715, 2.129401)
