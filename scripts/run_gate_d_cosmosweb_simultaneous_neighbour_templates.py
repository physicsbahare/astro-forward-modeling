#!/usr/bin/env python3
"""Gate D1h: simultaneous fixed neighbour-template diagnostic.

Nearby source components are identified only from the pre-injection SCI_ORIG
plane using the exact D1c/D1g >5-sigma connected-pixel definition.  Each
connected component that overlaps the 65x65 fit patch contributes one fixed
observed-space template with a non-negative free amplitude, while the injected
target retains exactly the D1e Sérsic model, bounds, ERR weighting and planar
background.  The neighbour templates are intentionally empirical diagnostics:
they use only the pre-injection high-significance component cores and are not a
production deblender, a literal survey-source model, or a scientific recovery
claim.
"""
from __future__ import annotations
import argparse, importlib.util, json, math
from pathlib import Path
import numpy as np
from scipy import ndimage, optimize
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
RSPEC = importlib.util.spec_from_file_location("gate_d_recovery", ROOT / "scripts" / "run_gate_d_cosmosweb_forced_recovery.py")
rec = importlib.util.module_from_spec(RSPEC); RSPEC.loader.exec_module(rec)
MSPEC = importlib.util.spec_from_file_location("gate_d_mask", ROOT / "scripts" / "run_gate_d_cosmosweb_neighbour_mask_control.py")
maskmod = importlib.util.module_from_spec(MSPEC); MSPEC.loader.exec_module(maskmod)

THRESHOLD_SIGMA = 5.0
STRUCTURE_8 = np.ones((3, 3), dtype=int)


def labelled_scene_components(orig: np.ndarray, err: np.ndarray):
    scene_mask, bg = maskmod.build_scene_mask(orig, err)
    labels, n_labels = ndimage.label(scene_mask, structure=STRUCTURE_8)
    return labels, int(n_labels), float(bg), scene_mask


def component_templates(orig_patch: np.ndarray, labels_patch: np.ndarray, bg: float):
    """Return fixed positive observed-space templates for labels in one patch."""
    templates = []
    meta = []
    for label in np.unique(labels_patch):
        if label <= 0:
            continue
        footprint = labels_patch == label
        values = np.where(footprint, np.maximum(orig_patch - bg, 0.0), 0.0)
        norm = float(np.sqrt(np.sum(values * values)))
        if not np.isfinite(norm) or norm <= 0:
            continue
        templates.append(values / norm)
        meta.append({"label": int(label), "pixels": int(footprint.sum()), "l2_norm_native": norm})
    if not templates:
        return np.empty((0,) + orig_patch.shape, dtype=float), meta
    return np.stack(templates), meta


def fit_one_with_templates(image, err, orig, labels, bg, x, y, psf, pixar_sr):
    data = rec._crop(image, x, y)
    sigma = rec._crop(err, x, y)
    orig_patch = rec._crop(orig, x, y)
    labels_patch = rec._crop(labels, x, y).astype(int)
    valid = np.isfinite(data) & np.isfinite(sigma) & (sigma > 0)
    if valid.sum() < 0.8 * data.size:
        return {"optimizer_success": False, "reason": "insufficient_valid_weight_pixels", "valid_fraction": float(valid.mean())}

    templates, tmeta = component_templates(orig_patch, labels_patch, bg)
    nt = int(templates.shape[0])
    base_flux_jy = rec.inj.ab_to_jy(27.5)
    base_amp = base_flux_jy / (1e6 * pixar_sr)
    med = float(np.nanmedian(data[valid]))
    target0 = np.array([0.0, 0.0, 0.0, math.log(5.0), 1.5, 0.7, 0.0, med, 0.0, 0.0])
    p0 = np.concatenate([target0, np.ones(nt)])
    lo = np.concatenate([rec.BOUNDS_LO, np.zeros(nt)])
    hi = np.concatenate([rec.BOUNDS_HI, np.full(nt, np.inf)])

    def model(p):
        m = rec._render(p[:10], psf, 0.03, base_amp)
        if nt:
            m = m + np.tensordot(p[10:], templates, axes=(0, 0))
        return m

    def resid(p):
        return ((model(p) - data) / sigma)[valid]

    res = optimize.least_squares(resid, p0, bounds=(lo, hi), method="trf", loss="linear", x_scale="jac", max_nfev=500)
    p = res.x
    tol = 1e-5
    hits = []
    names = ["log_amp_ratio", "dx", "dy", "log_re", "n", "q", "pa", "b0", "bx", "by"]
    for i, name in enumerate(names):
        if np.isfinite(rec.BOUNDS_LO[i]) and np.isfinite(rec.BOUNDS_HI[i]):
            span = rec.BOUNDS_HI[i] - rec.BOUNDS_LO[i]
            if p[i] - rec.BOUNDS_LO[i] <= tol * span or rec.BOUNDS_HI[i] - p[i] <= tol * span:
                hits.append(name)
    nuisance_zero = [tmeta[j]["label"] for j in range(nt) if p[10 + j] <= 1e-10]
    dof = max(1, int(valid.sum()) - len(p))
    chi2 = float(np.sum(res.fun ** 2))
    amp_total = base_amp * math.exp(float(p[0]))
    flux_jy = amp_total * 1e6 * pixar_sr
    ab = float(-2.5 * math.log10(flux_jy / rec.inj.AB_ZERO_JY)) if flux_jy > 0 else float("nan")
    return {
        "optimizer_success": bool(res.success), "optimizer_status": int(res.status), "optimizer_message": str(res.message),
        "nfev": int(res.nfev), "valid_fraction": float(valid.mean()), "chi2": chi2, "reduced_chi2_proxy": chi2 / dof,
        "bound_hits": hits, "any_bound_hit": bool(hits), "recovered_ab_mag": ab,
        "recovered_dx_pix": float(p[1]), "recovered_dy_pix": float(p[2]), "recovered_re_pix": float(math.exp(p[3])),
        "recovered_re_arcsec": float(math.exp(p[3]) * 0.03), "recovered_n": float(p[4]), "recovered_q": float(p[5]),
        "recovered_pa_deg": float(p[6]), "finite_solution": bool(np.all(np.isfinite(p)) and np.isfinite(chi2)),
        "n_neighbour_templates": nt, "neighbour_template_metadata": tmeta,
        "neighbour_amplitudes": [float(v) for v in p[10:]], "neighbour_zero_amplitude_labels": nuisance_zero,
    }


