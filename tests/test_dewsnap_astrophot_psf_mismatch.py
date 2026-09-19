import pytest
pytest.importorskip("astrophot")
pytest.importorskip("torch")
from scripts import run_dewsnap_astrophot_psf_mismatch as c6c


def test_c6c_is_frozen_crossed_psf_only():
    cfg = c6c.configuration()
    assert cfg["stage"].startswith("C6c")
    assert cfg["ratio"] == 10.0
    assert cfg["directions"] == ["A_data_B_psf", "B_data_A_psf"]
    assert cfg["pa_mapping"] == "same_imfit"
    assert cfg["shape_bounds"] == {"q": [0.15, 1.0], "n": [0.5, 6.0], "re": [0.5, 60.0]}
    assert cfg["point_flux_bounds"] == [0.0, 1.0e6]
    assert "no morphology recovery band" in cfg["acceptance"]
