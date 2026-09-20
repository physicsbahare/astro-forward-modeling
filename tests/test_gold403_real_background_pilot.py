import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


def _load_module():
    path = Path("scripts/run_gold403_real_background_pilot.py")
    sys.path.insert(0, str(path.parent.resolve()))
    try:
        spec = importlib.util.spec_from_file_location("gold403_real_pilot", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


def test_case_seed_is_accepted_by_legacy_numpy_rng():
    seed = _load_module().case_seed(9)
    assert 0 <= seed <= 2**32 - 1
    np.random.RandomState(seed)


def test_pilot_uses_the_documented_morphology_band_key():
    assert 'str(_morph["morph_filter"])' in Path("scripts/run_gold403_real_background_pilot.py").read_text()


def test_pilot_reports_nonfinite_output_fields_before_json_serialization():
    source = Path("scripts/run_gold403_real_background_pilot.py").read_text()
    assert "NONFINITE_OUTPUT_FIELDS=" in source
    assert "_out=_normalize_receipt_record(_out)" in source


def test_kernel_receipt_normalizer_preserves_nonphysical_bt_as_structured_error():
    module = _load_module()
    namespace = {"json": json, "np": np}
    exec(module.KERNEL_JSON_SAFETY_BOOTSTRAP, namespace)
    record = namespace["_normalize_receipt_record"](
        {
            "status": "OK",
            "error": "",
            "real_bt": float("nan"),
            "delta_real_minus_clean_bt": float("nan"),
            "real_disk": False,
            "clean_to_real_flip": True,
            "real_n": 1.7,
        }
    )

    assert record["status"] == "ERROR"
    assert record["error"] == 'NONFINITE_OUTPUT_FIELDS={"delta_real_minus_clean_bt": "nan", "real_bt": "nan"}'
    assert record["real_bt"] is None
    assert record["delta_real_minus_clean_bt"] is None
    assert record["real_disk"] is None
    assert record["clean_to_real_flip"] is None
    assert record["real_n"] == 1.7
    json.dumps(record, allow_nan=False)
