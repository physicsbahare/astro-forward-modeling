import unittest
from types import SimpleNamespace
from optimizer_quality import restore_saved_prior
class PriorTests(unittest.TestCase):
    def test_restore_deleted_galight_prior(self):
        shared={};fit=SimpleNamespace(prior='<function bd_physical_condition at 0x0123>',fitting_specify_class=SimpleNamespace(kwargs_likelihood=shared),fitting_seq=SimpleNamespace(_updateManager=SimpleNamespace(kwargs_likelihood=shared)))
        restore_saved_prior(fit,'bd')
        fn=shared['custom_logL_addition']
        components=[dict(e1=0.,e2=0.,center_x=0.,center_y=0.),dict(e1=0.,e2=0.,center_x=.04,center_y=0.)]
        self.assertEqual(fn(None,None,components,None,None,None),-1e15)
        self.assertIs(shared['custom_logL_addition'],fit.fitting_seq._updateManager.kwargs_likelihood['custom_logL_addition'])
    def test_unknown_prior_is_rejected(self):
        fit=SimpleNamespace(prior='<function unknown at 0x0123>')
        with self.assertRaises(ValueError):restore_saved_prior(fit,'bd')
if __name__=='__main__':unittest.main()
