#!/usr/bin/env python3
"""Gate D1n-i: ERR-weighted residual / target-tangent alignment diagnostic."""
from __future__ import annotations
import argparse, importlib.util, json, math, sys
from pathlib import Path
import numpy as np
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

d1nh = _load("gate_d_d1nh", "scripts/run_gate_d_cosmosweb_residual_dose.py")
d1g = d1nh.d1g
d1m = d1nh.d1m
rec = d1m.rec
d1k = d1m.d1k
d1l = d1m.d1l
inj = rec.inj

SELECTED = d1nh.SELECTED
PARAM_NAMES = ("log_amp_ratio", "dx", "dy", "log_re", "n", "q", "pa")
FD_STEPS = np.array([1e-3, 1e-3, 1e-3, 1e-3, 1e-3, 1e-4, 1e-2], dtype=float)
ALPHA_SMALL = 0.25

def truth_theta():
    log_amp = math.log(inj.ab_to_jy(26.0) / inj.ab_to_jy(27.5))
    return np.array([log_amp, 0.0, 0.0, math.log(6.0), 1.0, 0.65, 30.0], dtype=float)

def target_source(theta7, psf, pixar_sr):
    base_flux_jy = inj.ab_to_jy(27.5)
    base_amp = base_flux_jy / (1e6 * float(pixar_sr))
    p = np.concatenate([np.asarray(theta7, dtype=float), np.zeros(3, dtype=float)])
    return rec._render(p, psf, 0.03, base_amp)

def central_jacobian(theta7, psf, pixar_sr):
    theta7 = np.asarray(theta7, dtype=float)
    cols = []
    for j, step in enumerate(FD_STEPS):
        plus = theta7.copy(); plus[j] += step
        minus = theta7.copy(); minus[j] -= step
        cols.append((target_source(plus, psf, pixar_sr) -
                     target_source(minus, psf, pixar_sr)) / (2.0 * step))
    return np.stack(cols, axis=-1)

def _background_matrix(sigma, valid):
    yy, xx = np.indices((rec.PATCH, rec.PATCH), dtype=float)
    xx = (xx - rec.HALF) / rec.HALF
    yy = (yy - rec.HALF) / rec.HALF
    return np.column_stack([
        (np.ones_like(sigma) / sigma)[valid],
        (xx / sigma)[valid],
        (yy / sigma)[valid],
    ])

def remove_subspace(values, basis):
    """Remove the column space of basis from vector/matrix values."""
    values = np.asarray(values, dtype=float)
    basis = np.asarray(basis, dtype=float)
    coef, _, _, _ = np.linalg.lstsq(basis, values, rcond=None)
    return values - basis @ coef

def tangent_projection(weighted_residual, weighted_jacobian, weighted_background):
    y = remove_subspace(weighted_residual, weighted_background)
    j = remove_subspace(weighted_jacobian, weighted_background)
    delta, _, rank, singular = np.linalg.lstsq(j, y, rcond=None)
    prediction = j @ delta
    ynorm2 = float(y @ y)
    pnorm2 = float(prediction @ prediction)
    frac = pnorm2 / ynorm2 if ynorm2 > 0 else None
    cosines = []
    for k in range(j.shape[1]):
        den = float(np.linalg.norm(j[:, k]) * np.linalg.norm(y))
        cosines.append(float(j[:, k] @ y / den) if den > 0 else None)
    condition = float(singular[0] / singular[-1]) if len(singular) and singular[-1] > 0 else None
    return {
        "background_residualized_residual_l2": float(np.linalg.norm(y)),
        "target_tangent_projection_l2": float(np.linalg.norm(prediction)),
        "target_tangent_power_fraction": frac,
        "rank": int(rank),
        "singular_values": [float(v) for v in singular],
        "condition_number": condition,
        "delta_theta_per_alpha": {name: float(delta[i]) for i, name in enumerate(PARAM_NAMES)},
        "parameter_cosine_alignment": {name: cosines[i] for i, name in enumerate(PARAM_NAMES)},
    }

def row_theta(row):
    """Convert a D1n-h recovery row to the seven target coordinates."""
    delta_mag = float(row["delta_mag"])
    return np.array([
        truth_theta()[0] - 0.4 * math.log(10.0) * delta_mag,
        float(row["recovered_dx_pix"]),
        float(row["recovered_dy_pix"]),
        math.log(float(row["recovered_re_pix"])),
        float(row["recovered_n"]),
        float(row["recovered_q"]),
        float(row["recovered_pa_deg"]),
    ], dtype=float)

def observed_small_dose(dose_summary, cls, idx):
    candidates = [r for r in dose_summary["rows"]
                  if str(r["class"]) == cls and int(r["index"]) == idx
                  and float(r["alpha"]) in (0.0, ALPHA_SMALL)]
    by_alpha = {float(r["alpha"]): r for r in candidates}
    if set(by_alpha) != {0.0, ALPHA_SMALL}:
        raise RuntimeError("D1n-h small-dose rows missing")
    derivative = (row_theta(by_alpha[ALPHA_SMALL]) - row_theta(by_alpha[0.0])) / ALPHA_SMALL
    return {name: float(derivative[i]) for i, name in enumerate(PARAM_NAMES)}

