import importlib.util
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
