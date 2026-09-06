#!/usr/bin/env python3
"""Gate D1n-g: deterministic multistart audit of the frozen D1m real-scene objective."""
from __future__ import annotations
import argparse, importlib.util, json, math, sys
from pathlib import Path
import numpy as np
from scipy import optimize
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

d1m = _load("gate_d_d1m", "scripts/run_gate_d_cosmosweb_frozen_prefit_neighbour_scene.py")
rec = d1m.rec
d1k = d1m.d1k
d1l = d1m.d1l
inj = rec.inj
TARGET_MAX_NFEV = 500
TARGET_NAMES = d1m.TARGET_NAMES
SELECTED = (
    ("near_source_2_5", 0, 168, 66, "catastrophic"),
    ("relatively_isolated_ge30", 1, 69, 195, "catastrophic"),
    ("near_source_2_5", 1, 379, 254, "control"),
    ("relatively_isolated_ge30", 0, 358, 97, "control"),
)
TRUTH_LOG_RATIO = math.log(inj.ab_to_jy(26.0) / inj.ab_to_jy(27.5))
STARTS = {
    "d1m_default": (0.0, 0.0, 0.0, math.log(5.0), 1.5, 0.7, 0.0),
    "disk_compact": (0.0, 0.0, 0.0, math.log(3.0), 1.0, 0.65, 30.0),
    "disk_extended": (0.0, 0.0, 0.0, math.log(10.0), 1.0, 0.65, 30.0),
    "high_n_extended": (0.0, 0.0, 0.0, math.log(10.0), 3.5, 0.8, 0.0),
    "injection_truth_oracle": (TRUTH_LOG_RATIO, 0.0, 0.0, math.log(6.0), 1.0, 0.65, 30.0),
}

def fit_from_start(image, err, x, y, psf, pixar_sr, prefit, start_name):
    base = {
        "start_name": start_name,
        "prefit_optimizer_success": bool(prefit.get("optimizer_success")),
        "prefit_finite_solution": bool(prefit.get("finite_solution")),
        "prefit_any_nuisance_bound_hit": bool(prefit.get("any_nuisance_bound_hit")),
    }
    if not prefit.get("finite_solution"):
        return {**base, "optimizer_success": False, "finite_solution": False,
                "reason": "nonfinite_preinjection_neighbour_prefit"}
    data = rec._crop(image, x, y)
    sigma = rec._crop(err, x, y)
    child_mask = np.asarray(prefit["_child_mask"], dtype=bool)
    valid = np.isfinite(data) & np.isfinite(sigma) & (sigma > 0) & ~child_mask
    base["valid_fraction"] = float(valid.mean())
    if valid.sum() < 0.8 * data.size:
        return {**base, "optimizer_success": False, "finite_solution": False,
                "reason": "insufficient_valid_weight_pixels_after_exact_child_mask"}
    frozen = np.asarray(prefit["_frozen_source"], dtype=float)
    base_flux_jy = inj.ab_to_jy(27.5)
    base_amp = base_flux_jy / (1e6 * float(pixar_sr))
    med = float(np.nanmedian((data - frozen)[valid]))
    target = np.asarray(STARTS[start_name], dtype=float)
    p0 = np.concatenate([target, np.array([med, 0.0, 0.0])])
    if np.any(p0 < rec.BOUNDS_LO) or np.any(p0 > rec.BOUNDS_HI):
        raise RuntimeError("frozen start outside target bounds")

    def residual(p):
        model = rec._render(p, psf, 0.03, base_amp) + frozen
        return ((model - data) / sigma)[valid]

    result = optimize.least_squares(
        residual, p0, bounds=(rec.BOUNDS_LO, rec.BOUNDS_HI), method="trf",
        loss="linear", x_scale="jac", max_nfev=TARGET_MAX_NFEV,
    )
    p = result.x
    chi2 = float(np.sum(result.fun ** 2))
    dof = max(1, int(valid.sum()) - len(p))
    hits = d1l._bound_hits(p, rec.BOUNDS_LO, rec.BOUNDS_HI, TARGET_NAMES)
    amp_total = base_amp * math.exp(float(p[0]))
    flux_jy = amp_total * 1e6 * float(pixar_sr)
    ab = float(-2.5 * math.log10(flux_jy / inj.AB_ZERO_JY)) if flux_jy > 0 else float("nan")
    return {
        **base,
        "optimizer_success": bool(result.success), "optimizer_status": int(result.status),
        "optimizer_message": str(result.message), "nfev": int(result.nfev),
        "chi2": chi2, "reduced_chi2_proxy": chi2 / dof,
        "target_bound_hits": hits, "any_bound_hit": bool(hits),
        "finite_solution": bool(np.all(np.isfinite(p)) and np.isfinite(chi2)),
        "recovered_ab_mag": ab, "delta_mag": ab - 26.0,
        "recovered_dx_pix": float(p[1]), "recovered_dy_pix": float(p[2]),
        "centroid_excursion_pix": float(math.hypot(p[1], p[2])),
        "recovered_re_pix": float(math.exp(p[3])), "recovered_re_arcsec": float(math.exp(p[3]) * 0.03),
        "recovered_n": float(p[4]), "recovered_q": float(p[5]), "recovered_pa_deg": float(p[6]),
        "initial_target": dict(zip(TARGET_NAMES[:7], [float(v) for v in target])),
    }

