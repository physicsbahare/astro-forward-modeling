import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from corrected_four_stage import component_parameters, render_truth

class TruthContractTests(unittest.TestCase):
    def test_requested_sizes_and_q_are_not_clipped(self):
        for radius,q in [(.002955,.08),(3.737163,.5),(.009791,.99)]:
            params=component_parameters(radius,1.,q,.31,267,fixed_n=1.)
            self.assertEqual(params[0]['R_sersic'],radius)
            from lenstronomy.Util.param_util import ellipticity2phi_q
            self.assertAlmostEqual(ellipticity2phi_q(params[0]['e1'],params[0]['e2'])[1],q)
            self.assertLess(params[3]['R_sersic'],radius)
            self.assertGreater(params[4]['R_sersic'],radius)

    def test_integrated_bt_contract_is_independent_of_window(self):
        model={'single_n':2.,'single_re_arcsec':.4,'single_q':.6,'bt':.61,
               'disk_re_arcsec':.8,'bulge_re_arcsec':.7,'disk_q':.5,'bulge_q':.8}
        psf=np.zeros((9,9));psf[4,4]=1.01;psf[0,0]=-.01
        for npix in [51,101]:
            image,kwargs,meta=render_truth(model,psf,.2,branch='bd',scale=1.,npix=npix)
            self.assertAlmostEqual(meta['integrated_bt'],.61,places=12)
            self.assertEqual(kwargs[0]['R_sersic'],.8)
            self.assertEqual(kwargs[1]['R_sersic'],.7)
            self.assertAlmostEqual(meta['analytic_integrated_flux'],1e4,places=8)
            self.assertLess(image.sum(),1e4)
            self.assertAlmostEqual(image.sum()/1e4,meta['stamp_to_analytic_flux_ratio'],places=12)
            self.assertGreater(meta['psf_negative_flux'],0)

if __name__=='__main__':unittest.main()
