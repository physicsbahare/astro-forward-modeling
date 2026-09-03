"""Protocol and adapter tests; no post-hoc science bands."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_agn_imfit_refinement as m


def test_frozen_scope():
    for n in (1,4):
        cfg=m.configuration(n)
        assert cfg['samples']==(8,16) and cfg['expected_workers']==8 and cfg['expected_starts']==16
        assert cfg['timeout_seconds']==120 and cfg['address_space_bytes']==6*1024**3
        assert cfg['parent_run']==33798675379 and cfg['pins']==cfg['runtime_versions']
        assert [(c['re'],c['q']) for c in cfg['cases']]==[(.5,.15),(.5,1.)]


def test_sampling_adapter_restores_on_error():
    original=m.h.SAMPLES
    with pytest.raises(RuntimeError):
        with m.sampling_scope():
            assert m.h.SAMPLES==(8,16)
            raise RuntimeError('controlled')
    assert m.h.SAMPLES==original==(2,4,8)


@pytest.mark.parametrize('sampling',[8,16])
def test_units_center_and_flux(sampling):
    case=dict(n=6.,re=.5,q=.15)
    with m.sampling_scope():
        text=m.h.model_text(case,sampling)
        assert f'X0 {100*sampling+1}' in text and f'r_e {.5*sampling:.17g}' in text
        assert 'PA -45' in text
        ie=m.h.unit_sersic_ie(6.,.5,.15,sampling)
        assert ie*sampling**2==pytest.approx(m.h.unit_sersic_ie(6.,.5,.15,8)*64)
        fine=np.zeros((200*sampling+1,)*2);fine[100*sampling,100*sampling]=1/sampling**2
        native=m.h.native_from_fine(fine,sampling)
        assert native.shape==(201,201) and native[100,100]==1 and native.sum()==1


def test_outside_new_sampling_rejected():
    with m.sampling_scope(),pytest.raises(ValueError):m.h.unit_sersic_ie(1.,.5,.6,32)


def test_timeout_is_recorded_once(tmp_path,monkeypatch):
    calls=[]
    def fake(command,**kwargs):calls.append(command);return SimpleNamespace(returncode=124)
    monkeypatch.setattr(m.subprocess,'run',fake)
    result=m.run_worker(dict(n=6.,re=.5,q=.15),'A',16,Path('/binary'),Path('/psfs'),tmp_path/'worker')
    assert not result['success'] and result['returncode']==124 and len(calls)==1
    assert calls[0][:3]==['/usr/bin/timeout','--kill-after=5s','120']
    assert json.loads((tmp_path/'worker/process_result.json').read_text())==result


def test_c5l_psf_archive_schema(tmp_path):
    a=np.zeros((401,401));a[200,200]=1.1;a[0,0]=-.1
    path=tmp_path/'psfs.npz';np.savez(path,A=a,B=a)
    np.testing.assert_array_equal(m.load_psf(path,'A'),a)
    np.savez(tmp_path/'bad.npz',A_normalized_input=a)
    with pytest.raises(ValueError):m.load_psf(tmp_path/'bad.npz','A')
