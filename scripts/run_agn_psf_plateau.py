#!/usr/bin/env python3
"""C5b: deterministic search for alternatives to zero-host NNLS plateaus.

Archived C5a outcomes remain historical. This is a finite search, not a proof
of global optimality or a change to the production fitting policy.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from run_agn_nuclear_fraction_noiseless import (
    profile_flux, write_csv, RE_BOUNDS, N_BOUNDS, Q_BOUNDS, MAX_NFEV,
)
from run_agn_psf_width import WidthRenderer

SOURCE_RUN = 33701100594
SOURCE_COMMIT = '47ea514056fcdcf0af19eaf637ef1a9a9948c9c6'
GRID_RE = (.5, 1., 2., 4., 8., 12., 16., 24., 40., 60.)
GRID_N = (.5, 1., 2.5, 4., 6.)
GRID_Q = (.3, .6, .75, 1.)
RATIO = 10.
WIDTH_FACTOR = 1.03


def evaluate(data, renderer, re, n, q):
    flux, pred = profile_flux(data, renderer.host(re, n, q), renderer.point)
    scale = np.sqrt(np.mean(data**2))
    row = dict(re_pix=float(re), n=float(n), q=float(q),
               host_flux=float(flux[0]), nuclear_flux=float(flux[1]),
               cost=float(.5*np.sum(((pred-data)/scale)**2)),
               residual_l1_over_data_l1=float(np.abs(pred-data).sum()/np.abs(data).sum()),
               hit_host_flux_zero=bool(flux[0] == 0),
               hit_nuclear_flux_zero=bool(flux[1] == 0))
    for name, value, bounds in [('re', re, RE_BOUNDS), ('n', n, N_BOUNDS), ('q', q, Q_BOUNDS)]:
        row[f'hit_{name}_lower_bound'] = bool(value <= bounds[0]*(1+1e-5))
        row[f'hit_{name}_upper_bound'] = bool(value >= bounds[1]*(1-1e-5))
    return row, pred


def select_seeds(rows):
    # Stable grid-index tie break; no filtering by flux, success, or truth.
    return sorted(rows, key=lambda r: (r['cost'], r['grid_index']))[:3]


def refine(data, renderer, seed):
    scale = np.sqrt(np.mean(data**2))
    def residual(p):
        return ((evaluate(data, renderer, np.exp(p[0]), np.exp(p[1]), p[2])[1]-data)/scale).ravel()
    lo = [np.log(RE_BOUNDS[0]), np.log(N_BOUNDS[0]), Q_BOUNDS[0]]
    hi = [np.log(RE_BOUNDS[1]), np.log(N_BOUNDS[1]), Q_BOUNDS[1]]
    result = least_squares(residual, [np.log(seed['re_pix']), np.log(seed['n']), seed['q']],
                           bounds=(lo, hi), method='trf', max_nfev=MAX_NFEV,
                           ftol=1e-10, xtol=1e-10, gtol=1e-7)
    row, pred = evaluate(data, renderer, np.exp(result.x[0]), np.exp(result.x[1]), result.x[2])
    row.update(seed_grid_index=seed['grid_index'], seed_re=seed['re_pix'],
               seed_n=seed['n'], seed_q=seed['q'], success=bool(result.success),
               status=int(result.status), message=result.message, nfev=int(result.nfev),
               optimality=float(result.optimality))
    return row, pred


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--host-n', type=int, choices=(1, 4), required=True)
    p.add_argument('--output', type=Path, default=Path('benchmark_output/agn_psf_plateau'))
    a = p.parse_args(); out = a.output; out.mkdir(parents=True, exist_ok=True)
    config = dict(stage='C5b zero-host plateau search', source_run=SOURCE_RUN,
                  source_commit=SOURCE_COMMIT, host_n=a.host_n, ratio=RATIO,
                  width_factor=WIDTH_FACTOR, grid_re=GRID_RE, grid_n=GRID_N, grid_q=GRID_Q,
                  fit_oversample=8, seeds='lowest three grid costs; grid-index tie break',
                  bounds=dict(re=RE_BOUNDS, n=N_BOUNDS, q=Q_BOUNDS), max_nfev=MAX_NFEV,
                  ftol=1e-10, xtol=1e-10, gtol=1e-7,
                  acceptance='complete finite diagnostic outputs only; signed cost differences retained',
                  limitations='finite search cannot prove global optimality; no new PSF/noise/geometry effect')
    (out/'config.json').write_text(json.dumps(config, indent=2)+'\n')
    if (a.input/'commit.txt').read_text().strip() != SOURCE_COMMIT:
        raise RuntimeError('wrong C5a source commit')
    source = json.loads((a.input/'summary.json').read_text())
    matches = [r for r in source['results'] if r['agn_to_host']==RATIO and r['psf_width_factor']==WIDTH_FACTOR]
    if len(matches)!=1: raise RuntimeError('ambiguous/missing source case')
    old = matches[0]
    z = np.load(a.input/'ratio10_width1.03.npz'); data = z['data']
    if old['true_n']!=a.host_n or hashlib.sha256(data.tobytes()).hexdigest()!=old['data_sha256']:
        raise RuntimeError('wrong source data/host')
    original_starts = [r for r in source['starts'] if r['agn_to_host']==RATIO and r['psf_width_factor']==WIDTH_FACTOR]
    if len(original_starts)!=3: raise RuntimeError('incomplete source starts')
    (out/'source_record.json').write_text(json.dumps(dict(winner=old, starts=original_starts), indent=2)+'\n')
    renderer = WidthRenderer(3*WIDTH_FACTOR)
    np.testing.assert_array_equal(renderer.point, z['fit_point'])
    grid = []
    for i, (re, n, q) in enumerate(itertools.product(GRID_RE, GRID_N, GRID_Q)):
        row, _ = evaluate(data, renderer, re, n, q)
        row.update(grid_index=i, delta_cost_vs_original=row['cost']-old['cost'])
        grid.append(row)
        write_csv(out/'grid.csv', grid)
    rows = []; predictions = []
    for seed in select_seeds(grid):
        row, pred = refine(data, renderer, seed)
        row['delta_cost_vs_original'] = row['cost']-old['cost']
        rows.append(row); predictions.append(pred)
        write_csv(out/'fit_starts.csv', rows)
        print(json.dumps(row), flush=True)
    winner_index = min(range(len(rows)), key=lambda i: rows[i]['cost'])
    winner = rows[winner_index]
    write_csv(out/'metrics.csv', [winner])
    np.savez_compressed(out/'images.npz', data=data, host_reference=z['host_reference'],
                        fit_point=renderer.point, original_prediction=z['prediction'],
                        original_residual=z['residual'], prediction=predictions[winner_index],
                        residual=predictions[winner_index]-data,
                        start_predictions=np.stack(predictions))
    if len(grid)!=200 or len(rows)!=3 or not all(np.isfinite(r['cost']) for r in grid+rows):
        raise RuntimeError('incomplete/nonfinite search; partial records retained')
    (out/'summary.json').write_text(json.dumps(dict(config=config, data_sha256=old['data_sha256'],
        original_winner=old, grid=grid, best_grid=select_seeds(grid)[0], starts=rows, winner=winner,
        interpretation='lowest refined candidate; compare grid and historical C5a separately'), indent=2)+'\n')


if __name__ == '__main__': main()
