import importlib.util, sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
SPEC=importlib.util.spec_from_file_location('d1ne',ROOT/'scripts'/'run_gate_d_cosmosweb_published_empirical_psf.py')
d1ne=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(d1ne)


def test_scale_inference_fallback_uses_official_15mas_psf_grid():
    scale, source=d1ne.infer_scale_arcsec({})
    assert scale == 0.015
    assert source == 'official_release_notes_15mas_psf_grid'


def test_positive_metrics_preserve_negative_diagnostics():
    a=np.zeros((5,5),float); a[2,2]=1.; a[0,0]=-0.1
    m=d1ne.positive_metrics(a,0.03)
    assert m['negative_pixel_fraction'] > 0
    assert m['negative_absolute_fraction'] > 0
    assert m['ee50_radius_arcsec'] >= 0


def test_compare_identity_and_no_sharpening_operation():
    a=np.zeros((7,7),float); a[3,3]=1
    c=d1ne.compare(a,a)
    assert c['normalized_l1'] == 0
    assert abs(c['normalized_cross_correlation']-1) < 1e-15
