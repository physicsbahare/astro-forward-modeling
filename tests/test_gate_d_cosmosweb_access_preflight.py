import importlib.util
from pathlib import Path

RUNNER = Path(__file__).resolve().parents[1] / "scripts" / "run_gate_d_cosmosweb_access_preflight.py"
spec = importlib.util.spec_from_file_location("gate_d0_runner", RUNNER)
experiment = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(experiment)


def test_frozen_gate_d0_contract():
    cfg = experiment.configuration()
    assert cfg["survey"] == "COSMOS-Web DR1"
    assert cfg["instrument"] == "JWST/NIRCam"
    assert cfg["filter"] == "F444W"
    assert cfg["pixel_scale_mas"] == 30
    assert cfg["tile"] == "A1"
    assert cfg["request_method"] == "HEAD"
    assert cfg["tile_downloaded"] is False
    assert cfg["injection_performed"] is False
    assert "does not close Gate D" in cfg["claim"]


def test_exact_public_product_names():
    expected_suffix = {
        "sci": "mosaic_nircam_f444w_COSMOS-Web_30mas_A1_v1.0_sci.fits.gz",
        "err": "mosaic_nircam_f444w_COSMOS-Web_30mas_A1_v1.0_err.fits.gz",
        "wht": "mosaic_nircam_f444w_COSMOS-Web_30mas_A1_v1.0_wht.fits.gz",
    }
    assert set(experiment.PRODUCTS) == set(expected_suffix)
    for key, suffix in expected_suffix.items():
        assert experiment.PRODUCTS[key].endswith(suffix)
        assert experiment.PRODUCTS[key].startswith("https://cosmos2025.iap.fr/data/nircam/extensions/")
