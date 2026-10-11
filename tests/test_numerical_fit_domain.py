import unittest
from lenstronomy.Util.param_util import phi_q2_ellipticity
from numerical_domain_probe import NumericalDomain
class DomainTests(unittest.TestCase):
    def component(self,q,r):
        a,b=phi_q2_ellipticity(.3,q)
        return dict(e1=a,e2=b,R_sersic=r,center_x=0.,center_y=0.)
    def test_retains_limiting_supported_truth(self):
        d=NumericalDomain(.1,.0015)
        self.assertEqual(d(None,None,[self.component(.2523,.0067),self.component(.8,.0031)],None,None,None),0.)
    def test_rejects_under_sampled_thin_component(self):
        d=NumericalDomain(.1,.0015)
        self.assertEqual(d(None,None,[self.component(.5,.2),self.component(.0004,.0055)],None,None,None),-1e15)
        self.assertEqual(d(None,None,[self.component(.5,.2),self.component(.11,.005)],None,None,None),-1e15)
if __name__=='__main__':unittest.main()
