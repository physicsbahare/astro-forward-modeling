#!/usr/bin/env python3
"""Gate D1i: fixed empirical neighbour-support growth diagnostic.

This diagnostic keeps the D1h >5-sigma connected-component identities frozen
from SCI_ORIG, but asks whether the empirical neighbour templates failed mainly
because their support was truncated to the high-significance cores.  For each
component, the support is grown by a frozen number of pixels while template
values remain the positive pre-injection SCI_ORIG-background signal.  No PSF is
applied to neighbour templates because they are already observed-space data.
Target rendering, target bounds, ERR weighting, and linear loss are unchanged.
"""
from __future__ import annotations
import argparse, importlib.util, json, math
from pathlib import Path
import numpy as np
from scipy import ndimage, optimize
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
HSPEC = importlib.util.spec_from_file_location(
    "gate_d_neighbours",
    ROOT / "scripts" / "run_gate_d_cosmosweb_simultaneous_neighbour_templates.py",
)
h = importlib.util.module_from_spec(HSPEC)
HSPEC.loader.exec_module(h)
rec = h.rec

# Frozen before inspecting D1i output.
GROWTH_PIXELS = (0, 2, 4)
STRUCTURE_8 = np.ones((3, 3), dtype=bool)


def grown_component_templates(
    orig_patch: np.ndarray,
    labels_patch: np.ndarray,
    bg: float,
    growth_pixels: int,
):
    """Build observed-space templates with frozen support growth.

    Component identity comes only from the D1h >5-sigma labels.  Growth changes
    support, not the detection threshold or component identity.  Values are
    sampled from SCI_ORIG itself and are never PSF-convolved again.
    """
    if growth_pixels < 0:
        raise ValueError("growth_pixels must be non-negative")
    templates, meta = [], []
    for label in np.unique(labels_patch):
        if label <= 0:
            continue
        core = labels_patch == label
        support = core.copy()
        if growth_pixels:
            support = ndimage.binary_dilation(
                core, structure=STRUCTURE_8, iterations=int(growth_pixels)
            )
        values = np.where(support, np.maximum(orig_patch - bg, 0.0), 0.0)
        norm = float(np.sqrt(np.sum(values * values)))
        if not np.isfinite(norm) or norm <= 0:
            continue
        templates.append(values / norm)
        meta.append(
            {
                "label": int(label),
                "core_pixels": int(core.sum()),
                "support_pixels": int(support.sum()),
                "growth_pixels": int(growth_pixels),
                "l2_norm_native": norm,
            }
        )
    if not templates:
        return np.empty((0,) + orig_patch.shape, dtype=float), meta
    return np.stack(templates), meta


def fit_one(image, err, orig, labels, bg, x, y, psf, pixar_sr, growth_pixels):
    data = rec._crop(image, x, y)
    sigma = rec._crop(err, x, y)
    orig_patch = rec._crop(orig, x, y)
    labels_patch = rec._crop(labels, x, y).astype(int)
    valid = np.isfinite(data) & np.isfinite(sigma) & (sigma > 0)
    if valid.sum() < 0.8 * data.size:
        return {
            "optimizer_success": False,
            "reason": "insufficient_valid_weight_pixels",
            "valid_fraction": float(valid.mean()),
        }

    templates, tmeta = grown_component_templates(
        orig_patch, labels_patch, bg, int(growth_pixels)
    )
    nt = int(templates.shape[0])
    base_flux_jy = rec.inj.ab_to_jy(27.5)
    base_amp = base_flux_jy / (1e6 * pixar_sr)
    med = float(np.nanmedian(data[valid]))
    target0 = np.array(
        [0.0, 0.0, 0.0, math.log(5.0), 1.5, 0.7, 0.0, med, 0.0, 0.0]
    )
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

    result = optimize.least_squares(
        resid,
        p0,
        bounds=(lo, hi),
        method="trf",
        loss="linear",
        x_scale="jac",
        max_nfev=500,
    )
    p = result.x
    tol = 1e-5
    hits = []
    names = [
        "log_amp_ratio", "dx", "dy", "log_re", "n",
        "q", "pa", "b0", "bx", "by",
    ]
    for i, name in enumerate(names):
        if np.isfinite(rec.BOUNDS_LO[i]) and np.isfinite(rec.BOUNDS_HI[i]):
            span = rec.BOUNDS_HI[i] - rec.BOUNDS_LO[i]
            if (
                p[i] - rec.BOUNDS_LO[i] <= tol * span
                or rec.BOUNDS_HI[i] - p[i] <= tol * span
            ):
                hits.append(name)

    dof = max(1, int(valid.sum()) - len(p))
    chi2 = float(np.sum(result.fun ** 2))
    amp_total = base_amp * math.exp(float(p[0]))
    flux_jy = amp_total * 1e6 * pixar_sr
    ab = (
        float(-2.5 * math.log10(flux_jy / rec.inj.AB_ZERO_JY))
        if flux_jy > 0 else float("nan")
    )
    return {
        "optimizer_success": bool(result.success),
        "optimizer_status": int(result.status),
        "optimizer_message": str(result.message),
        "nfev": int(result.nfev),
        "valid_fraction": float(valid.mean()),
        "chi2": chi2,
        "reduced_chi2_proxy": chi2 / dof,
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
        "n_neighbour_templates": nt,
        "neighbour_template_metadata": tmeta,
        "neighbour_amplitudes": [float(v) for v in p[10:]],
        "growth_pixels": int(growth_pixels),
    }


