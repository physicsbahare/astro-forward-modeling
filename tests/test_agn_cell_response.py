import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
pytest.importorskip('galsim');pytest.importorskip('photutils')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_agn_cell_response as c


def test_frozen_design_and_actual_prerequisites():
    assert c.ARMS==('no_cell','cell2','cell4','cell8') and c.SAMPLES==(2,4,8)
    for n in (1,4):
        cfg=c.configuration(n)
        assert cfg['parent_run']==33788705952 and cfg['secondary_parent_run']==33766246396
        assert cfg['expected_workers']==16 and cfg['expected_direct_starts']==48
        assert cfg['expected_pairwise_comparisons']==24
        assert cfg['worker_timeout_seconds']==120 and cfg['worker_address_space_bytes']==6*1024**3
    receipt=c.e.read(c.AUDIT)
    assert receipt['github_confirmation']['conclusion']=='success'
    assert sum(a['counts']['new_arrays'] for a in receipt['artifacts'])==896
    assert sum(a['counts']['incomplete_initial_fft_logs'] for a in receipt['artifacts'])==0


@pytest.mark.parametrize('arm',c.ARMS)
def test_cell_units_flux_signed_inputs_and_fourier_composition(arm):
    raw=np.zeros((401,401));raw[200,200]=1.2;raw[200,202]=-.2
    case=c.p.cases(1)[0]
    host,psf,conv,meta=c.models(case,raw,arm)
    base_host,base_psf,base_conv,_=c.grid.models(case,raw,'grid1536_k4')
    assert host==base_host and host.gsparams==psf.gsparams==conv.gsparams
    assert meta['cell_is_physical_detector_response'] is False
    if arm=='no_cell':assert psf==base_psf and conv==base_conv
    else:
        sampling=int(arm[4:]);cell=psf.obj_list[1]
        assert cell.scale==.03/sampling and cell.flux==1
        np.testing.assert_array_equal(psf.obj_list[0].image.array,raw)
        assert psf.obj_list[0].maxk==base_psf.maxk
        for x,y in ((0,0),(4.,7.),(13.,-2.)):
            np.testing.assert_allclose(psf.kValue(x,y),base_psf.kValue(x,y)*cell.kValue(x,y),rtol=0,atol=1e-12)
            np.testing.assert_allclose(conv.kValue(x,y),host.kValue(x,y)*psf.kValue(x,y),rtol=0,atol=1e-12)


def test_unknown_cell_is_not_silently_accepted():
    with pytest.raises(ValueError):c.arm_config('cell16')


@pytest.mark.parametrize('receipts,status',[(1,1),(2,0)])
def test_receipt_guard_and_adapter_restoration(tmp_path,monkeypatch,receipts,status):
    cfg=tmp_path/'config.json';c.e.dump(cfg,dict(case=dict(n=.5)))
    c.e.dump(tmp_path/'fft_trace.json',[{}]*receipts)
    c.e.dump(tmp_path/'result.json',dict(success=True,render=dict(retained=True)))
    old=c.e.models
    def fake(path):
        assert c.e.models is c.models
        return 0
    monkeypatch.setattr(c.e,'worker',fake)
    assert c.worker(cfg)==status and c.e.models is old
    assert c.e.read(tmp_path/'result.json')['success']==(status==0)


def test_timeout_preserves_single_attempt(tmp_path,monkeypatch):
    commands=[]
    def fail(command,**kwargs):commands.append(command);return subprocess.CompletedProcess(command,124)
    monkeypatch.setattr(c.subprocess,'run',fail)
    row=c.run_worker(c.p.cases(4)[0],'A','cell8',tmp_path/'psf.npz',tmp_path/'render')
    assert not row['success'] and len(commands)==1
    assert commands[0][:3]==['/usr/bin/timeout','--kill-after=5s','120']
    assert Path(commands[0][4]).name=='run_agn_cell_response.py'
