#!/usr/bin/env python3
"""Gate D1j: moment-extrapolated observed-space neighbour-template diagnostic.

D1i showed that simply growing the empirical >5-sigma component support does
not monotonically solve the recovery bias.  D1j therefore keeps the same
pre-injection component identities but replaces hard-edged empirical templates
with smooth elliptical-Gaussian templates whose centroids and covariance are
measured from the component's positive pre-injection pixels.

The neighbour templates are *observed-space* nuisance models.  They are not
PSF-convolved again.  The injected target renderer, PSF, ERR weighting, linear
loss, and all target bounds are unchanged from D1e.
"""
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
HSPEC = importlib.util.spec_from_file_location(
    "gate_d_neighbours",
    ROOT / "scripts" / "run_gate_d_cosmosweb_simultaneous_neighbour_templates.py",
)
h = importlib.util.module_from_spec(HSPEC)
HSPEC.loader.exec_module(h)
rec = h.rec

# Frozen before inspecting D1j output.
MIN_SIGMA_PIX = 0.5
MAX_MAHALANOBIS = 6.0


def _regularized_covariance(dx, dy, weights):
    """Return a finite positive-definite 2x2 second-moment covariance."""
    sw = float(np.sum(weights))
    if not np.isfinite(sw) or sw <= 0:
        raise ValueError("non-positive moment weight")
    cxx = float(np.sum(weights * dx * dx) / sw)
    cyy = float(np.sum(weights * dy * dy) / sw)
    cxy = float(np.sum(weights * dx * dy) / sw)
    cov = np.array([[cxx, cxy], [cxy, cyy]], dtype=float)
    vals, vecs = np.linalg.eigh(cov)
    vals = np.maximum(vals, MIN_SIGMA_PIX**2)
    return (vecs * vals) @ vecs.T


def moment_gaussian_templates(orig_patch, labels_patch, bg):
    """Build smooth observed-space templates from frozen labelled components."""
    yy, xx = np.indices(orig_patch.shape, dtype=float)
    templates, meta = [], []
    signal = np.maximum(orig_patch - bg, 0.0)

    for label in np.unique(labels_patch):
        if label <= 0:
            continue
        core = labels_patch == label
        weights = np.where(core, signal, 0.0)
        sw = float(weights.sum())
        if not np.isfinite(sw) or sw <= 0:
            continue

        xc = float(np.sum(weights * xx) / sw)
        yc = float(np.sum(weights * yy) / sw)
        dx = xx - xc
        dy = yy - yc
        cov = _regularized_covariance(dx[core], dy[core], weights[core])
        inv = np.linalg.inv(cov)
        r2 = inv[0, 0] * dx * dx + 2.0 * inv[0, 1] * dx * dy + inv[1, 1] * dy * dy
        values = np.exp(-0.5 * r2)
        values[r2 > MAX_MAHALANOBIS**2] = 0.0
        norm = float(np.sqrt(np.sum(values * values)))
        if not np.isfinite(norm) or norm <= 0:
            continue
        vals = np.linalg.eigvalsh(cov)
        templates.append(values / norm)
        meta.append(
            {
                "label": int(label),
                "core_pixels": int(core.sum()),
                "centroid_x_patch": xc,
                "centroid_y_patch": yc,
                "covariance_pix2": cov.tolist(),
                "sigma_minor_pix": float(np.sqrt(vals[0])),
                "sigma_major_pix": float(np.sqrt(vals[1])),
                "mahalanobis_truncation": MAX_MAHALANOBIS,
                "l2_norm_native": norm,
            }
        )

    if not templates:
        return np.empty((0,) + orig_patch.shape, dtype=float), meta
    return np.stack(templates), meta


def fit_one(image, err, orig, labels, bg, x, y, psf, pixar_sr):
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

    templates, tmeta = moment_gaussian_templates(orig_patch, labels_patch, bg)
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
    chi2 = float(np.sum(result.fun**2))
    amp_total = base_amp * math.exp(float(p[0]))
    flux_jy = amp_total * 1e6 * pixar_sr
    ab = (
        float(-2.5 * math.log10(flux_jy / rec.inj.AB_ZERO_JY))
        if flux_jy > 0
        else float("nan")
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

        for exp in summary["experiments"]:
            image = np.asarray(hdul[exp["output_extname"]].data, dtype=float)
            fit = fit_one(
                image,
                err,
                orig,
                labels,
                bg,
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
            "moment-extrapolated observed-space neighbour-template diagnostic "
            "on real COSMOS-Web context; not blind detection, not a production "
            "deblender, and not literal survey-source reproduction"
        ),
        "n_fits": len(rows),
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
            "moment_model": "elliptical Gaussian from positive core second moments",
            "minimum_sigma_pix": MIN_SIGMA_PIX,
            "mahalanobis_truncation": MAX_MAHALANOBIS,
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
            "component_identities_frozen": True,
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
    print(
        json.dumps(
            {
                "n_fits": out["n_fits"],
                "optimizer_success": sum(
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
