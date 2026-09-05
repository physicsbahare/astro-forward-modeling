import sys
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip('galsim')
pytest.importorskip('astropy')
pytest.importorskip('photutils')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_agn_empirical_psf_phase as experiment


def test_frozen_phase_configuration():
    cfg=experiment.configuration('B')
    assert cfg['runtime_versions']==experiment.PINS
    assert experiment.PARENT_RUN==33717899427 and experiment.PARENT_ARTIFACT==9880481087
    assert cfg['phase_x_native_pix']==(0.,.25,.5,.75)==cfg['phase_y_native_pix']
    assert cfg['rows_per_module']==48 and cfg['control_rows_per_module']==96
    assert cfg['full_stamp']==211 and cfg['fit_stamp']==201
    assert cfg['photutils']['oversampling']==2 and cfg['photutils']['input_factor']==4.
    assert cfg['galsim']['draw_method']=='no_pixel' and not cfg['galsim']['depixelize']


def signed_input():
    data=np.zeros((401,401)); data[200,200]=.8; data[202,197]=.3; data[199,204]=-.1
    return data


@pytest.mark.parametrize('method',experiment.METHODS)
def test_signed_input_normalization_origin_and_integer_translation(method):
    data=signed_input(); model=experiment.models(data)[method]
    zero=experiment.render(model,method,(0.,0.))
    center=(experiment.STAMP-1)//2
    # Both adapters evaluate the same input grid node and area convention.
    assert zero[center,center]==pytest.approx(4*.8,abs=1e-12)
    half_y=experiment.render(model,method,(0.,.5))
    assert half_y[center,center+2]==pytest.approx(-.4,abs=1e-12)
    shifted=experiment.render(model,method,(1.,0.))
    np.testing.assert_allclose(shifted[:,1:],zero[:,:-1],rtol=0,atol=1e-12)
    if method=='photutils_cubic':
        np.testing.assert_array_equal(model.data,4*np.pad(data,experiment.ZERO_PAD))
        assert tuple(model.origin)==(208.,208.)


@pytest.mark.parametrize('fwhm',experiment.CONTROL_FWHMS)
def test_existing_zero_phase_gaussian_check(fwhm):
    sigma=fwhm/np.sqrt(8*np.log(2))
    raw=experiment.gaussian_effective_samples(sigma,401,experiment.PSF_SCALE)
    normalized,_=experiment.normalize_psf(raw)
    exact=experiment.gaussian_exact(sigma,(0.,0.))
    for method,model in experiment.models(normalized).items():
        actual=experiment.render(model,method,(0.,0.))
        # Inherited Gaussian sanity bound, not a new off-grid acceptance band.
        assert np.abs(actual-exact).sum()<1e-6


def test_even_odd_phase_partition_is_algebra_not_a_renormalization():
    raw=signed_input()
    sums=[4*raw[y::2,x::2].sum() for x in (0,1) for y in (0,1)]
    assert np.mean(sums)==pytest.approx(raw.sum(),abs=1e-14)
    assert max(sums)!=min(sums)  # preserves phase dependence in a counterexample


def test_single_amplitude_nnls_keeps_zero_and_signed_residual():
    template=np.array([[1.,-.2],[.3,0.]])
    row,pred,residual=experiment.scalar_fit(2*template,template)
    assert row['flux']==pytest.approx(2) and not row['hit_flux_zero']
    np.testing.assert_allclose(pred,2*template,rtol=0,atol=1e-14)
    np.testing.assert_allclose(residual,0,rtol=0,atol=1e-14)
    zero,pred,residual=experiment.scalar_fit(-template,template)
    assert zero['hit_flux_zero'] and zero['flux']==0
    np.testing.assert_array_equal(pred,np.zeros_like(template))
    np.testing.assert_array_equal(residual,template)


def test_aperture_summaries_retain_negative_mass_and_declared_center():
    image=np.zeros((211,211)); image[105,105]=1.; image[105,106]=-.1
    result=experiment.image_stats(image,(0.,0.))
    assert result['negative_pixels']==1
    assert result['negative_absolute_fraction']==pytest.approx(.1/1.1)
    assert result['apertures'][0]['signed_sum']==pytest.approx(.9)
    assert result['apertures'][0]['negative_abs_sum']==pytest.approx(.1)
    assert result['signed_centroid_dx_arcsec']==pytest.approx(-.003/.9)


def test_parent_checksum_rejects_substituted_bytes(tmp_path):
    source=tmp_path/'source'; source.mkdir()
    (source/'commit.txt').write_text('not the inspected C5d commit\n')
    with pytest.raises(RuntimeError,match='parent file checksum mismatch'):
        experiment.load_parent(source,tmp_path/'output','A')
