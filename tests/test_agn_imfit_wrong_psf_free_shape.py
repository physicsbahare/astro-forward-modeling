import json
from pathlib import Path
import sys

import pytest

pytest.importorskip('astropy')
pytest.importorskip('galsim')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_agn_imfit_wrong_psf_free_shape as experiment


def test_frozen_wrong_psf_high_contrast_matrix():
    for n in (1,4):
        cfg=experiment.configuration(n)
        assert cfg['ratio']==10. and cfg['truth_modules']==['A','B']
        assert cfg['fit_psf_for_truth']=={'A':'B','B':'A'}
        assert cfg['expected_cases']==2 and cfg['expected_attempts']==6
        assert cfg['shape_bounds']==dict(pa=(-180.,180.),ell=(0.,.85),n=(.5,6.),re=(.5,60.))
        assert cfg['amplitude_bounds']==(0.,1e6) and cfg['timeout_seconds']==180
        assert cfg['parent_run']==33717899427 and cfg['c5q_run']==33830661656
        assert 'opposite-module' in cfg['psf'] and '--no-normalize' in cfg['psf']
        assert 'no convergence or recovery band' in cfg['acceptance']
    with pytest.raises(ValueError): experiment.configuration(2)


def test_reuses_exact_c5o_starts_and_bounds():
    cfg=experiment.configuration(4)
    assert [row['label'] for row in cfg['starts']]==['truth','compact','extended']
    assert [row['n'] for row in cfg['starts']]==[4.,2.,5.]
    text=experiment.c5o.model_text(4,cfg['starts'][1],10.)
    assert 'X0 101 fixed\nY0 101 fixed' in text
    assert 'n 2 0.5,6' in text and 'r_e 8 0.5,60' in text
    assert text.count('0,1e+06')==2


def test_c5q_receipt_is_successful_but_all_seeds_timed_out():
    receipt=json.loads(experiment.C5Q_RECEIPT.read_text())
    assert receipt['run_id']==33830661656 and receipt['commit']==experiment.C5Q_COMMIT
    assert receipt['github_conclusion']=='success'
    rows=[]
    for module in ('module_A','module_B'): rows.extend(receipt[module].values())
    assert len(rows)==4 and all(row['returncode']==124 and not row['finite'] for row in rows)
