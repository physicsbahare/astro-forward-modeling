#!/usr/bin/env python3
"""Paired source-shot-noise pilot with fixed oracle variance, not Poisson MLE."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from run_agn_nuclear_fraction_noiseless import Renderer, fit, write_csv
from run_agn_nuclear_fraction_noiseless import RE_BOUNDS, N_BOUNDS, Q_BOUNDS, START_N, START_RE, START_Q, MAX_NFEV

SOURCE_RUN = 33668364723
SOURCE_COMMIT = '46c7af879cb0c27432c2a34352b37dcada9d1be3'
HOST_ELECTRONS = 10000
SEEDS = (20260903, 20260904, 20260905)
RATIOS = (.1, 1., 10.)
ARMS = ('background_only', 'background_plus_shot')


def source_noise(noiseless, seed, ratio_index):
    if not np.isfinite(noiseless).all() or np.any(noiseless < 0):
        raise ValueError('Poisson intensity must be finite and nonnegative; never clip')
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed, 4, ratio_index, 310])))
    counts = rng.poisson(HOST_ELECTRONS * noiseless)
    return counts, counts / HOST_ELECTRONS - noiseless


class WhitenedRenderer:
    def __init__(self, renderer, sigma):
        if not np.isfinite(sigma).all() or np.any(sigma <= 0):
            raise ValueError('invalid fixed variance')
        self.renderer, self.sigma = renderer, sigma
        self.point = renderer.point / sigma

    def host(self, re, n, q):
        return self.renderer.host(re, n, q) / self.sigma


def weighted_fit(data, renderer, sigma):
    winner, starts, white_prediction = fit(data / sigma, WhitenedRenderer(renderer, sigma), True)
    # The inherited L1 diagnostic refers to whitened pixels, not physical flux.
    for row in starts:
        row['whitened_residual_l1_over_whitened_data_l1'] = row.pop('residual_l1_over_data_l1')
    return winner, starts, white_prediction * sigma


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, default=Path('benchmark_output/agn_shot_noise'))
    args = p.parse_args(); out = args.output; out.mkdir(parents=True, exist_ok=True)
    config = dict(stage='3c paired source-shot-noise oracle-WLS pilot', source_run=SOURCE_RUN,
                  source_commit=SOURCE_COMMIT, true_n=4, host_electrons=HOST_ELECTRONS,
                  seeds=SEEDS, ratios=RATIOS, arms=ARMS, fit_factor=8,
                  rng='PCG64 SeedSequence([seed,4,ratio_index,310]); shared across SNR shards',
                  variance='sigma_background**2 + noiseless/HOST_ELECTRONS; SAME oracle weights for both arms',
                  optimizer='inherited TRF and NNLS on whitened templates/data; approximate WLS, NOT exact Poisson likelihood',
                  re_bounds=RE_BOUNDS, n_bounds=N_BOUNDS, q_bounds=Q_BOUNDS,
                  start_n=START_N, start_re=START_RE, start_q=START_Q,
                  max_nfev=MAX_NFEV, ftol=1e-10, xtol=1e-10, gtol=1e-7,
                  exclusions='no new background draw, PSF mismatch, centroid/PA freedom, fitted sky or resampling',
                  acceptance='finite complete matrix only; no recovery or confidence bands',
                  limitations='3 paired seeds, n=4 only; truth-based weights are not an operational estimator')
    (out/'config.json').write_text(json.dumps(config, indent=2)+'\n')
    if (args.input/'commit.txt').read_text().strip() != SOURCE_COMMIT:
        raise RuntimeError('wrong source commit')
    source = json.loads((args.input/'summary.json').read_text())
    originals = source['results']
    keys = {(r['seed'], r['agn_to_host']) for r in originals}
    if len(originals) != 9 or keys != {(s,r) for s in SEEDS for r in RATIOS} or any(r['true_n'] != 4 for r in originals):
        raise RuntimeError('wrong source cases')
    if len({r['host_snr'] for r in originals}) != 1:
        raise RuntimeError('mixed source SNR shards')
    (out/'source_record.json').write_text(json.dumps(source, indent=2)+'\n')
    renderer = Renderer(oversample=8); rows = []; all_starts = []
    for old in originals:
        seed, ratio = old['seed'], old['agn_to_host']
        z = np.load(args.input/f'seed{seed}_ratio{ratio:g}.npz')
        if hashlib.sha256(z['data'].tobytes()).hexdigest() != old['data_sha256']:
            raise RuntimeError('source data hash mismatch')
        truth = z['noiseless']; counts, shot = source_noise(truth, seed, RATIOS.index(ratio))
        sigma = np.sqrt(old['pixel_sigma']**2 + truth/HOST_ELECTRONS)
        for arm in ARMS:
            data = z['data'].copy() if arm == ARMS[0] else z['data'] + shot
            winner, starts, pred = weighted_fit(data, renderer, sigma)
            common = dict(seed=seed, agn_to_host=ratio, host_snr=old['host_snr'], arm=arm,
                          true_n=4, true_re_pix=16, true_q=.6, true_host_flux=1., true_nuclear_flux=ratio,
                          source_data_sha256=old['data_sha256'], data_sha256=hashlib.sha256(data.tobytes()).hexdigest(),
                          shot_sha256=hashlib.sha256(shot.tobytes()).hexdigest())
            rows.append(dict(**common, **winner, re_ratio=winner['re_pix']/16,
                             delta_n=winner['n']-4, delta_q=winner['q']-.6,
                             weighted_residual_sum=float(np.sum(((pred-data)/sigma)**2))))
            all_starts.extend(dict(**common, **s) for s in starts)
            write_csv(out/'metrics.csv', rows); write_csv(out/'fit_starts.csv', all_starts)
            np.savez_compressed(out/f'seed{seed}_ratio{ratio:g}_{arm}.npz', data=data,
                                noiseless=truth, host_reference=z['host_reference'], nuclear_reference=z['nuclear_reference'],
                                background=z['noise'], source_counts=counts, shot_noise=shot,
                                sigma=sigma, prediction=pred, residual=pred-data)
            print(json.dumps(rows[-1]), flush=True)
    if len(rows) != 18 or len(all_starts) != 54 or not all(np.isfinite(r['cost']) for r in all_starts):
        raise RuntimeError('incomplete/nonfinite matrix; retain partial outputs')
    (out/'summary.json').write_text(json.dumps(dict(config=config, results=rows, starts=all_starts), indent=2)+'\n')


if __name__ == '__main__':
    main()
