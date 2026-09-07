#!/usr/bin/env python3
"""Controlled IID Gaussian background-noise pilot; not survey or Poisson noise."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from run_agn_galsim import render, SETTINGS, VERSION, galsim
from run_agn_cross_sampling import configuration
from run_agn_nuclear_fraction_noiseless import Renderer, fit, write_csv

HOST_SNRS = (100, 20, 5)
SEEDS = (20260903, 20260904, 20260905)
RATIOS = (.1, 1., 10.)


def noise_field(shape, host_n, seed):
    # Deliberately shared across ratios/SNRs within a host/seed: paired cases.
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed, int(host_n)])))
    return rng.standard_normal(shape)


def noise_sigma(host, snr):
    return float(np.linalg.norm(host)/snr)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--host-n', type=float, choices=(1,4), required=True)
    p.add_argument('--host-snr', type=int, choices=HOST_SNRS, required=True)
    p.add_argument('--output', type=Path, default=Path('benchmark_output/agn_noise_pilot'))
    args = p.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    config = configuration(args.host_n, 8)
    config.update(stage='3a background-noise pilot', reference_factor=None,
                  reference='GalSim fine host + analytic pixel-integrated Gaussian nucleus',
                  galsim_version=VERSION, galsim_settings=SETTINGS['fine'],
                  host_snr=args.host_snr, snr_definition='L2 norm of noiseless unit host / IID pixel sigma; known-template host-only SNR, not marginalized SNR',
                  seeds=SEEDS, ratios=RATIOS, rng='PCG64 SeedSequence([seed, int(host_n)])',
                  pairing='same unit noise per host/seed across ratios and SNRs',
                  noise='zero-mean IID Gaussian background only; sigma spatially constant',
                  exclusions='no shot noise, resampling covariance, physical PSF mismatch, free centroid/PA or sky fit',
                  limitations='3 realizations per case: pilot, not calibrated error bars or reliable failure probabilities')
    (out/'config.json').write_text(json.dumps(config, indent=2)+'\n')
    if galsim.__version__ != VERSION:
        raise RuntimeError('GalSim version differs from frozen reference')
    host, _ = render(args.host_n, SETTINGS['fine'])
    renderer = Renderer(oversample=8)
    point = renderer.point
    sigma = noise_sigma(host, args.host_snr)
    local_host = renderer.host(16, args.host_n, .6)
    config.update(pixel_sigma=sigma, host_flux_in_stamp=float(host.sum()),
                  unit_host_renderer_difference_over_sigma=float(np.linalg.norm(local_host-host)/sigma))
    (out/'config.json').write_text(json.dumps(config, indent=2)+'\n')
    rows, all_starts = [], []
    for seed in SEEDS:
        noise = sigma*noise_field(host.shape, args.host_n, seed)
        for ratio in RATIOS:
            noiseless = host + ratio*point
            data = noiseless + noise
            winner, starts, prediction = fit(data, renderer, True)
            common = dict(true_n=args.host_n, true_re_pix=16, true_q=.6,
                          true_host_flux=1., true_nuclear_flux=ratio, agn_to_host=ratio,
                          host_snr=args.host_snr, seed=seed, pixel_sigma=sigma,
                          noise_sha256=hashlib.sha256(noise.tobytes()).hexdigest(),
                          data_sha256=hashlib.sha256(data.tobytes()).hexdigest())
            rows.append(dict(**common, **winner, delta_n=winner['n']-args.host_n,
                             re_ratio=winner['re_pix']/16, delta_q=winner['q']-.6,
                             chi2=float(np.sum(((prediction-data)/sigma)**2)),
                             model_l1_over_noiseless_l1=float(abs(prediction-noiseless).sum()/abs(noiseless).sum())))
            all_starts.extend(dict(**common, **s) for s in starts)
            write_csv(out/'metrics.csv', rows)
            write_csv(out/'fit_starts.csv', all_starts)
            np.savez_compressed(out/f'seed{seed}_ratio{ratio:g}.npz', data=data,
                                noiseless=noiseless, host_reference=host,
                                nuclear_reference=ratio*point, noise=noise,
                                prediction=prediction, residual=prediction-data)
            print(json.dumps(rows[-1]), flush=True)
    if len(rows)!=9 or len(all_starts)!=27 or not all(np.isfinite(s['cost']) for s in all_starts):
        raise RuntimeError('incomplete/nonfinite experiment; preserve partial outputs')
    (out/'summary.json').write_text(json.dumps(dict(config=config, results=rows, starts=all_starts,
        interpretation='all starts, bounds and low-information outcomes retained; no recovery pass band'),indent=2)+'\n')


if __name__ == '__main__':
    main()
