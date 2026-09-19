#!/usr/bin/env python3
"""C7 source-SED / chromatic-PSF mismatch stress test."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.signal import fftconvolve


def gaussian(shape: int, sigma: float) -> np.ndarray:
    c = shape // 2
    y, x = np.mgrid[:shape, :shape]
    g = np.exp(-0.5 * ((x-c)**2 + (y-c)**2) / sigma**2)
    return g / g.sum()


def throughput(lam):
    core = np.exp(-0.5 * ((lam - 3.0) / 1.15) ** 4)
    return np.where((lam >= 1.0) & (lam <= 5.0), core, 0.0)


def disk_sed(lam):
    return (lam / 2.5) ** -1.8


def bulge_sed(lam):
    return 0.75 * (lam / 2.5) ** 1.25


def photon_weight(sed, thr, lam):
    return sed * thr * lam


def trap_weights(n: int, dl: float) -> np.ndarray:
    w = np.ones(n) * dl
    w[[0, -1]] *= 0.5
    return w


def second_moment(image):
    f = image / image.sum()
    y, x = np.indices(f.shape)
    cx, cy = np.sum(f*x), np.sum(f*y)
    return float(np.sqrt(0.5*(np.sum(f*(x-cx)**2)+np.sum(f*(y-cy)**2))))


def aperture_fraction(image, radius):
    c = image.shape[0]//2
    y, x = np.indices(image.shape)
    mask = (x-c)**2 + (y-c)**2 <= radius**2
    return float(image[mask].sum()/image.sum())


def render_case(*, same_sed=False, achromatic_psf=False, samples=401, shape=161):
    lam = np.linspace(1.0, 5.0, samples)
    dl = lam[1]-lam[0]
    tw = trap_weights(samples, dl)
    thr = throughput(lam)
    sd = disk_sed(lam)
    sb = sd.copy() if same_sed else bulge_sed(lam)
    wd = photon_weight(sd, thr, lam)
    wb = photon_weight(sb, thr, lam)
    psig = np.full_like(lam, 0.72*3.0) if achromatic_psf else 0.72*lam

    disk = gaussian(shape, 7.0)
    bulge = gaussian(shape, 1.7)
    correct = np.zeros((shape, shape))
    global_psf_num = np.zeros_like(correct)
    global_w = wd + wb
    fd = float(np.sum(tw*wd))
    fb = float(np.sum(tw*wb))

    for i in range(samples):
        psf = gaussian(shape, float(psig[i]))
        correct += tw[i]*(wd[i]*fftconvolve(disk, psf, mode='same') + wb[i]*fftconvolve(bulge, psf, mode='same'))
        global_psf_num += tw[i]*global_w[i]*psf

    global_psf = global_psf_num / float(np.sum(tw*global_w))
    intrinsic_band = fd*disk + fb*bulge
    shortcut = fftconvolve(intrinsic_band, global_psf, mode='same')

    cn = correct/correct.sum(); sn = shortcut/shortcut.sum()
    m2c, m2s = second_moment(correct), second_moment(shortcut)
    sig2_d = float(np.sum(tw*wd*psig**2)/np.sum(tw*wd))
    sig2_b = float(np.sum(tw*wb*psig**2)/np.sum(tw*wb))
    sig2_g = float(np.sum(tw*global_w*psig**2)/np.sum(tw*global_w))
    metrics = {
        'same_sed': same_sed,
        'achromatic_psf': achromatic_psf,
        'correct_flux': float(correct.sum()),
        'shortcut_flux': float(shortcut.sum()),
        'flux_relative_error': float(abs(shortcut.sum()-correct.sum())/correct.sum()),
        'normalized_l1_difference': float(np.sum(np.abs(cn-sn))),
        'second_moment_correct': m2c,
        'second_moment_shortcut': m2s,
        'second_moment_relative_difference': float(abs(m2s-m2c)/m2c),
        'aperture_r3_correct': aperture_fraction(correct,3),
        'aperture_r3_shortcut': aperture_fraction(shortcut,3),
        'aperture_r10_correct': aperture_fraction(correct,10),
        'aperture_r10_shortcut': aperture_fraction(shortcut,10),
        'disk_effective_psf_sigma': float(np.sqrt(sig2_d)),
        'bulge_effective_psf_sigma': float(np.sqrt(sig2_b)),
        'global_effective_psf_sigma': float(np.sqrt(sig2_g)),
    }
    return metrics, {'correct':correct,'shortcut':shortcut,'global_psf':global_psf,'intrinsic_band':intrinsic_band}


def configuration():
    return {'stage':'C7 source-SED / chromatic-PSF mismatch','samples':401,'shape':161,'noise':False,'fit':False,'acceptance':'controls validate algebra; color-gradient bias is measured, not thresholded'}


def run(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    cases = [('color_gradient',{}),('same_sed_control',{'same_sed':True}),('achromatic_psf_control',{'achromatic_psf':True})]
    rows=[]; arrays={}
    for name, kwargs in cases:
        row, arr = render_case(**kwargs)
        row['case']=name; rows.append(row)
        for k,v in arr.items(): arrays[f'{name}__{k}']=v
    summary={'config':configuration(),'results':rows}
    (out/'config.json').write_text(json.dumps(configuration(),indent=2,sort_keys=True)+'\n')
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    np.savez_compressed(out/'arrays.npz',**arrays)
    return summary


def main():
    p=argparse.ArgumentParser(); p.add_argument('--out',type=Path,required=True); a=p.parse_args()
    print(json.dumps(run(a.out),indent=2,sort_keys=True))

if __name__=='__main__': main()
