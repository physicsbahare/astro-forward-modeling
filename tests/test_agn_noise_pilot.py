import sys
from pathlib import Path
import numpy as np
import pytest
pytest.importorskip('galsim')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_agn_noise_pilot import noise_field, noise_sigma, HOST_SNRS, SEEDS


def test_frozen_noise_design():
    assert HOST_SNRS == (100,20,5)
    assert SEEDS == (20260903,20260904,20260905)
    a=noise_field((17,17),4,SEEDS[0])
    np.testing.assert_array_equal(a,noise_field((17,17),4,SEEDS[0]))
    assert not np.array_equal(a,noise_field((17,17),4,SEEDS[1]))
    assert not np.array_equal(a,noise_field((17,17),1,SEEDS[0]))


def test_sigma_definition_and_pairing():
    host=np.array([[1.,2.],[3.,4.]])
    for snr in HOST_SNRS:
        np.testing.assert_allclose(np.linalg.norm(host)/noise_sigma(host,snr),snr)
    unit=noise_field(host.shape,1,SEEDS[0])
    np.testing.assert_allclose(20*noise_sigma(host,100)*unit,noise_sigma(host,5)*unit)
