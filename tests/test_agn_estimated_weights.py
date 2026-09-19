import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_agn_estimated_weights import estimated_sigma, SOURCE_RUN


def test_single_model_variance_formula():
    prediction=np.array([[0.,1.],[2.,10.]])
    np.testing.assert_allclose(estimated_sigma(prediction,.01)**2,.0001+prediction/10000)
    assert SOURCE_RUN==33680659156


def test_invalid_variance_not_clipped():
    for prediction,sigma in [(np.array([-1e-12]),1.),(np.array([np.nan]),1.),(np.array([1.]),0.)]:
        with pytest.raises(ValueError):
            estimated_sigma(prediction,sigma)
