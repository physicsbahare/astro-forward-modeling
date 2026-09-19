#!/usr/bin/env python3
"""Gate D1g: neighbour-mask diagnostic on frozen real COSMOS-Web injections.

The mask is derived only from the pre-injection SCI_ORIG plane using the exact
D1c >5-sigma source-pixel definition. Masked pixels are excluded from the same
D1e forced-position fitter. This is a contamination diagnostic, not a final
survey-recovery method and not simultaneous neighbour modelling.
"""
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
RSPEC = importlib.util.spec_from_file_location("gate_d_recovery", ROOT / "scripts" / "run_gate_d_cosmosweb_forced_recovery.py")
rec = importlib.util.module_from_spec(RSPEC); RSPEC.loader.exec_module(rec)
ASPEC = importlib.util.spec_from_file_location("gate_d_context", ROOT / "scripts" / "audit_gate_d_cosmosweb_real_context.py")
aud = importlib.util.module_from_spec(ASPEC); ASPEC.loader.exec_module(aud)

THRESHOLD_SIGMA = 5.0


def build_scene_mask(orig: np.ndarray, err: np.ndarray):
    bg, _, _ = aud.robust_background(orig)
    significance = (orig - bg) / err
    mask = np.isfinite(significance) & (significance > THRESHOLD_SIGMA)
    return mask, bg


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
        scene_mask, bg = build_scene_mask(orig, err)
        for exp in summary["experiments"]:
            x = int(exp["x"]); y = int(exp["y"])
            image = np.asarray(h[exp["output_extname"]].data, dtype=float)
            patch_mask = rec._crop(scene_mask, x, y).astype(bool)
            fit = rec.fit_one(image, err, x, y, psf, float(summary["pixar_sr"]), exclude_mask=scene_mask)
            row = dict(exp); row.update(fit)
            row["scene_mask_fraction_patch"] = float(patch_mask.mean())
            row["scene_mask_pixels_patch"] = int(patch_mask.sum())
            row["scene_mask_used"] = True
            rows.append(row)
    out = {
        "claim": "fixed pre-injection neighbour/source-pixel masking diagnostic on real COSMOS-Web context; not blind detection, not simultaneous neighbour modelling, and not literal survey-source reproduction",
        "n_experiments": len(rows),
        "patch_pixels": rec.PATCH,
        "psf_provenance": psf_prov,
        "scene_mask": {
            "definition": "(SCI_ORIG - robust_background_median) / ERR > 5.0",
            "threshold_sigma": THRESHOLD_SIGMA,
            "dilation_applied": False,
            "background_median": float(bg),
            "global_mask_fraction": float(scene_mask.mean()),
            "derived_from_pre_injection_scene_only": True
        },
        "bounds": {"centroid_offset_pix": [-2,2], "re_pix": [1,20], "n": [0.3,6], "q": [0.2,1], "pa_deg": [-90,90], "amplitude_positive": True},
        "semantics": {
            "same_forced_fitter_as_d1e": True,
            "mask_threshold_reused_from_d1c": True,
            "masked_pixels_unmasked_for_target": False,
            "insufficient_valid_pixels_retained_as_failure": True,
            "low_snr_failures_retained": True,
            "bound_hits_retained": True,
            "blind_detection_performed": False,
            "simultaneous_neighbour_modelling_performed": False,
            "tolman_factor_applied": False,
            "extra_background_added": False,
            "source_shot_noise_added": False,
            "scientific_success_claimed": False
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
        "bound_hits": sum(bool(r.get("any_bound_hit")) for r in out["experiments"]),
        "insufficient_valid": sum(r.get("reason") == "insufficient_valid_weight_pixels" for r in out["experiments"]),
        "global_mask_fraction": out["scene_mask"]["global_mask_fraction"],
    }, indent=2))

if __name__ == "__main__":
    main()
