#!/usr/bin/env python3
"""Gate D1n-h: causal residual-dose audit of the frozen D1m objective."""
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

d1g = _load("gate_d_d1ng", "scripts/run_gate_d_cosmosweb_multistart_identifiability.py")
d1m = d1g.d1m
rec = d1m.rec
d1k = d1m.d1k
d1l = d1m.d1l
inj = rec.inj

SELECTED = d1g.SELECTED
ALPHAS = (0.0, 0.25, 0.5, 0.75, 1.0)
START_NAME = "d1m_default"
TARGET_MAX_NFEV = 500

def _patch_insert(base, patch, x, y):
    out = np.array(base, copy=True)
    h = rec.HALF
    out[y-h:y+h+1, x-h:x+h+1] = patch
    return out

def _norms(a):
    x = np.asarray(a, dtype=float)
    return {
        "l1": float(np.sum(np.abs(x))),
        "l2": float(np.sqrt(np.sum(x*x))),
        "rms": float(np.sqrt(np.mean(x*x))),
        "median": float(np.median(x)),
        "mad_sigma": float(1.4826*np.median(np.abs(x-np.median(x)))),
    }

def run(injected_fits: Path, injection_summary: Path, out_json: Path):
    summary = json.loads(injection_summary.read_text())
    matrix = summary["matrix"]
    psf, psf_prov = inj.build_stpsf(matrix, float(matrix["pixel_scale_arcsec"]))
    exps = {(str(e["class"]), int(e["index"])): e for e in summary["experiments"]
            if float(e["ab_mag"]) == 26.0}
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
            if not prefit.get("finite_solution"):
                for alpha in ALPHAS:
                    rows.append({
                        "class": cls, "index": idx, "x": x, "y": y, "role": role,
                        "alpha": alpha, "optimizer_success": False,
                        "finite_solution": False,
                        "reason": "nonfinite_preinjection_neighbour_prefit",
                    })
                continue

            orig_patch = rec._crop(orig, x, y)
            inj_patch = rec._crop(injected, x, y)
            delta = inj_patch - orig_patch
            frozen = np.asarray(prefit["_frozen_source"], dtype=float)
            bp = prefit["background_prefit"]
            plane = d1m._plane(np.array([bp["b0"], bp["bx"], bp["by"]], dtype=float))
            model0 = frozen + plane
            residual = orig_patch - model0
            delta_norms = _norms(delta)
            residual_norms = _norms(residual)

            reconstructed = model0 + delta + residual
            recon_abs_max = float(np.max(np.abs(reconstructed - inj_patch)))
            if not np.allclose(reconstructed, inj_patch, rtol=0.0, atol=2e-7):
                raise RuntimeError("alpha=1 construction does not reconstruct injected patch")

            location_rows = []
            for alpha in ALPHAS:
                patch = model0 + delta + float(alpha) * residual
                image = _patch_insert(injected, patch, x, y)
                fit = d1g.fit_from_start(
                    image, err, x, y, psf, float(summary["pixar_sr"]), prefit, START_NAME
                )
                row = {
                    "class": cls, "index": idx, "x": x, "y": y, "role": role,
                    "ab_mag": 26.0, "output_extname": exp["output_extname"],
                    "alpha": float(alpha), "start_name": START_NAME,
                    "injection_delta_norms": delta_norms,
                    "preinjection_residual_norms": residual_norms,
                    "alpha1_reconstruction_abs_max": recon_abs_max,
                    **fit,
                }
                rows.append(row)
                location_rows.append(row)

            groups.append({
                "class": cls, "index": idx, "x": x, "y": y, "role": role,
                "alphas": [r["alpha"] for r in location_rows],
                "delta_mag": [r.get("delta_mag") for r in location_rows],
                "recovered_re_arcsec": [r.get("recovered_re_arcsec") for r in location_rows],
                "recovered_n": [r.get("recovered_n") for r in location_rows],
                "centroid_excursion_pix": [r.get("centroid_excursion_pix") for r in location_rows],
                "chi2": [r.get("chi2") for r in location_rows],
                "any_bound_hit": [bool(r.get("any_bound_hit")) for r in location_rows],
                "optimizer_success": [bool(r.get("optimizer_success")) for r in location_rows],
            })

    out = {
        "claim": "injection-only causal residual-dose audit; alpha<1 scenes are synthetic diagnostics, while alpha=1 reconstructs the literal D1d injected patch",
        "selected_rows": [{"class": c, "index": i, "x": x, "y": y, "role": role}
                          for c, i, x, y, role in SELECTED],
        "alphas": list(ALPHAS),
        "n_rows": len(rows),
        "psf_provenance": psf_prov,
        "optimizer": {"implementation": "scipy.optimize.least_squares", "method": "trf",
                      "loss": "linear", "x_scale": "jac", "max_nfev": TARGET_MAX_NFEV,
                      "start": START_NAME},
        "semantics": {
            "alpha0_literal_survey_reproduction": False,
            "alpha1_literal_injected_patch_reconstruction": True,
            "intermediate_alpha_synthetic_diagnostic": True,
            "existing_residual_scaled_not_duplicated": True,
            "new_noise_added": False,
            "source_shot_noise_added": False,
            "err_or_wht_modified": False,
            "tolman_factor_applied": False,
            "psf_sharpening_performed": False,
            "same_d1m_scene_decomposition": True,
            "same_d1m_stpsf": True,
            "same_d1m_target_bounds": True,
            "same_d1m_optimizer_budget": True,
            "optimizer_failures_retained": True,
            "bound_hits_retained": True,
            "acceptance_threshold_defined": False,
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
