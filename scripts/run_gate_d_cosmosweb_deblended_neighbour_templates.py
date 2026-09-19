#!/usr/bin/env python3
"""Gate D1k: multi-threshold deblended neighbour-template diagnostic.

This is deliberately a diagnostic, not a production deblender.  The parent
scene support is frozen to the same pre-injection >5-sigma, 8-connected mask
used by D1c/D1g/D1h.  Photutils is used only to split already-detected parent
components by multi-threshold watershed topology.  Each resulting child keeps
an empirical observed-space core template with only a non-negative amplitude
free in the simultaneous target fit.  Target model, PSF, bounds, ERR weights,
loss, and fit patch remain exactly those of D1e/D1h.
"""
from __future__ import annotations
import argparse, importlib.util, json, warnings
from pathlib import Path
import numpy as np
from astropy.io import fits
from photutils.segmentation import SegmentationImage, deblend_sources

ROOT = Path(__file__).resolve().parents[1]
HSPEC = importlib.util.spec_from_file_location(
    "gate_d_d1h", ROOT / "scripts" / "run_gate_d_cosmosweb_simultaneous_neighbour_templates.py"
)
d1h = importlib.util.module_from_spec(HSPEC); HSPEC.loader.exec_module(d1h)
rec = d1h.rec

DEBLEND_N_PIXELS = 3
DEBLEND_N_LEVELS = 32
DEBLEND_CONTRAST = 0.001
DEBLEND_MODE = "exponential"
DEBLEND_CONNECTIVITY = 8


def deblend_scene_components(orig: np.ndarray, err: np.ndarray):
    """Split only the frozen D1h parent components; never expand their support."""
    labels, n_parent, bg, scene_mask = d1h.labelled_scene_components(orig, err)
    sn = (orig - bg) / err
    seg = SegmentationImage(labels.astype(int, copy=False))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        out = deblend_sources(
            sn,
            seg,
            DEBLEND_N_PIXELS,
            n_levels=DEBLEND_N_LEVELS,
            contrast=DEBLEND_CONTRAST,
            mode=DEBLEND_MODE,
            connectivity=DEBLEND_CONNECTIVITY,
            relabel=True,
            n_processes=1,
            progress_bar=False,
        )
    deblended = np.asarray(out.data, dtype=int)
    if not np.array_equal(deblended > 0, labels > 0):
        raise RuntimeError("deblending changed frozen >5-sigma parent support")
    split_parents = 0
    max_children = 1
    child_counts = {}
    for parent in range(1, n_parent + 1):
        kids = np.unique(deblended[labels == parent])
        kids = kids[kids > 0]
        nk = int(kids.size)
        child_counts[str(parent)] = nk
        if nk > 1:
            split_parents += 1
        max_children = max(max_children, nk)
    meta = {
        "parent_component_count": int(n_parent),
        "deblended_component_count": int(np.max(deblended)) if np.any(deblended) else 0,
        "split_parent_count": int(split_parents),
        "max_children_per_parent": int(max_children),
        "child_counts_by_parent": child_counts,
        "warnings": [str(w.message) for w in caught],
    }
    return deblended, float(bg), scene_mask, meta


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
        labels, bg, scene_mask, dmeta = deblend_scene_components(orig, err)
        for exp in summary["experiments"]:
            image = np.asarray(h[exp["output_extname"]].data, dtype=float)
            fit = d1h.fit_one_with_templates(
                image, err, orig, labels, bg, int(exp["x"]), int(exp["y"]), psf, float(summary["pixar_sr"])
            )
            row = dict(exp); row.update(fit); rows.append(row)
    out = {
        "claim": "multi-threshold deblended empirical neighbour-template diagnostic on real COSMOS-Web context; not blind detection, not a production deblender, and not literal survey-source reproduction",
        "n_experiments": len(rows), "patch_pixels": rec.PATCH, "psf_provenance": psf_prov,
        "scene_components": {
            "parent_definition": "8-connected components of (SCI_ORIG - robust_background_median) / ERR > 5.0",
            "threshold_sigma": d1h.THRESHOLD_SIGMA,
            "background_median": bg,
            "global_mask_fraction": float(scene_mask.mean()),
            "derived_from_pre_injection_scene_only": True,
            "parent_support_changed_by_deblending": False,
            "template_definition": "positive SCI_ORIG-background values inside each deblended child footprint, L2-normalized; one non-negative amplitude per overlapping child",
            "deblending": {
                "package": "photutils",
                "algorithm": "multi-threshold watershed",
                "n_pixels": DEBLEND_N_PIXELS,
                "n_levels": DEBLEND_N_LEVELS,
                "contrast": DEBLEND_CONTRAST,
                "mode": DEBLEND_MODE,
                "connectivity": DEBLEND_CONNECTIVITY,
                **dmeta,
            },
        },
        "bounds": {
            "centroid_offset_pix": [-2, 2], "re_pix": [1, 20], "n": [0.3, 6], "q": [0.2, 1],
            "pa_deg": [-90, 90], "amplitude_positive": True, "neighbour_template_amplitude": [0, "inf"]
        },
        "semantics": {
            "same_target_fitter_and_bounds_as_d1e": True,
            "same_parent_detection_threshold_as_d1c_d1g_d1h": True,
            "parent_support_frozen_before_deblending": True,
            "target_pixels_masked": False,
            "neighbour_templates_observed_space": True,
            "neighbour_psf_reconvolution_applied": False,
            "neighbour_amplitudes_fitted_simultaneously": True,
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
    p = argparse.ArgumentParser()
    p.add_argument("--injected-fits", type=Path, required=True)
    p.add_argument("--injection-summary", type=Path, required=True)
    p.add_argument("--out-json", type=Path, required=True)
    a = p.parse_args()
    out = run(a.injected_fits, a.injection_summary, a.out_json)
    deb = out["scene_components"]["deblending"]
    print(json.dumps({
        "n_experiments": out["n_experiments"],
        "optimizer_success": sum(bool(r.get("optimizer_success")) for r in out["experiments"]),
        "target_bound_hits": sum(bool(r.get("any_bound_hit")) for r in out["experiments"]),
        "parent_components": deb["parent_component_count"],
        "deblended_components": deb["deblended_component_count"],
        "split_parents": deb["split_parent_count"],
    }, indent=2))

if __name__ == "__main__":
    main()
