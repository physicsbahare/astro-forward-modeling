import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_corrected_models import supported_flux
from verification.nircam_throughput_sensitivity import ThroughputCurve,fnu_response_moments,mapped_target_moments

class BandpassTests(unittest.TestCase):
    def curves(self):
        curves={}
        for name,center in [('F115W',1.15),('F150W',1.5),('F277W',2.77),('F444W',4.44)]:
            lam=np.linspace(.8*center,1.2*center,201)
            curves[name]=ThroughputCurve(lam,np.exp(-.5*((lam-center)/(.05*center))**2))
        return curves
    def test_quadratic_spectrum_is_transferred_exactly(self):
        curves=self.curves();coeff=np.array([1.,.2,.3])
        fluxes={b:float(fnu_response_moments(c.wavelength_um,c.throughput,2)@coeff) for b,c in curves.items()}
        result=supported_flux(fluxes,curves,.85)
        target=mapped_target_moments(fnu_response_moments(curves['F444W'].wavelength_um,curves['F444W'].throughput,2),.85,3.)
        self.assertAlmostEqual(result['source_equivalent_target_fnu_jy'],target@coeff,places=12)
        self.assertAlmostEqual(sum(result['source_weights']),1.,places=12)
    def test_blue_extrapolation_and_missing_bands_are_explicit(self):
        curves=self.curves()
        restricted=dict(curves);c=curves['F115W'];mask=c.wavelength_um>=1.07
        restricted['F115W']=ThroughputCurve(c.wavelength_um[mask],c.throughput[mask])
        with self.assertRaisesRegex(ValueError,'SPECTRAL_SUPPORT_FAILURE'):
            supported_flux({b:1. for b in curves},restricted,0.)
        with self.assertRaisesRegex(ValueError,'SPECTRAL_SUPPORT_FAILURE'):
            supported_flux({'F115W':1.,'F150W':1.},curves,.85)
    def test_same_filter_same_redshift_is_supported_identity(self):
        curves=self.curves();fluxes={'F115W':1.,'F150W':2.,'F277W':3.,'F444W':4.}
        result=supported_flux(fluxes,curves,3.)
        self.assertAlmostEqual(result['source_equivalent_target_fnu_jy'],4.,places=12)

if __name__=='__main__':unittest.main()
