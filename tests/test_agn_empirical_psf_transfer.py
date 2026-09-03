import sys
import io
from pathlib import Path
import numpy as np
import pytest

pytest.importorskip('galsim')
pytest.importorskip('astropy')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_agn_empirical_psf_transfer import (
    configuration, normalize_psf, effective_psf, draw, solve_fluxes,
    gaussian_effective_samples, SETTINGS, PINS, NATIVE_SCALE, PSF_SCALE,
    SOURCE_FILES, UPSTREAM_COMMIT, STAMP, CONTROL_FWHMS,
)
import run_agn_empirical_psf_transfer as experiment


def test_frozen_sources_and_transfer_policy():
    config=configuration(4)
    assert config['runtime_versions']==PINS
    assert UPSTREAM_COMMIT=='0a55283e973e2dc055ab807e29a04d89733fee48'
    assert len(SOURCE_FILES)==4 and STAMP==201
    assert PSF_SCALE==.015 and NATIVE_SCALE==.03
    assert config['draw_method']=='no_pixel'
    assert config['truth_variant']=='fine_quintic'
    assert not config['interpolation']['depixelize']
    assert config['rows_per_host']==24 and config['re_native_pix']==16.
    assert config['agn_to_host']==(.1,1.,10.)


def test_signed_psf_normalization_does_not_clip_or_recenter():
    raw=np.zeros((5,5)); raw[2,3]=2.; raw[0,0]=-.25
    actual,total=normalize_psf(raw)
    assert total==1.75
    np.testing.assert_array_equal(actual,raw/1.75)
    assert actual[0,0]<0 and np.unravel_index(actual.argmax(),actual.shape)==(2,3)
    with pytest.raises(ValueError): normalize_psf(np.zeros((5,5)))
    with pytest.raises(ValueError): normalize_psf(np.ones((4,4)))
    raw[0,0]=np.nan
    with pytest.raises(ValueError): normalize_psf(raw)


@pytest.mark.parametrize('fwhm',CONTROL_FWHMS)
def test_native_redraw_includes_effective_pixel_once(fwhm):
    sigma=fwhm/np.sqrt(8*np.log(2))
    samples=gaussian_effective_samples(sigma,401,PSF_SCALE)
    normalized,_=normalize_psf(samples)
    psf=effective_psf(normalized,SETTINGS['fine'])
    native=draw(psf)
    exact=gaussian_effective_samples(sigma,STAMP,NATIVE_SCALE)
    # Same pre-existing Gaussian L1 sanity bound; not an empirical recovery band.
    assert abs(native-exact).sum()<1e-6
    # Native centers coincide with every other sample; scale^2 is essential.
    np.testing.assert_allclose(native,normalized[::2,::2]*4,rtol=0,atol=1e-12)
    np.testing.assert_allclose(native,native[::-1,::-1],rtol=0,atol=1e-12)


def test_direct_nnls_keeps_zero_flux_and_truth_control():
    host=np.array([[1.,0.],[0.,0.]])
    point=np.array([[0.,1.],[0.,0.]])
    row,pred=solve_fluxes(host+10*point,host,point)
    np.testing.assert_array_equal(pred,host+10*point)
    assert row['host_flux']==1. and row['nuclear_flux']==10. and row['cost']==0
    zero,pred=solve_fluxes(3*point,host,point)
    assert zero['host_flux']==0 and zero['hit_host_flux_zero']
    assert zero['nuclear_flux']==3 and not zero['hit_nuclear_flux_zero']
    np.testing.assert_array_equal(pred,3*point)


def test_source_fetch_checks_bytes_and_preserves_cached_identity(tmp_path,monkeypatch):
    raw=b'immutable test data including negative samples\n'
    monkeypatch.setattr(experiment,'SOURCE_FILES',{'test.dat':experiment.git_blob_sha1(raw)})
    calls=[]
    def download(url,timeout):
        calls.append(url)
        return io.BytesIO(raw)
    monkeypatch.setattr(experiment,'urlopen',download)
    first=experiment.fetch_sources(tmp_path)
    assert (tmp_path/'test.dat').read_bytes()==raw
    assert experiment.fetch_sources(tmp_path)==first and len(calls)==1
    (tmp_path/'test.dat').write_bytes(b'wrong cached bytes')
    with pytest.raises(RuntimeError,match='immutable source mismatch'):
        experiment.fetch_sources(tmp_path)
