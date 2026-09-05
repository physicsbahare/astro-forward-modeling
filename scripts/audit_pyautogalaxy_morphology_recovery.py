#!/usr/bin/env python3
"""Read-only B9b artifact audit."""
import argparse, json
from pathlib import Path
import numpy as np


def audit(root: Path):
    cfg = json.loads((root / "config.json").read_text())
    summary = json.loads((root / "summary.json").read_text())
    assert cfg == summary["config"]
    assert abs(summary["psf_sum"] - 1.0) < 1e-12
    assert len(summary["attempts"]) == 12
    assert len(summary["winners"]) == 4
    assert len(summary["comparisons"]) == 2
    for row in summary["attempts"]:
        assert row["renderer"] in {"independent", "pyautogalaxy"}
        assert row["scene"] in {"n1", "n4"}
        assert row["finite"]
        assert np.isfinite(row["interior_sse"]) and np.isfinite(row["full_sse"])
        assert row["interior_sse"] >= 0 and row["full_sse"] >= row["interior_sse"]
        for key in ["cy", "cx", "q", "n", "re", "ie"]:
            assert np.isfinite(row["params"][key])
        assert np.isfinite(row["analytic_total_flux"])
    with np.load(root / "arrays.npz") as arrays:
        assert np.isfinite(arrays["psf"]).all()
        for scene in ("n1", "n4"):
            assert np.isfinite(arrays[f"{scene}__data"]).all()
            for renderer in ("independent", "pyautogalaxy"):
                for suffix in ("winner_raw", "winner_model", "winner_residual"):
                    key = f"{scene}__{renderer}__{suffix}"
                    assert key in arrays.files and np.isfinite(arrays[key]).all()
    result = {"stage": "B9b", "attempts": 12, "winners": 4, "status": "complete finite common-scene recovery diagnostic", "claim": cfg["acceptance"]}
    (root / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main():
    p = argparse.ArgumentParser(); p.add_argument("--source", type=Path, required=True); a = p.parse_args(); print(audit(a.source))

if __name__ == "__main__": main()
