from pathlib import Path
import sys

import pytest

pytest.importorskip('astropy')
pytest.importorskip('galsim')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_agn_imfit_optimizer_path as experiment


def test_frozen_scope_preserves_c5o_bounds_and_resource_limit():
    for module in experiment.MODULES:
        cfg=experiment.configuration(module)
        assert cfg['host_n']==4 and cfg['ratio']==10 and cfg['module']==module
        assert cfg['solvers']==['lm','nm'] and cfg['timeout_seconds']==180
        assert cfg['shape_bounds']==experiment.c5o.SHAPE_BOUNDS
        assert cfg['amplitude_bounds']==experiment.c5o.AMPLITUDE_BOUNDS
        assert cfg['start']['label']=='compact' and cfg['expected_attempts']==2
        assert cfg['c5o_run']==33819349854 and cfg['c5o_artifact_id']==9917827458
    with pytest.raises(ValueError): experiment.configuration('C')


def test_solver_flags_are_author_cli_flags():
    assert experiment.SOLVERS==(('lm',()),('nm',('--nm',)))


def test_c5o_receipt_preserves_split_failure():
    import json
    receipt=json.loads(experiment.C5O_RECEIPT.read_text())
    assert receipt['github_conclusion']=='failure'
    assert receipt['jobs']['n1']['conclusion']=='success'
    assert receipt['jobs']['n4']['conclusion']=='failure'
    assert receipt['failure']['returncode']==124
