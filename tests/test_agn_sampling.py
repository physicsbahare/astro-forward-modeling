import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from run_agn_sampling import compare, FACTORS


def test_identical_templates_recover_flux():
    host = np.array([[1., 2.], [2., 1.]]) / 6
    point = np.array([[1., 0.], [0., 0.]])
    result, prediction = compare(host, host, point, 10.)
    np.testing.assert_allclose([result['host_flux'], result['nuclear_flux']], [1,10], atol=1e-12)
    np.testing.assert_allclose(prediction, host+10*point, atol=1e-12)
    assert result['host_l1_difference'] == 0


def test_sampling_and_no_stamp_renormalization():
    assert FACTORS == (4,8,16)
    host = np.array([[.1,.2],[.2,.1]])
    point = np.array([[1.,0.],[0.,0.]])
    result, _ = compare(host, host*2, point, 1.)
    np.testing.assert_allclose(result['host_flux'], .5)
    np.testing.assert_allclose(result['host_stamp_flux'], 1.2)
    assert result['normalized_two_template_condition'] > 1
