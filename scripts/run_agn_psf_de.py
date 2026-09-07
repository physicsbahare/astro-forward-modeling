#!/usr/bin/env python3
"""C5c: thin SciPy differential-evolution adapter for the C5b objective.

No new renderer or optimizer implementation; all scientific conventions remain
in the archived C5b helpers. Finite-budget search is not a global-optimum proof.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import differential_evolution

from run_agn_psf_plateau import evaluate, refine
from run_agn_psf_width import WidthRenderer
from run_agn_nuclear_fraction_noiseless import RE_BOUNDS, N_BOUNDS, Q_BOUNDS, write_csv

SOURCE_RUN = 33705072892
SOURCE_COMMIT = '9159a6342880d5b2d21eee7371ba577736a923bc'
SCIPY_VERSION = '1.18.1'
NUMPY_VERSION = '2.5.2'
RNG_SEEDS = (20260903, 20260904)
DE_OPTIONS = dict(strategy='best1bin', maxiter=60, popsize=10, tol=1e-7,
                  atol=0., mutation=(.5, 1.), recombination=.7,
                  init='sobol', updating='deferred', workers=1,
                  vectorized=False, polish=False, x0=None)
SEARCH_BOUNDS = (tuple(np.log(RE_BOUNDS)), tuple(np.log(N_BOUNDS)), Q_BOUNDS)
POPULATION_SIZE = 32  # Sobol rounds 10 * 3 up to the next power of two.


def package_search(objective, seed, callback=None, *, options=None):
    """Use the public package API; options override is for small unit tests only."""
    settings = dict(DE_OPTIONS)
    if options is not None:
        settings.update(options)
    return differential_evolution(objective, bounds=SEARCH_BOUNDS,
                                  rng=np.random.default_rng(seed),
                                  callback=callback, **settings)


def checked_source(root, host_n):
    if (root/'commit.txt').read_text().strip() != SOURCE_COMMIT:
        raise RuntimeError('wrong C5b commit')
    source = json.loads((root/'summary.json').read_text())
    if source['config']['host_n'] != host_n:
        raise RuntimeError('wrong host shard')
    if source['config']['ratio'] != 10. or source['config']['width_factor'] != 1.03:
        raise RuntimeError('wrong source experiment')
    with np.load(root/'images.npz') as z:
        images = {k:z[k] for k in z.files}
    if hashlib.sha256(images['data'].tobytes()).hexdigest() != source['data_sha256']:
        raise RuntimeError('wrong source image hash')
    if not all(np.all(np.isfinite(v)) for v in images.values()):
        raise RuntimeError('nonfinite source image')
    return source, images


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--host-n', type=int, choices=(1,4), required=True)
    p.add_argument('--output', type=Path, default=Path('benchmark_output/agn_psf_de'))
    a = p.parse_args(); out = a.output; out.mkdir(parents=True, exist_ok=True)
    config = dict(stage='C5c package-based DE search', source_run=SOURCE_RUN,
        source_commit=SOURCE_COMMIT, host_n=a.host_n, ratio=10., psf_width_factor=1.03,
        github_run_id=os.environ.get('GITHUB_RUN_ID'), github_sha=os.environ.get('GITHUB_SHA'),
        numpy_pin=NUMPY_VERSION, scipy_pin=SCIPY_VERSION,
        runtime_numpy=np.__version__, runtime_scipy=scipy.__version__,
        rng_seeds=RNG_SEEDS, rng='numpy default_rng PCG64; independent search seeds, not noise',
        coordinates=['log(Re_pix)','log(n)','q'], search_bounds=SEARCH_BOUNDS,
        de_options=DE_OPTIONS, population_size=POPULATION_SIZE,
        max_objective_evaluations_per_search=POPULATION_SIZE*(DE_OPTIONS['maxiter']+1),
        refinement='one inherited C5b TRF refinement per DE seed; all bounds/tolerances/budget unchanged',
        selection='save DE and TRF candidates independently; lowest cost among all candidates regardless of success',
        acceptance='complete finite records and bookkeeping identities only; no truth-recovery or improvement band',
        limitations='same fixed renderer/objective; not independent image-code validation or proof of global optimum')
    (out/'config.json').write_text(json.dumps(config, indent=2)+'\n')
    if scipy.__version__ != SCIPY_VERSION or np.__version__ != NUMPY_VERSION:
        raise RuntimeError('package pin mismatch; do not silently change the experiment')
    source, images = checked_source(a.input, a.host_n)
    (out/'source_record.json').write_text(json.dumps(source, indent=2)+'\n')
    manifest = {name:hashlib.sha256((a.input/name).read_bytes()).hexdigest()
                for name in ('commit.txt','config.json','summary.json','images.npz','pip-freeze.txt')}
    (out/'input_sha256.json').write_text(json.dumps(manifest, indent=2)+'\n')
    renderer = WidthRenderer(3*1.03)
    np.testing.assert_array_equal(renderer.point, images['fit_point'])
    data = images['data']; reference = source['winner']; original = source['original_winner']
    recalculated, _ = evaluate(data, renderer, reference['re_pix'], reference['n'], reference['q'])
    (out/'baseline_recalculated.json').write_text(json.dumps(dict(
        archived_cost=reference['cost'], recalculated=recalculated,
        delta_cost=recalculated['cost']-reference['cost']), indent=2)+'\n')
    rows, search_records = [], []
    for seed in RNG_SEEDS:
        trial_count = 0; generation_count = 0
        with (out/f'evaluations_seed{seed}.csv').open('w', newline='') as trial_file, \
             (out/f'populations_seed{seed}.jsonl').open('w') as population_file:
            writer = None
            def objective(params):
                nonlocal writer, trial_count
                row, _ = evaluate(data, renderer, np.exp(params[0]), np.exp(params[1]), params[2])
                row.update(evaluation=trial_count, seed=seed,
                           phase='initial_population' if trial_count<POPULATION_SIZE else 'de_trial')
                if writer is None:
                    writer = csv.DictWriter(trial_file, fieldnames=list(row))
                    writer.writeheader()
                writer.writerow(row); trial_file.flush(); trial_count += 1
                if not np.isfinite(row['cost']):
                    raise RuntimeError('nonfinite objective; trial retained')
                return row['cost']
            def callback(intermediate_result):
                nonlocal generation_count
                generation_count += 1
                record = dict(generation=generation_count, nfev=int(intermediate_result.nfev),
                    best=intermediate_result.x.tolist(), cost=float(intermediate_result.fun),
                    population=intermediate_result.population.tolist(),
                    energies=intermediate_result.population_energies.tolist())
                population_file.write(json.dumps(record)+'\n'); population_file.flush()
                return False
            result = package_search(objective, seed, callback)
        if trial_count != result.nfev or generation_count != result.nit:
            raise RuntimeError('incomplete search trace')
        de_row, de_pred = evaluate(data, renderer, np.exp(result.x[0]), np.exp(result.x[1]), result.x[2])
        de_row.update(solver='differential_evolution', seed=seed, success=bool(result.success),
                      status=None, message=str(result.message), nfev=int(result.nfev),
                      optimality=None, seed_grid_index=None, seed_re=None, seed_n=None, seed_q=None)
        trf_row, trf_pred = refine(data, renderer, dict(de_row, grid_index=-1))
        # -1 denotes a DE seed rather than one of the historical grid indices.
        trf_row.update(solver='inherited_trf', seed=seed)
        for row, pred in ((de_row, de_pred),(trf_row, trf_pred)):
            row.update(delta_cost_vs_c5a=row['cost']-original['cost'],
                       delta_cost_vs_c5b=row['cost']-reference['cost'])
            rows.append(row)
            print(json.dumps(row), flush=True)
        write_csv(out/'metrics.csv', rows)
        write_csv(out/'fit_starts.csv', rows)
        record = dict(seed=seed, success=bool(result.success), message=str(result.message),
            nit=int(result.nit), nfev=int(result.nfev), x=result.x.tolist(), cost=float(result.fun),
            population=result.population.tolist(), energies=result.population_energies.tolist())
        search_records.append(record)
        (out/f'search_seed{seed}.json').write_text(json.dumps(record, indent=2)+'\n')
        np.savez_compressed(out/f'images_seed{seed}.npz', data=data,
            host_reference=images['host_reference'], fit_point=renderer.point,
            c5a_prediction=images['original_prediction'], c5b_prediction=images['prediction'],
            de_prediction=de_pred, de_residual=de_pred-data,
            trf_prediction=trf_pred, trf_residual=trf_pred-data)
    if len(rows)!=4 or not all(np.isfinite(r['cost']) for r in rows):
        raise RuntimeError('incomplete/nonfinite candidates; partial outputs retained')
    winner = min(rows, key=lambda r:r['cost'])
    (out/'summary.json').write_text(json.dumps(dict(config=config, data_sha256=source['data_sha256'],
        results=rows, searches=search_records, winner=winner,
        interpretation='optimizer termination, morphology validity and global optimality are distinct'), indent=2)+'\n')


if __name__ == '__main__': main()
