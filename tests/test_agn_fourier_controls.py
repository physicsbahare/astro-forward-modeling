import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

pytest.importorskip('galsim')
pytest.importorskip('astropy')
pytest.importorskip('photutils')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_agn_fourier_controls as experiment


def test_frozen_interventions_only_change_declared_parameters():
    coarse, fine = experiment.parent.SETTINGS['coarse'], experiment.parent.SETTINGS['fine']
    assert experiment.ARMS == ('coarse','folding_only','maxk_only','kvalue_only','xvalue_only',
        'fine','fine_hankel','fine_psf_extent','fine_psf_bandlimit')
    assert experiment.arm_config('coarse')['settings'] == coarse
    assert experiment.arm_config('fine')['settings'] == fine
    for arm,key in [('folding_only','folding_threshold'),('maxk_only','maxk_threshold'),
                    ('kvalue_only','kvalue_accuracy'),('xvalue_only','xvalue_accuracy')]:
        cfg = experiment.arm_config(arm)
        assert cfg['settings'] == dict(coarse,**{key:fine[key]})
        assert cfg['calculate_stepk'] and cfg['calculate_maxk']
        assert fine[key] < coarse[key]
    assert experiment.arm_config('fine_hankel')['settings'] == dict(fine,
        integration_relerr=1e-8,integration_abserr=1e-10)
    assert experiment.arm_config('fine_psf_extent') == dict(settings=fine,calculate_stepk=False,calculate_maxk=True)
    assert experiment.arm_config('fine_psf_bandlimit') == dict(settings=fine,calculate_stepk=True,calculate_maxk=False)
    with pytest.raises(ValueError): experiment.arm_config('pick_closest')


@pytest.mark.parametrize('host_n',[1,4])
def test_configuration_keeps_physics_pins_counts_and_per_worker_caps(host_n):
    cfg = experiment.configuration(host_n)
    assert cfg['parent_run'] == 33766246396 and cfg['parent_commit'] == experiment.PARENT_COMMIT
    assert cfg['pins'] == cfg['runtime_versions']
    assert len(cfg['cases']) == 2 and {c['re'] for c in cfg['cases']} == {.5}
    assert {c['q'] for c in cfg['cases']} == {.15,1.}
    assert cfg['convention'] == 'nominal_hlr' and cfg['truncation'] == 0
    assert cfg['stamp'] == 201 and cfg['draw_method'] == 'no_pixel'
    assert cfg['worker_timeout_seconds'] == 120 and cfg['kill_grace_seconds'] == 5
    assert cfg['worker_address_space_bytes'] == 6*1024**3
    assert cfg['expected_workers'] == cfg['expected_sersic_images'] == cfg['expected_direct_starts'] == 36
    assert cfg['expected_gaussian_images'] == (36 if host_n == 1 else 0)


def test_finite_fourier_probe_grid_has_fixed_physical_units_and_product_identity():
    x,y = experiment.probe_coordinates()
    assert x.shape == y.shape == (260,)
    radius = np.hypot(x,y).reshape(65,4)
    np.testing.assert_allclose(radius[:,0],np.r_[0.,np.geomspace(1e-3,8*np.pi/.015,64)],rtol=1e-14,atol=0)
    np.testing.assert_allclose(radius,radius[:,0,None]*np.ones((1,4)),rtol=1e-14,atol=0)
    a = experiment.galsim.Gaussian(sigma=.1).shift(.03,-.01)
    b = experiment.galsim.Gaussian(sigma=.2)
    product = experiment.sample_k(a,x,y)*experiment.sample_k(b,x,y)
    actual = experiment.sample_k(experiment.galsim.Convolve(a,b),x,y)
    np.testing.assert_allclose(actual,product,rtol=0,atol=1e-12)


