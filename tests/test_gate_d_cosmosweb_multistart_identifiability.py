import importlib.util, math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "d1ng", ROOT / "scripts" / "run_gate_d_cosmosweb_multistart_identifiability.py"
)
d1ng = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(d1ng)

def test_sample_and_optimizer_budget_are_frozen():
    assert d1ng.TARGET_MAX_NFEV == d1ng.d1m.TARGET_MAX_NFEV == 500
    assert len(d1ng.SELECTED) == 4
    assert d1ng.SELECTED[0][:4] == ("near_source_2_5", 0, 168, 66)
    assert d1ng.SELECTED[1][:4] == ("relatively_isolated_ge30", 1, 69, 195)

def test_all_multistarts_are_strictly_inside_existing_bounds():
    for target in d1ng.STARTS.values():
        p = np.concatenate([np.asarray(target, dtype=float), [0.0, 0.0, 0.0]])
        finite = np.isfinite(d1ng.rec.BOUNDS_LO) & np.isfinite(d1ng.rec.BOUNDS_HI)
        assert np.all(p[finite] > d1ng.rec.BOUNDS_LO[finite])
        assert np.all(p[finite] < d1ng.rec.BOUNDS_HI[finite])

def test_truth_oracle_encodes_only_known_injection_truth():
    p = d1ng.STARTS["injection_truth_oracle"]
    assert math.isclose(math.exp(p[3]), 6.0)
    assert p[4:7] == (1.0, 0.65, 30.0)
    assert math.isclose(
        p[0], math.log(d1ng.inj.ab_to_jy(26.0) / d1ng.inj.ab_to_jy(27.5))
    )
