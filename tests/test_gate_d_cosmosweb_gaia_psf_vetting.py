import importlib.util
from pathlib import Path
import astropy.units as u
from astropy.coordinates import SkyCoord

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "d1nd", ROOT / "scripts" / "run_gate_d_cosmosweb_gaia_psf_vetting.py"
)
d1nd = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(d1nd)

def test_frozen_match_radius():
    assert d1nd.MATCH_RADIUS_ARCSEC == 0.15
    assert d1nd.TARGET_EPOCH_JYEAR == 2023.5

def test_nearest_matches_preserves_unmatched_rows():
    cand = SkyCoord(ra=[10.0, 10.01]*u.deg, dec=[20.0, 20.0]*u.deg)
    gaia = SkyCoord(ra=[10.0]*u.deg, dec=[20.0]*u.deg)
    out = d1nd.nearest_matches(cand, gaia)
    assert len(out) == 2
    assert out[0]["matched"]
    assert out[0]["separation_arcsec"] < 1e-8
    assert not out[1]["matched"]

def test_no_gaia_rows_is_not_a_failure():
    cand = SkyCoord(ra=[10.0]*u.deg, dec=[20.0]*u.deg)
    gaia = SkyCoord(ra=[]*u.deg, dec=[]*u.deg)
    out = d1nd.nearest_matches(cand, gaia)
    assert out == [{"gaia_index": None, "separation_arcsec": None, "matched": False}]
