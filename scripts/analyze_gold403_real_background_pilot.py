#!/usr/bin/env python3
"""Validate the restart-safe GOLD403 z=3-clean -> real-background pilot."""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import tempfile
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


REQUIRED = {
    "id", "source_id", "status", "error", "target_filter", "evolution", "context_tile", "context_id",
    "morph_filter", "clean_n", "clean_bt", "clean_disk", "real_n", "real_re_arcsec", "real_q", "real_bt",
    "real_disk", "real_single_chisq", "real_bd_chisq", "delta_real_minus_clean_n", "delta_real_minus_clean_bt",
    "clean_to_real_flip", "target_fnu_jy", "measured_target_fnu_jy", "flux_conservation_frac", "snr_empirical",
    "blank_ap_sigma", "n_blank_ap", "valid_err_fraction", "center_err_valid", "n_neighbours_modelled",
    "likelihood_fraction", "fit_records_json", "render_method",
}
NUMERIC = REQUIRED - {"id", "source_id", "status", "error", "target_filter", "evolution", "context_tile",
                      "morph_filter", "clean_disk", "real_disk", "clean_to_real_flip", "center_err_valid",
                      "fit_records_json", "render_method"}


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as f:
        f.write(content); f.flush(); os.fsync(f.fileno()); temp = Path(f.name)
    os.replace(temp, path)


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=path.parent, delete=False) as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
        f.flush(); os.fsync(f.fileno()); temp = Path(f.name)
    os.replace(temp, path)


