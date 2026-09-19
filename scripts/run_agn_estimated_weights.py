#!/usr/bin/env python3
"""One predeclared model-based variance update on archived shot-noise data."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from run_agn_shot_noise import weighted_fit, HOST_ELECTRONS, SEEDS, RATIOS
from run_agn_nuclear_fraction_noiseless import Renderer, fit, write_csv

SOURCE_RUN = 33680659156
SOURCE_COMMIT = '335b76bdf6b83f1d0374252affe5ebcf4c29995c'


def estimated_sigma(prediction, background_sigma):
    if not np.isfinite(prediction).all() or np.any(prediction < 0) or not np.isfinite(background_sigma) or background_sigma <= 0:
        raise ValueError('invalid model intensity or background sigma; never clip')
    return np.sqrt(background_sigma**2 + prediction/HOST_ELECTRONS)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, default=Path('benchmark_output/agn_estimated_weights'))
    args = p.parse_args(); out = args.output; out.mkdir(parents=True, exist_ok=True)
    config = dict(stage='3d single estimated-variance update', source_run=SOURCE_RUN,
                  source_commit=SOURCE_COMMIT, seeds=SEEDS, ratios=RATIOS, host_n=4,
                  fit_factor=8, host_electrons=HOST_ELECTRONS,
                  initial='unweighted fit of actual background_plus_shot data, no truth inputs',
                  update='exactly once: fixed variance = known background sigma squared + initial prediction/10000',
                  optimizer='unchanged inherited three starts, bounds, TRF/NNLS and tolerances in each pass',
                  acceptance='finite complete output only; preserve failures and bounds',
                  limitations='feasible WLS diagnostic, not exact Poisson likelihood or calibrated uncertainties; three paired seeds',
                  exclusions='no new images/noise, PSF mismatch, centroid/PA freedom, fitted sky, iteration to convergence')
    (out/'config.json').write_text(json.dumps(config, indent=2)+'\n')
    if (args.input/'commit.txt').read_text().strip() != SOURCE_COMMIT:
        raise RuntimeError('wrong source commit')
    source = json.loads((args.input/'summary.json').read_text())
    # Background calibration is known; true source intensity is never used in fitting.
    ancestor = json.loads((args.input/'source_record.json').read_text())
    originals = [r for r in source['results'] if r['arm']=='background_plus_shot']
    if len(originals)!=9 or {(r['seed'],r['agn_to_host']) for r in originals}!={(s,r) for s in SEEDS for r in RATIOS}:
        raise RuntimeError('wrong source matrix')
    (out/'source_record.json').write_text(json.dumps(dict(source=source, ancestor=ancestor), indent=2)+'\n')
    renderer = Renderer(oversample=8); rows=[]; starts=[]
    for old in originals:
        seed,ratio = old['seed'],old['agn_to_host']
        z=np.load(args.input/f'seed{seed}_ratio{ratio:g}_background_plus_shot.npz')
        data=z['data']
        if hashlib.sha256(data.tobytes()).hexdigest()!=old['data_sha256']:
            raise RuntimeError('source data hash mismatch')
        bg=next(r['pixel_sigma'] for r in ancestor['results'] if r['seed']==seed and r['agn_to_host']==ratio)
        first, first_starts, initial_prediction = fit(data,renderer,True)
        sigma=estimated_sigma(initial_prediction,bg)
        final, final_starts, prediction = weighted_fit(data,renderer,sigma)
        common=dict(seed=seed,agn_to_host=ratio,host_snr=old['host_snr'],data_sha256=old['data_sha256'],
                    background_sigma=bg,oracle_n=old['n'],oracle_re_pix=old['re_pix'],
                    oracle_host_flux=old['host_flux'],oracle_nuclear_flux=old['nuclear_flux'])
        for label,win,all_rows in [('initial_unweighted',first,first_starts),('estimated_weight',final,final_starts)]:
            # Use one explicit schema; these L1 quantities have different meanings.
            for row in all_rows:
                row.setdefault('residual_l1_over_data_l1', None)
                row.setdefault('whitened_residual_l1_over_whitened_data_l1', None)
            rows.append(dict(**common,pass_name=label,**win))
            starts.extend(dict(**common,pass_name=label,**s) for s in all_rows)
        write_csv(out/'metrics.csv',rows);write_csv(out/'fit_starts.csv',starts)
        np.savez_compressed(out/f'seed{seed}_ratio{ratio:g}.npz',data=data,
                            initial_prediction=initial_prediction,estimated_sigma=sigma,
                            prediction=prediction,residual=prediction-data,
                            oracle_prediction=z['prediction'],oracle_sigma=z['sigma'])
        print(json.dumps(rows[-1]),flush=True)
    if len(rows)!=18 or len(starts)!=54 or not all(np.isfinite(s['cost']) for s in starts):
        raise RuntimeError('incomplete/nonfinite output; retain partial results')
    (out/'summary.json').write_text(json.dumps(dict(config=config,results=rows,starts=starts),indent=2)+'\n')


if __name__=='__main__':
    main()
