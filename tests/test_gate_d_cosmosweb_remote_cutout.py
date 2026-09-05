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


def ancillary_without_wcs(nx=1000, ny=900):
    h = fits.Header()
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
    result = mod.verify_header_against_sci("ERR", header(dx=0.02), sci, 149.86715, 2.129401)
    assert result["wcs_status"] == "present"
    assert result["alignment_mode"].endswith("<=0.05 pixel")
    with pytest.raises(ValueError, match=">0.05 pixel"):
        mod.verify_header_against_sci("WHT", header(dx=0.2), sci, 149.86715, 2.129401)


def test_missing_ancillary_wcs_uses_explicit_cogrid_provenance_not_fake_coordinate():
    result = mod.verify_header_against_sci(
        "ERR", ancillary_without_wcs(), header(), 149.86715, 2.129401
    )
    assert result["wcs_status"] == "absent"
    assert "official-COSMOS-Web-co-grid" in result["alignment_mode"]
    assert result["center_pixel_xy_zero_based"] is None


def test_malformed_declared_celestial_wcs_fails():
    bad = ancillary_without_wcs()
    bad["CTYPE1"] = "RA---TAN"
    bad["CTYPE2"] = "LINEAR"
    with pytest.raises(ValueError, match="malformed celestial WCS"):
        mod.verify_header_against_sci("ERR", bad, header(), 149.86715, 2.129401)


def test_shape_mismatch_fails_even_when_ancillary_wcs_missing():
    with pytest.raises(ValueError, match="shape"):
        mod.verify_header_against_sci("ERR", ancillary_without_wcs(nx=999), header(), 149.86715, 2.129401)


def test_wcs_metadata_propagation_does_not_change_pixel_grid_semantics():
    sci = header(nx=32, ny=32)
    anc = ancillary_without_wcs(nx=32, ny=32)
    out, origin = mod._copy_sci_wcs_if_absent("ERR", anc, sci)
    assert origin == "propagated-from-SCI-co-grid"
    assert mod._celestial_wcs(out) is not None
    assert out["NAXIS1"] == 32 and out["NAXIS2"] == 32
