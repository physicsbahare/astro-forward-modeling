import unittest
import pandas as pd
import numpy as np
from summarize_continuation import fits_flags
class FlagTests(unittest.TestCase):
    def test_unknown_stays_unknown(self):
        result=fits_flags(pd.DataFrame({'analytic_real_bd_fit_valid':[True,False,None], 'validated_morphology_class':['UNKNOWN']*3}))
        self.assertEqual(result.analytic_real_bd_fit_valid.iloc[0],1.)
        self.assertEqual(result.analytic_real_bd_fit_valid.iloc[1],0.)
        self.assertTrue(np.isnan(result.analytic_real_bd_fit_valid.iloc[2]))
        self.assertTrue((result.validated_morphology_class=='UNKNOWN').all())
    def test_ambiguous_text_rejected(self):
        with self.assertRaises(TypeError):fits_flags(pd.DataFrame({'analytic_real_bd_fit_valid':['False']}))
if __name__=='__main__':unittest.main()
