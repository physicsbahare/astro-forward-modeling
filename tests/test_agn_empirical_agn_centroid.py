import sys
from pathlib import Path
import numpy as np
import pytest

pytest.importorskip('galsim')
pytest.importorskip('photutils')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_agn_empirical_agn_centroid as c
from run_agn_empirical_psf_transfer import gaussian_effective_samples, normalize_psf


def toy():
    normalized,_=normalize_psf(gaussian_effective_samples(.07,401,.015))
    model=c.models(normalized)['photutils_cubic']
    host=gaussian_effective_samples(.4,201,.03)
    yy,xx=np.indices(host.shape,dtype=float)
    return host,model,xx,yy


def test_frozen_protocol_and_provenance():
    cfg=c.configuration(4)
    assert c.PARENT_RUN==33717899427
    assert cfg['parent_artifact_id']==9880386950
    assert cfg['prerequisite_run']==33734876563
    assert cfg['ratios']==(.1,1.,10.)
    assert cfg['bounds']==((-1.,-1.),(1.,1.))
    assert cfg['starts']==((0.,0.),(.5,.5),(-.5,-.5))
    assert cfg['optimizer']==dict(method='trf',jac='2-point',loss='linear',max_nfev=160,
        ftol=1e-10,xtol=1e-10,gtol=1e-7)
    assert cfg['expected_comparisons']==12 and cfg['expected_nonlinear_starts']==36
    assert cfg['pins']['photutils']=='3.0.0' and cfg['pins']['scipy']=='1.18.1'


def test_matched_scene_all_starts_and_fluxes():
    host,model,xx,yy=toy()
    point=model.evaluate(xx,yy,1,100.25,100.75)
    data=1.3*host+2.1*point
    fixed,winner,rows,arrays=c.fit_scene(data,host,model)
    assert len(rows)==3 and len(arrays)==14
    assert winner['x']==pytest.approx(.25,abs=1e-6)
    assert winner['y']==pytest.approx(.75,abs=1e-6)
    assert winner['host_flux']==pytest.approx(1.3,abs=1e-6)
    assert winner['nuclear_flux']==pytest.approx(2.1,abs=1e-6)
    assert winner['cost']==min(r['cost'] for r in rows)
    np.testing.assert_array_equal(arrays['data'],data)
    np.testing.assert_array_equal(arrays['host_template'],host)
    for row in rows:
        i=row['start']
        prediction=row['host_flux']*host+row['nuclear_flux']*arrays[f'start{i}_point_template']
        np.testing.assert_allclose(prediction,arrays[f'start{i}_prediction'],atol=1e-14)
        np.testing.assert_allclose(prediction-data,arrays[f'start{i}_residual'],atol=1e-14)


def test_zero_phase_fixed_baseline_is_existing_two_component_solve():
    host,model,xx,yy=toy()
    point=model.evaluate(xx,yy,1,100,100)
    data=host+10*point
    expected,pred=c.solve_fluxes(data,host,point)
    fixed,winner,rows,arrays=c.fit_scene(data,host,model)
    assert fixed==expected
    np.testing.assert_array_equal(arrays['fixed_prediction'],pred)
    assert winner['radial_offset_pix']<1e-6


def test_zero_flux_plateau_is_recorded_not_hidden():
    host,model,xx,yy=toy()
    data=-host-model.evaluate(xx,yy,1,100,100)
    fixed,winner,rows,arrays=c.fit_scene(data,host,model)
    assert all(r['hit_host_flux_zero'] and r['hit_nuclear_flux_zero'] for r in rows)
    assert [r['x'] for r in rows]==[s[0] for s in c.STARTS]
    assert len(rows)==3 and winner['cost_start_range']==0


def test_failed_start_is_preserved_and_remaining_starts_attempted(monkeypatch):
    host,model,xx,yy=toy()
    data=host+model.evaluate(xx,yy,1,100,100)
    original=c.least_squares
    calls=[]; checkpoints=[]
    def fail_once(*args,**kwargs):
        calls.append(1)
        if len(calls)==1:
            raise RuntimeError('injected test failure')
        return original(*args,**kwargs)
    monkeypatch.setattr(c,'least_squares',fail_once)
    def checkpoint(fixed,rows,arrays):
        checkpoints.append([dict(r) for r in rows])
    with pytest.raises(RuntimeError,match='starts raised'):
        c.fit_scene(data,host,model,checkpoint)
    assert len(calls)==3 and len(checkpoints[-1])==3
    assert checkpoints[-1][0]['exception_type']=='RuntimeError'
    assert checkpoints[-1][0]['cost'] is None
    assert checkpoints[-1][1]['exception_type']==''


@pytest.mark.parametrize('kind',['shape','nonfinite','zero'])
def test_invalid_scene_rejected(kind):
    host,model,xx,yy=toy()
    data=np.zeros_like(host)
    if kind=='shape': data=data[:5,:5]
    if kind=='nonfinite': data[0,0]=np.nan
    with pytest.raises(ValueError): c.fit_scene(data,host,model)


def test_missing_or_tampered_parent_rejected(tmp_path):
    with pytest.raises((FileNotFoundError,RuntimeError)):
        c.load_parent(tmp_path,tmp_path/'out',1)
