#!/usr/bin/env python3
"""Run controlled, checkpointed z=3 exact-B+D recovery diagnostics.

This is deliberately a *recovery gate*, rather than the production sweep.  It
loads the validated helper definitions from the supplied notebook in a fresh
Jupyter kernel, freezes each object's Lenstronomy truth image/context PSF and
initial parameters once, and then repeats only the stochastic Galight PSO.
Every attempted repeat receives its own JSON receipt and is appended atomically
to a resumable CSV.  The source notebook is never modified.

Example (run from the Passive_Spiral project):
  conda run -n phd python astro-forward-modeling/scripts/
    run_gold403_controlled_recovery_diagnostics.py \
    --notebook Codes/05_GOLD403_z3_MODEL_based_injection_FAST_PILOT.ipynb \
    --output-dir Data/forward_z3_GOLD403_v1/model_based_v1/run_receipts/
      controlled_recovery_20260919
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
from pathlib import Path
import queue
import tempfile
import textwrap
import time
from typing import Iterable

import nbformat
from jupyter_client import KernelManager


OBJECT_REPEATS = {751217: 5, 322095: 2, 162363: 2}
# Cell 11 restores the ACS F814W throughput path consumed by Cell 12.
SETUP_CELLS = (2, 4, 6, 10, 11, 12, 13, 15, 17, 19, 20, 22, 24, 26, 35, 37)


def atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


def atomic_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", newline="", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


def code_function_definitions(source: str) -> str:
    """Return imports and definitions but no notebook execution/fit loops."""
    tree = ast.parse(source)
    retained = [
        node
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef))
    ]
    return "\n\n".join(ast.unparse(node) for node in retained) + "\n"


def wait_for_idle(client, *, timeout: float) -> str:
    deadline = time.monotonic() + timeout
    messages: list[str] = []
    while time.monotonic() < deadline:
        try:
            message = client.get_iopub_msg(
                timeout=min(30, max(1, deadline - time.monotonic()))
            )
        except queue.Empty:
            # Galight/Lenstronomy can spend longer than the channel poll
            # interval in a PSO call without emitting a stream message.
            continue
        kind = message["msg_type"]
        content = message["content"]
        if kind == "stream":
            messages.append(content.get("text", ""))
        elif kind == "error":
            messages.append("\n".join(content.get("traceback", [])))
        elif kind == "status" and content.get("execution_state") == "idle":
            return "".join(messages)
    raise TimeoutError("kernel execution did not become idle before timeout")


def execute(client, code: str, *, timeout: float, label: str) -> str:
    message_id = client.execute(code, store_history=False, allow_stdin=False)
    output = wait_for_idle(client, timeout=timeout)
    # A cell can report an error then become idle.  Detect the traceback output
    # rather than accidentally continuing with partially initialized helpers.
    if "\u001b[31m" in output or "Traceback (most recent call last)" in output:
        raise RuntimeError(f"kernel failure in {label}:\n{output[-4000:]}")
    return output


def notebook_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def existing_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def completed_keys(rows: Iterable[dict[str, str]]) -> set[tuple[str, str]]:
    return {
        (str(row["id"]), str(row["repeat_index"]))
        for row in rows
        if row.get("status") in {"OK", "ERROR"}
    }


def diagnostic_kernel_code(output_dir: Path, object_repeats: dict[int, int]) -> str:
    """The code run after validated notebook helpers are loaded into the kernel."""
    return textwrap.dedent(
        f"""
        import copy, csv, hashlib, json, os, random, tempfile, traceback
        from pathlib import Path
        import numpy as np
        import pandas as pd
        import galight, lenstronomy

        CONTROLLED_RECOVERY_DIR = Path({str(output_dir)!r})
        CONTROLLED_RECOVERY_DIR.mkdir(parents=True, exist_ok=True)
        CONTROLLED_RECOVERY_REPEATS = {object_repeats!r}
        CONTROLLED_RECOVERY_FILTER = "F444W"
        CONTROLLED_RECOVERY_PSO_REPEATS = 2
        # These are frozen values from notebook Cell 49.  Function-only AST
        # loading intentionally excludes its top-level assignments.
        BD_SELFTEST_TOTAL_FLUX = 1.0e4
        BD_SELFTEST_PSO_REPEATS = 2

        def _controlled_jsonable(value):
            if isinstance(value, float):
                return value if np.isfinite(value) else None
            if isinstance(value, (str, int, bool)) or value is None:
                return value
            if isinstance(value, Path):
                return str(value)
            if isinstance(value, np.generic):
                return value.item()
            if isinstance(value, np.ndarray):
                return value.tolist()
            if isinstance(value, dict):
                return {{str(key): _controlled_jsonable(item) for key, item in value.items()}}
            if isinstance(value, (list, tuple)):
                return [_controlled_jsonable(item) for item in value]
            return repr(value)

        def _controlled_atomic_json(path, payload):
            path = Path(path)
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as h:
                json.dump(_controlled_jsonable(payload), h, indent=2, sort_keys=True, allow_nan=False)
                h.write("\\n"); h.flush(); os.fsync(h.fileno()); tmp = h.name
            os.replace(tmp, path)

        def _controlled_q(component):
            _, q = param_util.ellipticity2phi_q(float(component["e1"]), float(component["e2"]))
            return float(q)

        def _controlled_bound_hits(component, lower, upper, tolerance=1.e-5):
            hits = []
            for key, value in component.items():
                if key not in lower or key not in upper:
                    continue
                try:
                    value = float(value); lo = float(lower[key]); hi = float(upper[key])
                except (TypeError, ValueError):
                    continue
                if abs(value - lo) <= tolerance * max(1., abs(lo)):
                    hits.append(f"{{key}}:lower")
                if abs(value - hi) <= tolerance * max(1., abs(hi)):
                    hits.append(f"{{key}}:upper")
            return hits

        def _controlled_fit_record(dp, bd_start, single_start, oid, repeat_index, seed):
            random.seed(seed); np.random.seed(seed)
            fit_bd = run_galight_model(
                dp, copy.deepcopy(bd_start), n_components=2,
                savename=CONTROLLED_RECOVERY_DIR / f"ID{{oid}}_z3_BD_repeat{{repeat_index:02d}}",
                condition=bd_condition, pso_repeats=CONTROLLED_RECOVERY_PSO_REPEATS,
            )
            disk, bulge = fit_bd.final_result_galaxy[:2]
            fd = float(disk["flux_sersic_model"]); fb = float(bulge["flux_sersic_model"])
            random.seed(seed); np.random.seed(seed)
            fit_single = run_galight_model(
                dp, copy.deepcopy(single_start), n_components=1,
                savename=CONTROLLED_RECOVERY_DIR / f"ID{{oid}}_z3_single_repeat{{repeat_index:02d}}",
                condition=None, pso_repeats=CONTROLLED_RECOVERY_PSO_REPEATS,
            )
            single = fit_single.final_result_galaxy[0]
            return {{
                "recovered_bt": fb / (fb + fd),
                "recovered_disk_re_arcsec": float(disk["R_sersic"]),
                "recovered_bulge_re_arcsec": float(bulge["R_sersic"]),
                "recovered_disk_q": _controlled_q(disk),
                "recovered_bulge_q": _controlled_q(bulge),
                "clean_single_n": float(single["n_sersic"]),
                "clean_single_re_arcsec": float(single["R_sersic"]),
                "clean_single_q": _controlled_q(single),
                "bd_chisq": float(fit_bd.reduced_Chisq),
                "single_chisq": float(fit_single.reduced_Chisq),
                "bd_bound_hits": _controlled_bound_hits(disk, bd_start[3][0], bd_start[4][0])
                    + _controlled_bound_hits(bulge, bd_start[3][1], bd_start[4][1]),
                "single_bound_hits": _controlled_bound_hits(single, single_start[3][0], single_start[4][0]),
                "bd_fitting_kwargs": copy.deepcopy(fit_bd.fitting_kwargs_list),
                "single_fitting_kwargs": copy.deepcopy(fit_single.fitting_kwargs_list),
            }}

        for _controlled_oid, _controlled_nrepeat in CONTROLLED_RECOVERY_REPEATS.items():
            _controlled_row = gold.loc[gold["id"].astype(int) == int(_controlled_oid)].iloc[0].copy()
            _controlled_context = choose_contexts_for_object(int(_controlled_oid), 1).iloc[0].copy()
            _controlled_image, _controlled_psf, _controlled_meta, _controlled_truth_params, _controlled_truth = make_exact_lenstronomy_bd_truth(
                _controlled_row, CONTROLLED_RECOVERY_FILTER, _controlled_context
            )
            # The perturbation uses fixed factors, but this explicit seed makes its provenance unambiguous.
            random.seed(900000 + int(_controlled_oid)); np.random.seed(900000 + int(_controlled_oid))
            _controlled_bd_start = perturb_bd_source_params(copy.deepcopy(_controlled_truth_params))
            _controlled_single_start = make_single_start_for_bd_truth(
                _controlled_row, _controlled_truth, _controlled_meta, _controlled_image.shape[0]
            )
            _controlled_psf_array = np.asarray(_controlled_psf, dtype=float)
            _controlled_static = {{
                "id": int(_controlled_oid), "z_source": float(_controlled_row["z"]),
                "filter": CONTROLLED_RECOVERY_FILTER,
                "context": _controlled_context.to_dict(),
                "truth": copy.deepcopy(_controlled_truth),
                "truth_image_sha256": hashlib.sha256(np.asarray(_controlled_image, dtype=np.float64).tobytes()).hexdigest(),
                "psf_sha256": hashlib.sha256(_controlled_psf_array.astype(np.float64).tobytes()).hexdigest(),
                "psf_shape": list(_controlled_psf_array.shape),
                "psf_sum": float(np.sum(_controlled_psf_array)),
                "psf_min": float(np.min(_controlled_psf_array)),
                "psf_negative_elements": int(np.sum(_controlled_psf_array < 0)),
                "bd_start": copy.deepcopy(_controlled_bd_start),
                "single_start": copy.deepcopy(_controlled_single_start),
                "bounds": {{"bd_lower": _controlled_bd_start[3], "bd_upper": _controlled_bd_start[4],
                           "single_lower": _controlled_single_start[3], "single_upper": _controlled_single_start[4]}},
                "fitting": {{"algorithm": "PSO", "pso_repeats": CONTROLLED_RECOVERY_PSO_REPEATS,
                            "fitting_level": "norm", "threadCount": 1}},
                "software_versions": {{"galight": galight.__version__, "lenstronomy": lenstronomy.__version__, "numpy": np.__version__}},
            }}
            _controlled_atomic_json(CONTROLLED_RECOVERY_DIR / f"ID{{_controlled_oid}}_frozen_inputs.json", _controlled_static)
            for _controlled_repeat in range(1, int(_controlled_nrepeat) + 1):
                _controlled_seed = 2026091900 + int(_controlled_oid) * 10 + _controlled_repeat
                _controlled_record = {{**_controlled_static, "repeat_index": _controlled_repeat,
                    "seed_python": _controlled_seed, "seed_numpy": _controlled_seed,
                    "seed_scope": "set immediately before each Galight PSO call; Galight API exposes no separate PSO seed"}}
                try:
                    _controlled_dp, _ = build_galight_data_process(
                        _controlled_image, np.ones_like(_controlled_image, dtype=float),
                        np.zeros_like(_controlled_image, dtype=int), _controlled_psf, _controlled_meta,
                        neighbour_metas=[], model_labels=[]
                    )
                    _controlled_metrics = _controlled_fit_record(
                        _controlled_dp, _controlled_bd_start, _controlled_single_start,
                        int(_controlled_oid), _controlled_repeat, _controlled_seed
                    )
                    _controlled_record.update(_controlled_metrics)
                    _controlled_record["disk_classification"] = bool(
                        _controlled_metrics["clean_single_n"] < NSERSIC_MAX and _controlled_metrics["recovered_bt"] < BT_MAX
                    )
                    _controlled_record["status"] = "OK"
                except Exception as _controlled_exc:
                    _controlled_record.update({{"status": "ERROR", "error": repr(_controlled_exc),
                                               "traceback": traceback.format_exc()}})
                _controlled_atomic_json(
                    CONTROLLED_RECOVERY_DIR / f"ID{{_controlled_oid}}_z3_repeat{{_controlled_repeat:02d}}.json",
                    _controlled_record
                )
                print(json.dumps({{"id": int(_controlled_oid), "repeat": _controlled_repeat,
                                  "status": _controlled_record["status"],
                                  "n": _controlled_record.get("clean_single_n"),
                                  "bt": _controlled_record.get("recovered_bt")}}, sort_keys=True), flush=True)
        """
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--kernel-name", default="phd")
    parser.add_argument("--timeout-seconds", type=float, default=7200)
    arguments = parser.parse_args()
    notebook = arguments.notebook.resolve()
    output_dir = arguments.output_dir.resolve()
    if not notebook.is_file():
        raise FileNotFoundError(notebook)
    output_dir.mkdir(parents=True, exist_ok=True)

    receipt_csv = output_dir / "controlled_recovery_summary.csv"
    host_log = output_dir / "host_run.log"
    provenance = {
        "notebook": str(notebook),
        "notebook_sha256": notebook_sha256(notebook),
        "setup_cells": list(SETUP_CELLS),
        "object_repeats": OBJECT_REPEATS,
        "target_filter": "F444W",
        "pso_repeats": 2,
        "purpose": "Controlled recovery gate after the interrupted clean sweep.",
    }
    atomic_json(output_dir / "provenance.json", provenance)

    notebook_data = nbformat.read(notebook, as_version=4)
    km = KernelManager(kernel_name=arguments.kernel_name)
    km.start_kernel(cwd=str(notebook.parent))
    client = km.client()
    client.start_channels()
    rows: list[dict[str, object]] = []
    try:
        for index in SETUP_CELLS:
            output = execute(
                client, "".join(notebook_data.cells[index].source),
                timeout=arguments.timeout_seconds, label=f"notebook setup cell {index}"
            )
            host_log.write_text(host_log.read_text() + f"setup cell {index}:\n{output}\n" if host_log.exists() else f"setup cell {index}:\n{output}\n")
        exact_definitions = code_function_definitions("".join(notebook_data.cells[49].source))
        execute(client, exact_definitions, timeout=arguments.timeout_seconds, label="exact B+D definitions")
        output = execute(
            client, diagnostic_kernel_code(output_dir, OBJECT_REPEATS),
            timeout=arguments.timeout_seconds, label="controlled recovery diagnostics"
        )
        with host_log.open("a", encoding="utf-8") as handle:
            handle.write(f"controlled diagnostic output:\n{output}\n")
    finally:
        client.stop_channels()
        km.shutdown_kernel(now=False)

    for receipt in sorted(output_dir.glob("ID*_z3_repeat*.json")):
        record = json.loads(receipt.read_text(encoding="utf-8"))
        rows.append({
            "id": record["id"], "repeat_index": record["repeat_index"], "status": record["status"],
            "seed_python": record.get("seed_python"), "seed_numpy": record.get("seed_numpy"),
            "clean_single_n": record.get("clean_single_n"), "clean_single_re_arcsec": record.get("clean_single_re_arcsec"),
            "clean_single_q": record.get("clean_single_q"), "recovered_bt": record.get("recovered_bt"),
            "recovered_disk_re_arcsec": record.get("recovered_disk_re_arcsec"),
            "recovered_bulge_re_arcsec": record.get("recovered_bulge_re_arcsec"),
            "recovered_disk_q": record.get("recovered_disk_q"), "recovered_bulge_q": record.get("recovered_bulge_q"),
            "bd_chisq": record.get("bd_chisq"), "single_chisq": record.get("single_chisq"),
            "disk_classification": record.get("disk_classification"),
            "bd_bound_hits": json.dumps(record.get("bd_bound_hits", [])),
            "single_bound_hits": json.dumps(record.get("single_bound_hits", [])),
            "error": record.get("error", ""),
        })
    fields = list(rows[0]) if rows else ["id", "repeat_index", "status"]
    atomic_csv(receipt_csv, rows, fields)
    print(f"Wrote {len(rows)} independent diagnostic receipts to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
