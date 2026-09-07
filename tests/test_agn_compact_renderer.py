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
import run_agn_compact_renderer as experiment


def test_frozen_cases_and_resources_without_changing_original_bounds():
    assert {(c['n'],c['re'],c['q']) for n in (1,4) for c in experiment.cases(n)} == {
        (n,.5,q) for n in (.5,6.) for q in (.15,1.)}
    for host_n in (1,4):
        cfg=experiment.configuration(host_n)
        assert cfg['parent_run']==33759931812 and cfg['runtime_versions']==cfg['pins']
        assert cfg['expected_workers']==8 and cfg['expected_sersic_images']==16
        assert cfg['expected_direct_fits']==24 and cfg['expected_refinements']==8
        assert cfg['expected_gaussian_images']==(16 if host_n==1 else 0)
        assert cfg['worker_timeout_seconds']==120 and cfg['worker_kill_grace_seconds']==5
        assert cfg['worker_address_space_bytes']==6*1024**3
        assert cfg['archived_imfit_sampling']==(2,4,8)
        assert cfg['draw_method']=='no_pixel' and cfg['profile_truncation']==0
        assert cfg['gsparams']['coarse']==dict(folding_threshold=1e-4,maxk_threshold=1e-5,
                                              kvalue_accuracy=1e-7,xvalue_accuracy=1e-7)
        assert cfg['gsparams']['fine']==dict(folding_threshold=1e-5,maxk_threshold=1e-6,
                                            kvalue_accuracy=1e-8,xvalue_accuracy=1e-8)
    with pytest.raises(ValueError):experiment.cases(2)


@pytest.mark.parametrize('case',experiment.cases(1)+experiment.cases(4))
def test_bn_equivalence_is_an_analytic_unit_conversion_not_a_fit(case):
    nominal=experiment.radius_convention(case,'nominal_hlr')
    equivalent=experiment.radius_convention(case,'imfit_bn_equivalent')
    assert nominal['galsim_semimajor_hlr_native_pix']==.5
    # Equality of the exponent coefficient of the same analytic Sersic law.
    left=equivalent['exact_bn']/equivalent['galsim_semimajor_hlr_native_pix']**(1/case['n'])
    right=equivalent['imfit_bn']/.5**(1/case['n'])
    assert abs(left/right-1)<1e-12
    assert equivalent['circularized_hlr_arcsec']==(
        equivalent['galsim_semimajor_hlr_native_pix']*.03*np.sqrt(case['q']))
    for convention in experiment.CONVENTIONS:
        galaxy,values=experiment.galaxy(case,experiment.SETTINGS['fine'],convention)
        assert abs(galaxy.flux-1)<1e-12
        assert galaxy.original.n==case['n']
        assert galaxy.original.half_light_radius==values['circularized_hlr_arcsec']


def test_gaussian_control_uses_same_size_and_flux_and_is_not_allowed_for_n6():
    case=experiment.cases(1)[0]
    source,values=experiment.galaxy(case,experiment.SETTINGS['fine'],'imfit_bn_equivalent',True)
    assert isinstance(source.original,experiment.galsim.Gaussian)
    assert abs(source.flux-1)<1e-12
    assert source.original.half_light_radius==values['circularized_hlr_arcsec']
    with pytest.raises(ValueError):
        experiment.galaxy(experiment.cases(4)[0],experiment.SETTINGS['fine'],'nominal_hlr',True)
    with pytest.raises(ValueError):
        experiment.radius_convention(case,'choose_closest')


def test_direct_amplitude_projection_preserves_signed_template_and_zero_bound():
    template=np.zeros((201,201));template[100,100]=1.2;template[102,105]=-.2
    row,prediction=experiment.amplitude_comparison(2*template,template)
    assert row['amplitude']==pytest.approx(2,abs=1e-12)
    assert row['gradient']==pytest.approx(0,abs=1e-12)
    assert row['cost']==pytest.approx(0,abs=1e-12) and not row['hit_amplitude_zero']
    np.testing.assert_allclose(prediction,2*template,rtol=0,atol=1e-12)
    row,prediction=experiment.amplitude_comparison(-template,template)
    assert row['amplitude']==0 and row['hit_amplitude_zero']
    assert row['gradient']>0 and row['cost']>0 and np.count_nonzero(prediction)==0


