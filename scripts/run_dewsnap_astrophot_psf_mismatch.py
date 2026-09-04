#!/usr/bin/env python3
"""C6c: crossed empirical-PSF construction diagnostic in AstroPhot."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import numpy as np
from astropy.io import fits

# When this file is executed directly (``python scripts/...py``), Python puts
# ``scripts/`` rather than the repository root on sys.path. Add the repository
# root explicitly so the same import works both in CI execution and when the
# module is imported by pytest. This changes no scientific settings.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import run_dewsnap_astrophot_common_scene as c6b

C5R_RUN_ID = 33842347328
C5R_JSON = Path("benchmarks/zhuang_shen_2024/c5r_33842347328.json")


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def configuration() -> dict:
    base = c6b.configuration()
    return {
        "stage": "C6c crossed empirical-PSF construction diagnostic",
        "astrophot_version": base["astrophot_version"],
        "torch_version": base["torch_version"],
        "c5o_run_id": base["c5o_run_id"],
        "c5o_artifact_id": base["c5o_artifact_id"],
        "c5r_run_id": C5R_RUN_ID,
        "host_n": 1.0,
        "ratio": 10.0,
        "directions": ["A_data_B_psf", "B_data_A_psf"],
        "pa_mapping": "same_imfit",
        "shape_bounds": base["shape_bounds"],
        "point_flux_bounds": base["point_flux_bounds"],
        "objective": base["objective"],
        "lm": base["lm"],
        "psf": "cross archived signed empirical PSFs; no clipping; no manual normalization",
        "winner": base["winner"],
        "acceptance": "diagnostic completeness/algebra only; no morphology recovery band",
        "claim": "PSF-construction mismatch diagnostic only",
    }


def case_name(data_module: str, psf_module: str) -> str:
    return f"n1_truth{data_module}_fit{psf_module}_ratio10"


def run(source: Path, out: Path) -> dict:
    cfg = configuration()
    out.mkdir(parents=True, exist_ok=True)
    dump(out / "config.json", cfg)

    c5o_summary = json.loads((source / "summary.json").read_text())
    starts = c5o_summary["config"]["starts"]
    if len(starts) != 3:
        raise AssertionError("expected exactly three frozen C5o starts")

    c5r = json.loads(C5R_JSON.read_text())
    imfit = {row["case"]: row for row in c5r["selected"] if row["case"].startswith("n1_")}
    if set(imfit) != {"n1_truthA_fitB_ratio10", "n1_truthB_fitA_ratio10"}:
        raise AssertionError("persisted C5r n=1 winners incomplete")

    files = [
        source / "inputs" / "data_A_ratio10.fits",
        source / "inputs" / "data_B_ratio10.fits",
        source / "inputs" / "psf_A.fits",
        source / "inputs" / "psf_B.fits",
    ]
    missing = [str(p) for p in files if not p.exists()]
    if missing:
        raise FileNotFoundError(missing)
    dump(out / "input_hashes.json", {str(p.relative_to(source)): c6b.sha256_file(p) for p in files})

    arrays = {}
    attempts = []
    winners = []
    comparisons = []
    for data_module, psf_module in [("A", "B"), ("B", "A")]:
        case = case_name(data_module, psf_module)
        data = np.asarray(fits.getdata(source / "inputs" / f"data_{data_module}_ratio10.fits"), dtype=float)
        psf = np.asarray(fits.getdata(source / "inputs" / f"psf_{psf_module}.fits"), dtype=float)
        arrays[f"{case}__data"] = data
        arrays[f"{case}__fit_psf"] = psf
        finite = []
        for s in starts:
            start = {
                "pa_rad": c6b.mapped_pa(float(s["pa"]), "same_imfit"),
                "q": float(s["q"]),
                "n": float(s["n"]),
                "re": float(s["re"]),
                "host_flux": float(s["host_flux"]),
                "point_flux": 10.0 * float(s["point_fraction"]),
            }
            row, model_arr, resid, host_arr, point_arr = c6b.fit_attempt(data, psf, start)
            row.update({
                "case": case,
                "data_module": data_module,
                "fit_psf_module": psf_module,
                "label": s["label"],
                "start": start,
                "psf_input_sum": float(psf.sum()),
                "selected_pa_mapping": "same_imfit",
            })
            attempts.append(row)
            prefix = f"{case}__{s['label']}"
            arrays[f"{prefix}__model"] = model_arr
            arrays[f"{prefix}__residual"] = resid
            arrays[f"{prefix}__host"] = host_arr
            arrays[f"{prefix}__point"] = point_arr
            if row.get("finite") and row.get("sse") is not None:
                finite.append(row)
        if not finite:
            continue
        winner = dict(min(finite, key=lambda r: r["sse"]))
        winner["winner"] = True
        winners.append(winner)
        ref = imfit[case]
        comparison = {
            "case": case,
            "astrophot_label": winner["label"],
            "imfit_label": ref["start"],
            "astrophot_sse": winner["sse"],
            "imfit_sse": ref["sse"],
            "sse_ratio_astrophot_over_imfit": winner["sse"] / ref["sse"],
            "astrophot_n": winner["n"],
            "imfit_n": ref["n"],
            "astrophot_re": winner["re"],
            "imfit_re": ref["re"],
            "astrophot_q": winner["q"],
            "imfit_q": ref["q"],
            "astrophot_point_flux": winner["point_flux"],
            "imfit_point_flux": ref["point_flux"],
            "astrophot_bound_hits": winner["bound_hits"],
            "imfit_bound_hits": ref["bound_hits"],
        }
        comparisons.append(comparison)

    np.savez_compressed(out / "arrays.npz", **arrays)
    dump(out / "attempts.json", attempts)
    dump(out / "comparison.json", comparisons)
    summary = {
        "config": cfg,
        "attempt_count": len(attempts),
        "finite_attempt_count": sum(bool(r.get("finite")) for r in attempts),
        "winner_count": len(winners),
        "winners": winners,
        "comparisons": comparisons,
        "interpretation": "diagnostic only; fitter-dependent response to PSF exchange is an observable",
    }
    dump(out / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.source, args.out), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
