#!/usr/bin/env python3
"""Restart-safe corrected GOLD403 real-background E0/E1J pilot.

This runner deliberately takes the z=3 source image from
``make_exact_lenstronomy_bd_truth``.  It does *not* call either deprecated
``build_intrinsic_bd_model_z3`` or ``render_model_to_context``.  A physical
flux-scaled, already PSF-convolved exact image is deterministically added to
the real SCI context; the corresponding real ERR/segmentation arrays are
retained unchanged.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

import nbformat
from jupyter_client import KernelManager

from gold403_restartable_sweep import run_restartable_sweep
from run_gold403_controlled_recovery_diagnostics import (
    SETUP_CELLS,
    code_function_definitions,
    execute,
    notebook_sha256,
)


# The compact non-identifiable case, an identifiable n-boundary flip, and a
# stable control.  E1J is intentionally F444W-only by the frozen methodology.
CASES = [
    (751217, "F277W", "E0"), (751217, "F444W", "E0"), (751217, "F444W", "E1J"),
    (514739, "F277W", "E0"), (514739, "F444W", "E0"), (514739, "F444W", "E1J"),
    (162363, "F277W", "E0"), (162363, "F444W", "E0"), (162363, "F444W", "E1J"),
]

FIELDS = [
    "id", "source_id", "z_source", "target_filter", "evolution", "context_tile", "context_id",
    "status", "error", "morph_filter", "published_n", "input_bt", "input_disk",
    "native_clean_n", "native_bt", "native_bt_abs_error", "native_bt_identifiable", "native_clean_disk",
    "native_disk_re_pix", "native_bulge_re_pix",
    "clean_n", "clean_bt", "clean_single_chisq", "clean_bd_chisq", "clean_disk",
    "real_n", "real_re_arcsec", "real_q", "real_bt", "real_disk", "real_single_chisq", "real_bd_chisq",
    "delta_real_minus_clean_n", "delta_real_minus_clean_bt", "clean_to_real_flip",
    "target_fnu_jy", "measured_target_fnu_jy", "flux_conservation_frac", "source_to_target_ratio", "evolution_factor",
    "snr_empirical", "blank_ap_sigma", "n_blank_ap", "valid_err_fraction", "center_err_valid",
    "fit_radius_pix", "n_neighbours_modelled", "likelihood_fraction", "fit_records_json", "seed",
    "render_method",
]


def case_seed(case_id: int) -> int:
    """Return the same valid 32-bit deterministic seed convention as the sweep."""
    return 2026091900 + int(case_id)


def marker(output: str, name: str) -> object:
    found = re.findall(rf"^{re.escape(name)}(.*)$", output, flags=re.MULTILINE)
    if not found:
        raise RuntimeError(f"missing {name} marker in kernel output:\n{output[-4000:]}")
    return json.loads(found[-1])


def start_kernel(notebook: Path, diagnostics: Path, timeout: float):
    """Load only validated definitions; never execute notebook run-loop cells."""
    nb = nbformat.read(notebook, as_version=4)
    km = KernelManager(kernel_name="phd")
    km.start_kernel(cwd=str(notebook.parent))
    client = km.client(); client.start_channels()
    try:
        for index in SETUP_CELLS:
            execute(client, nb.cells[index].source, timeout=timeout, label=f"setup {index}")
        # Cell 35 provides real SCI/ERR/segmentation loading and deterministic injection.
        execute(client, code_function_definitions(nb.cells[35].source), timeout=timeout, label="context definitions")
        # Cell 37 provides photometry/radiometric helpers.  Its deprecated renderer is
        # defined but never invoked by this script; source rendering is Cell 49 only.
        execute(client, code_function_definitions(nb.cells[37].source), timeout=timeout, label="flux definitions")
        execute(client, code_function_definitions(nb.cells[41].source), timeout=timeout, label="real fit definitions")
        execute(client, code_function_definitions(nb.cells[49].source), timeout=timeout, label="exact truth definitions")
        execute(client, code_function_definitions(nb.cells[51].source), timeout=timeout, label="native baseline definitions")
        execute(client, code_function_definitions(nb.cells[52].source), timeout=timeout, label="native PSF correction")
        # Execute the quality-control cell itself because it builds the valid-context
        # manifest and replaces the selector.  It makes no source injections or fits.
        execute(client, nb.cells[42].source, timeout=timeout, label="ERR context quality control")
        bootstrap = f'''
from pathlib import Path
import json, random, copy, numpy as np
PILOT_DIAGNOSTICS = Path({str(diagnostics)!r}); PILOT_DIAGNOSTICS.mkdir(parents=True, exist_ok=True)
MODEL_PILOT_DIAG = PILOT_DIAGNOSTICS / "real"; MODEL_PILOT_DIAG.mkdir(exist_ok=True)
BD_SELFTEST_DIAG = PILOT_DIAGNOSTICS / "clean"; BD_SELFTEST_DIAG.mkdir(exist_ok=True)
MODEL_GALIGHT_PSO_REPEATS = 2
BD_SELFTEST_PSO_REPEATS = 2
BD_SELFTEST_TOTAL_FLUX = 1.0e4
BASELINE_TOTAL_FLUX = 1.0e4
BASELINE_PSO_REPEATS = 2
NATIVE_BASELINE_DIAG = PILOT_DIAGNOSTICS / "native"; NATIVE_BASELINE_DIAG.mkdir(exist_ok=True)
PILOT_FIT_RECORDS = []
_pilot_run_galight_model = run_galight_model
def _pilot_q(comp):
    return float(param_util.ellipticity2phi_q(float(comp["e1"]), float(comp["e2"]))[1])
def _pilot_hits(comp, lower, upper):
    hits=[]
    for key,value in comp.items():
        if key not in lower or key not in upper: continue
        try: value,lo,hi=float(value),float(lower[key]),float(upper[key])
        except (ValueError, TypeError): continue
        if abs(value-lo)<=1e-5*max(1.,abs(lo)): hits.append(key+":lower")
        if abs(value-hi)<=1e-5*max(1.,abs(hi)): hits.append(key+":upper")
    return hits
def run_galight_model(dp, source_params, n_components, savename, condition=None, pso_repeats=1):
    fit=_pilot_run_galight_model(dp, source_params, n_components, savename, condition, pso_repeats)
    comps=[]
    for ix,comp in enumerate(fit.final_result_galaxy[:int(n_components)]):
        comps.append({{"re_arcsec":float(comp["R_sersic"]),"n":float(comp["n_sersic"]),"q":_pilot_q(comp),"bound_hits":_pilot_hits(comp,source_params[3][ix],source_params[4][ix])}})
    PILOT_FIT_RECORDS.append({{"savename":str(savename),"n_components":int(n_components),"reduced_chisq":float(fit.reduced_Chisq),"components":comps}})
    return fit
'''
        execute(client, bootstrap, timeout=timeout, label="pilot bootstrap")
        return km, client
    except Exception:
        client.stop_channels(); km.shutdown_kernel(now=False); raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--force-case", action="append", type=int, default=[])
    parser.add_argument("--timeout-seconds", type=float, default=14400)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    notebook = args.notebook.resolve(); output = args.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    case_ids = list(range(1, len(CASES) + 1))
    manifest = [{"case_id": i, "source_id": oid, "target_filter": filt, "evolution": evo}
                for i, (oid, filt, evo) in zip(case_ids, CASES)]
    (output / "case_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    km, client = start_kernel(notebook, output / "diagnostics", args.timeout_seconds)
    config = {
        "stage_chain": "published->native_clean->z3_clean->z3_real_background",
        "pilot_cases": manifest,
        "source_renderer": "Lenstronomy ImageModel exact B+D truth (Cell 49)",
        "recovery": "Galight single + B+D, 2 PSO repeats",
        "real_background": "deterministic source addition to SCI; real ERR/SEG retained; no independent sky/noise",
        "psf": "position-dependent signed PSFEx; signed-total normalization; no clipping",
        "evolution": "E0 all filters; E1J F444W only",
        "notebook_sha256": notebook_sha256(notebook),
    }
    if args.prepare_only:
        client.stop_channels(); km.shutdown_kernel(now=False)
        print(f"Prepared {len(CASES)} quality-controlled pilot cases in {output}")
        return 0

    def runner(case_id: int) -> dict[str, object]:
        oid, target_filter, evolution = CASES[case_id - 1]
        seed = case_seed(case_id)
        code = f'''
PILOT_FIT_RECORDS.clear()
_oid={oid}; _filter={target_filter!r}; _evolution={evolution!r}; _seed={seed}
random.seed(_seed); np.random.seed(_seed)
_row=gold.loc[gold["id"].astype(int)==_oid].iloc[0]
_context=choose_contexts_for_object(_oid,1).iloc[0]
_native=run_native_clean_baseline(_row)
_sci,_err,_seg=load_context(_context["tile"],int(_context["context_id"]),_filter)
_image,_psf,_meta,_params,_truth0=make_exact_lenstronomy_bd_truth(_row,_filter,_context)
_truth=dict(_truth0)
_morph=choose_model_morphology(_row,_truth["mapped_source_wavelength_um"])
_truth.update({{"single_re_arcsec":float(_morph["single_re_arcsec"]),"single_q":float(_morph["single_q"]),"theta_image_rad":float(_truth["theta"]),"input_disk_classification":bool(_truth["catalog_disk_classification"]),"single_n":float(_truth["published_single_n"]),"bt":float(_truth["truth_bt"])}})
_phot=measure_source_photometry(_row)
_source_fnu,_fdiag=source_fnu_at_wavelength(_phot,_truth["mapped_source_wavelength_um"])
_ratio=source_to_target_fnu_ratio(float(_row["z"]),Z_TARGET)
_evo=1.0 if _evolution=="E0" else luminosity_evolution_factor(float(_row["z"]),Z_TARGET,exponent=ETA_J)
_target_fnu=float(_source_fnu)*float(_ratio)*float(_evo)
_stamp=np.asarray(_image,dtype=float)/float(np.sum(_image))*(_target_fnu/(1.0e6*PIX_SR))
_measured=float(np.sum(_stamp))*1.0e6*PIX_SR
_injected,_injection_slice=inject_center(_sci,_stamp)
_valid=np.isfinite(_sci)&np.isfinite(_err)&(_err>0)
_cy,_cx=_err.shape[0]//2,_err.shape[1]//2
_clean=run_exact_bd_validation(_row,_filter,_context)
_real=run_model_injected_galight_case(_row,_injected,_err,_seg,_psf,_truth,_filter,_evolution,_context)
_out={{"id":{case_id},"source_id":_oid,"z_source":float(_row["z"]),"target_filter":_filter,"evolution":_evolution,"context_tile":str(_context["tile"]),"context_id":int(_context["context_id"]),"status":"OK","error":"","morph_filter":str(_morph["morph_filter"]),"published_n":float(_truth["published_single_n"]),"input_bt":float(_truth["truth_bt"]),"input_disk":bool(_truth["catalog_disk_classification"]),"native_clean_n":float(_native["native_single_n_from_bd"]),"native_bt":float(_native["native_recovered_bt"]),"native_bt_abs_error":float(abs(_native["native_recovered_bt"]-_native["truth_bt"])),"native_bt_identifiable":bool(abs(_native["native_recovered_bt"]-_native["truth_bt"])<=.10),"native_clean_disk":bool(_native["native_clean_disk_classification"]),"native_disk_re_pix":float(_native["native_disk_re_over_pixel"]),"native_bulge_re_pix":float(_native["native_bulge_re_over_pixel"]),"clean_n":float(_clean["clean_single_n_from_bd"]),"clean_bt":float(_clean["recovered_bt"]),"clean_single_chisq":float(_clean["single_chisq"]),"clean_bd_chisq":float(_clean["bd_chisq"]),"clean_disk":bool(_clean["clean_model_disk_classification"]),"real_n":float(_real["recovered_n"]),"real_re_arcsec":float(_real["recovered_re_arcsec"]),"real_q":float(_real["recovered_q"]),"real_bt":float(_real["recovered_bt"]),"real_disk":bool(_real["recovered_disk"]),"real_single_chisq":float(_real["single_chisq"]),"real_bd_chisq":float(_real["bd_chisq"]),"delta_real_minus_clean_n":float(_real["recovered_n"]-_clean["clean_single_n_from_bd"]),"delta_real_minus_clean_bt":float(_real["recovered_bt"]-_clean["recovered_bt"]),"clean_to_real_flip":bool(_real["recovered_disk"]!=_clean["clean_model_disk_classification"]),"target_fnu_jy":_target_fnu,"measured_target_fnu_jy":_measured,"flux_conservation_frac":float(_measured/_target_fnu-1.0),"source_to_target_ratio":float(_ratio),"evolution_factor":float(_evo),"snr_empirical":float(_real["snr_empirical"]),"blank_ap_sigma":float(_real["blank_ap_sigma"]),"n_blank_ap":int(_real["n_blank_ap"]),"valid_err_fraction":float(np.mean(_valid)),"center_err_valid":bool(_valid[_cy,_cx]),"fit_radius_pix":int(_real["fit_radius_pix"]),"n_neighbours_modelled":int(_real["n_neighbours_modelled"]),"likelihood_fraction":float(_real["likelihood_fraction"]),"fit_records_json":json.dumps(PILOT_FIT_RECORDS,sort_keys=True),"seed":_seed,"render_method":"exact_lenstronomy_bd_truth_scaled_then_deterministic_SCI_addition"}}
print("GOLD403_PILOT_ROW="+json.dumps(_out,allow_nan=False,sort_keys=True))
'''
        return marker(execute(client, code, timeout=args.timeout_seconds, label=f"pilot case {case_id}"), "GOLD403_PILOT_ROW=")

    try:
        run_restartable_sweep(case_ids, output_csv=output / "real_background_pilot.csv", fieldnames=FIELDS,
            object_runner=runner, provenance_path=output / "provenance.json", log_path=output / "run.log",
            config=config, software_versions={"kernel": "phd"}, force_ids=set(args.force_case))
    finally:
        client.stop_channels(); km.shutdown_kernel(now=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