def run(injected_fits: Path, injection_summary: Path, out_json: Path):
    summary = json.loads(injection_summary.read_text())
    matrix = summary["matrix"]
    psf, psf_prov = rec.inj.build_stpsf(
        matrix, float(matrix["pixel_scale_arcsec"])
    )
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
        labels, n_labels, bg, scene_mask = h.labelled_scene_components(orig, err)

        for growth in GROWTH_PIXELS:
            for exp in summary["experiments"]:
                image = np.asarray(hdul[exp["output_extname"]].data, dtype=float)
                fit = fit_one(
                    image, err, orig, labels, bg,
                    int(exp["x"]), int(exp["y"]),
                    psf, float(summary["pixar_sr"]), growth,
                )
                row = dict(exp)
                row.update(fit)
                rows.append(row)

    out = {
        "claim": (
            "fixed empirical neighbour-support growth diagnostic on real "
            "COSMOS-Web context; not blind detection, not a production "
            "deblender, and not literal survey-source reproduction"
        ),
        "n_base_experiments": len(summary["experiments"]),
        "n_fits": len(rows),
        "growth_pixels": list(GROWTH_PIXELS),
        "patch_pixels": rec.PATCH,
        "psf_provenance": psf_prov,
        "scene_components": {
            "definition": (
                "8-connected component identities of "
                "(SCI_ORIG - robust_background_median) / ERR > 5.0"
            ),
            "threshold_sigma": h.THRESHOLD_SIGMA,
            "background_median": bg,
            "global_mask_fraction": float(scene_mask.mean()),
            "global_component_count": n_labels,
            "derived_from_pre_injection_scene_only": True,
            "support_growth_only": True,
            "neighbour_psf_convolution_applied": False,
        },
        "bounds": {
            "centroid_offset_pix": [-2, 2],
            "re_pix": [1, 20],
            "n": [0.3, 6],
            "q": [0.2, 1],
            "pa_deg": [-90, 90],
            "amplitude_positive": True,
            "neighbour_template_amplitude": [0, "inf"],
        },
        "semantics": {
            "same_target_fitter_and_bounds_as_d1e": True,
            "same_component_detection_threshold_as_d1h": True,
            "component_identities_frozen_before_support_growth": True,
            "growth_values_frozen_before_results": True,
            "target_pixels_masked": False,
            "neighbour_templates_observed_space": True,
            "neighbour_psf_reconvolution": False,
            "blind_detection_performed": False,
            "low_snr_failures_retained": True,
            "bound_hits_retained": True,
            "tolman_factor_applied": False,
            "extra_background_added": False,
            "source_shot_noise_added": False,
            "scientific_success_claimed": False,
        },
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
    by_growth = {}
    for growth in GROWTH_PIXELS:
        subset = [r for r in out["experiments"] if r["growth_pixels"] == growth]
        by_growth[str(growth)] = {
            "fits": len(subset),
            "optimizer_success": sum(bool(r.get("optimizer_success")) for r in subset),
            "target_bound_hits": sum(bool(r.get("any_bound_hit")) for r in subset),
        }
    print(json.dumps({"n_fits": out["n_fits"], "by_growth": by_growth}, indent=2))


if __name__ == "__main__":
    main()
