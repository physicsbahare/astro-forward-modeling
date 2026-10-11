"""Set integrated B/T without changing Lenstronomy rendering or signed PSFs.

Pass LightModel.total_flux for two unit-amplitude SERSIC_ELLIPSE components
with sersic_major_axis=True. Render with these amplitudes, then multiply
the entire stamp by one common photometric normalization. Never normalize
each rendered component by its finite image sum to define integrated B/T.
"""
import numpy as np

def integrated_component_amplitudes(unit_integrated_flux, bt):
    flux = np.asarray(unit_integrated_flux, dtype=float)
    if flux.shape != (2,) or not np.all(np.isfinite(flux)) or np.any(flux <= 0):
        raise ValueError('Two positive finite integrated unit-component fluxes required')
    if not np.isfinite(bt) or not 0 <= bt <= 1:
        raise ValueError('Integrated B/T must lie in [0,1]')
    return np.array([1 - bt, bt]) / flux