def run(injected_fits: Path, injection_summary: Path, out_json: Path):
    summary = json.loads(injection_summary.read_text())
    matrix = summary["matrix"]
    psf, psf_prov = inj.build_stpsf(matrix, float(matrix["pixel_scale_arcsec"]))
    exps = {(str(e["class"]), int(e["index"])): e for e in summary["experiments"] if float(e["ab_mag"]) == 26.0}
    rows = []
    with fits.open(injected_fits, mode="readonly") as h:
        orig = np.asarray(h["SCI_ORIG"].data, dtype=float)
        err = np.asarray(h["ERR"].data, dtype=float)
        labels, bg, scene_mask, deblend = d1k.deblend_scene_components(orig, err)
        catalog = d1l.build_child_catalog(orig, labels, bg)
        for cls, idx, x, y, role in SELECTED:
            exp = exps[(cls, idx)]
            if int(exp["x"]) != x or int(exp["y"]) != y:
                raise RuntimeError("frozen selected coordinate changed")
            prefit = d1m.prefit_neighbour_scene(
                orig, err, labels, catalog, x, y, psf, float(summary["pixar_sr"])
            )
            image = np.asarray(h[exp["output_extname"]].data, dtype=float)
            for name in STARTS:
                fit = fit_from_start(image, err, x, y, psf, float(summary["pixar_sr"]), prefit, name)
                rows.append({"class": cls, "index": idx, "x": x, "y": y, "role": role,
                             "ab_mag": 26.0, "output_extname": exp["output_extname"], **fit})
    groups = []
    for cls, idx, x, y, role in SELECTED:
        g = [r for r in rows if r["class"] == cls and r["index"] == idx]
        finite = [r for r in g if r.get("optimizer_success") and r.get("finite_solution")
                  and np.isfinite(r.get("chi2", np.nan))]
        best = min(finite, key=lambda r: r["chi2"]) if finite else None
        bestchi = best["chi2"] if best else None
        for r in g:
            r["delta_chi2_from_best"] = (
                float(r["chi2"] - bestchi)
                if bestchi is not None and np.isfinite(r.get("chi2", np.nan)) else None
            )
        groups.append({"class": cls, "index": idx, "x": x, "y": y, "role": role,
                       "best_start": best["start_name"] if best else None,
                       "best_chi2": bestchi, "n_successful_finite_starts": len(finite)})
    out = {
        "claim": "deterministic multistart audit of the unchanged D1m real-scene target objective; injection-truth start is an oracle only, not a production initialization policy",
        "selected_rows": [{"class": c, "index": i, "x": x, "y": y, "role": role}
                          for c, i, x, y, role in SELECTED],
        "starts": {k: list(v) for k, v in STARTS.items()}, "n_rows": len(rows),
        "psf_provenance": psf_prov,
        "optimizer": {"implementation": "scipy.optimize.least_squares", "method": "trf",
                      "loss": "linear", "x_scale": "jac", "max_nfev": TARGET_MAX_NFEV},
        "target_bounds": {"centroid_offset_pix": [-2, 2], "re_pix": [1, 20], "n": [0.3, 6],
                          "q": [0.2, 1], "pa_deg": [-90, 90], "amplitude_positive": True},
        "semantics": {"same_d1m_scene_decomposition": True, "same_d1m_stpsf": True,
                      "same_d1m_err_weighting": True, "same_d1m_target_bounds": True,
                      "same_d1m_objective": True, "same_d1m_max_nfev": True,
                      "truth_start_injection_oracle_only": True, "random_restart_used": False,
                      "posthoc_start_added": False, "noise_added": False,
                      "err_or_wht_modified": False, "tolman_factor_applied": False,
                      "psf_sharpening_performed": False, "optimizer_failures_retained": True,
                      "bound_hits_retained": True, "acceptance_threshold_defined": False},
        "groups": groups, "rows": rows,
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
    print(json.dumps({"n_rows": out["n_rows"], "groups": out["groups"],
                      "bound_hits": sum(bool(r.get("any_bound_hit")) for r in out["rows"]),
                      "optimizer_failures": sum(not bool(r.get("optimizer_success")) for r in out["rows"])}, indent=2))

if __name__ == "__main__":
    main()
