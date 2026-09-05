#!/usr/bin/env python3
"""Gate D1m: pre-injection fitted, frozen-neighbour scene diagnostic."""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
from scipy import optimize
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "gate_d_d1l",
    ROOT / "scripts" / "run_gate_d_cosmosweb_parametric_neighbour_sersic.py",
)
d1l = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(d1l)
rec = d1l.rec
d1k = d1l.d1k

MAX_NEIGHBOURS = d1l.MAX_NEIGHBOURS
PREFIT_MAX_NFEV = 500
TARGET_MAX_NFEV = 500
TARGET_NAMES = ["log_amp_ratio", "dx", "dy", "log_re", "n", "q", "pa", "b0", "bx", "by"]


def _plane(theta: np.ndarray) -> np.ndarray:
    b0, bx, by = [float(v) for v in theta]
    yy, xx = np.indices((rec.PATCH, rec.PATCH), dtype=float)
    xx = (xx - rec.HALF) / rec.HALF
    yy = (yy - rec.HALF) / rec.HALF
    return b0 + bx * xx + by * yy


def _scene_setup(orig, err, labels, catalog, x, y):
    data = rec._crop(orig, x, y)
    sigma = rec._crop(err, x, y)
    labels_patch = rec._crop(labels, x, y).astype(int)
    selected, masked_labels, child_mask = d1l.select_neighbours(labels_patch, catalog, x, y)
    valid = np.isfinite(data) & np.isfinite(sigma) & (sigma > 0) & ~child_mask
    return data, sigma, selected, masked_labels, child_mask, valid


def prefit_neighbour_scene(orig, err, labels, catalog, x, y, psf, pixar_sr):
    data, sigma, selected, masked_labels, child_mask, valid = _scene_setup(
        orig, err, labels, catalog, x, y
    )
    base = {
        "n_neighbour_models": len(selected),
        "selected_neighbour_labels": [int(m["label"]) for m in selected],
        "selected_neighbour_seed_metadata": selected,
        "masked_child_labels": [int(v) for v in masked_labels],
        "masked_child_pixels": int(child_mask.sum()),
        "target_center_masked": bool(child_mask[rec.HALF, rec.HALF]),
        "valid_fraction": float(valid.mean()),
        "_child_mask": child_mask,
    }
    if valid.sum() < 0.8 * data.size:
        return {
            **base,
            "optimizer_success": False,
            "finite_solution": False,
            "reason": "insufficient_valid_weight_pixels_after_exact_child_mask",
        }

    base_flux_jy = rec.inj.ab_to_jy(27.5)
    base_amp = base_flux_jy / (1e6 * float(pixar_sr))
    med = float(np.nanmedian(data[valid]))
    neigh0 = [d1l.initial_neighbour_theta(m, base_amp) for m in selected]
    p0 = np.concatenate([np.array([med, 0.0, 0.0])] + neigh0) if neigh0 else np.array([med, 0.0, 0.0])
    lo = np.concatenate([np.full(3, -np.inf)] + [d1l.NEIGH_LO] * len(selected))
    hi = np.concatenate([np.full(3, np.inf)] + [d1l.NEIGH_HI] * len(selected))

    def model(p):
        out = _plane(p[:3])
        for j, meta in enumerate(selected):
            k = 3 + 7 * j
            out = out + d1l.render_neighbour(p[k:k+7], meta, psf, base_amp)
        return out

    def residual(p):
        return ((model(p) - data) / sigma)[valid]

    result = optimize.least_squares(
        residual,
        p0,
        bounds=(lo, hi),
        method="trf",
        loss="linear",
        x_scale="jac",
        max_nfev=PREFIT_MAX_NFEV,
    )
    p = result.x
    chi2 = float(np.sum(result.fun**2))
    finite_parameters = bool(np.all(np.isfinite(p)) and np.isfinite(chi2))
    if not finite_parameters:
        return {
            **base,
            "optimizer_success": bool(result.success),
            "optimizer_status": int(result.status),
            "optimizer_message": str(result.message),
            "nfev": int(result.nfev),
            "chi2": chi2,
            "finite_solution": False,
            "reason": "nonfinite_preinjection_neighbour_prefit_parameters",
        }

    nuisance = []
    nuisance_hits = []
    frozen_source = np.zeros_like(data, dtype=float)
    for j, meta in enumerate(selected):
        k = 3 + 7 * j
        vals = p[k:k+7]
        hits = d1l._bound_hits(vals, d1l.NEIGH_LO, d1l.NEIGH_HI, d1l.NEIGH_NAMES)
        nuisance_hits.append({"label": int(meta["label"]), "bound_hits": hits})
        nuisance.append({
            "label": int(meta["label"]),
            "log_amp_ratio": float(vals[0]),
            "dx_from_seed_pix": float(vals[1]),
            "dy_from_seed_pix": float(vals[2]),
            "re_pix": float(math.exp(vals[3])),
            "n": float(vals[4]),
            "q": float(vals[5]),
            "pa_deg": float(vals[6]),
        })
        frozen_source += d1l.render_neighbour(vals, meta, psf, base_amp)

    dof = max(1, int(valid.sum()) - len(p))
    finite = bool(np.all(np.isfinite(frozen_source)))
    return {
        **base,
        "optimizer_success": bool(result.success),
        "optimizer_status": int(result.status),
        "optimizer_message": str(result.message),
        "nfev": int(result.nfev),
        "chi2": chi2,
        "reduced_chi2_proxy": chi2 / dof,
        "finite_solution": finite,
        "background_prefit": {"b0": float(p[0]), "bx": float(p[1]), "by": float(p[2])},
        "nuisance_parameters": nuisance,
        "nuisance_bound_hits": nuisance_hits,
        "any_nuisance_bound_hit": any(bool(v["bound_hits"]) for v in nuisance_hits),
        "_frozen_source": frozen_source,
    }