def run(injected_fits: Path, injection_summary: Path, dose_summary_path: Path, out_json: Path):
    summary = json.loads(injection_summary.read_text())
    dose_summary = json.loads(dose_summary_path.read_text())
    if tuple(float(a) for a in dose_summary["alphas"]) != d1nh.ALPHAS:
        raise RuntimeError("D1n-h alpha grid changed")
    matrix = summary["matrix"]
    psf, psf_prov = inj.build_stpsf(matrix, float(matrix["pixel_scale_arcsec"]))
    rows = []
    truth = truth_theta()

    with fits.open(injected_fits, mode="readonly") as h:
        orig = np.asarray(h["SCI_ORIG"].data, dtype=float)
        err = np.asarray(h["ERR"].data, dtype=float)
        labels, bg, scene_mask, deblend = d1k.deblend_scene_components(orig, err)
        catalog = d1l.build_child_catalog(orig, labels, bg)

        for cls, idx, x, y, role in SELECTED:
            prefit = d1m.prefit_neighbour_scene(
                orig, err, labels, catalog, x, y, psf, float(summary["pixar_sr"])
            )
            base = {"class": cls, "index": idx, "x": x, "y": y, "role": role}
            if not prefit.get("finite_solution"):
                rows.append({**base, "finite_prefit": False,
                             "reason": "nonfinite_preinjection_neighbour_prefit"})
                continue
            orig_patch = rec._crop(orig, x, y)
            sigma = rec._crop(err, x, y)
            child_mask = np.asarray(prefit["_child_mask"], dtype=bool)
            valid = np.isfinite(orig_patch) & np.isfinite(sigma) & (sigma > 0) & ~child_mask

            frozen = np.asarray(prefit["_frozen_source"], dtype=float)
            bp = prefit["background_prefit"]
            plane = d1m._plane(np.array([bp["b0"], bp["bx"], bp["by"]], dtype=float))
            residual = orig_patch - frozen - plane

            jac = central_jacobian(truth, psf, float(summary["pixar_sr"]))
            weighted_residual = (residual / sigma)[valid]
            weighted_jac = np.column_stack([(jac[..., k] / sigma)[valid]
                                             for k in range(len(PARAM_NAMES))])
            weighted_bg = _background_matrix(sigma, valid)
            projection = tangent_projection(weighted_residual, weighted_jac, weighted_bg)
            observed = observed_small_dose(dose_summary, cls, idx)
            predicted = projection["delta_theta_per_alpha"]

            comparison = {}
            for name in PARAM_NAMES:
                p = float(predicted[name]); o = float(observed[name])
                comparison[name] = {
                    "predicted_per_alpha": p,
                    "observed_alpha0_to_0p25_per_alpha": o,
                    "same_sign": bool((p == 0 and o == 0) or (p * o > 0)),
                    "observed_minus_predicted": float(o - p),
                }

            rows.append({
                **base,
                "finite_prefit": True,
                "valid_fraction": float(valid.mean()),
                "n_neighbour_models": int(prefit.get("n_neighbour_models", 0)),
                "weighted_residual_l2_before_background_removal": float(np.linalg.norm(weighted_residual)),
                "projection": projection,
                "small_dose_crosscheck": comparison,
            })

    out = {
        "claim": "local first-order ERR-weighted residual / target-tangent identifiability diagnostic; no target recovery refit and no literal survey reproduction claim beyond the inherited real pre-injection residual",
        "selected_rows": [{"class": c, "index": i, "x": x, "y": y, "role": role}
                          for c, i, x, y, role in SELECTED],
        "parameter_names": list(PARAM_NAMES),
        "finite_difference_steps": {name: float(FD_STEPS[i]) for i, name in enumerate(PARAM_NAMES)},
        "truth_theta": {name: float(truth[i]) for i, name in enumerate(PARAM_NAMES)},
        "alpha_small_crosscheck": ALPHA_SMALL,
        "psf_provenance": psf_prov,
        "semantics": {
            "same_d1m_scene_decomposition": True,
            "same_d1m_stpsf": True,
            "same_d1m_err_weighting": True,
            "same_d1m_exact_child_mask": True,
            "planar_background_projected_out": True,
            "target_recovery_refit_performed": False,
            "regularization_applied": False,
            "bounds_changed": False,
            "optimizer_tolerance_changed": False,
            "acceptance_threshold_defined": False,
            "new_noise_added": False,
            "source_shot_noise_added": False,
            "err_or_wht_modified": False,
            "tolman_factor_applied": False,
            "psf_sharpening_performed": False,
            "rank_deficiency_retained": True,
        },
        "rows": rows,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    return out

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--injected-fits", type=Path, required=True)
    p.add_argument("--injection-summary", type=Path, required=True)
    p.add_argument("--dose-summary", type=Path, required=True)
    p.add_argument("--out-json", type=Path, required=True)
    a = p.parse_args()
    out = run(a.injected_fits, a.injection_summary, a.dose_summary, a.out_json)
    print(json.dumps({
        "n_rows": len(out["rows"]),
        "rows": [{
            "role": r.get("role"),
            "target_tangent_power_fraction": r.get("projection", {}).get("target_tangent_power_fraction"),
            "condition_number": r.get("projection", {}).get("condition_number"),
        } for r in out["rows"]],
    }, indent=2))

if __name__ == "__main__":
    main()
