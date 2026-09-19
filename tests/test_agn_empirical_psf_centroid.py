import sys
from pathlib import Path
import numpy as np
import pytest
pytest.importorskip('galsim')
pytest.importorskip('photutils')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import run_agn_empirical_psf_centroid as c


def test_frozen_protocol():
    assert c.STARTS == ((0.,0.),(.5,.5),(-.5,-.5))
    assert c.OPTIONS['max_nfev'] == 160
    assert c.OPTIONS['ftol'] == c.OPTIONS['xtol'] == 1e-10
    assert c.OPTIONS['gtol'] == 1e-7
    assert c.PARENT_RUN == 33727185586


def test_matching_model_recovers_position_and_records_all_starts():
    raw = c.gaussian_effective_samples(.07, 401, c.PSF_SCALE)
    normalized, _ = c.normalize_psf(raw)
    model = c.models(normalized)['photutils_cubic']
    yy, xx = np.indices((201,201), dtype=float)
    data = model.evaluate(xx, yy, 1.7, 100.25, 100.75)
    winner, rows, arrays = c.fit_case(data, model, (.25,.75))
    assert len(rows) == 3 and len(arrays) == 10
    assert winner['x'] == pytest.approx(.25, abs=1e-6)
    assert winner['y'] == pytest.approx(.75, abs=1e-6)
    assert winner['flux'] == pytest.approx(1.7, abs=1e-6)
    for row in rows:
        i = row['start']
        np.testing.assert_allclose(arrays[f'start{i}_prediction']-data,
                                   arrays[f'start{i}_residual'], atol=1e-15)


@pytest.mark.parametrize('data',[np.zeros((201,201)),np.ones((3,3)),np.full((201,201),np.nan)])
def test_invalid_data(data):
    with pytest.raises(ValueError): c.fit_case(data, None, (0,0))


def test_parent_tampering_rejected(tmp_path):
    with pytest.raises((FileNotFoundError,ValueError)):
        c.verify_parent(tmp_path,'A')
