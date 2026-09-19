#!/usr/bin/env python3
"""Read-only C6b completeness and algebra audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_dewsnap_astrophot_common_scene as experiment


def audit(root: Path) -> dict:
    cfg = json.loads((root / "config.json").read_text())
    summary = json.loads((root / "summary.json").read_text())
    attempts = json.loads((root / "attempts.json").read_text())
    winners = json.loads((root / "comparison.json").read_text())
    convention = json.loads((root / "convention.json").read_text())
    hashes = json.loads((root / "input_hashes.json").read_text())

    assert cfg == summary["config"] == experiment.configuration()
    assert summary["attempt_count"] == len(attempts) == 12
    assert len(winners) == summary["winner_count"] == 4
    assert len(convention["rows"]) == 8
    assert convention["selected_mapping"] in {"negate_imfit", "same_imfit"}
    assert set(convention["candidate_total_sse"]) == {"negate_imfit", "same_imfit"}
    assert all(np.isfinite(float(v)) for v in convention["candidate_total_sse"].values())
    assert len(hashes) == 7 and all(len(v) == 64 for v in hashes.values())

    cases = {experiment.case_name(m, r) for m in cfg["modules"] for r in cfg["ratios"]}
    assert {w["case"] for w in winners} == cases
    assert {r["case"] for r in attempts} == cases

    finite_by_case = {case: 0 for case in cases}
    for row in attempts:
        assert row["label"] in {"truth", "compact", "extended"}
        if row["finite"]:
            assert row["sse"] is not None and np.isfinite(row["sse"])
            assert np.isfinite(row["residual_l1_over_data_l1"])
            finite_by_case[row["case"]] += 1
    assert all(v >= 1 for v in finite_by_case.values())

    with np.load(root / "arrays.npz") as arrays:
        for case in cases:
            data = arrays[f"{case}__data"]
            psf = arrays[f"{case}__psf"]
            assert data.shape == psf.shape == (201, 201)
            assert np.isfinite(data).all() and np.isfinite(psf).all()
            assert np.any(psf < 0)
            for pa in (45, 135):
                model = arrays[f"{case}__truth_{pa}__model"]
                residual = arrays[f"{case}__truth_{pa}__residual"]
                host = arrays[f"{case}__truth_{pa}__host"]
                point = arrays[f"{case}__truth_{pa}__point"]
                assert model.shape == residual.shape == host.shape == point.shape == data.shape
                assert np.isfinite(model).all() and np.isfinite(residual).all()
                assert np.max(np.abs(residual - (data - model))) <= 1e-12
            case_rows = [r for r in attempts if r["case"] == case]
            for row in case_rows:
                prefix = f"{case}__{row['label']}"
                model = arrays[f"{prefix}__model"]
                residual = arrays[f"{prefix}__residual"]
                host = arrays[f"{prefix}__host"]
                point = arrays[f"{prefix}__point"]
                assert model.shape == residual.shape == host.shape == point.shape == data.shape
                if row["finite"]:
                    assert np.isfinite(model).all() and np.isfinite(residual).all()
                    assert np.max(np.abs(residual - (data - model))) <= 1e-12
                    recomputed = float(np.sum((data - model) ** 2))
                    assert np.isclose(recomputed, row["sse"], rtol=1e-12, atol=1e-15)
            finite_rows = [r for r in case_rows if r["finite"] and r["sse"] is not None]
            selected = next(w for w in winners if w["case"] == case)
            assert np.isclose(selected["sse"], min(r["sse"] for r in finite_rows), rtol=0, atol=1e-15)
            assert np.isfinite(selected["comparison"]["sse_ratio_astrophot_over_imfit"])

    result = {
        "stage": "C6b",
        "attempts": len(attempts),
        "finite_attempts": sum(r["finite"] for r in attempts),
        "winners": len(winners),
        "selected_pa_mapping": convention["selected_mapping"],
        "status": "complete common-scene diagnostic artifact; no morphology acceptance band applied",
        "claim": cfg["claim"],
    }
    dump = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (root / "audit.json").write_text(dump)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.source), sort_keys=True))


if __name__ == "__main__":
    main()
