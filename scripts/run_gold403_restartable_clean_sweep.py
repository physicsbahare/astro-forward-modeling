#!/usr/bin/env python3
"""Restart-safe representative native-clean -> z=3-clean GOLD403 sweep.

The supplied notebook remains the source of the validated renderer helpers.
This runner executes only setup/definition cells in a new kernel, freezes the
Cell-53 stratified selection, and uses the generic atomic checkpoint utility
after every object.  It never edits or executes the notebook's monolithic loop.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from gold403_restartable_sweep import run_restartable_sweep
from run_gold403_controlled_recovery_diagnostics import (
    SETUP_CELLS,
    code_function_definitions,
    execute,
    notebook_sha256,
)

import nbformat
from jupyter_client import KernelManager


FIELDS = [
    "id", "z_source", "morph_filter", "published_n", "published_re_arcsec", "published_q",
    "native_clean_n", "z3_clean_n", "delta_n_catalog_to_native", "delta_n_native_to_z3",
    "native_model_n_consistent", "input_bt", "native_recovered_bt", "z3_recovered_bt",
    "bt_native_abs_error", "bt_z3_abs_error", "bt_native_identifiable", "bt_z3_identifiable",
    "native_disk_re_pix", "native_bulge_re_pix", "z3_disk_re_pix", "z3_bulge_re_pix",
    "z3_disk_re_over_psf", "z3_bulge_re_over_psf", "native_clean_disk", "z3_clean_disk",
    "resolution_classification_flip", "native_bd_chisq", "native_single_chisq", "z3_bd_chisq",
    "z3_single_chisq", "fit_records_json", "seed_native", "seed_z3", "status", "error",
]


def extract_marker(output: str, marker: str) -> object:
    matches = re.findall(rf"^{re.escape(marker)}(.*)$", output, flags=re.MULTILINE)
    if not matches:
        raise RuntimeError(f"missing {marker!r} marker in kernel output:\n{output[-4000:]}")
    return json.loads(matches[-1])


def setup_kernel(notebook: Path, diagnostics: Path, timeout: float):
    data = nbformat.read(notebook, as_version=4)
    km = KernelManager(kernel_name="phd")
    km.start_kernel(cwd=str(notebook.parent))
    client = km.client(); client.start_channels()
    try:
        for index in SETUP_CELLS:
            execute(client, "".join(data.cells[index].source), timeout=timeout, label=f"setup {index}")
        # Cell 51 contains the native clean functions but also an old run loop.
        execute(client, code_function_definitions("".join(data.cells[51].source)), timeout=timeout, label="native definitions")
        # Cell 52 replaces the native PSF helper with the corrected full-row API.
        execute(client, code_function_definitions("".join(data.cells[52].source)), timeout=timeout, label="native PSF correction")
        execute(client, code_function_definitions("".join(data.cells[49].source)), timeout=timeout, label="z3 exact definitions")
        bootstrap = f'''
from pathlib import Path
import json, random, copy, numpy as np
SWEEP_DIAGNOSTICS = Path({str(diagnostics)!r}); SWEEP_DIAGNOSTICS.mkdir(parents=True, exist_ok=True)
BASELINE_TOTAL_FLUX = 1.0e4; BASELINE_PSO_REPEATS = 2
BD_SELFTEST_TOTAL_FLUX = 1.0e4; BD_SELFTEST_PSO_REPEATS = 2
NATIVE_BASELINE_DIAG = SWEEP_DIAGNOSTICS / "native"; NATIVE_BASELINE_DIAG.mkdir(exist_ok=True)
BD_SELFTEST_DIAG = SWEEP_DIAGNOSTICS / "z3"; BD_SELFTEST_DIAG.mkdir(exist_ok=True)
SWEEP_FIT_RECORDS = []
_sweep_original_run_galight_model = run_galight_model
def _sweep_q(comp):
    return float(param_util.ellipticity2phi_q(float(comp["e1"]), float(comp["e2"]))[1])
def _sweep_hits(comp, lower, upper):
    hits=[]
    for key, value in comp.items():
        if key not in lower or key not in upper: continue
        try: value,lo,hi=float(value),float(lower[key]),float(upper[key])
        except (ValueError, TypeError): continue
        if abs(value-lo)<=1e-5*max(1.,abs(lo)): hits.append(key+":lower")
        if abs(value-hi)<=1e-5*max(1.,abs(hi)): hits.append(key+":upper")
    return hits
def run_galight_model(dp, source_params, n_components, savename, condition=None, pso_repeats=1):
    fit=_sweep_original_run_galight_model(dp, source_params, n_components, savename, condition, pso_repeats)
    comps=[]
    for index, component in enumerate(fit.final_result_galaxy[:int(n_components)]):
        comps.append({{"re_arcsec": float(component["R_sersic"]), "n": float(component["n_sersic"]),
                      "q": _sweep_q(component), "bound_hits": _sweep_hits(component, source_params[3][index], source_params[4][index])}})
    SWEEP_FIT_RECORDS.append({{"savename":str(savename),"n_components":int(n_components),"reduced_chisq":float(fit.reduced_Chisq),"components":comps}})
    return fit
'''
        execute(client, bootstrap, timeout=timeout, label="sweep bootstrap")
        selection = execute(client, '''
size_rows=[]
for _, row in gold.iterrows():
    zs=float(row["z"]); morph=choose_model_morphology(row,mapped_source_wavelength_um("F444W",zs))
    scale=float(Planck18.angular_diameter_distance(zs).value/Planck18.angular_diameter_distance(Z_TARGET).value)
    size_rows.append({"id":int(row["id"]),"z":zs,"z3_disk_re_pix":float(morph["disk_re_arcsec"])*scale/PIX})
size_good=pd.DataFrame(size_rows); size_good["rank_z"]=size_good["z"].rank(pct=True); size_good["rank_size"]=size_good["z3_disk_re_pix"].rank(pct=True)
size_good=size_good.sort_values(["rank_z","rank_size"]).reset_index(drop=True)
sample_ids=size_good.iloc[np.unique(np.linspace(0,len(size_good)-1,30).astype(int))]["id"].astype(int).tolist()
for diagnostic_id in [751217,322095,162363]:
    if diagnostic_id not in sample_ids: sample_ids.append(diagnostic_id)
sample_ids=list(dict.fromkeys(sample_ids))
print("GOLD403_SELECTION="+json.dumps(sample_ids))
''', timeout=timeout, label="stratified selection")
        return km, client, extract_marker(selection, "GOLD403_SELECTION=")
    except Exception:
        client.stop_channels(); km.shutdown_kernel(now=False); raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--force-id", action="append", type=int, default=[])
    parser.add_argument("--timeout-seconds", type=float, default=14400)
    parser.add_argument("--prepare-only", action="store_true", help="validate helpers and freeze selection without fitting")
    args=parser.parse_args(); notebook=args.notebook.resolve(); out=args.output_dir.resolve(); out.mkdir(parents=True,exist_ok=True)
    km, client, selection = setup_kernel(notebook, out/"diagnostics", args.timeout_seconds)
    if len(selection) != 31 or len(set(selection)) != 31:
        raise RuntimeError(f"expected the frozen 31-object selection; got {len(selection)} IDs")
    (out/"selected_ids.json").write_text(json.dumps(selection, indent=2)+"\n", encoding="utf-8")
    config={"stage_chain":"published->native_clean->z3_clean","renderer":"Lenstronomy ImageModel + Galight","target_filter":"F444W","pso_repeats":2,"seed_rule":"2026091900 + object_id (native), +1 (z3)","notebook_sha256":notebook_sha256(notebook),"selection_count":len(selection),"bt_identify_tolerance":0.10,"native_n_tolerance":0.50}
    if args.prepare_only:
        client.stop_channels(); km.shutdown_kernel(now=False)
        print(f"Prepared {len(selection)} selected IDs in {out}")
        return 0
    def runner(oid: int) -> dict[str, object]:
        code=f'''
SWEEP_FIT_RECORDS.clear()
_oid=int({oid}); _row=gold.loc[gold["id"].astype(int)==_oid].iloc[0]
_seed_native=2026091900+_oid; _seed_z3=_seed_native+1
random.seed(_seed_native); np.random.seed(_seed_native)
_native=run_native_clean_baseline(_row)
_context=choose_contexts_for_object(_oid,1).iloc[0]
random.seed(_seed_z3); np.random.seed(_seed_z3)
_z3=run_exact_bd_validation(_row,"F444W",_context)
_bne=abs(float(_native["native_recovered_bt"])-float(_native["truth_bt"])); _bze=abs(float(_z3["recovered_bt"])-float(_z3["truth_bt"]))
_out={{"id":_oid,"z_source":float(_row["z"]),"morph_filter":_native["morph_filter"],"published_n":float(_native["published_single_n"]),"published_re_arcsec":float(_native["published_single_re"]),"published_q":float(_native["published_single_q"]),"native_clean_n":float(_native["native_single_n_from_bd"]),"z3_clean_n":float(_z3["clean_single_n_from_bd"]),"delta_n_catalog_to_native":float(_native["native_single_n_from_bd"]-_native["published_single_n"]),"delta_n_native_to_z3":float(_z3["clean_single_n_from_bd"]-_native["native_single_n_from_bd"]),"native_model_n_consistent":bool(abs(float(_native["native_single_n_from_bd"]-_native["published_single_n"]))<=0.50),"input_bt":float(_native["truth_bt"]),"native_recovered_bt":float(_native["native_recovered_bt"]),"z3_recovered_bt":float(_z3["recovered_bt"]),"bt_native_abs_error":float(_bne),"bt_z3_abs_error":float(_bze),"bt_native_identifiable":bool(_bne<=0.10),"bt_z3_identifiable":bool(_bze<=0.10),"native_disk_re_pix":float(_native["native_disk_re_over_pixel"]),"native_bulge_re_pix":float(_native["native_bulge_re_over_pixel"]),"z3_disk_re_pix":float(_z3["disk_re_over_pixel"]),"z3_bulge_re_pix":float(_z3["bulge_re_over_pixel"]),"z3_disk_re_over_psf":float(_z3["disk_re_over_psf"]),"z3_bulge_re_over_psf":float(_z3["bulge_re_over_psf"]),"native_clean_disk":bool(_native["native_clean_disk_classification"]),"z3_clean_disk":bool(_z3["clean_model_disk_classification"]),"resolution_classification_flip":bool(_native["native_clean_disk_classification"]!=_z3["clean_model_disk_classification"]),"native_bd_chisq":float(_native["native_bd_chisq"]),"native_single_chisq":float(_native["native_single_chisq"]),"z3_bd_chisq":float(_z3["bd_chisq"]),"z3_single_chisq":float(_z3["single_chisq"]),"fit_records_json":json.dumps(SWEEP_FIT_RECORDS,sort_keys=True),"seed_native":_seed_native,"seed_z3":_seed_z3,"status":"OK"}}
print("GOLD403_SWEEP_ROW="+json.dumps(_out,allow_nan=False,sort_keys=True))
'''
        output=execute(client, code, timeout=args.timeout_seconds, label=f"sweep ID {oid}")
        return extract_marker(output,"GOLD403_SWEEP_ROW=")
    try:
        run_restartable_sweep(
            selection,
            output_csv=out / "clean_native_to_z3_identifiability_sweep_31.csv",
            fieldnames=FIELDS,
            object_runner=runner,
            provenance_path=out / "provenance.json",
            log_path=out / "run.log",
            config=config,
            software_versions={"kernel": "phd"},
            force_ids=set(args.force_id),
        )
    finally:
        client.stop_channels(); km.shutdown_kernel(now=False)
    return 0

if __name__=="__main__": raise SystemExit(main())
