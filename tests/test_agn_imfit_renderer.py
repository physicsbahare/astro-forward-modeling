import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

pytest.importorskip('galsim')
pytest.importorskip('astropy')
pytest.importorskip('photutils')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_agn_imfit_renderer as experiment


def test_frozen_protocol_and_all_eight_original_corners():
    configs=[experiment.configuration(n) for n in (1,4)]
    corners={(c['n'],c['re'],c['q']) for cfg in configs for c in cfg['cases'][1:]}
    assert corners == {(n,re,q) for n in (.5,6.) for re in (.5,60.) for q in (.15,1.)}
    for cfg in configs:
        assert cfg['samples']==(2,4,8)
        assert cfg['runtime_versions']==cfg['pins']
        assert cfg['expected_render_cases']==36 and cfg['expected_direct_fits']==36
        assert cfg['imfit_subsampling'] and cfg['imfit_threads']==1
        assert cfg['render_timeout_seconds']==120
        assert cfg['prerequisite_run']==33740141863
    with pytest.raises(ValueError): experiment.structural_cases(2)


@pytest.mark.parametrize('sampling',(2,4,8))
def test_native_geometry_and_area_are_not_a_block_sum(sampling):
    side=200*sampling+1
    fine=np.zeros((side,side)); fine[100*sampling,100*sampling]=1/sampling**2
    native=experiment.native_from_fine(fine,sampling)
    assert native.shape==(201,201) and native[100,100]==1 and native.sum()==1
    fine[100*sampling+1,100*sampling+1]=1.
    np.testing.assert_array_equal(native,experiment.native_from_fine(fine,sampling))
    text=experiment.model_text(dict(n=4.,re=16.,q=.6),sampling)
    assert f'X0 {100*sampling+1}\nY0 {100*sampling+1}' in text
    assert 'PA -45' in text and f'r_e {16*sampling}' in text


@pytest.mark.parametrize('n',(.5,1.,4.,6.))
def test_total_flux_unit_conversion_scales_with_grid_area(n):
    values=[experiment.unit_sersic_ie(n,16.,.6,s)*s*s for s in (2,4,8)]
    np.testing.assert_allclose(values,[values[0]]*3,rtol=1e-12,atol=0)
    b=experiment.imfit_bn(n)
    ie=experiment.unit_sersic_ie(n,16.,.6,2)
    # Algebraic inverse of the published total-flux expression, not a render test.
    flux=np.exp(np.log(2*np.pi*.6*n*ie)+2*np.log(32)+b
                +experiment.gammaln(2*n)-2*n*np.log(b))
    assert abs(flux-1)<1e-12


def test_signed_effective_psf_is_preserved_at_original_sampling():
    raw=np.zeros((401,401)); raw[200,200]=1.25; raw[197,211]=-.25
    actual=experiment.psf_kernel(raw,2)
    np.testing.assert_allclose(actual,np.pad(raw,8),rtol=0,atol=1e-12)
    assert actual.min()<0
    assert actual.shape==(417,417)


def test_invalid_geometry_is_rejected_without_adjusting_bounds():
    with pytest.raises(ValueError): experiment.unit_sersic_ie(6.1,16,.6,4)
    with pytest.raises(ValueError): experiment.unit_sersic_ie(4,61,.6,4)
    with pytest.raises(ValueError): experiment.unit_sersic_ie(4,16,.1,4)
    with pytest.raises(ValueError): experiment.native_from_fine(np.zeros((401,401)),4)
    with pytest.raises(ValueError): experiment.psf_kernel(np.zeros((400,400)),2)


def test_resource_timeout_is_retained_as_failure(tmp_path,monkeypatch):
    def fail(*args,**kwargs):
        raise subprocess.TimeoutExpired(args[0],120)
    monkeypatch.setattr(experiment.subprocess,'run',fail)
    image,row=experiment.run_renderer(Path('/unused/makeimage'),
        dict(n=4.,re=16.,q=.6),2,tmp_path/'psf.fits',tmp_path/'case')
    assert image is None and row['success'] is False
    assert row['exception_type']=='TimeoutExpired'
    assert json.loads((tmp_path/'case/result.json').read_text())==row
    cmd=json.loads((tmp_path/'case/command.json').read_text())
    assert '--no-normalize' in cmd and '--no-subsampling' not in cmd
    assert '--overpsf' not in cmd
    assert '--print-fluxes' not in cmd  # v1.9 disables FITS saving in that mode.
    assert cmd[:3]==['/usr/bin/timeout','--kill-after=5s','120']


@pytest.mark.skipif(not os.getenv('IMFIT_MAKEIMAGE'),reason='external binary only in dedicated C5h CI')
def test_author_binary_round_gaussian_smoke(tmp_path):
    from astropy.io import fits
    kernel=np.zeros((5,5));kernel[2,2]=1
    path=tmp_path/'delta.fits';fits.writeto(path,kernel)
    binary=Path(os.environ['IMFIT_MAKEIMAGE'])
    assert experiment.sha(binary)==experiment.IMFIT_BINARY_SHA
    image,row=experiment.run_renderer(binary,dict(sigma_arcsec=.12),2,path,tmp_path/'case')
    assert row['success'] and row['fits_bitpix'] in (-32,-64)
    assert image.shape==(201,201) and np.isfinite(image).all()
    np.testing.assert_allclose(image,image[::-1,::-1],rtol=0,atol=1e-12)
    assert image[100,100]==image.max()
    assert row['peak_child_rss_kib']>0
