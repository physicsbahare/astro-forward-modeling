#!/usr/bin/env python3
"""Read-only audit for C6c crossed-PSF AstroPhot diagnostic."""
import argparse
import json
from pathlib import Path
import numpy as np


def audit(root: Path):
    cfg = json.loads((root / "config.json").read_text())
    summary = json.loads((root / "summary.json").read_text())
    attempts = json.loads((root / "attempts.json").read_text())
    comparisons = json.loads((root / "comparison.json").read_text())
    assert cfg == summary["config"]
    assert cfg["stage"].startswith("C6c")
    assert cfg["ratio"] == 10.0
    assert cfg["pa_mapping"] == "same_imfit"
    assert summary["attempt_count"] == len(attempts) == 6
    assert summary["winner_count"] == len(summary["winners"]) == 2
    assert len(comparisons) == 2
    assert {r["case"] for r in summary["winners"]} == {"n1_truthA_fitB_ratio10", "n1_truthB_fitA_ratio10"}
    with np.load(root / "arrays.npz") as arrays:
        for winner in summary["winners"]:
            assert winner["finite"]
            assert np.isfinite(winner["sse"])
            prefix = f"{winner['case']}__{winner['label']}"
            data = arrays[f"{winner['case']}__data"]
            model = arrays[f"{prefix}__model"]
            residual = arrays[f"{prefix}__residual"]
            assert data.shape == model.shape == residual.shape == (201, 201)
            assert np.isfinite(data).all() and np.isfinite(model).all() and np.isfinite(residual).all()
            assert np.max(np.abs((data - model) - residual)) < 1e-12
            assert abs(np.sum(residual**2) - winner["sse"]) < 1e-12
    result = {"stage": "C6c", "attempts": 6, "winners": 2, "status": "complete crossed-PSF diagnostic artifact; failures/bounds retained as observables", "claim": cfg["claim"]}
    (root / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    args = p.parse_args()
    print(audit(args.source))


if __name__ == "__main__":
    main()
