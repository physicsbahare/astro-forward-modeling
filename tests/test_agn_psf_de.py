import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from run_agn_psf_de import package_search, SEARCH_BOUNDS, DE_OPTIONS, RNG_SEEDS, POPULATION_SIZE


def test_frozen_policy():
    assert RNG_SEEDS == (20260903,20260904)
    assert DE_OPTIONS == dict(strategy='best1bin',maxiter=60,popsize=10,tol=1e-7,
        atol=0.,mutation=(.5,1.),recombination=.7,init='sobol',updating='deferred',
        workers=1,vectorized=False,polish=False,x0=None)
    np.testing.assert_array_equal(SEARCH_BOUNDS[0],np.log([.5,60.]))
    np.testing.assert_array_equal(SEARCH_BOUNDS[1],np.log([.5,6.]))
    assert SEARCH_BOUNDS[2] == (.15,1.) and POPULATION_SIZE==32


def test_public_api_repeatability_and_trace():
    # Small known objective tests the adapter; never a morphology acceptance band.
    target=np.array([np.log(12.),np.log(2.),.6])
    objective=lambda x:float(np.sum((x-target)**2))
    calls=[]
    def callback(intermediate_result):
        calls.append((intermediate_result.population.copy(),intermediate_result.population_energies.copy()))
    a=package_search(objective,20260903,callback,options=dict(maxiter=2))
    b=package_search(objective,20260903,options=dict(maxiter=2))
    np.testing.assert_array_equal(a.x,b.x)
    np.testing.assert_array_equal(a.population,b.population)
    assert a.nfev==96 and len(calls)==2 and a.nit==2
    assert not a.success  # Budget exhaustion is retained, not changed to success.
    assert a.fun==min(a.population_energies)
    for population,energies in calls:
        assert population.shape==(32,3)
        assert np.all(population>=np.array(SEARCH_BOUNDS)[:,0])
        assert np.all(population<=np.array(SEARCH_BOUNDS)[:,1])
        np.testing.assert_allclose(energies,[objective(x) for x in population],rtol=1e-14)
