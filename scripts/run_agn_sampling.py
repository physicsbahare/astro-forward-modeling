#!/usr/bin/env python3
"""Stage 2a: quadrature sensitivity, not independent-renderer validation."""
import argparse
import json
from pathlib import Path
import numpy as np
from run_agn_nuclear_fraction_noiseless import Renderer, profile_flux, write_csv

FACTORS = (4, 8, 16)
RATIOS = (0.1, 1.0, 10.0)


def compare(reference, trial, point, ratio):
    data = reference + ratio * point
    flux, prediction = profile_flux(data, trial, point)
    cosine = float(np.vdot(trial, point) / (np.linalg.norm(trial)*np.linalg.norm(point)))
    return dict(host_l1_difference=float(abs(trial-reference).sum()/abs(reference).sum()),
                host_stamp_flux=float(trial.sum()), reference_stamp_flux=float(reference.sum()),
                host_flux=float(flux[0]), nuclear_flux=float(flux[1]),
                host_flux_bias=float(flux[0]-1), nuclear_flux_bias=float(flux[1]-ratio),
                template_cosine=cosine,
                normalized_two_template_condition=float(np.sqrt((1+cosine)/(1-cosine))),
                residual_l1_over_data_l1=float(abs(prediction-data).sum()/abs(data).sum())), prediction


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--host-n', type=float, choices=(1, 4), required=True)
    p.add_argument('--output', type=Path, default=Path('benchmark_output/agn_sampling'))
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    config = dict(stage='2a sampling and fixed-shape flux sensitivity', factors=FACTORS,
                  host_n=args.host_n, re_pix=16, q=0.6, pa_deg=45, stamp=129,
                  ratios=RATIOS, comparisons=[[4,8],[8,16],[4,16]],
                  reference='higher sampling, not truth or proven convergence',
                  fixed='center, PA, Re, n, q, zero background, perfect Gaussian FWHM=3',
                  acceptance='finite complete matrix only; no morphology acceptance band',
                  limitations='same renderer family; two-template condition is not full nonlinear identifiability')
    (args.output/'config.json').write_text(json.dumps(config, indent=2)+'\n')
    hosts = {}
    for factor in FACTORS:
        renderer = Renderer(oversample=factor)
        hosts[factor] = renderer.host(16, args.host_n, 0.6)
        point = renderer.point
        del renderer
    rows = []
    images = {'point': point, **{f'host_f{k}': v for k,v in hosts.items()}}
    for low, high in config['comparisons']:
        for ratio in RATIOS:
            result, prediction = compare(hosts[high], hosts[low], point, ratio)
            row = dict(host_n=args.host_n, fit_factor=low, reference_factor=high,
                       agn_to_host=ratio, **result)
            rows.append(row)
            images[f'fit_f{low}_ref{high}_ratio{ratio}'] = prediction
            print(json.dumps(row), flush=True)
    write_csv(args.output/'metrics.csv', rows)
    np.savez_compressed(args.output/'images.npz', **images)
    if len(rows) != 9 or not all(np.isfinite(list(r.values())).all() for r in rows):
        raise RuntimeError('incomplete or nonfinite diagnostic')
    (args.output/'summary.json').write_text(json.dumps(dict(config=config, results=rows), indent=2)+'\n')


if __name__ == '__main__':
    main()
