#!/usr/bin/env python3
"""Read-only C6a output audit."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_dewsnap_astrophot_psf_preflight as experiment


def audit(root):
    cfg = json.loads((root / "config.json").read_text())
    summary = json.loads((root / "summary.json").read_text())
    assert cfg == summary["config"] == experiment.configuration()
    assert len(summary["results"]) == 2
    with np.load(root / "arrays.npz") as arrays:
        assert len(arrays.files) == 6
        for row in summary["results"]:
            module = row["module"]
            raw = arrays[f"psf_{module}_input"]
            public = arrays[f"psf_{module}_normalized_public"]
            rendered = arrays[f"psf_{module}_delta_convolution_internal"]
            assert raw.shape == public.shape == rendered.shape == (201, 201)
            assert np.isfinite(raw).all() and np.isfinite(public).all() and np.isfinite(rendered).all()
            assert row["negative_pixel_count"] > 0 and row["input_min"] < 0
            assert row["public_roundtrip_max_abs_error"] <= cfg["absolute_identity_tolerance"]
            assert abs(row["normalized_sum"] - 1) <= cfg["absolute_identity_tolerance"]
            assert abs(row["convolution_sum"] - 1) <= cfg["absolute_identity_tolerance"]
            assert row["internal_transpose_max_abs_error"] <= cfg["absolute_identity_tolerance"]
            assert np.max(np.abs(rendered - public.T)) <= cfg["absolute_identity_tolerance"]
            assert row["untransposed_max_abs_error"] > cfg["absolute_identity_tolerance"]
            assert row["convolution_min"] < 0
    assert not list(root.rglob("*.partial"))
    result = {"modules": 2, "arrays": 6, "status": "signed samples and v0.18 axis convention preserved", "claim": cfg["claim"]}
    (root / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    print(audit(args.source))


if __name__ == "__main__":
    main()
