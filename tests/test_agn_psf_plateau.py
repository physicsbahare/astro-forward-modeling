import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from run_agn_psf_plateau import evaluate, refine, select_seeds, GRID_RE, GRID_N, GRID_Q


def test_frozen_grid_and_unfiltered_seeds():
    assert GRID_RE == (.5,1.,2.,4.,8.,12.,16.,24.,40.,60.)
    assert GRID_N == (.5,1.,2.5,4.,6.) and GRID_Q == (.3,.6,.75,1.)
    rows = [dict(cost=1.,grid_index=i,host_flux=0.) for i in (4,1,3,2)]
    assert [r['grid_index'] for r in select_seeds(rows)] == [1,2,3]


def test_zero_host_plateau_is_not_global_optimum():
    # Positive data/templates: one host direction is inactive, another improves cost.
    class Toy:
        point = np.array([[1., 1., 0.]])
        def host(self, re, n, q):
            return np.array([[0., 1., 0.]]) if re < 2 else np.array([[1., 0., 0.]])
    data = np.array([[2.,1.,0.]])
    a, pa = evaluate(data, Toy(), 1.,1.,.6)
    b, pb = evaluate(data, Toy(), 1.1,1.,.6)
    c, pc = evaluate(data, Toy(), 4.,1.,.6)
    assert a['hit_host_flux_zero'] and b['hit_host_flux_zero']
    np.testing.assert_array_equal(pa,pb)
    assert c['cost'] < a['cost'] and c['host_flux'] > 0
    np.testing.assert_allclose(pc,data,atol=1e-14)
    row, pred = refine(data,Toy(),dict(re_pix=1.,n=1.,q=.6,grid_index=0))
    assert row['success'] and row['hit_host_flux_zero']
    assert row['seed_grid_index']==0 and row['seed_re']==1.
    np.testing.assert_array_equal(pred,pa)
