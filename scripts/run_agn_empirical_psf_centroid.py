#!/usr/bin/env python3
"""C5f thin bounded-centroid adapter; see C5F_PROTOCOL.md before interpretation."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import time

import numpy as np
from scipy.optimize import least_squares
from run_agn_empirical_psf_phase import (
    ROOT, PINS, PHASES, FIT_SLICE, CONTROL_FWHMS, PSF_SCALE,
    models, gaussian_effective_samples, normalize_psf, scalar_fit, dump, write_csv,
)

PARENT_RUN = 33727185586
PARENT_COMMIT = 'b23d2a21f1d6cb2823b1adb44c04e9a14b55fac7'
STARTS = ((0., 0.), (.5, .5), (-.5, -.5))
OPTIONS = dict(method='trf', jac='2-point', loss='linear', max_nfev=160,
               ftol=1e-10, xtol=1e-10, gtol=1e-7)
AUDIT = ROOT/'benchmarks/zhuang_shen_2024/phase_33727185586.json'


def verify_parent(source, module):
    audit = json.loads(AUDIT.read_text())
    if audit['run_id'] != PARENT_RUN or audit['commit'] != PARENT_COMMIT:
        raise ValueError('wrong parent audit')
    record = next(a for a in audit['artifacts'] if a['module'] == module)
    # Verify the complete archived shard before using any data.
    for name, expected in record['file_sha256'].items():
        if hashlib.sha256((source/name).read_bytes()).hexdigest() != expected:
            raise ValueError('parent checksum mismatch: '+name)
    config = json.loads((source/'config.json').read_text())
    if config['module'] != module or config['github_run_id'] != str(PARENT_RUN):
        raise ValueError('wrong parent shard/run')
    return record


def fit_case(data, model, phase):
    if data.shape != (201, 201) or not np.isfinite(data).all():
        raise ValueError('invalid data')
    scale = float(np.sqrt(np.mean(data**2)))
    if scale <= 0:
        raise ValueError('zero data norm')
    yy, xx = np.indices(data.shape, dtype=float)
    def template(p):
        return np.asarray(model.evaluate(xx, yy, 1., 100+p[0], 100+p[1]))
    def evaluate(p):
        t = template(p)
        row, prediction, residual = scalar_fit(data, t)
        return row, prediction, residual, t
    baseline = evaluate(phase)[0]
    rows, arrays = [], dict(data=data)
    for i, start in enumerate(STARTS):
        result = least_squares(lambda p: evaluate(p)[2].ravel()/scale,
                               start, bounds=([-1., -1.], [1., 1.]), **OPTIONS)
        row, prediction, residual, t = evaluate(result.x)
        row.update(start=i, initial_x=start[0], initial_y=start[1],
                   x=float(result.x[0]), y=float(result.x[1]),
                   dx=float(result.x[0]-phase[0]), dy=float(result.x[1]-phase[1]),
                   success=bool(result.success), status=int(result.status),
                   message=str(result.message), nfev=int(result.nfev),
                   optimality=float(result.optimality),
                   active_x=int(result.active_mask[0]), active_y=int(result.active_mask[1]),
                   hit_centroid_bound=bool(np.any(result.active_mask)),
                   fixed_cost=baseline['cost'], fixed_flux=baseline['flux'])
        rows.append(row)
        arrays.update({f'start{i}_prediction':prediction,
                       f'start{i}_residual':residual, f'start{i}_template':t})
    winner = dict(min(rows, key=lambda r:r['cost']))
    winner.update(x_start_range=float(np.ptp([r['x'] for r in rows])),
                  y_start_range=float(np.ptp([r['y'] for r in rows])),
                  cost_start_range=float(np.ptp([r['cost'] for r in rows])))
    return winner, rows, arrays


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--module', choices=['A','B'], required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    versions = {k:importlib.metadata.version(k) for k in PINS}
    if versions != PINS:
        raise RuntimeError('dependency pin mismatch')
    record = verify_parent(args.source, args.module)
    dump(args.out/'config.json', dict(stage='C5f', module=args.module,
         github_run_id=os.getenv('GITHUB_RUN_ID'), github_sha=os.getenv('GITHUB_SHA'),
         parent_run=PARENT_RUN, parent_commit=PARENT_COMMIT, parent_artifact=record['artifact_id'],
         audit_sha256=hashlib.sha256(AUDIT.read_bytes()).hexdigest(),
         pins=versions, starts=STARTS, bounds=[-1,1], optimizer=OPTIONS,
         phases=PHASES, expected_cases=64, expected_starts=192,
         limitations='signed numerical PSFs, not photon models or physical truth'))
    dump(args.out/'source_manifest.json', record)
    with np.load(args.source/'input_models.npz') as bundle:
        normalized = bundle['normalized_input'].copy()
    np.savez_compressed(args.out/'input_models.npz', normalized_input=normalized)
    empirical = models(normalized)['photutils_cubic']
    gaussian = {}
    for f in CONTROL_FWHMS:
        sigma = f/(2*np.sqrt(2*np.log(2)))
        normalized_g, _ = normalize_psf(gaussian_effective_samples(sigma, 401, PSF_SCALE))
        gaussian[f] = models(normalized_g)['photutils_cubic']
    winners, starts = [], []
    for dx in PHASES:
        for dy in PHASES:
            phase = (dx,dy)
            with np.load(args.source/f'phase_x{dx:g}_y{dy:g}.npz') as bundle:
                cases = [(arm, bundle[arm][FIT_SLICE,FIT_SLICE].copy(), empirical)
                         for arm in ('photutils_cubic','galsim_quintic')]
            for f in CONTROL_FWHMS:
                with np.load(args.source/f'control_fwhm{f:g}_x{dx:g}_y{dy:g}.npz') as bundle:
                    cases.append((f'gaussian_{f:g}', bundle['exact'][FIT_SLICE,FIT_SLICE].copy(), gaussian[f]))
            for arm, data, model in cases:
                case = f'{arm}_x{dx:g}_y{dy:g}'
                winner, rows, arrays = fit_case(data, model, phase)
                metadata = dict(case=case, module=args.module, arm=arm, phase_x=dx, phase_y=dy)
                winner.update(metadata)
                for row in rows: row.update(metadata)
                winners.append(winner); starts.extend(rows)
                np.savez_compressed(args.out/(case+'.npz'), **arrays)
                write_csv(args.out/'metrics.csv', winners)
                write_csv(args.out/'fit_starts.csv', starts)
    if len(winners) != 64 or len(starts) != 192:
        raise RuntimeError('incomplete case coverage')
    dump(args.out/'summary.json', dict(results=winners, starts=starts,
         runtime_seconds=time.monotonic()-started,
         interpretation='No new physical recovery acceptance band; retain failures and boundary hits.'))


if __name__ == '__main__':
    main()