@pytest.mark.parametrize('arm',['coarse','fine','fine_psf_extent','fine_psf_bandlimit','fine_hankel'])
def test_public_psf_options_preserve_signed_input_and_global_gsparams(arm):
    raw = np.zeros((401,401));raw[200,200]=1.25;raw[200,202]=-.25
    saved = raw.copy()
    source,psf,convolution,radius = experiment.models(experiment.parent.cases(1)[0],raw,arm)
    np.testing.assert_array_equal(raw,saved)
    np.testing.assert_array_equal(psf.image.array,raw)
    assert psf.flux == 1 and source.flux == pytest.approx(1.,abs=1e-12)
    assert source.gsparams == psf.gsparams == convolution.gsparams
    assert radius['galsim_semimajor_hlr_native_pix'] == .5
    assert psf._calculate_stepk == experiment.arm_config(arm)['calculate_stepk']
    assert psf._calculate_maxk == experiment.arm_config(arm)['calculate_maxk']


def test_fft_observer_does_not_change_drawn_arrays_or_leak_patch(tmp_path):
    g = experiment.galsim
    model = g.Convolve(g.Gaussian(sigma=.06),g.Gaussian(sigma=.04))
    before = experiment.draw(model)
    original = g.GSObject.drawFFT_makeKImage
    trace = []
    with experiment.observe_fft(trace,tmp_path/'fft.json'):
        observed = experiment.draw(model)
    np.testing.assert_array_equal(before,observed)
    assert g.GSObject.drawFFT_makeKImage is original
    assert len(trace) == 1 and trace[0]['wrap_size'] >= 201
    assert trace[0]['k_spacing'] > 0 and trace[0]['k_dtype'] == 'complex128'
    assert json.loads((tmp_path/'fft.json').read_text()) == trace
    with pytest.raises(RuntimeError):
        with experiment.observe_fft([],tmp_path/'other.json'):
            raise RuntimeError('intentional test')
    assert g.GSObject.drawFFT_makeKImage is original


def test_timeout_is_retained_once_without_accuracy_change(tmp_path,monkeypatch):
    commands = []
    def timeout(command,**kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command,124)
    monkeypatch.setattr(experiment.subprocess,'run',timeout)
    row = experiment.run_worker(experiment.parent.cases(4)[0],'B','fine_psf_bandlimit',
        tmp_path/'psfs.npz',tmp_path/'attempt')
    assert len(commands) == 1 and commands[0][:3] == ['/usr/bin/timeout','--kill-after=5s','120']
    assert not row['success'] and row['process_error'] == 'timeout'
    cfg = experiment.read(tmp_path/'attempt/worker_config.json')
    assert cfg['arm_config'] == experiment.arm_config('fine_psf_bandlimit')
    assert cfg['address_space_bytes'] == 6*1024**3
    assert experiment.read(tmp_path/'attempt/process_result.json') == row


def test_actual_parent_audit_covers_all_science_products():
    audit = experiment.read(experiment.AUDIT)
    assert audit['run_id'] == 33766246396 and audit['commit'] == experiment.PARENT_COMMIT
    assert audit['github_confirmation']['status'] == 'completed'
    assert audit['github_confirmation']['conclusion'] == 'success'
    assert len(audit['github_confirmation']['jobs']) == 2
    assert sum(a['counts']['new_npz_arrays'] for a in audit['artifacts']) == 308
    assert sum(a['counts']['starts'] for a in audit['artifacts']) == 48
    assert all(a['counts']['worker_failures'] == 0 for a in audit['artifacts'])


def test_parent_hash_tampering_blocks_science(tmp_path,monkeypatch):
    source=tmp_path/'source';source.mkdir()
    audit=experiment.read(experiment.AUDIT)
    record=audit['artifacts'][0]
    record['file_sha256']={'altered.dat':'0'*64}
    fake=tmp_path/'audit.json';experiment.dump(fake,audit)
    (source/'altered.dat').write_text('tampered')
    monkeypatch.setattr(experiment,'AUDIT',fake)
    with pytest.raises(RuntimeError,match='C5i source checksum mismatch'):
        experiment.verified_inputs(source,tmp_path/'output',1)
    assert not (tmp_path/'output').exists()
