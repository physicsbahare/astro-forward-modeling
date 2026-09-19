import importlib.util
from pathlib import Path
import numpy as np
import pytest
astropy = pytest.importorskip("astropy")
from astropy.io import fits

SCRIPT = Path(__file__).parents[1] / "scripts" / "audit_gate_d_cosmosweb_real_context.py"
spec = importlib.util.spec_from_file_location("gate_d_context", SCRIPT)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


def make_bundle(path, bad=None):
    y, x = np.mgrid[:64, :64]
    sci = np.random.default_rng(1).normal(0, 1, (64, 64)).astype(np.float32)
    sci += 20*np.exp(-((x-22)**2 + (y-31)**2)/(2*2.0**2))
    err = np.ones((64,64), dtype=np.float32)
    wht = np.ones((64,64), dtype=np.float32)*100
    if bad == "err": err[0,0] = 0
    if bad == "wht": wht[0,0] = 0
    fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU(sci,name="SCI"), fits.ImageHDU(err,name="ERR"), fits.ImageHDU(wht,name="WHT")]).writeto(path)


def test_real_context_audit_contract(tmp_path):
    p=tmp_path/"b.fits"; out=tmp_path/"s.json"; make_bundle(p)
    s=mod.audit(p,out)
    assert out.exists()
    assert s["significance"]["connected_islands_8conn"] >= 1
    assert s["significance"]["source_pixel_fraction"] > 0
    assert s["planes_modified"] is False
    assert s["injection_performed"] is False and s["recovery_performed"] is False

@pytest.mark.parametrize("bad", ["err","wht"])
def test_nonpositive_uncertainty_or_weight_is_hard_failure(tmp_path,bad):
    p=tmp_path/"b.fits"; make_bundle(p,bad)
    with pytest.raises(ValueError): mod.audit(p,tmp_path/"s.json")
