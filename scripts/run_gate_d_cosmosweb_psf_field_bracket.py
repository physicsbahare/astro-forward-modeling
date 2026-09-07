#!/usr/bin/env python3
"""Gate D1n-a: quantify STPSF detector-field sensitivity without source recovery."""
from __future__ import annotations
import argparse, copy, json, math
from pathlib import Path
import numpy as np

import run_gate_d_cosmosweb_real_injection as inj

BRACKET_POSITIONS = (
    ("field_256_256", (256, 256)),
    ("field_1792_256", (1792, 256)),
    ("field_256_1792", (256, 1792)),
    ("field_1792_1792", (1792, 1792)),
)


def _center_pad(a: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    out = np.zeros(shape, dtype=float)
    y0 = (shape[0] - a.shape[0]) // 2
    x0 = (shape[1] - a.shape[1]) // 2
    out[y0:y0+a.shape[0], x0:x0+a.shape[1]] = a
    return out


def common_centered(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    sy = max(a.shape[0], b.shape[0]); sx = max(a.shape[1], b.shape[1])
    return _center_pad(a, (sy, sx)), _center_pad(b, (sy, sx))


def psf_metrics(psf: np.ndarray) -> dict:
    p = np.asarray(psf, dtype=float)
    if p.ndim != 2 or not np.all(np.isfinite(p)) or np.any(p < 0) or p.sum() <= 0:
        raise ValueError("PSF must be finite, non-negative, two-dimensional, positive-sum")
    p = p / p.sum()
    yy, xx = np.indices(p.shape, dtype=float)
    cx = float((p * xx).sum()); cy = float((p * yy).sum())
    dx = xx - cx; dy = yy - cy
    cxx = float((p * dx * dx).sum()); cyy = float((p * dy * dy).sum()); cxy = float((p * dx * dy).sum())
    cov = np.array([[cxx, cxy], [cxy, cyy]], dtype=float)
    vals, vecs = np.linalg.eigh(cov); order = np.argsort(vals)[::-1]; vals = vals[order]; vecs = vecs[:, order]
    major = math.sqrt(max(0.0, float(vals[0]))); minor = math.sqrt(max(0.0, float(vals[1])))
    vx, vy = vecs[:, 0]; pa = math.degrees(math.atan2(vy, vx))
    center_x = (p.shape[1] - 1) / 2.0; center_y = (p.shape[0] - 1) / 2.0
    rr = np.hypot(xx - cx, yy - cy).ravel(); flux = p.ravel(); idx = np.argsort(rr)
    rr = rr[idx]; cdf = np.cumsum(flux[idx])
    def er(frac: float) -> float:
        return float(rr[min(int(np.searchsorted(cdf, frac, side="left")), len(rr)-1)])
    return {"centroid_x_pix": cx, "centroid_y_pix": cy,
            "centroid_offset_from_array_center_pix": float(math.hypot(cx-center_x, cy-center_y)),
            "sigma_major_pix": major, "sigma_minor_pix": minor, "axis_ratio_moment": (minor/major if major > 0 else float("nan")),
            "moment_pa_deg": pa, "ee50_radius_pix": er(0.5), "ee80_radius_pix": er(0.8), "sum": float(p.sum()),
            "shape": list(p.shape)}


def compare_psfs(base: np.ndarray, other: np.ndarray) -> dict:
    a, b = common_centered(np.asarray(base, float), np.asarray(other, float))
    a /= a.sum(); b /= b.sum()
    l1 = float(np.abs(a-b).sum())
    denom = math.sqrt(float((a*a).sum() * (b*b).sum()))
    corr = float((a*b).sum()/denom) if denom > 0 else float("nan")
    return {"normalized_l1": l1, "normalized_cross_correlation": corr, "common_shape": list(a.shape)}


def run(injection_summary: Path, out_json: Path) -> dict:
    src = json.loads(injection_summary.read_text())
    matrix = src["matrix"]
    scale = float(matrix["pixel_scale_arcsec"])
    original = tuple(int(v) for v in matrix["psf"]["detector_position_xy"])
    conditions = [("baseline", original)] + list(BRACKET_POSITIONS)
    rendered: dict[str, np.ndarray] = {}; rows = []
    for name, position in conditions:
        m = copy.deepcopy(matrix); m["psf"]["detector_position_xy"] = [int(position[0]), int(position[1])]
        psf, prov = inj.build_stpsf(m, scale)
        rendered[name] = psf
        rows.append({"name": name, "detector_position_xy": list(position), "metrics": psf_metrics(psf), "stpsf_provenance": prov})
    base = rendered["baseline"]
    for row in rows:
        row["comparison_to_baseline"] = compare_psfs(base, rendered[row["name"]])
    result = {
        "claim": "STPSF detector-field bracket sensitivity only; not a local/effective COSMOS-Web mosaic PSF reconstruction and not morphology recovery",
        "stpsf_version": "2.2.0",
        "baseline_detector_position_xy": list(original),
        "frozen_bracket_positions": [list(p) for _, p in BRACKET_POSITIONS],
        "conditions": rows,
        "semantics": {"source_injection_performed": False, "morphology_recovery_performed": False,
                      "psf_sharpening_performed": False, "acceptance_threshold_defined": False,
                      "mosaic_pixel_mapped_to_detector_position": False, "literal_effective_cosmosweb_psf_claimed": False,
                      "target_bounds_changed": False, "tolman_factor_applied": False, "noise_added": False},
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--injection-summary", type=Path, required=True); p.add_argument("--out-json", type=Path, required=True)
    a = p.parse_args(); r = run(a.injection_summary, a.out_json)
    print(json.dumps({"n_conditions": len(r["conditions"]), "baseline_detector_position_xy": r["baseline_detector_position_xy"]}, indent=2))

if __name__ == "__main__": main()
