import importlib.util,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; SCRIPTS=ROOT/"scripts"
if str(SCRIPTS) not in sys.path: sys.path.insert(0,str(SCRIPTS))
SPEC=importlib.util.spec_from_file_location("d1nc",SCRIPTS/"run_gate_d_cosmosweb_background_residual_audit.py"); d=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(d)
def test_pair_corr_detects_neighbor_correlation():
    rng=np.random.default_rng(3); b=rng.normal(size=(65,65)); z=b+np.roll(b,1,axis=1); assert d.pair_corr(z,np.ones_like(z,dtype=bool),0,1)>.3
def test_quadratic_explained_fraction_recovers_smooth_structure():
    yy,xx=np.indices((65,65),dtype=float); x=(xx-32)/32; y=(yy-32)/32; r=.2+.7*x*x-.3*x*y+.4*y*y; out=d.quadratic_explained_fraction(r,np.ones_like(r),np.ones_like(r,dtype=bool)); assert out["weighted_variance_explained_fraction"]>.999999
def test_low_frequency_metric_is_finite_for_smooth_plus_noise():
    rng=np.random.default_rng(7); yy,xx=np.indices((65,65),dtype=float); r=.5*np.sin(xx/15)+rng.normal(scale=.1,size=(65,65)); f=d.low_frequency_variance_fraction(r,np.ones_like(r,dtype=bool)); assert f is not None and np.isfinite(f) and f>=0
