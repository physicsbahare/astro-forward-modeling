from pathlib import Path
import sys
import pytest
pytest.importorskip('galsim')
pytest.importorskip('astropy')
pytest.importorskip('photutils')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_agn_imfit_bounded as b


def test_separate_scope_restores_everything():
    m=b.m;old=(m.SAMPLES,m.PROTOCOL,m.configuration,m.__file__)
    with pytest.raises(RuntimeError):
        with b.experiment_scope():
            cfg=m.configuration(1)
            assert cfg['samples']==(8,10) and cfg['stage'].startswith('C5n')
            assert cfg['protocol_sha256']==m.h.sha(b.PROTOCOL)
            assert cfg['producer_sha256']==m.h.sha(Path(b.__file__))
            assert cfg['reused_adapter_sha256']==m.h.sha(Path(old[3]))
            assert cfg['timeout_seconds']==120 and cfg['address_space_bytes']==6*1024**3
            with m.sampling_scope():assert 'r_e 5' in m.h.model_text(dict(n=6,re=.5,q=.15),10)
            raise RuntimeError('controlled')
    assert old==(m.SAMPLES,m.PROTOCOL,m.configuration,m.__file__)
    assert m.h.SAMPLES==(2,4,8)


def test_source_derived_fft_lower_bound():
    assert b.fft_allocation_bytes(16)>6*1024**3
    assert b.fft_allocation_bytes(10)<3.1*1024**3
    assert b.fft_allocation_bytes(8)<b.fft_allocation_bytes(10)
