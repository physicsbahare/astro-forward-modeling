import sys
from pathlib import Path
import numpy as np
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from passive_disk_mass_redshift import joint_rates, shapley_change, common_support, wilson

class ScientificInvariants(unittest.TestCase):
 def test_joint_rates_preserve_decomposition(self):
    c=np.array([[8,12,30,50],[0,10,0,90]])
    rates=joint_rates(c)
    assert np.allclose(rates['pd_all'],rates['passive_all']*rates['disk_passive'])
    assert rates['pd_all'][1]==0

 def test_shapley_exact_with_opposing_factors(self):
    p,d=shapley_change(.4,.1,.2,.3)
    assert np.isclose(p+d,.2*.3-.4*.1)
    assert p<0 and d>0

 def test_support_uses_denominators_not_favorable_outcomes(self):
    n=np.array([[100,80,70],[200,120,90]])
    p=np.array([[30,25,21],[50,19,60]])
    assert np.array_equal(common_support(n,p,50,20),[True,False])

class IntervalEndpoints(unittest.TestCase):
 def test_exact_zero_and_one(self):
  assert wilson(0,47)[0]==0
  assert wilson(47,47)[1]==1

if __name__=="__main__": unittest.main()