def run(injected_fits: Path, injection_summary: Path, out_json: Path):
    summary = json.loads(injection_summary.read_text())
    matrix = summary["matrix"]
    psf, psf_prov = rec.inj.build_stpsf(matrix, float(matrix["pixel_scale_arcsec"]))
    rows = []
    with fits.open(injected_fits, mode="readonly") as h:
        orig = np.asarray(h["SCI_ORIG"].data, dtype=float)
        err = np.asarray(h["ERR"].data, dtype=float)
        if orig.shape != err.shape:
            raise ValueError("SCI_ORIG and ERR shapes differ")
        if not np.all(np.isfinite(orig)) or not np.all(np.isfinite(err)) or not np.all(err > 0):
            raise ValueError("invalid SCI_ORIG/ERR inputs")
        labels, n_labels, bg, scene_mask = labelled_scene_components(orig, err)
        for exp in summary["experiments"]:
            image = np.asarray(h[exp["output_extname"]].data, dtype=float)
            fit = fit_one_with_templates(image, err, orig, labels, bg, int(exp["x"]), int(exp["y"]), psf, float(summary["pixar_sr"]))
            row = dict(exp); row.update(fit); rows.append(row)
    out = {
        "claim": "simultaneous fixed empirical neighbour-template diagnostic on real COSMOS-Web context; not blind detection, not a production deblender, and not literal survey-source reproduction",
        "n_experiments": len(rows), "patch_pixels": rec.PATCH, "psf_provenance": psf_prov,
        "scene_components": {
            "definition": "8-connected components of (SCI_ORIG - robust_background_median) / ERR > 5.0",
            "threshold_sigma": THRESHOLD_SIGMA, "dilation_applied": False,
            "background_median": bg, "global_mask_fraction": float(scene_mask.mean()), "global_component_count": n_labels,
            "derived_from_pre_injection_scene_only": True,
            "template_definition": "positive SCI_ORIG-background values inside each connected >5-sigma footprint, L2-normalized; one non-negative amplitude per overlapping component",
        },
        "bounds": {"centroid_offset_pix": [-2, 2], "re_pix": [1, 20], "n": [0.3, 6], "q": [0.2, 1], "pa_deg": [-90, 90], "amplitude_positive": True,
                   "neighbour_template_amplitude": [0, "inf"]},
        "semantics": {
            "same_target_fitter_and_bounds_as_d1e": True, "same_threshold_as_d1c_d1g": True,
            "target_pixels_masked": False, "neighbour_shapes_fixed_from_pre_injection_scene": True,
            "neighbour_amplitudes_fitted_simultaneously": True, "blind_detection_performed": False,
            "low_snr_failures_retained": True, "bound_hits_retained": True, "tolman_factor_applied": False,
            "extra_background_added": False, "source_shot_noise_added": False, "scientific_success_claimed": False,
        },
        "experiments": rows,
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
        "n_experiments": out["n_experiments"],
        "optimizer_success": sum(bool(r.get("optimizer_success")) for r in out["experiments"]),
        "target_bound_hits": sum(bool(r.get("any_bound_hit")) for r in out["experiments"]),
        "global_component_count": out["scene_components"]["global_component_count"],
        "experiments_with_neighbour_templates": sum(int(r.get("n_neighbour_templates", 0)) > 0 for r in out["experiments"]),
    }, indent=2))

if __name__ == "__main__":
    main()
