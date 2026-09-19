import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from run_agn_cross_sampling import configuration, FIT_FACTORS, REFERENCE_FACTOR
from run_agn_nuclear_fraction_noiseless import MAX_NFEV, START_N


def test_frozen_quadratures_and_budget():
    assert FIT_FACTORS == (4, 8)
    assert REFERENCE_FACTOR == 16
    for n in (1,4):
        for factor in FIT_FACTORS:
            c = configuration(n, factor)
            assert c['reference_factor'] > c['fit_factor']
            assert c['max_nfev'] == MAX_NFEV == 160
            assert c['start_n'] == START_N == (1,2.5,5)
            assert c['re_bounds'] == (0.5,60)
            assert c['n_bounds'] == (0.5,6)
            assert c['q_bounds'] == (0.15,1)
