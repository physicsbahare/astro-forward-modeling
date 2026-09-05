import importlib.util,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; SCRIPTS=ROOT/"scripts"
if str(SCRIPTS) not in sys.path: sys.path.insert(0,str(SCRIPTS))
SPEC=importlib.util.spec_from_file_location("d1nb",SCRIPTS/"run_gate_d_cosmosweb_empirical_psf_support.py"); d=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(d)
def test_d1nb_protocol_constants_are_frozen():
    assert d.PIXEL_SCALE==0.03 and np.isclose(d.DETECTION_FWHM_PIX,0.145/0.03) and d.DETECTION_THRESHOLD_SIGMA==8.0 and d.CORE_SNR_MIN==10.0 and d.STAMP_SIZE==31 and d.STACK_MIN_CANDIDATES==3
def test_center_crop_and_metrics_on_symmetric_gaussian():
    y,x=np.indices((65,65),dtype=float); g=np.exp(-.5*(((x-32)/2)**2+((y-32)/2)**2)); c=d.crop_center(g,31); m=d._positive_shape_metrics(c); assert c.shape==(31,31); assert abs(m["centroid_x_pix"]-15)<1e-10; assert abs(m["centroid_y_pix"]-15)<1e-10; assert abs(m["axis_ratio_moment"]-1)<1e-8; assert 0<m["ee50_radius_pix"]<m["ee80_radius_pix"]
def test_normalized_image_identity_metrics():
    a=np.zeros((31,31)); a[15,15]=1; assert d.normalized_l1(a,a)==0 and np.isclose(d.normalized_corr(a,a),1)
