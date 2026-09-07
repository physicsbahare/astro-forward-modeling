#!/usr/bin/env python3
"""Gate D1n-j: causal split of the real residual into tangent and orthogonal parts."""
from __future__ import annotations
import argparse, importlib.util, json, sys
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

d1ni = _load("gate_d_d1ni", "scripts/run_gate_d_cosmosweb_residual_tangent.py")
d1nh = d1ni.d1nh
d1g = d1nh.d1g
d1m = d1ni.d1m
rec = d1ni.rec
d1k = d1ni.d1k
d1l = d1ni.d1l
inj = d1ni.inj

SELECTED = d1ni.SELECTED
MODES = ("none", "tangent_only", "orthogonal_only", "background_residualized_full", "original_full")
START_NAME = d1nh.START_NAME
TARGET_MAX_NFEV = d1nh.TARGET_MAX_NFEV

def _patch_insert(base, patch, x, y):
    out = np.array(base, copy=True)
    h = rec.HALF
    out[y-h:y+h+1, x-h:x+h+1] = patch
    return out

def decompose(weighted_residual, weighted_jacobian, weighted_background):
    y = d1ni.remove_subspace(weighted_residual, weighted_background)
    j = d1ni.remove_subspace(weighted_jacobian, weighted_background)
    delta, _, rank, singular = np.linalg.lstsq(j, y, rcond=None)
    tangent = j @ delta
    orthogonal = y - tangent
    return {
        "background_residualized": y,
        "jacobian": j,
        "tangent": tangent,
        "orthogonal": orthogonal,
        "delta": delta,
        "rank": int(rank),
        "singular": singular,
    }

def _component_patch(injected_patch, model0, delta_image, sigma, valid, mode, weighted_residual, parts):
    patch = np.array(injected_patch, copy=True)
    baseline = model0 + delta_image
    if mode == "none":
        weighted = np.zeros_like(weighted_residual)
    elif mode == "tangent_only":
        weighted = parts["tangent"]
    elif mode == "orthogonal_only":
        weighted = parts["orthogonal"]
    elif mode == "background_residualized_full":
        weighted = parts["background_residualized"]
    elif mode == "original_full":
        weighted = weighted_residual
    else:
        raise ValueError(mode)
    patch[valid] = baseline[valid] + sigma[valid] * weighted
    return patch, weighted

