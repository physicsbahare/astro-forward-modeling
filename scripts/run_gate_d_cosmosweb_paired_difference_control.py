#!/usr/bin/env python3
"""Gate D1f: paired-difference recovery control for frozen real-mosaic injections.

This deliberately subtracts the exact pre-injection SCI scene from each injected
extension and then runs the same forced-position fitter. It is a numerical
identifiability/control experiment, not a realistic survey recovery mode.
"""
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("gate_d_recovery", ROOT / "scripts" / "run_gate_d_cosmosweb_forced_recovery.py")
rec = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(rec)


def run(injected_fits: Path, injection_summary: Path, out_json: Path):
    summary = json.loads(injection_summary.read_text())
    matrix = summary["matrix"]
    psf, psf_prov = rec.inj.build_stpsf(matrix, float(matrix["pixel_scale_arcsec"]))
    rows = []
    with fits.open(injected_fits, mode="readonly") as h:
        orig = np.asarray(h["SCI_ORIG"].data, dtype=float)
        err = np.asarray(h["ERR"].data, dtype=float)
        for exp in summary["experiments"]:
            injected = np.asarray(h[exp["output_extname"]].data, dtype=float)
            delta = injected - orig
            fit = rec.fit_one(delta, err, int(exp["x"]), int(exp["y"]), psf, float(summary["pixar_sr"]))
            row = dict(exp); row.update(fit)
            row["paired_difference_used"] = True
            rows.append(row)
    out = {
        "claim": "paired injected-minus-original numerical recovery control on the exact real-mosaic grid; not a realistic survey recovery and not literal survey-source reproduction",
        "n_experiments": len(rows),
        "patch_pixels": rec.PATCH,
        "psf_provenance": psf_prov,
        "bounds": {"centroid_offset_pix": [-2,2], "re_pix": [1,20], "n": [0.3,6], "q": [0.2,1], "pa_deg": [-90,90], "amplitude_positive": True},
        "semantics": {
            "paired_difference_control": True,
            "real_scene_cancelled_by_construction": True,
            "real_noise_cancelled_by_construction": True,
            "real_err_used_only_as_fixed_weights": True,
            "blind_detection_performed": False,
            "tolman_factor_applied": False,
            "extra_background_added": False,
            "source_shot_noise_added": False,
            "low_snr_failures_retained": True,
            "bound_hits_retained": True,
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
    }, indent=2))

if __name__ == "__main__":
    main()