def fit_target_with_frozen_scene(image, err, x, y, psf, pixar_sr, prefit):
    base = {
        "n_neighbour_models": int(prefit.get("n_neighbour_models", 0)),
        "selected_neighbour_labels": list(prefit.get("selected_neighbour_labels", [])),
        "masked_child_labels": list(prefit.get("masked_child_labels", [])),
        "masked_child_pixels": int(prefit.get("masked_child_pixels", 0)),
        "prefit_optimizer_success": bool(prefit.get("optimizer_success")),
        "prefit_finite_solution": bool(prefit.get("finite_solution")),
        "prefit_any_nuisance_bound_hit": bool(prefit.get("any_nuisance_bound_hit")),
    }
    if not prefit.get("finite_solution"):
        return {
            **base,
            "optimizer_success": False,
            "finite_solution": False,
            "reason": "nonfinite_preinjection_neighbour_prefit",
        }

    data = rec._crop(image, x, y)
    sigma = rec._crop(err, x, y)
    child_mask = np.asarray(prefit["_child_mask"], dtype=bool)
    valid = np.isfinite(data) & np.isfinite(sigma) & (sigma > 0) & ~child_mask
    base["valid_fraction"] = float(valid.mean())
    if valid.sum() < 0.8 * data.size:
        return {
            **base,
            "optimizer_success": False,
            "finite_solution": False,
            "reason": "insufficient_valid_weight_pixels_after_exact_child_mask",
        }

    frozen_source = np.asarray(prefit["_frozen_source"], dtype=float)
    base_flux_jy = rec.inj.ab_to_jy(27.5)
    base_amp = base_flux_jy / (1e6 * float(pixar_sr))
    med = float(np.nanmedian((data - frozen_source)[valid]))
    p0 = np.array([0.0, 0.0, 0.0, math.log(5.0), 1.5, 0.7, 0.0, med, 0.0, 0.0])

    def residual(p):
        model = rec._render(p, psf, 0.03, base_amp) + frozen_source
        return ((model - data) / sigma)[valid]

    result = optimize.least_squares(
        residual,
        p0,
        bounds=(rec.BOUNDS_LO, rec.BOUNDS_HI),
        method="trf",
        loss="linear",
        x_scale="jac",
        max_nfev=TARGET_MAX_NFEV,
    )
    p = result.x
    hits = d1l._bound_hits(p, rec.BOUNDS_LO, rec.BOUNDS_HI, TARGET_NAMES)
    chi2 = float(np.sum(result.fun**2))
    dof = max(1, int(valid.sum()) - len(p))
    amp_total = base_amp * math.exp(float(p[0]))
    flux_jy = amp_total * 1e6 * float(pixar_sr)
    ab = float(-2.5 * math.log10(flux_jy / rec.inj.AB_ZERO_JY)) if flux_jy > 0 else float("nan")
    return {
        **base,
        "optimizer_success": bool(result.success),
        "optimizer_status": int(result.status),
        "optimizer_message": str(result.message),
        "nfev": int(result.nfev),
        "chi2": chi2,
        "reduced_chi2_proxy": chi2 / dof,
        "target_bound_hits": hits,
        "bound_hits": hits,
        "any_bound_hit": bool(hits),
        "recovered_ab_mag": ab,
        "recovered_dx_pix": float(p[1]),
        "recovered_dy_pix": float(p[2]),
        "recovered_re_pix": float(math.exp(p[3])),
        "recovered_re_arcsec": float(math.exp(p[3]) * 0.03),
        "recovered_n": float(p[4]),
        "recovered_q": float(p[5]),
        "recovered_pa_deg": float(p[6]),
        "finite_solution": bool(np.all(np.isfinite(p)) and np.isfinite(chi2)),
    }


def _public_prefit(prefit):
    return {k: v for k, v in prefit.items() if not k.startswith("_")}