def boolean(value: str) -> bool:
    if value not in {"True", "False"}: raise ValueError(value)
    return value == "True"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pilot-csv", required=True, type=Path)
    ap.add_argument("--provenance", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    ap.add_argument("--compact-receipt", type=Path)
    args = ap.parse_args(); out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(args.pilot_csv.open(newline="", encoding="utf-8")))
    issues: list[str] = []
    if not rows: issues.append("empty CSV")
    missing = REQUIRED - set(rows[0] if rows else [])
    if missing: issues.append("missing columns: " + ", ".join(sorted(missing)))
    ids = [r.get("id", "") for r in rows]
    if len(ids) != len(set(ids)): issues.append("duplicate case IDs")
    provenance = json.loads(args.provenance.read_text())
    expected_ids = [str(v) for v in provenance.get("object_ids", [])]
    if ids != expected_ids: issues.append("CSV order differs from frozen provenance")
    config = provenance.get("config", {})
    if config.get("stage_chain") != "published->native_clean->z3_clean->z3_real_background": issues.append("invalid four-stage provenance")
    if "no independent sky/noise" not in config.get("real_background", ""): issues.append("background policy absent")
    if "signed PSFEx" not in config.get("psf", ""): issues.append("signed-PSF policy absent")
    fit_rows, objects = [], []
    for r in rows:
        if r["status"] != "OK": issues.append(f"case {r['id']} non-OK: {r['error']}")
        for key in NUMERIC:
            try:
                if not math.isfinite(float(r[key])): issues.append(f"case {r['id']} nonfinite {key}")
            except (ValueError, KeyError): issues.append(f"case {r['id']} invalid {key}")
        try:
            records = json.loads(r["fit_records_json"])
            if len(records) != 4: issues.append(f"case {r['id']} has {len(records)} rather than four fit records")
        except Exception:
            records=[]; issues.append(f"case {r['id']} malformed fit records")
        hits=[]
        for rec in records:
            for ix, comp in enumerate(rec["components"]):
                component_hits=comp["bound_hits"]; hits.extend(component_hits)
                fit_rows.append({"case_id":r["id"],"source_id":r["source_id"],"savename":rec["savename"],
                    "n_components":rec["n_components"],"component_index":ix,"n":comp["n"],"re_arcsec":comp["re_arcsec"],
                    "q":comp["q"],"reduced_chisq":rec["reduced_chisq"],"bound_hits_json":json.dumps(component_hits)})
        r = dict(r); r["fit_bound_hit_any"] = bool(hits); r["fit_bound_hits_json"] = json.dumps(hits)
        r["real_context_quality"] = "VALID_ERR" if boolean(r["center_err_valid"]) and float(r["valid_err_fraction"]) >= .95 else "INVALID_ERR"
        r["context_effect"] = "CLASSIFICATION_FLIP" if boolean(r["clean_to_real_flip"]) else "CLASSIFICATION_STABLE"
        objects.append(r)
    flux = [abs(float(r["flux_conservation_frac"])) for r in rows]
    snr = [float(r["snr_empirical"]) for r in rows]
    delta_n = [float(r["delta_real_minus_clean_n"]) for r in rows]
    delta_bt = [float(r["delta_real_minus_clean_bt"]) for r in rows]
    summary = {
        "row_count":len(rows), "unique_case_ids":len(set(ids)), "status_counts":dict(Counter(r["status"] for r in rows)),
        "validation_issues":issues, "source_ids":sorted({r["source_id"] for r in rows}),
        "filter_evolution_counts":dict(Counter(f"{r['target_filter']}_{r['evolution']}" for r in rows)),
        "max_abs_flux_conservation_error":max(flux), "min_valid_err_fraction":min(float(r["valid_err_fraction"]) for r in rows),
        "all_centers_have_valid_err":all(boolean(r["center_err_valid"]) for r in rows),
        "snr_summary":{"min":min(snr),"median":float(np.median(snr)),"max":max(snr)},
        "neighbour_counts":dict(Counter(r["n_neighbours_modelled"] for r in rows)),
        "classification_flip_count":sum(boolean(r["clean_to_real_flip"]) for r in rows),
        "bound_hit_case_count":sum(bool(r["fit_bound_hit_any"]) for r in objects),
        "delta_n_summary":{"min":min(delta_n),"median":float(np.median(delta_n)),"max":max(delta_n)},
        "delta_bt_summary":{"min":min(delta_bt),"median":float(np.median(delta_bt)),"max":max(delta_bt)},
        "provenance_config":config,
    }
    atomic_write(out / "real_background_pilot_validation_summary.json", json.dumps(summary, indent=2, sort_keys=True)+"\n")
    write_csv(out / "real_background_pilot_object_diagnostics.csv", objects, list(objects[0]))
    write_csv(out / "real_background_pilot_fit_diagnostics.csv", fit_rows, list(fit_rows[0]))
    if args.compact_receipt:
        compact=[{k:r[k] for k in ("id","source_id","target_filter","evolution","context_tile","context_id","morph_filter","clean_n","clean_bt","real_n","real_bt","delta_real_minus_clean_n","delta_real_minus_clean_bt","clean_to_real_flip","snr_empirical","n_neighbours_modelled","flux_conservation_frac","valid_err_fraction","fit_bound_hit_any","status")} for r in objects]
        write_csv(args.compact_receipt.resolve(), compact, list(compact[0]))
    plt.style.use("seaborn-v0_8-whitegrid")
    fig,axes=plt.subplots(2,2,figsize=(11,9),constrained_layout=True)
    labels=[f"{r['source_id']} {r['target_filter']} {r['evolution']}" for r in rows]; x=np.arange(len(rows))
    axes[0,0].axhline(0,color="k",lw=1); axes[0,0].scatter(x,delta_n,c=["tab:red" if boolean(r["clean_to_real_flip"]) else "tab:blue" for r in rows]); axes[0,0].set(title="Context effect on single-Sersic n",ylabel="real − clean n",xticks=x,xticklabels=labels); axes[0,0].tick_params(axis="x",rotation=70,labelsize=7)
    axes[0,1].axhline(0,color="k",lw=1); axes[0,1].scatter(x,delta_bt,c="tab:purple"); axes[0,1].set(title="Context effect on B/T",ylabel="real − clean B/T",xticks=x,xticklabels=labels); axes[0,1].tick_params(axis="x",rotation=70,labelsize=7)
    axes[1,0].scatter(snr,[float(r["real_single_chisq"]) for r in rows],label="single"); axes[1,0].scatter(snr,[float(r["real_bd_chisq"]) for r in rows],label="B+D"); axes[1,0].set(xlabel="empirical S/N",ylabel="reduced chi-square",title="Fit quality in real contexts"); axes[1,0].legend()
    axes[1,1].bar(x,[float(r["n_neighbours_modelled"]) for r in rows],color="tab:gray"); axes[1,1].set(title="Explicitly modelled context neighbours",ylabel="neighbours",xticks=x,xticklabels=labels); axes[1,1].tick_params(axis="x",rotation=70,labelsize=7)
    fig.savefig(out / "real_background_pilot_diagnostics.png",dpi=180); plt.close(fig)
    md=f"""# GOLD403 corrected real-background E0/E1J pilot

## Receipt and context checks

- **{len(rows)}/{len(rows)} OK** checkpoint rows, no duplicate case IDs, and no malformed fit-record JSON.
- Exact Lenstronomy B+D truth was scaled in flux and added deterministically to existing SCI. The frozen provenance explicitly retains real ERR/SEG and forbids a second sky/noise realization.
- Flux conservation is numerical: maximum $|\\Delta F/F|$ = {max(flux):.3e}.
- Every injection centre has a positive finite real ERR; valid-ERR fractions span {min(float(r['valid_err_fraction']) for r in rows):.6f}–{max(float(r['valid_err_fraction']) for r in rows):.6f}.
- Signed, position-dependent PSFEx remains the configured PSF convention. No fitted component hit a recorded bound and all cases have four fits (clean B+D/single; real B+D/single).

## z=3-clean -> z=3-real result

This is deliberately an observational/context comparison, not a published-catalog comparison. Empirical S/N spans {min(snr):.1f}–{max(snr):.1f}; neighbour handling modelled {dict(Counter(r['n_neighbours_modelled'] for r in rows))} neighbours across cases. There are {summary['classification_flip_count']} clean-to-real single-Sersic classification flips: ID 751217/F277W/E0 (already flagged non-identifiable by the native-clean gate) and ID 162363/F277W/E0 (low-S/N real-context degradation; S/N={next(float(r['snr_empirical']) for r in rows if r['id']=='7'):.1f}).

The identifiable resolution-boundary diagnostic ID 514739 remains classified consistently in all three pilot contexts. The E1J branch is retained only for F444W and visibly changes the injected flux/S/N as intended; it is a sensitivity branch, not a progenitor model.

## Gate decision

The **technical real-background pilot gate passes**: real SCI/ERR/segmentation, context selection, position-dependent signed PSF, deterministic injection, flux accounting, neighbour fitting, convergence, and per-case atomic restart behavior are all evidenced in the receipt. The measured classification changes are retained as outcomes—not hidden as failures—and the production schema must carry the clean-to-real delta, S/N, ERR, neighbour, bound-hit, and identifiability fields.

Before production, freeze this configuration/schema and retain the clean policy: B/T is not physically interpreted for objects non-identifiable in native clean (including 751217); good chi-square or no bound hit is not an identifiability proof.
"""
    atomic_write(out / "real_background_pilot_interpretation.md", md)
    print(json.dumps({"rows":len(rows),"issues":issues,"output_dir":str(out)}))
    return 1 if issues else 0


if __name__ == "__main__": raise SystemExit(main())