def test_manifest_rejects_modified_parent_before_rendering(tmp_path):
    path=tmp_path/'parent.dat';path.write_bytes(b'frozen')
    manifest={'parent.dat':experiment.sha(path)}
    experiment.verify_manifest(tmp_path,manifest)
    path.write_bytes(b'changed')
    with pytest.raises(RuntimeError,match='checksum mismatch'):
        experiment.verify_manifest(tmp_path,manifest)


def test_npz_readback_preserves_signed_data_and_rejects_incomplete_writes(tmp_path,monkeypatch):
    import zipfile
    path=tmp_path/'values.npz';values=np.array([1.25,-.25])
    experiment.save_arrays(path,values=values)
    with np.load(path) as f:np.testing.assert_array_equal(f['values'],values)
    with pytest.raises(FileExistsError):experiment.save_arrays(path,values=values)
    def truncated(output,**kwargs):
        output.write(b'PK\x03\x04incomplete')
    monkeypatch.setattr(experiment.np,'savez_compressed',truncated)
    with pytest.raises(zipfile.BadZipFile):experiment.save_arrays(tmp_path/'broken.npz',values=values)
    assert not (tmp_path/'broken.npz').exists()
    assert (tmp_path/'broken.npz.partial').exists()


def test_timeout_is_preserved_without_rerun_or_altered_science(tmp_path,monkeypatch):
    attempts=[]
    def fail(command,**kwargs):
        attempts.append(command)
        return subprocess.CompletedProcess(command,124)
    monkeypatch.setattr(experiment.subprocess,'run',fail)
    row=experiment.run_worker(experiment.cases(4)[0],'B','fine',tmp_path/'psfs.npz',tmp_path/'case')
    assert len(attempts)==1 and not row['success'] and row['returncode']==124
    assert attempts[0][:3]==['/usr/bin/timeout','--kill-after=5s','120']
    assert json.loads((tmp_path/'case/process_result.json').read_text())==row
    cfg=json.loads((tmp_path/'case/worker_config.json').read_text())
    assert cfg['accuracy']=='fine' and cfg['case']==experiment.cases(4)[0]
    assert cfg['address_space_bytes']==6*1024**3


def test_worker_preserves_partial_products_and_warning_before_failure(tmp_path,monkeypatch):
    case=experiment.cases(4)[0]
    config=tmp_path/'worker_config.json'
    experiment.dump(config,dict(case=case,module='A',accuracy='coarse',psf_path=str(tmp_path/'psfs.npz')))
    image=np.zeros((401,401));image[200,200]=1.25;image[200,201]=-.25
    np.savez(tmp_path/'psfs.npz',A=image)
    limits=[];calls=[]
    monkeypatch.setattr(experiment.resource,'setrlimit',lambda key,value:limits.append((key,value)))
    def fake_draw(obj):
        calls.append(obj)
        if len(calls)==2:
            experiment.warnings.warn('deliberate resource diagnostic')
            raise MemoryError('deliberate test failure')
        data=np.zeros((201,201));data[100,100]=1.25;data[100,101]=-.25
        return data
    monkeypatch.setattr(experiment,'draw',fake_draw)
    assert experiment.worker(config)==1
    result=json.loads((tmp_path/'result.json').read_text())
    assert not result['success'] and result['exception_type']=='MemoryError'
    assert len(result['renders'])==1 and (tmp_path/'nominal_hlr.npz').exists()
    assert limits==[(experiment.resource.RLIMIT_AS,(6*1024**3,6*1024**3))]
    assert json.loads((tmp_path/'warnings.json').read_text())[0]['message']=='deliberate resource diagnostic'
    assert json.loads((tmp_path/'runtime.json').read_text())['peak_rss_kib']>0


def test_inherited_audit_records_explicit_ci_success_and_all_arrays():
    audit=json.loads(experiment.AUDIT.read_text())
    assert audit['run_id']==33759931812 and audit['commit']==experiment.PARENT_COMMIT
    assert audit['github_confirmation']['conclusion']=='success'
    assert sum(a['counts']['renders'] for a in audit['artifacts'])==72
    assert sum(a['counts']['direct_fits'] for a in audit['artifacts'])==72
    assert sum(a['counts']['npz_arrays']+a['counts']['fits_arrays'] for a in audit['artifacts'])==600
    assert all(not a['counts']['render_failures'] for a in audit['artifacts'])
