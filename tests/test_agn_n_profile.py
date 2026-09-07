import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_agn_n_profile import N_GRID, START_RE, profile_at_n, MAX_NFEV


def test_frozen_profile_design():
    assert N_GRID==(.5,1,2,3,4,5,6)
    assert START_RE==(4,12,36)
    assert MAX_NFEV==160


def test_profile_bookkeeping():
    class Toy:
        y,x=np.mgrid[-3:4,-3:4]
        point=np.eye(7)/7
        def host(self,re,n,q):
            return np.exp(-(self.x**2+self.y**2/q**2)/(2*re**2))/(re**2*q)
    t=Toy();data=t.host(3,1,.6)+.2*t.point
    win,starts,pred=profile_at_n(data,t,1,.1)
    assert len(starts)==3 and win['cost']==min(s['cost'] for s in starts)
    np.testing.assert_allclose(win['chi2'],np.sum(((pred-data)/.1)**2))
    assert all(s['fixed_n']==1 for s in starts)
