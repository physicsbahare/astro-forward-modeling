#!/usr/bin/env python3
"""C6b: matched-PSF noiseless common-scene AstroPhot/Imfit diagnostic."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import time

import numpy as np
from astropy.io import fits
from scipy.special import gamma, gammaincinv
import torch
import astrophot as ap

ASTROPHOT_VERSION = "0.18.0"
ASTROPHOT_TAG_COMMIT = "b20c98b4acba4b9708938610e61aced60f205620"
TORCH_VERSION = "2.14.0+cpu"
C5O_RUN_ID = 33819349854
C5O_ARTIFACT_ID = 9917787955
C5O_ARTIFACT_SHA256 = "4d168eb8f26c7be0b2906cd659c12d99ae327b4ef3f2aabfb19422e35094d74b"
PA_ENDPOINT_EPS_RAD = 1e-10


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def scalar(value) -> float:
    if hasattr(value, "detach"):
        value = value.detach().cpu().numpy()
    return float(np.asarray(value))


def array(image) -> np.ndarray:
    data = image.data
    if hasattr(data, "detach"):
        data = data.detach().cpu().numpy()
    return np.asarray(data, dtype=float)


def sersic_bn(n: float) -> float:
    return float(gammaincinv(2.0 * n, 0.5))


def total_flux_to_ie(total_flux: float, n: float, re: float, q: float) -> float:
    bn = sersic_bn(n)
    coeff = 2.0 * math.pi * q * re**2 * n * math.exp(bn) * bn ** (-2.0 * n) * gamma(2.0 * n)
    return float(total_flux / coeff)


def configuration() -> dict:
    return {
        "stage": "C6b matched-PSF noiseless common-scene AstroPhot/Imfit diagnostic",
        "astrophot_version": ASTROPHOT_VERSION,
        "astrophot_tag_commit": ASTROPHOT_TAG_COMMIT,
        "torch_version": TORCH_VERSION,
        "c5o_run_id": C5O_RUN_ID,
        "c5o_artifact_id": C5O_ARTIFACT_ID,
        "c5o_artifact_sha256": C5O_ARTIFACT_SHA256,
        "host_n": 1.0,
        "modules": ["A", "B"],
        "ratios": [1.0, 10.0],
        "stamp": 201,
        "pixelscale": 1.0,
        "crpix": [100.0, 100.0],
        "center": [0.0, 0.0],
        "truth": {"pa_deg": 45.0, "q": 0.6, "n": 1.0, "re": 16.0, "host_flux": 1.0},
        "shape_bounds": {"q": [0.15, 1.0], "n": [0.5, 6.0], "re": [0.5, 60.0]},
        "point_flux_bounds": [0.0, 1.0e6],
        "host_amplitude": "AstroPhot Ie; no claimed Imfit-total-flux ceiling equivalence",
        "pa_native": "AstroPhot cyclic East-of-North on (0,pi); mapping audited with 45/135 deg truth renders",
        "pa_endpoint_epsilon_rad": PA_ENDPOINT_EPS_RAD,
        "psf": "archived matched signed PSF; negative samples retained; no manual normalization",
        "objective": "full 201x201 unit-variance Gaussian least squares; recomputed pixel SSE",
        "lm": {"max_iter": 100, "relative_tolerance": 1e-5},
        "winner": "minimum finite recomputed SSE per case regardless of optimizer message",
        "acceptance": "diagnostic completeness/algebra only; no morphology recovery band",
        "claim": "cross-fitter common-scene diagnostic only",
    }


def interior_pa(rad: float) -> float:
    x = float(rad % math.pi)
    if x <= 0.0:
        return PA_ENDPOINT_EPS_RAD
    if x >= math.pi:
        return math.pi - PA_ENDPOINT_EPS_RAD
    return x


def mapped_pa(imfit_deg: float, mapping: str) -> float:
    if mapping == "negate_imfit":
        deg = (-imfit_deg) % 180.0
    elif mapping == "same_imfit":
        deg = imfit_deg % 180.0
    else:
        raise ValueError(mapping)
    return interior_pa(math.radians(deg))


def build_model(data: np.ndarray, psf_data: np.ndarray, start: dict):
    target = ap.TargetImage(
        data=data,
        variance=np.ones_like(data),
        pixelscale=1.0,
        crpix=[100.0, 100.0],
    )
    psf = ap.PSFImage(data=psf_data)
    host = ap.Model(
        name="host",
        model_type="sersic galaxy model",
        target=target,
        psf=psf,
        center={"value": [0.0, 0.0], "dynamic": False},
        PA={"value": interior_pa(start["pa_rad"]), "valid": (0.0, math.pi)},
        q={"value": start["q"], "valid": (0.15, 1.0)},
        n={"value": start["n"], "valid": (0.5, 6.0)},
        Re={"value": start["re"], "valid": (0.5, 60.0)},
        Ie={"value": total_flux_to_ie(start["host_flux"], start["n"], start["re"], start["q"]), "valid": (0.0, None)},
    )
    point = ap.Model(
        name="nucleus",
        model_type="point model",
        target=target,
        psf=psf,
        center={"value": [0.0, 0.0], "dynamic": False},
        flux={"value": start["point_flux"], "valid": (0.0, 1.0e6)},
    )
    model = ap.Model(name="host_plus_nucleus", model_type="group model", models=[host, point], target=target)
    model.initialize()
    return target, psf, host, point, model


def render_state(data: np.ndarray, psf: np.ndarray, pa_deg: float, ratio: float):
    start = {"pa_rad": math.radians(pa_deg), "q": 0.6, "n": 1.0, "re": 16.0, "host_flux": 1.0, "point_flux": ratio}
    _, _, host, point, model = build_model(data, psf, start)
    model_arr = array(model())
    host_arr = array(host())
    point_arr = array(point())
    resid = data - model_arr
    return {
        "pa_deg": pa_deg,
        "sse": float(np.sum(resid**2)),
        "residual_l1_over_data_l1": float(np.sum(np.abs(resid)) / np.sum(np.abs(data))),
        "host_rendered_sum": float(host_arr.sum()),
        "point_rendered_sum": float(point_arr.sum()),
        "point_parameter": scalar(point.flux.value),
    }, model_arr, resid, host_arr, point_arr


def near_bound(name: str, value: float) -> bool:
    bounds = {"q": (0.15, 1.0), "n": (0.5, 6.0), "re": (0.5, 60.0), "point_flux": (0.0, 1.0e6)}
    lo, hi = bounds[name]
    atol = 1e-6 * max(1.0, hi - lo)
    return bool(abs(value - lo) <= atol or abs(value - hi) <= atol)


def fit_attempt(data: np.ndarray, psf: np.ndarray, start: dict):
    started = time.monotonic()
    target, psf_image, host, point, model = build_model(data, psf, start)
    initial_model = array(model())
    initial_sse = float(np.sum((data - initial_model) ** 2))
    outcome = "completed"
    message = ""
    loss_history = []
    try:
        opt = ap.fit.LM(model, max_iter=100, relative_tolerance=1e-5, verbose=0)
        opt.fit(update_uncertainty=False)
        message = str(opt.message)
        loss_history = [float(x) for x in getattr(opt, "loss_history", [])]
    except Exception as exc:
        outcome = "exception"
        message = f"{type(exc).__name__}: {exc}"
    wall = time.monotonic() - started
    try:
        model_arr = array(model())
        host_arr = array(host())
        point_arr = array(point())
        resid = data - model_arr
        pa = scalar(host.PA.value)
        q = scalar(host.q.value)
        n = scalar(host.n.value)
        re = scalar(host.Re.value)
        ie = scalar(host.Ie.value)
        point_flux = scalar(point.flux.value)
        finite = bool(np.isfinite(model_arr).all() and np.isfinite(resid).all() and all(np.isfinite([pa, q, n, re, ie, point_flux])))
        sse = float(np.sum(resid**2)) if finite else None
        l1 = float(np.sum(np.abs(resid)) / np.sum(np.abs(data))) if finite else None
        bound_hits = [name for name, val in [("q", q), ("n", n), ("re", re), ("point_flux", point_flux)] if near_bound(name, val)]
        result = {
            "outcome": outcome,
            "message": message,
            "wall_seconds": wall,
            "initial_sse": initial_sse,
            "loss_history": loss_history,
            "finite": finite,
            "pa_rad": pa,
            "pa_deg": math.degrees(pa) % 180.0,
            "q": q,
            "n": n,
            "re": re,
            "ie": ie,
            "point_flux": point_flux,
            "host_rendered_sum": float(host_arr.sum()),
            "point_rendered_sum": float(point_arr.sum()),
            "sse": sse,
            "residual_l1_over_data_l1": l1,
            "bound_hits": bound_hits,
        }
        return result, model_arr, resid, host_arr, point_arr
    except Exception as exc:
        result = {"outcome": outcome, "message": message, "wall_seconds": wall, "initial_sse": initial_sse, "loss_history": loss_history, "finite": False, "render_exception": f"{type(exc).__name__}: {exc}", "sse": None, "bound_hits": []}
        empty = np.full_like(data, np.nan)
        return result, empty, empty, empty, empty


def case_name(module: str, ratio: float) -> str:
    return f"n1_{module}_ratio{int(ratio)}"


def run(source: Path, out: Path) -> dict:
    assert importlib.metadata.version("astrophot") == ASTROPHOT_VERSION
    assert torch.__version__ == TORCH_VERSION
    cfg = configuration()
    out.mkdir(parents=True, exist_ok=True)
    dump(out / "config.json", cfg)

    expected = [source / "inputs" / name for name in ["data_A_ratio1.fits", "data_A_ratio10.fits", "data_B_ratio1.fits", "data_B_ratio10.fits", "noise.fits", "psf_A.fits", "psf_B.fits"]]
    if not all(p.exists() for p in expected):
        missing = [str(p) for p in expected if not p.exists()]
        raise FileNotFoundError(f"missing C5o inputs: {missing}")
    input_hashes = {str(p.relative_to(source)): sha256_file(p) for p in expected}
    dump(out / "input_hashes.json", input_hashes)

    c5o_summary = json.loads((source / "summary.json").read_text())
    imfit_winners = {r["case"]: r for r in c5o_summary["results"] if r.get("winner")}
    starts = c5o_summary["config"]["starts"]
    assert len(imfit_winners) == 4 and len(starts) == 3

    arrays = {}
    convention_rows = []
    case_cache = {}
    total_sse = {"negate_imfit": 0.0, "same_imfit": 0.0}
    for module in cfg["modules"]:
        psf = np.asarray(fits.getdata(source / "inputs" / f"psf_{module}.fits"), dtype=float)
        for ratio in cfg["ratios"]:
            case = case_name(module, ratio)
            data = np.asarray(fits.getdata(source / "inputs" / f"data_{module}_ratio{int(ratio)}.fits"), dtype=float)
            case_cache[case] = (data, psf, module, ratio)
            arrays[f"{case}__data"] = data
            arrays[f"{case}__psf"] = psf
            for pa_deg, mapping in [(45.0, "negate_imfit"), (135.0, "same_imfit")]:
                row, model_arr, resid, host_arr, point_arr = render_state(data, psf, pa_deg, ratio)
                row.update({"case": case, "module": module, "ratio": ratio, "mapping": mapping, "psf_input_sum": float(psf.sum())})
                convention_rows.append(row)
                total_sse[mapping] += row["sse"]
                arrays[f"{case}__truth_{int(pa_deg)}__model"] = model_arr
                arrays[f"{case}__truth_{int(pa_deg)}__residual"] = resid
                arrays[f"{case}__truth_{int(pa_deg)}__host"] = host_arr
                arrays[f"{case}__truth_{int(pa_deg)}__point"] = point_arr
    mapping = min(total_sse, key=total_sse.get)
    convention = {"candidate_total_sse": total_sse, "selected_mapping": mapping, "rows": convention_rows}
    dump(out / "convention.json", convention)

    attempts = []
    winners = []
    for case, (data, psf, module, ratio) in case_cache.items():
        finite_rows = []
        for s in starts:
            start = {
                "pa_rad": mapped_pa(float(s["pa"]), mapping),
                "q": float(s["q"]),
                "n": float(s["n"]),
                "re": float(s["re"]),
                "host_flux": float(s["host_flux"]),
                "point_flux": float(ratio) * float(s["point_fraction"]),
            }
            row, model_arr, resid, host_arr, point_arr = fit_attempt(data, psf, start)
            row.update({"case": case, "module": module, "ratio": ratio, "label": s["label"], "start": start, "selected_pa_mapping": mapping, "psf_input_sum": float(psf.sum())})
            attempts.append(row)
            prefix = f"{case}__{s['label']}"
            arrays[f"{prefix}__model"] = model_arr
            arrays[f"{prefix}__residual"] = resid
            arrays[f"{prefix}__host"] = host_arr
            arrays[f"{prefix}__point"] = point_arr
            if row["finite"] and row["sse"] is not None:
                finite_rows.append(row)
        if not finite_rows:
            continue
        winner = min(finite_rows, key=lambda r: r["sse"])
        winner = dict(winner)
        winner["winner"] = True
        imfit = imfit_winners[case]
        imfit_pa_physical = math.degrees(mapped_pa(float(imfit["pa"]), mapping)) % 180.0
        winner["imfit_winner"] = {k: imfit[k] for k in ["label", "pa", "q", "n", "re", "point_flux", "sse", "residual_l1_over_data_l1", "bound_hits"]}
        winner["comparison"] = {
            "delta_n": winner["n"] - float(imfit["n"]),
            "delta_re": winner["re"] - float(imfit["re"]),
            "delta_q": winner["q"] - float(imfit["q"]),
            "delta_pa_deg_mapped": ((winner["pa_deg"] - imfit_pa_physical + 90.0) % 180.0) - 90.0,
            "delta_point_parameter": winner["point_flux"] - float(imfit["point_flux"]),
            "sse_ratio_astrophot_over_imfit": winner["sse"] / float(imfit["sse"]),
        }
        winners.append(winner)

    np.savez_compressed(out / "arrays.npz", **arrays)
    dump(out / "attempts.json", attempts)
    dump(out / "comparison.json", winners)
    summary = {
        "config": cfg,
        "convention": convention,
        "attempt_count": len(attempts),
        "finite_attempt_count": sum(bool(r["finite"]) for r in attempts),
        "winner_count": len(winners),
        "winners": winners,
        "interpretation": "diagnostic only; scientific agreement or disagreement is not converted into a pass band",
    }
    dump(out / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.source, args.out)
    print(json.dumps({"attempt_count": result["attempt_count"], "finite_attempt_count": result["finite_attempt_count"], "winner_count": result["winner_count"], "selected_pa_mapping": result["convention"]["selected_mapping"]}, sort_keys=True))


if __name__ == "__main__":
    main()
