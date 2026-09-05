from pathlib import Path
import json
import sys

import pytest

pytest.importorskip('astropy')
pytest.importorskip('galsim')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_agn_imfit_global_search as experiment


def test_seeded_global_scope_preserves_c5p_inputs_bounds_and_cap():
    for module in experiment.c5p.MODULES:
        cfg=experiment.configuration(module)
        assert cfg['host_n']==4 and cfg['ratio']==10 and cfg['module']==module
        assert cfg['cli_solver_flag']=='--de-lhs' and cfg['seeds']==[20260904,20260905]
        assert cfg['timeout_seconds']==experiment.c5p.TIMEOUT==180
        assert cfg['shape_bounds']==experiment.c5p.c5o.SHAPE_BOUNDS
        assert cfg['amplitude_bounds']==experiment.c5p.c5o.AMPLITUDE_BOUNDS
        assert cfg['c5p_run']==33823405733 and cfg['c5p_artifact_id']==experiment.C5P_ARTIFACTS[module]
    with pytest.raises(ValueError):experiment.configuration('C')


def test_c5p_receipt_preserves_actual_solver_path_result():
    receipt=json.loads(experiment.C5P_RECEIPT.read_text())
    assert receipt['github_conclusion']=='success'
    assert receipt['module_A']['lm']['returncode']==124
    assert receipt['module_A']['nm_sse_over_c5o_finite_solution']>80
    assert receipt['module_B']['nm_sse_over_lm']>30
