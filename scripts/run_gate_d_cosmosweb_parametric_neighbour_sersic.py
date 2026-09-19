#!/usr/bin/env python3
"""Gate D1l: limited simultaneous parametric-neighbour Sérsic diagnostic.

This is deliberately a pre-production scene-modelling diagnostic.  It reuses
D1k's frozen pre-injection detection/deblending and D1e's target renderer,
bounds, ERR weighting, background plane, and linear loss.  Only up to the
three nearest deblended neighbours gain free PSF-convolved Sérsic morphology.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
from scipy import ndimage, optimize
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
KSPEC = importlib.util.spec_from_file_location(
    "gate_d_d1k",
    ROOT / "scripts" / "run_gate_d_cosmosweb_deblended_neighbour_templates.py",
)
d1k = importlib.util.module_from_spec(KSPEC)
KSPEC.loader.exec_module(d1k)
rec = d1k.d1h.rec

MAX_NEIGHBOURS = 3
MAX_NFEV = 500
SEED_MIN_SIGMA_PIX = 0.5
GAUSSIAN_HALF_LIGHT_PER_SIGMA = math.sqrt(2.0 * math.log(2.0))

NEIGH_LO = np.array(
    [math.log(1e-4), -2.0, -2.0, math.log(1.0), 0.3, 0.2, -90.0],
    dtype=float,
)
NEIGH_HI = np.array(
    [math.log(1e4), 2.0, 2.0, math.log(20.0), 6.0, 1.0, 90.0],
    dtype=float,
)
NEIGH_NAMES = ["log_amp_ratio", "dx", "dy", "log_re", "n", "q", "pa"]


def _wrap_pa_deg(pa: float) -> float:
    """Wrap an ellipse position angle to the frozen [-90, 90) interval."""
    return float((float(pa) + 90.0) % 180.0 - 90.0)


def build_child_catalog(orig: np.ndarray, labels: np.ndarray, bg: float) -> dict[int, dict]:
    """Measure pre-injection positive-core moments for every deblended child."""
    if orig.shape != labels.shape:
        raise ValueError("orig/labels shape mismatch")
    signal = np.maximum(np.asarray(orig, dtype=float) - float(bg), 0.0)
    yy, xx = np.indices(orig.shape, dtype=float)
    catalog: dict[int, dict] = {}

    for label in np.unique(labels):
        label = int(label)
        if label <= 0:
            continue
        core = labels == label
        w = signal[core]
        sw = float(np.sum(w))
        if not np.isfinite(sw) or sw <= 0:
            continue
        xc = float(np.sum(w * xx[core]) / sw)
        yc = float(np.sum(w * yy[core]) / sw)
        dx = xx[core] - xc
        dy = yy[core] - yc
        cxx = float(np.sum(w * dx * dx) / sw)
        cyy = float(np.sum(w * dy * dy) / sw)
        cxy = float(np.sum(w * dx * dy) / sw)
        cov = np.array([[cxx, cxy], [cxy, cyy]], dtype=float)
        vals, vecs = np.linalg.eigh(cov)
        vals = np.maximum(vals, SEED_MIN_SIGMA_PIX**2)
        minor_var, major_var = float(vals[0]), float(vals[1])
        major_vec = vecs[:, 1]
        sigma_minor = math.sqrt(minor_var)
        sigma_major = math.sqrt(major_var)
        q0 = float(np.clip(sigma_minor / sigma_major, 0.2, 1.0))
        re0 = float(np.clip(GAUSSIAN_HALF_LIGHT_PER_SIGMA * sigma_major, 1.0, 20.0))
        pa0 = _wrap_pa_deg(math.degrees(math.atan2(float(major_vec[1]), float(major_vec[0]))))
        catalog[label] = {
            "label": label,
            "core_pixels": int(core.sum()),
            "core_positive_sum_mjysr_pixels": sw,
            "centroid_x": xc,
            "centroid_y": yc,
            "sigma_minor_pix_seed": sigma_minor,
            "sigma_major_pix_seed": sigma_major,
            "re_pix_seed": re0,
            "q_seed": q0,
            "pa_deg_seed": pa0,
        }
    return catalog


def select_neighbours(
    labels_patch: np.ndarray,
    catalog: dict[int, dict],
    x_target: int,
    y_target: int,
) -> tuple[list[dict], list[int], np.ndarray]:
    """Select the three nearest in-patch child centroids; exact-mask the rest."""
    overlapping = sorted(int(v) for v in np.unique(labels_patch) if int(v) > 0)
    candidates = []
    unselected = []

    for label in overlapping:
        meta = catalog.get(label)
        if meta is None:
            unselected.append(label)
            continue
        ox = float(meta["centroid_x"]) - float(x_target)
        oy = float(meta["centroid_y"]) - float(y_target)
        if abs(ox) <= rec.HALF and abs(oy) <= rec.HALF:
            m = dict(meta)
            m["offset_x_pix_seed"] = ox
            m["offset_y_pix_seed"] = oy
            m["distance_to_target_pix"] = float(math.hypot(ox, oy))
            candidates.append(m)
        else:
            unselected.append(label)

    candidates.sort(key=lambda m: (m["distance_to_target_pix"], m["label"]))
    selected = candidates[:MAX_NEIGHBOURS]
    unselected.extend(int(m["label"]) for m in candidates[MAX_NEIGHBOURS:])
    unselected = sorted(set(unselected))
    exact_mask = np.isin(labels_patch, unselected)
    return selected, unselected, exact_mask


def _inside_clip(value: float, lo: float, hi: float) -> float:
    """Clip an initial value slightly inside finite optimizer bounds."""
    eps = 1e-7 * max(1.0, abs(hi - lo))
    return float(np.clip(value, lo + eps, hi - eps))


def initial_neighbour_theta(meta: dict, base_amp: float) -> np.ndarray:
    """Build the frozen moment-based initial point for one nuisance component."""
    ratio = float(meta["core_positive_sum_mjysr_pixels"]) / float(base_amp)
    log_ratio = math.log(max(ratio, 1e-300))
    p = np.array(
        [
            _inside_clip(log_ratio, NEIGH_LO[0], NEIGH_HI[0]),
            0.0,
            0.0,
            _inside_clip(math.log(float(meta["re_pix_seed"])), NEIGH_LO[3], NEIGH_HI[3]),
            1.0,
            _inside_clip(float(meta["q_seed"]), NEIGH_LO[5], NEIGH_HI[5]),
            _inside_clip(float(meta["pa_deg_seed"]), NEIGH_LO[6], NEIGH_HI[6]),
        ],
        dtype=float,
    )
    return p


def render_neighbour(theta: np.ndarray, meta: dict, psf: np.ndarray, base_amp: float) -> np.ndarray:
    """Render one nuisance Sérsic component into the target-centered 65x65 patch."""
    log_ratio, ddx, ddy, log_re, n, q, pa = [float(v) for v in theta]
    profile = rec.inj.sersic_profile(129, math.exp(log_re), n, q, pa, 4)
    model = rec.inj.convolve_normalized(profile, psf)
    shift_x = float(meta["offset_x_pix_seed"]) + ddx
    shift_y = float(meta["offset_y_pix_seed"]) + ddy
    model = ndimage.shift(
        model,
        shift=(shift_y, shift_x),
        order=1,
        mode="constant",
        cval=0.0,
        prefilter=False,
    )
    floor = -1e-12 * max(1.0, float(np.max(model)))
    if float(np.min(model)) < floor:
        raise ValueError("neighbour shift produced material negative flux")
    model = np.maximum(model, 0.0)
    c = model.shape[0] // 2
    patch = model[c - rec.HALF : c + rec.HALF + 1, c - rec.HALF : c + rec.HALF + 1]
    return patch * (float(base_amp) * math.exp(log_ratio))


def _bound_hits(values: np.ndarray, lo: np.ndarray, hi: np.ndarray, names: list[str]) -> list[str]:
    tol = 1e-5
    hits = []
    for i, name in enumerate(names):
        if np.isfinite(lo[i]) and np.isfinite(hi[i]):
            span = hi[i] - lo[i]
            if values[i] - lo[i] <= tol * span or hi[i] - values[i] <= tol * span:
                hits.append(name)
    return hits


def fit_one(
    image: np.ndarray,
    err: np.ndarray,
    orig: np.ndarray,
    labels: np.ndarray,
    child_catalog: dict[int, dict],
    x: int,
    y: int,
    psf: np.ndarray,
    pixar_sr: float,
) -> dict:
    data = rec._crop(image, x, y)
    sigma = rec._crop(err, x, y)
    labels_patch = rec._crop(labels, x, y).astype(int)

    selected, masked_labels, child_mask = select_neighbours(labels_patch, child_catalog, x, y)
    valid = np.isfinite(data) & np.isfinite(sigma) & (sigma > 0) & ~child_mask
    base_result = {
        "n_neighbour_models": len(selected),
        "selected_neighbour_labels": [int(m["label"]) for m in selected],
        "selected_neighbour_seed_metadata": selected,
        "masked_child_labels": [int(v) for v in masked_labels],
        "masked_child_pixels": int(child_mask.sum()),
        "target_center_masked": bool(child_mask[rec.HALF, rec.HALF]),
        "valid_fraction": float(valid.mean()),
    }
    if valid.sum() < 0.8 * data.size:
        return {
            **base_result,
            "optimizer_success": False,
            "finite_solution": False,
            "reason": "insufficient_valid_weight_pixels_after_exact_child_mask",
        }

    base_flux_jy = rec.inj.ab_to_jy(27.5)
    base_amp = base_flux_jy / (1e6 * float(pixar_sr))
    med = float(np.nanmedian(data[valid]))
    target0 = np.array([0.0, 0.0, 0.0, math.log(5.0), 1.5, 0.7, 0.0, med, 0.0, 0.0])
    neigh0 = [initial_neighbour_theta(m, base_amp) for m in selected]
    p0 = np.concatenate([target0] + neigh0) if neigh0 else target0.copy()
    lo = np.concatenate([rec.BOUNDS_LO] + [NEIGH_LO] * len(selected))
    hi = np.concatenate([rec.BOUNDS_HI] + [NEIGH_HI] * len(selected))

    def model(p: np.ndarray) -> np.ndarray:
        out = rec._render(p[:10], psf, 0.03, base_amp)
        for j, meta in enumerate(selected):
            k = 10 + 7 * j
            out = out + render_neighbour(p[k : k + 7], meta, psf, base_amp)
        return out

    def residual(p: np.ndarray) -> np.ndarray:
        return ((model(p) - data) / sigma)[valid]

    result = optimize.least_squares(
        residual,
        p0,
        bounds=(lo, hi),
        method="trf",
        loss="linear",
        x_scale="jac",
        max_nfev=MAX_NFEV,
    )
    p = result.x
    target_names = ["log_amp_ratio", "dx", "dy", "log_re", "n", "q", "pa", "b0", "bx", "by"]
    target_hits = _bound_hits(p[:10], rec.BOUNDS_LO, rec.BOUNDS_HI, target_names)
    nuisance_hits = []
    nuisance_params = []
    for j, meta in enumerate(selected):
        k = 10 + 7 * j
        vals = p[k : k + 7]
        hits = _bound_hits(vals, NEIGH_LO, NEIGH_HI, NEIGH_NAMES)
        nuisance_hits.append({"label": int(meta["label"]), "bound_hits": hits})
        nuisance_params.append(
            {
                "label": int(meta["label"]),
                "log_amp_ratio": float(vals[0]),
                "dx_from_seed_pix": float(vals[1]),
                "dy_from_seed_pix": float(vals[2]),
                "re_pix": float(math.exp(vals[3])),
                "n": float(vals[4]),
                "q": float(vals[5]),
                "pa_deg": float(vals[6]),
            }
        )

    dof = max(1, int(valid.sum()) - len(p))
    chi2 = float(np.sum(result.fun**2))
    amp_total = base_amp * math.exp(float(p[0]))
    flux_jy = amp_total * 1e6 * float(pixar_sr)
    ab = (
        float(-2.5 * math.log10(flux_jy / rec.inj.AB_ZERO_JY))
        if flux_jy > 0
        else float("nan")
    )
    return {
        **base_result,
        "optimizer_success": bool(result.success),
        "optimizer_status": int(result.status),
        "optimizer_message": str(result.message),
        "nfev": int(result.nfev),
        "chi2": chi2,
        "reduced_chi2_proxy": chi2 / dof,
        "target_bound_hits": target_hits,
        "bound_hits": target_hits,
        "any_bound_hit": bool(target_hits),
        "nuisance_bound_hits": nuisance_hits,
        "any_nuisance_bound_hit": any(bool(v["bound_hits"]) for v in nuisance_hits),
        "nuisance_parameters": nuisance_params,
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


def run(injected_fits: Path, injection_summary: Path, out_json: Path) -> dict:
    summary = json.loads(injection_summary.read_text())
    matrix = summary["matrix"]
    psf, psf_prov = rec.inj.build_stpsf(matrix, float(matrix["pixel_scale_arcsec"]))
    rows = []

    with fits.open(injected_fits, mode="readonly") as hdul:
        orig = np.asarray(hdul["SCI_ORIG"].data, dtype=float)
        err = np.asarray(hdul["ERR"].data, dtype=float)
        if orig.shape != err.shape:
            raise ValueError("SCI_ORIG and ERR shapes differ")
        if (
            not np.all(np.isfinite(orig))
            or not np.all(np.isfinite(err))
            or not np.all(err > 0)
        ):
            raise ValueError("invalid SCI_ORIG/ERR inputs")

        labels, bg, scene_mask, deblend_meta = d1k.deblend_scene_components(orig, err)
        catalog = build_child_catalog(orig, labels, bg)

        for exp in summary["experiments"]:
            image = np.asarray(hdul[exp["output_extname"]].data, dtype=float)
            fit = fit_one(
                image,
                err,
                orig,
                labels,
                catalog,
                int(exp["x"]),
                int(exp["y"]),
                psf,
                float(summary["pixar_sr"]),
            )
            row = dict(exp)
            row.update(fit)
            rows.append(row)

    out = {
        "claim": (
            "limited simultaneous PSF-convolved parametric-neighbour Sersic diagnostic "
            "on synthetic sources injected into literal real COSMOS-Web mosaic context; "
            "not blind detection, not a production deblender, not independent cross-code "
            "validation, and not literal survey-source reproduction"
        ),
        "n_experiments": len(rows),
        "patch_pixels": rec.PATCH,
        "psf_provenance": psf_prov,
        "scene_components": {
            "parent_definition": (
                "8-connected components of "
                "(SCI_ORIG - robust_background_median) / ERR > 5.0"
            ),
            "deblending_reused_from_d1k": True,
            "parent_support_changed_by_deblending": False,
            "background_median": float(bg),
            "global_mask_fraction": float(scene_mask.mean()),
            "deblending": deblend_meta,
            "child_catalog_count": len(catalog),
        },
        "parametric_neighbours": {
            "maximum_models_per_patch": MAX_NEIGHBOURS,
            "ranking": "child positive-core flux-weighted centroid distance to injection position",
            "selection_requires_child_centroid_inside_patch": True,
            "remaining_children": "exact frozen child support masked; no dilation",
            "model": "single PSF-convolved Sersic nuisance component per selected child",
            "seed_min_sigma_pix": SEED_MIN_SIGMA_PIX,
            "initial_n": 1.0,
            "initial_re": "sqrt(2 ln 2) * moment sigma_major, clipped to nuisance bounds",
            "same_declared_stpsf_as_target": True,
            "literal_effective_cosmosweb_psf_claimed": False,
            "bounds": {
                "amplitude_ratio": [1e-4, 1e4],
                "centroid_correction_pix": [-2, 2],
                "re_pix": [1, 20],
                "n": [0.3, 6],
                "q": [0.2, 1],
                "pa_deg": [-90, 90],
            },
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
            "max_nfev": MAX_NFEV,
        },
        "semantics": {
            "same_target_renderer_and_bounds_as_d1e": True,
            "same_detection_and_deblending_as_d1k": True,
            "segmentation_threshold_changed": False,
            "segmentation_support_grown": False,
            "neighbour_morphology_free": True,
            "neighbour_psf_convolution_applied": True,
            "blind_detection_performed": False,
            "low_snr_failures_retained": True,
            "target_bound_hits_retained": True,
            "nuisance_bound_hits_retained": True,
            "tolman_factor_applied": False,
            "extra_background_added": False,
            "source_shot_noise_added": False,
            "err_or_wht_modified": False,
            "scientific_success_claimed": False,
        },
        "experiments": rows,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    return out


def main() -> None:
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
                "optimizer_success": sum(
                    bool(r.get("optimizer_success")) for r in out["experiments"]
                ),
                "target_bound_hits": sum(
                    bool(r.get("any_bound_hit")) for r in out["experiments"]
                ),
                "nuisance_bound_hits": sum(
                    bool(r.get("any_nuisance_bound_hit")) for r in out["experiments"]
                ),
                "fits_with_parametric_neighbours": sum(
                    int(r.get("n_neighbour_models", 0)) > 0 for r in out["experiments"]
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
