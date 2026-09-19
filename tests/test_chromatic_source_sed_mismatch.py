import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('c7',Path(__file__).resolve().parents[1]/'scripts'/'run_chromatic_source_sed_mismatch.py')
c7=importlib.util.module_from_spec(spec); spec.loader.exec_module(c7)


def test_controls_and_required_mismatch():
    cg,_=c7.render_case()
    same,_=c7.render_case(same_sed=True)
    ach,_=c7.render_case(achromatic_psf=True)
    assert same['normalized_l1_difference'] <= 1e-10
    assert ach['normalized_l1_difference'] <= 1e-10
    assert cg['normalized_l1_difference'] > 1e-10
    assert cg['disk_effective_psf_sigma'] != cg['bulge_effective_psf_sigma']


def test_no_noise_fit_or_redshift_semantics():
    cfg=c7.configuration()
    assert cfg['noise'] is False and cfg['fit'] is False
    assert 'thresholded' in cfg['acceptance']
