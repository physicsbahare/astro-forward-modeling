#!/usr/bin/env python3
"""Stage 2b: nonlinear decomposition across quadratures, no noise/PSF mismatch."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from run_agn_nuclear_fraction_noiseless import (
    Renderer, fit, write_csv, RE_BOUNDS, N_BOUNDS, Q_BOUNDS, START_N,
    START_RE, START_Q, MAX_NFEV,
)

FIT_FACTORS = (4, 8)
REFERENCE_FACTOR = 16
RATIOS = (0.1, 1.0, 10.0)


def configuration(host_n, fit_factor):
    return dict(stage='2b nonlinear cross-sampling decomposition', host_n=host_n,
                fit_factor=fit_factor, reference_factor=REFERENCE_FACTOR,
                re_pix=16, q=0.6, pa_deg=45, stamp=129, fwhm_pix=3,
                ratios=RATIOS, fixed='common true center, PA, zero background',
                free='Re, n, q and nonnegative host/nuclear fluxes',
                re_bounds=RE_BOUNDS, n_bounds=N_BOUNDS, q_bounds=Q_BOUNDS,
                start_n=START_N, start_re=START_RE, start_q=START_Q,
                max_nfev=MAX_NFEV, optimizer='inherited Stage-1 TRF with NNLS',
                ftol=1e-10, xtol=1e-10, gtol=1e-7,
                winner='minimum cost regardless of success or truth proximity',
                acceptance='finite complete matrix only; no recovery pass band',
                limitations='16x is not proven truth; same renderer family; no independent convergence or global identifiability claim')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host-n', type=float, choices=(1, 4), required=True)
    parser.add_argument('--fit-factor', type=int, choices=FIT_FACTORS, required=True)
    parser.add_argument('--output', type=Path, default=Path('benchmark_output/agn_cross_sampling'))
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    config = configuration(args.host_n, args.fit_factor)
    (out/'config.json').write_text(json.dumps(config, indent=2)+'\n')
    reference = Renderer(oversample=REFERENCE_FACTOR)
    host = reference.host(16, args.host_n, 0.6)
    point = reference.point.copy()
    del reference
    renderer = Renderer(oversample=args.fit_factor)
    rows, all_starts = [], []
    for ratio in RATIOS:
        data = host + ratio*point
        winner, starts, prediction = fit(data, renderer, True)
        common = dict(true_n=args.host_n, true_re_pix=16, true_q=0.6,
                      true_host_flux=1.0, true_nuclear_flux=ratio, agn_to_host=ratio,
                      fit_factor=args.fit_factor, reference_factor=REFERENCE_FACTOR,
                      data_sha256=hashlib.sha256(data.tobytes()).hexdigest())
        rows.append(dict(**common, **winner, delta_n=winner['n']-args.host_n,
                         re_ratio=winner['re_pix']/16, delta_q=winner['q']-0.6,
                         host_flux_bias=winner['host_flux']-1,
                         nuclear_flux_bias=winner['nuclear_flux']-ratio))
        all_starts.extend(dict(**common, **start) for start in starts)
        write_csv(out/'metrics.csv', rows)
        write_csv(out/'fit_starts.csv', all_starts)
        np.savez_compressed(out/f'ratio{ratio:g}.npz', data=data,
                            host_reference=host, nuclear_reference=ratio*point,
                            prediction=prediction, residual=prediction-data)
        print(json.dumps(rows[-1]), flush=True)
    if len(rows) != 3 or len(all_starts) != 9 or not all(np.isfinite(r['cost']) for r in all_starts):
        raise RuntimeError('incomplete or nonfinite diagnostic; retain partial output')
    summary = dict(config=config, results=rows, starts=all_starts,
                   interpretation='review all starts and images; CI is not scientific acceptance')
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')


if __name__ == '__main__':
    main()
