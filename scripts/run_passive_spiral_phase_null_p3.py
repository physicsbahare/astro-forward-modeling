#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json, platform
from pathlib import Path
import numpy as np
import scipy
from astropy.io import fits

from verification.passive_spiral_phase_null import P3_PHASE_OFFSETS_DEG, run_p3_grid


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def aggregate(rows: list[dict]) -> list[dict]:
    out = []
    groups = {}
    for r in rows:
        groups.setdefault((r['crowding_class'], float(r['ab_mag'])), []).append(r)
    for (crowding, mag), members in sorted(groups.items()):
        ranks = np.array([m['raw_true_phase_rank'] for m in members], dtype=float)
        deltas = np.array([m['raw_true_minus_best_score'] for m in members], dtype=float)
        out.append({
            'crowding_class': crowding,
            'ab_mag': mag,
            'n': len(members),
            'raw_true_phase_rank_median': float(np.median(ranks)),
            'raw_true_phase_rank_values': [int(x) for x in ranks],
            'raw_true_minus_best_score_median': float(np.median(deltas)),
            'paired_true_phase_ranks': [int(m['paired_true_phase_rank']) for m in members],
        })
    return out


def run(real_fits: Path, matrix_path: Path, out_dir: Path) -> dict:
    matrix = json.loads(matrix_path.read_text())
    with fits.open(real_fits, mode='readonly', memmap=True) as hdul:
        sci = np.array(hdul['SCI'].data, dtype=float, copy=True)
        err = np.array(hdul['ERR'].data, dtype=float, copy=True)
        wht = np.array(hdul['WHT'].data, dtype=float, copy=True)
        hdr = hdul['SCI'].header.copy()
    if not (sci.shape == err.shape == wht.shape):
        raise ValueError('SCI/ERR/WHT shape mismatch')
    if str(hdr.get('BUNIT','')).strip().lower() != 'mjy/sr':
        raise ValueError('expected MJy/sr')
    pixar_sr = float(hdr['PIXAR_SR'])
    rows = run_p3_grid(sci, err, matrix, pixar_sr)
    if len(rows) != 18:
        raise RuntimeError(f'expected 18 frozen cases, got {len(rows)}')
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        'benchmark': 'Passive Spiral P3 raw-scene spiral phase/orientation null test',
        'input_real_fits': real_fits.name,
        'input_real_fits_sha256': sha256(real_fits),
        'phase_offsets_deg': list(P3_PHASE_OFFSETS_DEG),
        'n_cases': len(rows),
        'results': rows,
        'aggregate_descriptive': aggregate(rows),
        'measurement_semantics': {
            'scientific_ranking_uses_original_scene': False,
            'paired_difference_is_identifiability_control_only': True,
            'scientific_detection_threshold_applied': False,
            'arm_coefficients_constrained': False,
        },
        'mutations': {
            'science_input_modified_in_place': False,
            'err_modified': False,
            'wht_modified': False,
            'background_noise_added': False,
            'source_shot_noise_generated': False,
            'psf_sharpening_applied': False,
            'extra_tolman_factor_applied': False,
        },
        'software': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__},
    }
    p = out_dir / 'p3_phase_null_metrics.json'
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
    print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--real-fits', type=Path, required=True)
    ap.add_argument('--matrix', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    run(a.real_fits, a.matrix, a.out)

if __name__ == '__main__':
    main()
