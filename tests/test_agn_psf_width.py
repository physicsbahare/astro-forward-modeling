import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_agn_psf_width import WidthRenderer,Renderer,FACTORS


def test_matched_renderer_identity():
    assert FACTORS==(.97,1.,1.03)
    a=Renderer(stamp=33,oversample=4);b=WidthRenderer(3,stamp=33,oversample=4)
    np.testing.assert_array_equal(a.point,b.point)
    np.testing.assert_array_equal(a.host(4,2,.6),b.host(4,2,.6))


def test_psf_order_and_normalization():
    images=[WidthRenderer(3*f,stamp=33,oversample=4).point for f in FACTORS]
    for im in images:
        np.testing.assert_allclose(im.sum(),1.,atol=1e-14)
        np.testing.assert_allclose(im,im[::-1,::-1],rtol=0,atol=1e-16)
    assert images[0][16,16]>images[1][16,16]>images[2][16,16]
    with pytest.raises(ValueError):WidthRenderer(-1)
