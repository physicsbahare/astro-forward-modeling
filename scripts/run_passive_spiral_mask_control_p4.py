#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json, platform
from pathlib import Path
import numpy as np
import scipy
from astropy.io import fits

from verification.passive_spiral_mask_control import (
    P4_D1C_BACKGROUND_MJYSR,
    P4_D1C_SOURCE_SIGMA,
    frozen_d1c_source_mask,
    run_p4_grid,
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def aggregate(rows: list[dict]) -> list[dict]:
    groups = {}
    for r in rows:
        groups.setdefault((r['crowding_class'], float(r['ab_mag'])), []).append(r)
    out = []
    for (crowding, mag), members in sorted(groups.items()):
        masked = np.array([m['masked_true_phase_rank'] for m in members], dtype=float)
        unmasked = np.array([m['unmasked_true_phase_rank'] for m in members], dtype=float)
        frac = np.array([m['masked_fraction'] for m in members], dtype=float)
        out.append({
            'crowding_class': crowding,
            'ab_mag': mag,
            'n': len(members),
            'masked_true_phase_ranks': [int(x) for x in masked],
            'unmasked_true_phase_ranks': [int(x) for x in unmasked],
            'masked_rank_median': float(np.median(masked)),
            'unmasked_rank_median': float(np.median(unmasked)),
            'masked_fraction_median': float(np.median(frac)),
            'masked_paired_true_phase_ranks': [int(m['masked_paired_true_phase_rank']) for m in members],
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
    mask = frozen_d1c_source_mask(sci, err)
    rows = run_p4_grid(sci, err, matrix, pixar_sr)
    if len(rows) != 18:
        raise RuntimeError(f'expected 18 frozen cases, got {len(rows)}')
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        'benchmark': 'Passive Spiral P4 pre-injection source-mask contamination control',
        'input_real_fits': real_fits.name,
        'input_real_fits_sha256': sha256(real_fits),
        'n_cases': len(rows),
        'mask_definition': {
            'background_mjysr': P4_D1C_BACKGROUND_MJYSR,
            'source_sigma_threshold': P4_D1C_SOURCE_SIGMA,
            'global_masked_fraction': float(np.mean(mask)),
            'derived_from_pre_injection_original_only': True,
            'dilated_or_tuned': False,
        },
        'results': rows,
        'aggregate_descriptive': aggregate(rows),
        'measurement_semantics': {
            'scientific_ranking_uses_original_scene_values': False,
            'original_scene_used_only_for_frozen_boolean_mask': True,
            'paired_difference_is_identifiability_control_only': True,
            'scientific_detection_threshold_applied': False,
            'arm_coefficients_constrained': False,
        },
        'mutations': {
            'science_input_modified_in_place': False,
            'err_data_product_modified': False,
            'wht_modified': False,
            'fitting_err_copy_masked_with_nan': True,
            'background_noise_added': False,
            'source_shot_noise_generated': False,
            'psf_sharpening_applied': False,
            'extra_tolman_factor_applied': False,
        },
        'software': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__},
    }
    path = out_dir / 'p4_mask_control_metrics.json'
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
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
