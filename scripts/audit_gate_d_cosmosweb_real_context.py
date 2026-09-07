#!/usr/bin/env python3
"""Quantify real COSMOS-Web SCI/ERR/WHT context before Gate D injection."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from scipy import ndimage
from astropy.io import fits


def robust_background(a: np.ndarray, n_iter: int = 5) -> tuple[float, float, np.ndarray]:
    x = np.asarray(a, dtype=float)
    mask = np.isfinite(x)
    for _ in range(n_iter):
        vals = x[mask]
        med = float(np.median(vals))
        mad = float(np.median(np.abs(vals - med)))
        sigma = 1.4826 * mad
        if not np.isfinite(sigma) or sigma <= 0:
            break
        new = mask & (np.abs(x - med) <= 3.0 * sigma)
        if np.array_equal(new, mask):
            break
        mask = new
    vals = x[mask]
    med = float(np.median(vals))
    mad = float(np.median(np.abs(vals - med)))
    return med, 1.4826 * mad, mask


def _pick_positions(distance: np.ndarray, valid: np.ndarray, lo: float, hi: float | None, n: int = 8):
    m = valid & (distance >= lo)
    if hi is not None:
        m &= distance <= hi
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return []
    order = np.lexsort((xs, ys))
    ys, xs = ys[order], xs[order]
    idx = np.linspace(0, len(xs) - 1, min(n, len(xs)), dtype=int)
    return [[int(xs[i]), int(ys[i]), float(distance[ys[i], xs[i]])] for i in idx]


def audit(path: Path, out: Path) -> dict:
    with fits.open(path, mode="readonly") as h:
        data = {k: np.asarray(h[k].data, dtype=float) for k in ("SCI", "ERR", "WHT")}
    shape = data["SCI"].shape
    if any(data[k].shape != shape for k in data):
        raise ValueError("SCI/ERR/WHT cutout shapes differ")
    finite = {k: np.isfinite(data[k]) for k in data}
    if not all(v.all() for v in finite.values()):
        raise ValueError("non-finite pixels present in real cutout")
    if not np.all(data["ERR"] > 0):
        raise ValueError("ERR contains non-positive pixels")
    if not np.all(data["WHT"] > 0):
        raise ValueError("WHT contains non-positive pixels")

    bg, bg_sigma_mad, bgmask = robust_background(data["SCI"])
    significance = (data["SCI"] - bg) / data["ERR"]
    source = significance > 5.0
    labels, nlabels = ndimage.label(source, structure=np.ones((3, 3), dtype=int))
    distance = ndimage.distance_transform_edt(~source)
    edge = 24
    valid = np.ones(shape, dtype=bool)
    valid[:edge] = valid[-edge:] = False
    valid[:, :edge] = valid[:, -edge:] = False

    summary = {
        "claim": "real-context characterization only; no injection or recovery performed",
        "shape": list(shape),
        "finite_fraction": {k: float(finite[k].mean()) for k in data},
        "positive_fraction": {k: float((data[k] > 0).mean()) for k in ("ERR", "WHT")},
        "background": {"median": bg, "mad_sigma": bg_sigma_mad, "clip_kept_fraction": float(bgmask.mean())},
        "significance": {
            "threshold": 5.0,
            "source_pixel_fraction": float(source.mean()),
            "connected_islands_8conn": int(nlabels),
            "percentiles": {str(p): float(np.percentile(significance, p)) for p in (1, 16, 50, 84, 99, 99.9)},
        },
        "distance_to_source_pixels": {
            "percentiles_pixels": {str(p): float(np.percentile(distance[valid], p)) for p in (10, 25, 50, 75, 90, 95)},
            "candidate_positions_xy_distance": {
                "near_source_2_5": _pick_positions(distance, valid, 2, 5),
                "intermediate_8_20": _pick_positions(distance, valid, 8, 20),
                "relatively_isolated_ge30": _pick_positions(distance, valid, 30, None),
            },
        },
        "ERR_percentiles": {str(p): float(np.percentile(data["ERR"], p)) for p in (1, 5, 50, 95, 99)},
        "WHT_percentiles": {str(p): float(np.percentile(data["WHT"], p)) for p in (1, 5, 50, 95, 99)},
        "planes_modified": False,
        "injection_performed": False,
        "recovery_performed": False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fits", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(audit(a.fits, a.out), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