def run(injected_fits: Path, injection_summary: Path, out_json: Path):
    summary = json.loads(injection_summary.read_text())
    matrix = summary["matrix"]
    psf, psf_prov = rec.inj.build_stpsf(matrix, float(matrix["pixel_scale_arcsec"]))
    rows = []
    prefits = {}

    with fits.open(injected_fits, mode="readonly") as hdul:
        orig = np.asarray(hdul["SCI_ORIG"].data, dtype=float)
        err = np.asarray(hdul["ERR"].data, dtype=float)
        if (
            orig.shape != err.shape
            or not np.all(np.isfinite(orig))
            or not np.all(np.isfinite(err))
            or not np.all(err > 0)
        ):
            raise ValueError("invalid SCI_ORIG/ERR inputs")
        labels, bg, scene_mask, deblend_meta = d1k.deblend_scene_components(orig, err)
        catalog = d1l.build_child_catalog(orig, labels, bg)

        for exp in summary["experiments"]:
            x, y = int(exp["x"]), int(exp["y"])
            key = (x, y)
            if key not in prefits:
                prefits[key] = prefit_neighbour_scene(
                    orig,
                    err,
                    labels,
                    catalog,
                    x,
                    y,
                    psf,
                    float(summary["pixar_sr"]),
                )
            prefit = prefits[key]
            image = np.asarray(hdul[exp["output_extname"]].data, dtype=float)
            fit = fit_target_with_frozen_scene(
                image,
                err,
                x,
                y,
                psf,
                float(summary["pixar_sr"]),
                prefit,
            )
            row = dict(exp)
            row.update(fit)
            row["prefit_location_key"] = f"{x},{y}"
            row["prefit_reused_between_brightness_levels"] = True
            rows.append(row)

    prefit_rows = []
    for (x, y), prefit in sorted(prefits.items()):
        item = {"x": x, "y": y}
        item.update(_public_prefit(prefit))
        prefit_rows.append(item)

    out = {
        "claim": (
            "two-stage pre-injection fitted/frozen-neighbour diagnostic for synthetic "
            "sources injected into literal real COSMOS-Web mosaic context; not a "
            "production method, not blind detection, not independent cross-code "
            "validation, and not literal survey-source reproduction"
        ),
        "n_experiments": len(rows),
        "n_unique_prefit_locations": len(prefit_rows),
        "patch_pixels": rec.PATCH,
        "psf_provenance": psf_prov,
        "scene_components": {
            "same_detection_and_deblending_as_d1k_d1l": True,
            "background_median": float(bg),
            "global_mask_fraction": float(scene_mask.mean()),
            "deblending": deblend_meta,
            "child_catalog_count": len(catalog),
        },
        "frozen_design": {
            "maximum_neighbour_models_per_patch": MAX_NEIGHBOURS,
            "prefit_on_sci_orig": True,
            "prefit_reused_for_ab26_and_ab29_at_same_location": True,
            "neighbour_parameters_frozen_during_target_fit": True,
            "prefit_background_frozen_during_target_fit": False,
            "remaining_children_exact_support_masked": True,
            "segmentation_or_support_tuning": False,
            "same_declared_stpsf_as_d1l": True,
            "literal_effective_cosmosweb_psf_claimed": False,
        },
        "target_bounds": {
            "centroid_offset_pix": [-2, 2],
            "re_pix": [1, 20],
            "n": [0.3, 6],
            "q": [0.2, 1],
            "pa_deg": [-90, 90],
            "amplitude_positive": True,
        },
        "optimizer": {
            "implementation": "scipy.optimize.least_squares",
            "method": "trf",
            "loss": "linear",
            "x_scale": "jac",
            "prefit_max_nfev": PREFIT_MAX_NFEV,
            "target_max_nfev": TARGET_MAX_NFEV,
        },
        "semantics": {
            "target_bounds_changed": False,
            "tolman_factor_applied": False,
            "extra_background_added": False,
            "source_shot_noise_added": False,
            "err_or_wht_modified": False,
            "psf_sharpening_performed": False,
            "low_snr_failures_retained": True,
            "prefit_failures_retained": True,
            "target_bound_hits_retained": True,
            "nuisance_bound_hits_retained": True,
            "scientific_success_claimed": False,
        },
        "preinjection_prefits": prefit_rows,
        "experiments": rows,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--injected-fits", type=Path, required=True)
    parser.add_argument("--injection-summary", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    args = parser.parse_args()
    out = run(args.injected_fits, args.injection_summary, args.out_json)
    print(
        json.dumps(
            {
                "n_experiments": out["n_experiments"],
                "n_unique_prefit_locations": out["n_unique_prefit_locations"],
                "prefit_success": sum(
                    bool(r.get("optimizer_success")) for r in out["preinjection_prefits"]
                ),
                "prefit_nuisance_bound_hits": sum(
                    bool(r.get("any_nuisance_bound_hit")) for r in out["preinjection_prefits"]
                ),
                "target_optimizer_success": sum(
                    bool(r.get("optimizer_success")) for r in out["experiments"]
                ),
                "target_bound_hits": sum(
                    bool(r.get("any_bound_hit")) for r in out["experiments"]
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
