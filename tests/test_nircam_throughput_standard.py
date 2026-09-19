import numpy as np
import pytest
from pathlib import Path

from verification.nircam_throughput_sensitivity import (
    load_mean_throughput,
    pivot_wavelength_um,
    curved_fnu_bandpass_weights,
    synthesize_curved_fnu_image,
)


def _write_curve(root: Path, name: str, lo: float, hi: float):
    lam=np.linspace(lo,hi,1001)
    thr=np.ones_like(lam)
    fn={
        'F115W':'F115W_May2024_mean_system_throughput.txt',
        'F150W':'F150W_May2024_mean_system_throughput.txt',
        'F277W':'F277W_May2024_mean_system_throughput.txt',
        'F444W':'F444W_May2024_mean_system_throughput.txt',
    }[name]
    np.savetxt(root/fn, np.column_stack([lam,thr]), header='Microns Throughput', comments='')


def _fake_dir(tmp_path):
    _write_curve(tmp_path,'F115W',0.97,1.28)
    _write_curve(tmp_path,'F150W',1.25,1.75)
    _write_curve(tmp_path,'F277W',2.30,3.20)
    _write_curve(tmp_path,'F444W',3.65,5.15)
    return tmp_path


def test_explicit_throughput_directory_is_required(tmp_path):
    d=_fake_dir(tmp_path)
    c=load_mean_throughput('F150W', d)
    p=pivot_wavelength_um(c.wavelength_um,c.throughput)
    assert 1.25 < p < 1.75


def test_curved_standard_weights_sum_to_one_for_constant_spectrum(tmp_path):
    d=_fake_dir(tmp_path)
    for z,target in [(1.0,'F277W'),(1.5,'F277W'),(2.0,'F444W'),(2.5,'F444W'),(3.0,'F444W')]:
        w=curved_fnu_bandpass_weights(source_bands=('F115W','F150W','F277W'), target_band=target, z_source=0.4304, z_target=z, directory=d)
        assert np.sum(w)==pytest.approx(1.0,abs=1e-12)
        assert np.all(np.isfinite(w))


def test_curved_standard_preserves_constant_image(tmp_path):
    d=_fake_dir(tmp_path)
    img=np.full((7,7),2.5)
    out,w=synthesize_curved_fnu_image({'F115W':img,'F150W':img,'F277W':img}, target_band='F444W', z_source=0.4304, z_target=2.0, directory=d)
    assert np.allclose(out,2.5)
    assert w.shape==(3,)


def test_curvature_is_not_silently_reduced_to_two_band_linear(tmp_path):
    d=_fake_dir(tmp_path)
    a=np.full((5,5),1.0); b=np.full((5,5),2.0); c=np.full((5,5),6.0)
    out,w=synthesize_curved_fnu_image({'F115W':a,'F150W':b,'F277W':c}, target_band='F277W', z_source=0.4304, z_target=1.0, directory=d)
    assert abs(w[0])>1e-4
    assert np.allclose(out,w[0]*a+w[1]*b+w[2]*c)
