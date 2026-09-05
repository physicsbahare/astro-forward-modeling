#!/usr/bin/env python3
"""Verification only: nuclear contamination, noiseless and perfectly known PSF.

Fixed center/PA and background deliberately isolate profile/flux contamination.
This is a same-renderer reference, not an independent sampling validation or
literal reproduction of a JWST observation. No recovery threshold is applied.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.optimize import least_squares, nnls
from scipy.special import erf, gammaincinv, gammaln

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from verification.agn_nuclear_fraction import AGN_TO_HOST_ANCHORS, CONTROLLED_HOST_SCENES

# Frozen before Stage-1 execution. Bounds/start-n/budget follow the Yu diagnostic.
STAMP = 129
OVERSAMPLE = 4
FWHM_PIX = 3.0  # controlled Gaussian, not a claimed survey PSF
TRUNCATE = 6.0
RE_BOUNDS = (0.5, 60.0)
N_BOUNDS = (0.5, 6.0)
Q_BOUNDS = (0.15, 1.0)
START_N = (1.0, 2.5, 5.0)
START_RE = 12.0
START_Q = 0.75
MAX_NFEV = 160


class Renderer:
    def __init__(self, stamp=STAMP, oversample=OVERSAMPLE):
        self.stamp, self.f = stamp, oversample
        self.sigma = FWHM_PIX / np.sqrt(8 * np.log(2))
        self.pad = int(np.ceil(TRUNCATE * self.sigma)) + 1
        side = stamp + 2 * self.pad
        offsets = (np.arange(self.f) + 0.5) / self.f - 0.5
        coord = (np.arange(side)[:, None] + offsets).ravel() - (side - 1) / 2
        yy, xx = np.meshgrid(coord, coord, indexing='ij')
        # All frozen scenes have PA=45 degrees and are exactly co-centered.
        pa = np.deg2rad(CONTROLLED_HOST_SCENES[0].pa_deg)
        self.xp2 = (np.cos(pa) * xx + np.sin(pa) * yy) ** 2
        self.yp2 = (-np.sin(pa) * xx + np.cos(pa) * yy) ** 2
        # Exact detector-pixel integral of the same continuous Gaussian PSF.
        edges = np.arange(stamp + 1) - stamp / 2
        one = np.diff(0.5 * (1 + erf(edges / (np.sqrt(2) * self.sigma))))
        self.point = np.outer(one, one)

    def host(self, re, n, q):
        radius = np.sqrt(self.xp2 + self.yp2 / q ** 2)
        b = gammaincinv(2 * n, 0.5)
        # Analytic infinite-plane normalization: never renormalize the stamp.
        log_norm = 2*n*np.log(b) - np.log(2*np.pi*n*q*re**2) - gammaln(2*n)
        fine = np.exp(log_norm - b * (radius/re)**(1/n))
        fine = gaussian_filter(fine, self.sigma*self.f, mode='constant', truncate=TRUNCATE)
        side = self.stamp + 2*self.pad
        detector = fine.reshape(side, self.f, side, self.f).mean(axis=(1, 3))
        return detector[self.pad:-self.pad, self.pad:-self.pad]


def profile_flux(data, host, point=None):
    """Nonnegative linear amplitudes at each structural trial, no flux ceiling."""
    templates = [host.ravel()] if point is None else [host.ravel(), point.ravel()]
    matrix = np.column_stack(templates)
    flux, _ = nnls(matrix, data.ravel())
    return flux, (matrix @ flux).reshape(data.shape)


def fit(data, renderer, decomposition):
    scale = float(np.sqrt(np.mean(data**2)))
    lo = np.array([np.log(RE_BOUNDS[0]), np.log(N_BOUNDS[0]), Q_BOUNDS[0]])
    hi = np.array([np.log(RE_BOUNDS[1]), np.log(N_BOUNDS[1]), Q_BOUNDS[1]])
    point = renderer.point if decomposition else None

    def evaluate(p):
        host = renderer.host(np.exp(p[0]), np.exp(p[1]), p[2])
        flux, prediction = profile_flux(data, host, point)
        return flux, prediction

    def residual(p):
        return ((evaluate(p)[1] - data) / scale).ravel()

    starts = []
    predictions = []
    for ns in START_N:
        result = least_squares(residual, [np.log(START_RE), np.log(ns), START_Q],
                               bounds=(lo, hi), method='trf', max_nfev=MAX_NFEV,
                               ftol=1e-10, xtol=1e-10, gtol=1e-7)
        flux, prediction = evaluate(result.x)
        re, n, q = float(np.exp(result.x[0])), float(np.exp(result.x[1])), float(result.x[2])
        row = dict(start_n=ns, success=bool(result.success), status=int(result.status),
                   message=result.message, nfev=int(result.nfev), cost=float(result.cost),
                   optimality=float(result.optimality), re_pix=re, n=n, q=q,
                   host_flux=float(flux[0]), nuclear_flux=float(flux[1]) if decomposition else 0.0,
                   residual_l1_over_data_l1=float(np.abs(prediction-data).sum()/np.abs(data).sum()),
                   hit_host_flux_zero=bool(flux[0] == 0),
                   hit_nuclear_flux_zero=bool(decomposition and flux[1] == 0))
        # Inherited Yu reporting convention, not an acceptance band.
        for name, value, bounds in [('re', re, RE_BOUNDS), ('n', n, N_BOUNDS), ('q', q, Q_BOUNDS)]:
            row[f'hit_{name}_lower_bound'] = bool(value <= bounds[0] * (1+1e-5))
            row[f'hit_{name}_upper_bound'] = bool(value >= bounds[1] * (1-1e-5))
        starts.append(row)
        predictions.append(prediction)
    index = min(range(len(starts)), key=lambda k: starts[k]['cost'])
    return starts[index], starts, predictions[index]


def write_csv(path, rows):
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host-n', type=float, choices=[s.n for s in CONTROLLED_HOST_SCENES])
    parser.add_argument('--output', type=Path, default=Path('benchmark_output/agn_nuclear_fraction/noiseless'))
    args = parser.parse_args()
    scenes = [s for s in CONTROLLED_HOST_SCENES if args.host_n is None or args.host_n == s.n]
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    config = dict(experiment='AGN nuclear fraction Stage 1: noiseless perfect-PSF',
                  stamp=STAMP, oversample=OVERSAMPLE, psf='continuous circular Gaussian',
                  fwhm_pix=FWHM_PIX, convolution='4x fine-grid Gaussian then detector integration',
                  gaussian_truncate_sigma=TRUNCATE, flux_semantics='analytic infinite-plane total; no stamp renormalization',
                  fixed='true common center, PA=45 deg, zero background',
                  re_bounds=RE_BOUNDS, n_bounds=N_BOUNDS, q_bounds=Q_BOUNDS,
                  start_n=START_N, start_re=START_RE, start_q=START_Q,
                  optimizer='TRF least_squares; NNLS-profiled nonnegative fluxes',
                  max_nfev=MAX_NFEV, ftol=1e-10, xtol=1e-10, gtol=1e-7,
                  winner='lowest residual cost regardless of success or truth proximity',
                  ratios=AGN_TO_HOST_ANCHORS, host_scenes=[vars(s) for s in scenes],
                  limitations='same-renderer reference; not sampling convergence, survey reproduction, free-centroid inference, or gate closure',
                  acceptance='no new morphology acceptance band; failures and bounds are observables')
    # Persist choices before any optimization and preserve partial output on failure.
    (out/'config.json').write_text(json.dumps(config, indent=2)+'\n')
    renderer = Renderer()
    rows, all_starts = [], []
    for scene in scenes:
        host = renderer.host(scene.re_pix, scene.n, scene.q)
        for ratio in AGN_TO_HOST_ANCHORS:
            data = host + ratio*renderer.point
            key = f'n{scene.n:g}_ratio{ratio:g}'
            images = dict(data=data, host_truth=host, nuclear_truth=ratio*renderer.point)
            for decomposition in (False, True):
                label = 'sersic_plus_psf' if decomposition else 'host_only'
                winner, starts, prediction = fit(data, renderer, decomposition)
                common = dict(scene=key, model=label, true_n=scene.n, true_re_pix=scene.re_pix,
                              true_q=scene.q, agn_to_host=ratio, nuclear_fraction=ratio/(1+ratio),
                              true_host_flux=1.0, true_nuclear_flux=ratio,
                              host_flux_in_stamp=float(host.sum()), data_flux_in_stamp=float(data.sum()),
                              data_sha256=hashlib.sha256(data.tobytes()).hexdigest())
                rows.append(dict(**common, **winner, re_ratio=winner['re_pix']/scene.re_pix,
                                 delta_n=winner['n']-scene.n, delta_q=winner['q']-scene.q,
                                 host_flux_ratio=winner['host_flux'], nuclear_flux_ratio=winner['nuclear_flux']/ratio))
                all_starts.extend(dict(**common, **s) for s in starts)
                images[label] = prediction
                print(json.dumps(rows[-1]), flush=True)
                write_csv(out/'metrics.csv', rows)
                write_csv(out/'fit_starts.csv', all_starts)
            np.savez_compressed(out/f'{key}.npz', **images)
    expected = len(scenes)*len(AGN_TO_HOST_ANCHORS)*2
    if len(rows) != expected or any(not np.isfinite(r['cost']) for r in rows):
        raise RuntimeError('incomplete or nonfinite experiment; inspect partial outputs')
    summary = dict(config=config, matrix_rows=len(rows), expected_rows=expected,
                   successful_winners=sum(r['success'] for r in rows),
                   winners_with_bounds=sum(any(v for k,v in r.items() if k.startswith('hit_')) for r in rows),
                   results=rows, interpretation='execution is not scientific acceptance; review all starts and residuals')
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')


if __name__ == '__main__':
    main()
