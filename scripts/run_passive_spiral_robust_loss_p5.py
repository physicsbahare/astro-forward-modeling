#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json, platform
from pathlib import Path

import numpy as np
import scipy
from astropy.io import fits

from verification.passive_spiral_robust_loss import P5_F_SCALE, P5_LOSS, run_p5_grid


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def aggregate(rows: list[dict]) -> dict:
    p3 = np.asarray([r["p3_true_phase_rank"] for r in rows], dtype=int)
    p5 = np.asarray([r["p5_true_phase_rank"] for r in rows], dtype=int)
    paired = np.asarray([r["paired_p5_true_phase_rank"] for r in rows], dtype=int)
    phase_fits = [f for r in rows for f in r["p5_phase_fits"]]
    paired_phase_fits = [f for r in rows for f in r["paired_p5_phase_fits"]]

    by_group = []
    keys = sorted({(r["crowding_class"], float(r["ab_mag"])) for r in rows})
    for crowding, mag in keys:
        members = [r for r in rows if r["crowding_class"] == crowding and float(r["ab_mag"]) == mag]
        g3 = np.asarray([m["p3_true_phase_rank"] for m in members], dtype=int)
        g5 = np.asarray([m["p5_true_phase_rank"] for m in members], dtype=int)
        by_group.append({
            "crowding_class": crowding,
            "ab_mag": mag,
            "n": len(members),
            "p3_true_phase_ranks": g3.tolist(),
            "p5_true_phase_ranks": g5.tolist(),
            "p3_rank1_count": int(np.count_nonzero(g3 == 1)),
            "p5_rank1_count": int(np.count_nonzero(g5 == 1)),
            "p3_rank_median": float(np.median(g3)),
            "p5_rank_median": float(np.median(g5)),
            "improved": int(np.count_nonzero(g5 < g3)),
            "unchanged": int(np.count_nonzero(g5 == g3)),
            "worsened": int(np.count_nonzero(g5 > g3)),
        })

    return {
        "p3_rank1_count": int(np.count_nonzero(p3 == 1)),
        "p5_rank1_count": int(np.count_nonzero(p5 == 1)),
        "p3_rank_median": float(np.median(p3)),
        "p5_rank_median": float(np.median(p5)),
        "improved": int(np.count_nonzero(p5 < p3)),
        "unchanged": int(np.count_nonzero(p5 == p3)),
        "worsened": int(np.count_nonzero(p5 > p3)),
        "paired_rank1_count": int(np.count_nonzero(paired == 1)),
        "raw_optimizer_failure_count": int(sum(not f["optimizer_success"] for f in phase_fits)),
        "paired_optimizer_failure_count": int(sum(not f["optimizer_success"] for f in paired_phase_fits)),
        "raw_nonfinite_solution_count": int(sum(not f["finite_solution"] for f in phase_fits)),
        "paired_nonfinite_solution_count": int(sum(not f["finite_solution"] for f in paired_phase_fits)),
        "by_crowding_and_magnitude": by_group,
    }


def run(real_fits: Path, matrix_path: Path, out_dir: Path) -> dict:
    matrix = json.loads(matrix_path.read_text())
    with fits.open(real_fits, mode="readonly", memmap=True) as hdul:
        sci = np.array(hdul["SCI"].data, dtype=float, copy=True)
        err = np.array(hdul["ERR"].data, dtype=float, copy=True)
        wht = np.array(hdul["WHT"].data, dtype=float, copy=True)
        hdr = hdul["SCI"].header.copy()
    if not (sci.shape == err.shape == wht.shape):
        raise ValueError("SCI/ERR/WHT shape mismatch")
    if str(hdr.get("BUNIT", "")).strip().lower() != "mjy/sr":
        raise ValueError("expected MJy/sr")
    pixar_sr = float(hdr["PIXAR_SR"])

    rows = run_p5_grid(sci, err, matrix, pixar_sr)
    if len(rows) != 18:
        raise RuntimeError(f"expected 18 frozen cases, got {len(rows)}")

    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "benchmark": "Passive Spiral P5 Huber robust-loss contamination control",
        "input_real_fits": real_fits.name,
        "input_real_fits_sha256": sha256(real_fits),
        "n_cases": len(rows),
        "robust_fit": {
            "loss": P5_LOSS,
            "f_scale_standardized_err_units": P5_F_SCALE,
            "pixel_masking_or_clipping": False,
            "parameter_bounds": False,
            "starting_point": "ordinary diagonal-ERR weighted linear solution for same phase",
        },
        "results": rows,
        "aggregate_descriptive": aggregate(rows),
        "measurement_semantics": {
            "scientific_ranking_uses_raw_injected_scene": True,
            "paired_difference_is_identifiability_control_only": True,
            "scientific_detection_threshold_applied": False,
            "same_renderer_is_independent_crosscode_validation": False,
        },
        "mutations": {
            "science_input_modified_in_place": False,
            "err_data_product_modified": False,
            "wht_modified": False,
            "background_noise_added": False,
            "source_shot_noise_generated": False,
            "psf_sharpening_applied": False,
            "extra_tolman_factor_applied": False,
        },
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
    }
    path = out_dir / "p5_robust_loss_metrics.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--real-fits", type=Path, required=True)
    ap.add_argument("--matrix", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    run(args.real_fits, args.matrix, args.out)


if __name__ == "__main__":
    main()