def run(injected_fits: Path, injection_summary: Path, out_json: Path):
    summary = json.loads(injection_summary.read_text())
    matrix = summary["matrix"]
    psf, psf_prov = inj.build_stpsf(matrix, float(matrix["pixel_scale_arcsec"]))
    exps = {(str(e["class"]), int(e["index"])): e for e in summary["experiments"]
            if float(e["ab_mag"]) == 26.0}
    truth = d1ni.truth_theta()
    rows, groups = [], []

    with fits.open(injected_fits, mode="readonly") as h:
        orig = np.asarray(h["SCI_ORIG"].data, dtype=float)
        err = np.asarray(h["ERR"].data, dtype=float)
        labels, bg, scene_mask, deblend = d1k.deblend_scene_components(orig, err)
        catalog = d1l.build_child_catalog(orig, labels, bg)

        for cls, idx, x, y, role in SELECTED:
            exp = exps[(cls, idx)]
            if int(exp["x"]) != x or int(exp["y"]) != y:
                raise RuntimeError("frozen selected coordinate changed")
            injected = np.asarray(h[exp["output_extname"]].data, dtype=float)
            prefit = d1m.prefit_neighbour_scene(
                orig, err, labels, catalog, x, y, psf, float(summary["pixar_sr"])
            )
            base = {"class": cls, "index": idx, "x": x, "y": y, "role": role}
            if not prefit.get("finite_solution"):
                for mode in MODES:
                    rows.append({**base, "mode": mode, "optimizer_success": False,
                                 "finite_solution": False,
                                 "reason": "nonfinite_preinjection_neighbour_prefit"})
                continue

            orig_patch = rec._crop(orig, x, y)
            inj_patch = rec._crop(injected, x, y)
            sigma = rec._crop(err, x, y)
            child_mask = np.asarray(prefit["_child_mask"], dtype=bool)
            valid = np.isfinite(orig_patch) & np.isfinite(sigma) & (sigma > 0) & ~child_mask

            frozen = np.asarray(prefit["_frozen_source"], dtype=float)
            bp = prefit["background_prefit"]
            plane = d1m._plane(np.array([bp["b0"], bp["bx"], bp["by"]], dtype=float))
            model0 = frozen + plane
            residual = orig_patch - model0
            delta_image = inj_patch - orig_patch

            jac = d1ni.central_jacobian(truth, psf, float(summary["pixar_sr"]))
            weighted_residual = (residual / sigma)[valid]
            weighted_jac = np.column_stack([(jac[..., k] / sigma)[valid]
                                             for k in range(len(d1ni.PARAM_NAMES))])
            weighted_bg = d1ni._background_matrix(sigma, valid)
            parts = decompose(weighted_residual, weighted_jac, weighted_bg)

            tangent = parts["tangent"]
            orthogonal = parts["orthogonal"]
            bgfree = parts["background_residualized"]
            identity_max = float(np.max(np.abs((tangent + orthogonal) - bgfree)))
            orthogonality_max = float(np.max(np.abs(parts["jacobian"].T @ orthogonal)))
            original_recon = model0 + delta_image + residual
            original_recon_abs_max = float(np.max(np.abs((original_recon - inj_patch)[valid])))
            if identity_max > 1e-10:
                raise RuntimeError("tangent + orthogonal identity failed")
            if original_recon_abs_max > 2e-7:
                raise RuntimeError("original residual does not reconstruct injected patch")

            component_power = {
                "original_full": float(weighted_residual @ weighted_residual),
                "background_residualized_full": float(bgfree @ bgfree),
                "tangent_only": float(tangent @ tangent),
                "orthogonal_only": float(orthogonal @ orthogonal),
                "none": 0.0,
            }
            location_rows = []
            for mode in MODES:
                patch, weighted_component = _component_patch(
                    inj_patch, model0, delta_image, sigma, valid, mode,
                    weighted_residual, parts
                )
                image = _patch_insert(injected, patch, x, y)
                fit = d1g.fit_from_start(
                    image, err, x, y, psf, float(summary["pixar_sr"]), prefit, START_NAME
                )
                row = {
                    **base,
                    "ab_mag": 26.0,
                    "mode": mode,
                    "start_name": START_NAME,
                    "component_weighted_power": component_power[mode],
                    "component_weighted_l2": float(np.linalg.norm(weighted_component)),
                    "tangent_plus_orthogonal_identity_abs_max": identity_max,
                    "orthogonal_jacobian_inner_product_abs_max": orthogonality_max,
                    "original_full_reconstruction_abs_max_valid": original_recon_abs_max,
                    **fit,
                }
                rows.append(row)
                location_rows.append(row)

            groups.append({
                **base,
                "valid_fraction": float(valid.mean()),
                "tangent_rank": parts["rank"],
                "tangent_condition_number": float(parts["singular"][0] / parts["singular"][-1]),
                "original_weighted_power": component_power["original_full"],
                "background_residualized_weighted_power": component_power["background_residualized_full"],
                "tangent_weighted_power": component_power["tangent_only"],
                "orthogonal_weighted_power": component_power["orthogonal_only"],
                "tangent_power_fraction_of_background_residualized": (
                    component_power["tangent_only"] / component_power["background_residualized_full"]
                    if component_power["background_residualized_full"] > 0 else None
                ),
                "modes": [r["mode"] for r in location_rows],
                "delta_mag": [r.get("delta_mag") for r in location_rows],
                "recovered_re_arcsec": [r.get("recovered_re_arcsec") for r in location_rows],
                "recovered_n": [r.get("recovered_n") for r in location_rows],
                "centroid_excursion_pix": [r.get("centroid_excursion_pix") for r in location_rows],
                "chi2": [r.get("chi2") for r in location_rows],
                "any_bound_hit": [bool(r.get("any_bound_hit")) for r in location_rows],
                "optimizer_success": [bool(r.get("optimizer_success")) for r in location_rows],
            })

    out = {
        "claim": "injection-only causal split of the frozen real pre-injection residual into local target-tangent and orthogonal components; not a production residual correction or literal reproduction of another survey observation",
        "selected_rows": [{"class": c, "index": i, "x": x, "y": y, "role": role}
                          for c, i, x, y, role in SELECTED],
        "modes": list(MODES),
        "n_rows": len(rows),
        "psf_provenance": psf_prov,
        "optimizer": {"implementation": "scipy.optimize.least_squares", "method": "trf",
                      "loss": "linear", "x_scale": "jac", "max_nfev": TARGET_MAX_NFEV,
                      "start": START_NAME},
        "semantics": {
            "same_d1m_scene_decomposition": True,
            "same_d1m_stpsf": True,
            "same_d1m_err_weighting": True,
            "same_d1m_exact_child_mask": True,
            "same_d1m_target_bounds": True,
            "same_d1m_optimizer_budget": True,
            "same_d1ni_finite_difference_steps": True,
            "planar_background_subspace_removed_before_split": True,
            "regularization_applied": False,
            "jacobian_columns_dropped": False,
            "new_noise_added": False,
            "source_shot_noise_added": False,
            "err_or_wht_modified": False,
            "tolman_factor_applied": False,
            "psf_sharpening_performed": False,
            "optimizer_failures_retained": True,
            "bound_hits_retained": True,
            "acceptance_threshold_defined": False,
            "component_scenes_except_original_full_are_synthetic_diagnostics": True,
            "original_full_reconstructs_literal_d1d_injected_valid_pixels": True,
        },
        "groups": groups,
        "rows": rows,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    return out

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--injected-fits", type=Path, required=True)
    p.add_argument("--injection-summary", type=Path, required=True)
    p.add_argument("--out-json", type=Path, required=True)
    a = p.parse_args()
    out = run(a.injected_fits, a.injection_summary, a.out_json)
    print(json.dumps({
        "n_rows": out["n_rows"],
        "groups": out["groups"],
        "bound_hits": sum(bool(r.get("any_bound_hit")) for r in out["rows"]),
        "optimizer_failures": sum(not bool(r.get("optimizer_success")) for r in out["rows"]),
    }, indent=2))

if __name__ == "__main__":
    main()
