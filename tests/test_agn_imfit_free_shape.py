import os
from pathlib import Path
import subprocess
import sys

import pytest

pytest.importorskip('astropy')
pytest.importorskip('galsim')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_agn_imfit_free_shape as experiment


def test_frozen_nominal_matched_matrix_and_unchanged_shape_bounds():
    for n in (1,4):
        cfg=experiment.configuration(n)
        assert cfg['ratios']==[1.,10.] and cfg['modules']==['A','B']
        assert cfg['shape_bounds']==dict(pa=(-180.,180.),ell=(0.,.85),n=(.5,6.),re=(.5,60.))
        assert cfg['amplitude_bounds']==(0.,1e6)
        assert cfg['expected_cases']==4 and cfg['expected_starts']==12
        assert cfg['runtime_versions']==cfg['pins']
        assert cfg['parent_run']==33717899427 and cfg['parent_artifact_id']==experiment.ARTIFACTS[n]
        assert 'matched' in cfg['psf'] and '--no-normalize' in cfg['psf']
    with pytest.raises(ValueError):experiment.configuration(2)


def test_model_uses_fixed_center_free_shape_and_nonnegative_amplitudes():
    start=experiment.configuration(4)['starts'][1]
    text=experiment.model_text(4,start,10)
    assert 'X0 101 fixed\nY0 101 fixed' in text
    assert 'FUNCTION Sersic' in text and 'FUNCTION PointSource' in text
    assert 'PA 0 -180,180' in text and 'ell 0.19999999999999996 0,0.85' in text
    assert 'n 2 0.5,6' in text and 'r_e 8 0.5,60' in text
    assert text.count('0,1e+06')==2


def test_bestfit_parser_and_boundary_observables(tmp_path):
    path=tmp_path/'bestfit.dat'
    path.write_text('X0 101 # fixed\nY0 101\nFUNCTION Sersic\nPA -45\nell .4\nn 4\nI_e .001\nr_e 16\nFUNCTION PointSource\nI_tot 10\n')
    parsed=experiment.parse_bestfit(path)
    assert parsed==dict(pa=-45.,q=.6,n=4.,ie=.001,re=16.,point_flux=10.)
    assert experiment.bound_hits(parsed)==[]
    parsed['n']=6.;parsed['point_flux']=0.
    assert experiment.bound_hits(parsed)==['n','point_flux']


def test_incomplete_bestfit_is_rejected(tmp_path):
    path=tmp_path/'bad.dat';path.write_text('X0 101\nY0 101\nFUNCTION PointSource\nI_tot 1\n')
    with pytest.raises(RuntimeError):experiment.parse_bestfit(path)


@pytest.mark.skipif(not os.getenv('IMFIT_BINARY'),reason='external binary only in dedicated C5o CI')
def test_pinned_binary_exposes_required_author_components():
    binary=Path(os.environ['IMFIT_BINARY'])
    assert experiment.sha(binary)==experiment.IMFIT_SHA
    # The pinned v1.9 CLI deliberately exits 1 for reporting-only commands.
    result=subprocess.run([str(binary),'--list-parameters'],capture_output=True,text=True,check=False)
    assert result.returncode==1
    assert 'FUNCTION Sersic' in result.stdout and 'FUNCTION PointSource' in result.stdout
    assert 'I_tot' in result.stdout
