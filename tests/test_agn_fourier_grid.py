import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest

pytest.importorskip('galsim');pytest.importorskip('astropy');pytest.importorskip('photutils')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_agn_fourier_grid as experiment


def test_crossed_settings_and_historical_failure_are_frozen():
    assert experiment.GRIDS==(1024,1536) and experiment.MULTIPLIERS==(1,2,4)
    assert len(experiment.ARMS)==7 and experiment.ARMS[0]=='replay'
    for host_n in (1,4):
        cfg=experiment.configuration(host_n)
        assert cfg['expected_workers']==cfg['expected_sersic_images']==cfg['expected_direct_starts']==28
        assert cfg['expected_pairwise_comparisons']==84 and cfg['worker_timeout_seconds']==120
        assert cfg['worker_address_space_bytes']==6*1024**3
        assert cfg['protocol_sha256']==experiment.parent.sha(experiment.PROTOCOL)
    record=experiment.engine.read(experiment.LOCAL_RECORD)
    assert record['scope'].startswith('LOCAL ONLY')
    assert sum(a['counts']['failed_workers'] for a in record['artifacts'])==4
    assert sum(a['counts']['new_arrays'] for a in record['artifacts'])==892
    for path,digest in record['source_sha256'].items():assert experiment.parent.sha(experiment.ROOT/path)==digest
    assert not (experiment.ROOT/'.github/workflows/gate-c-agn-fourier-controls.yml').exists()


@pytest.mark.parametrize('arm',experiment.ARMS)
def test_frequency_override_units_propagation_and_signed_data(arm):
    raw=np.zeros((401,401));raw[200,200]=1.2;raw[200,202]=-.2
    source,psf,conv,radius=experiment.models(experiment.parent.cases(1)[0],raw,arm)
    np.testing.assert_array_equal(psf.image.array,raw)
    assert source.gsparams==psf.gsparams==conv.gsparams
    assert radius['galsim_semimajor_hlr_native_pix']==.5
    if arm!='replay':
        cfg=experiment.arm_config(arm)
        inherited=experiment.parent.effective_psf(raw,experiment.parent.SETTINGS['fine'])
        assert psf.maxk==inherited.maxk*cfg['force_maxk_multiplier']==conv.obj_list[1].maxk
        assert psf._calculate_stepk is False and psf._calculate_maxk is True
        assert source.gsparams.minimum_fft_size in (1024,1536)
        assert source.gsparams.integration_relerr==1e-6
    else:
        assert psf._calculate_stepk is True and source.gsparams.minimum_fft_size==128


def test_model_adapter_is_scoped_even_on_failure(tmp_path,monkeypatch):
    original=experiment.engine.models
    def fake(path):
        assert experiment.engine.models is experiment.models
        raise RuntimeError('deliberate worker failure')
    monkeypatch.setattr(experiment.engine,'worker',fake)
    with pytest.raises(RuntimeError):experiment.worker(tmp_path/'config.json')
    assert experiment.engine.models is original


def test_timeout_cannot_relaunch_with_changed_cutoff(tmp_path,monkeypatch):
    commands=[]
    def failed(command,**kwargs):
        commands.append(command);return subprocess.CompletedProcess(command,124)
    monkeypatch.setattr(experiment.subprocess,'run',failed)
    row=experiment.run_worker(experiment.parent.cases(4)[0],'A','grid1536_k4',tmp_path/'psfs.npz',tmp_path/'worker')
    assert len(commands)==1 and Path(commands[0][4]).name=='run_agn_fourier_grid.py'
    assert commands[0][:3]==['/usr/bin/timeout','--kill-after=5s','120']
    assert row['success'] is False and row['process_error']=='timeout'
    cfg=json.loads((tmp_path/'worker/worker_config.json').read_text())
    assert cfg['arm_config']==experiment.arm_config('grid1536_k4')


@pytest.mark.parametrize('trace_count,expected_status',[(1,1),(2,0)])
def test_successful_images_require_complete_fft_receipts(tmp_path,monkeypatch,trace_count,expected_status):
    cfg=tmp_path/'worker_config.json'
    experiment.engine.dump(cfg,dict(case=dict(n=.5)))
    experiment.engine.dump(tmp_path/'fft_trace.json',[{}]*trace_count)
    experiment.engine.dump(tmp_path/'result.json',dict(success=True,render=dict(retained=True)))
    monkeypatch.setattr(experiment.engine,'worker',lambda path:0)
    original=experiment.engine.models
    assert experiment.worker(cfg)==expected_status
    result=experiment.engine.read(tmp_path/'result.json')
    assert result['success']==(expected_status==0) and result['render']['retained']
    assert experiment.engine.models is original
