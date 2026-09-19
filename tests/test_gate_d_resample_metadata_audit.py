from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "audit_gate_d_cosmosweb_resample_metadata.py"
)

spec = importlib.util.spec_from_file_location("gate_d_resample_metadata_audit", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_nonfinite_fits_placeholders_become_json_null() -> None:
    assert module._jsonable(float("nan")) is None
    assert module._jsonable(float("inf")) is None
    assert module._jsonable(float("-inf")) is None


def test_missing_reference_values_do_not_look_distinct() -> None:
    values = [None, float("nan"), "nan", "N/A", "", "jwst_nircam_drizpars_0001.fits"]
    normalized = [module._jsonable(value) for value in values]
    assert module._nonempty(normalized) == ["jwst_nircam_drizpars_0001.fits"]
