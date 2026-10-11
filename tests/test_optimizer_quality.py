import unittest
import numpy as np
from optimizer_quality import capture_minimize,physical_ellipticity
from lenstronomy.Sampling import sampler
class QualityTests(unittest.TestCase):
    def test_failed_minimize_is_retained_and_restored(self):
        original=sampler.minimize
        with capture_minimize() as records:
            result=sampler.minimize(lambda x:float(np.dot(x,x)),np.array([8.,9.]),method='Nelder-Mead',options={'maxiter':1})
        self.assertIs(sampler.minimize,original)
        self.assertFalse(records[-1]['success']);self.assertEqual(records[-1]['nit'],result.nit)
        self.assertEqual(len(records),1)
    def test_rectangle_does_not_prove_valid_ellipticity(self):
        self.assertFalse(physical_ellipticity([{'e1':.9,'e2':.9}]))
        self.assertTrue(physical_ellipticity([{'e1':.93,'e2':.1}]))
        self.assertFalse(physical_ellipticity([{'e1':np.nan,'e2':0.}]))
if __name__=='__main__':unittest.main()
