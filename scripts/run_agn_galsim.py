#!/usr/bin/env python3
"""Stage 2c: independent GalSim host rendering, with numerical refinement."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import galsim
from run_agn_nuclear_fraction_noiseless import Renderer, fit, write_csv
from run_agn_cross_sampling import configuration

VERSION = '2.8.4'
SETTINGS = {
    'coarse': dict(folding_threshold=1e-4, maxk_threshold=1e-5,
                   kvalue_accuracy=1e-7, xvalue_accuracy=1e-7),
    'fine': dict(folding_threshold=1e-5, maxk_threshold=1e-6,
                 kvalue_accuracy=1e-8, xvalue_accuracy=1e-8),
}


def profile(n, settings, re=16., q=0.6):
    # Area-preserving shear: circular HLR = semi-major Re * sqrt(q).
    return galsim.Sersic(n=n, half_light_radius=re*np.sqrt(q), flux=1,
                         gsparams=galsim.GSParams(**settings)).shear(q=q, beta=45*galsim.degrees)


def render(n, settings):
    gs = galsim.GSParams(**settings)
    psf = galsim.Gaussian(fwhm=3., flux=1., gsparams=gs)
    obj = galsim.Convolve(profile(n, settings), psf, gsparams=gs)
    # drawImage(fft) integrates the detector pixel exactly once.
    kwargs = dict(nx=129, ny=129, scale=1., method='fft', dtype=np.float64,
                  use_true_center=True)
    return obj.drawImage(**kwargs).array, psf.drawImage(**kwargs).array


def l1(a, reference):
    return float(abs(a-reference).sum()/abs(reference).sum())


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--host-n', type=float, choices=(1,4), required=True)
    p.add_argument('--output', type=Path, default=Path('benchmark_output/agn_galsim'))
    args = p.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    config = configuration(args.host_n, 8)
    config.update(stage='2c independent GalSim host reference', reference_factor=None,
                  reference='GalSim fine settings; independently implemented, not exact truth',
                  galsim_version=VERSION, settings=SETTINGS,
                  local_comparison_factors=[4,8,16],
                  nuclear_template='shared analytic pixel-integrated Gaussian; GalSim PSF compared separately',
                  half_light_radius_conversion='circular HLR = semi-major Re * sqrt(q)',
                  limitations='fixed center/PA; no noise or physical PSF mismatch; GalSim refinement must be reviewed')
    (out/'config.json').write_text(json.dumps(config, indent=2)+'\n')
    if galsim.__version__ != VERSION:
        raise RuntimeError(f'Expected GalSim {VERSION}, got {galsim.__version__}')
    images, diagnostics = {}, []
    for label, settings in SETTINGS.items():
        images[f'host_{label}'], images[f'psf_{label}'] = render(args.host_n, settings)
    reference = images['host_fine']
    point = Renderer(stamp=129, oversample=1).point
    images['point_exact'] = point
    for label in SETTINGS:
        diagnostics.append(dict(comparison=f'galsim_{label}',
                                host_l1_to_fine=l1(images[f'host_{label}'], reference),
                                host_stamp_flux=float(images[f'host_{label}'].sum()),
                                point_l1_to_exact=l1(images[f'psf_{label}'], point)))
    for factor in (4,8,16):
        local = Renderer(oversample=factor)
        h = local.host(16, args.host_n, .6)
        images[f'local_f{factor}'] = h
        diagnostics.append(dict(comparison=f'local_f{factor}', host_l1_to_fine=l1(h,reference),
                                host_stamp_flux=float(h.sum()), point_l1_to_exact=0.))
        del local
    write_csv(out/'renderer_metrics.csv', diagnostics)
    np.savez_compressed(out/'renderer_images.npz', **images)
    print(json.dumps(dict(renderer_diagnostics=diagnostics)), flush=True)
    renderer = Renderer(oversample=8)
    rows, all_starts = [], []
    for ratio in (.1,1.,10.):
        data = reference + ratio*point
        winner, starts, prediction = fit(data, renderer, True)
        common = dict(true_n=args.host_n, true_re_pix=16, true_q=.6,
                      true_host_flux=1., true_nuclear_flux=ratio, agn_to_host=ratio,
                      data_sha256=hashlib.sha256(data.tobytes()).hexdigest())
        rows.append(dict(**common, **winner, delta_n=winner['n']-args.host_n,
                         re_ratio=winner['re_pix']/16, delta_q=winner['q']-.6))
        all_starts.extend(dict(**common, **s) for s in starts)
        write_csv(out/'metrics.csv', rows)
        write_csv(out/'fit_starts.csv', all_starts)
        np.savez_compressed(out/f'ratio{ratio:g}.npz', data=data, host_reference=reference,
                            nuclear_reference=ratio*point, prediction=prediction, residual=prediction-data)
        print(json.dumps(rows[-1]), flush=True)
    if len(all_starts)!=9 or not all(np.isfinite(s['cost']) for s in all_starts):
        raise RuntimeError('incomplete or nonfinite fitting diagnostic')
    if not all(np.isfinite(a).all() for a in images.values()):
        raise RuntimeError('nonfinite renderer output')
    (out/'summary.json').write_text(json.dumps(dict(config=config, renderer_metrics=diagnostics,
                                                  results=rows, starts=all_starts), indent=2)+'\n')


if __name__ == '__main__':
    main()
