#!/usr/bin/env python3
"""Read-only B9a artifact audit."""
import argparse, json
from pathlib import Path
import numpy as np

def main():
    p=argparse.ArgumentParser(); p.add_argument("--source", type=Path, required=True); a=p.parse_args(); r=a.source
    cfg=json.loads((r/"config.json").read_text()); s=json.loads((r/"summary.json").read_text())
    assert s["config"] == cfg; assert len(s["results"]) == 4
    assert abs(s["psf_sum"] - 1.0) < 1e-12; assert s["psf_min"] > 0
    with np.load(r/"arrays.npz") as z:
        assert "psf" in z and "grid_native" in z; assert z["psf"].shape == (9,9); assert z["grid_native"].shape == (101,101,2)
        assert np.isfinite(z["psf"]).all() and np.isfinite(z["grid_native"]).all()
        for row in s["results"]:
            name=row["scene"]
            for k in ("ref_raw","ag_raw","ref_conv","ag_conv"):
                arr=z[f"{name}__{k}"]; assert arr.shape == (101,101); assert np.isfinite(arr).all(); assert arr.sum() > 0
            for key in ("raw_diff","conv_global_diff","conv_interior_diff"):
                assert np.isfinite(row[key]["max_abs"]); assert np.isfinite(row[key]["l1_over_reference_l1"])
    out={"stage":"B9a","status":"complete finite convention diagnostic; numerical differences retained as evidence","scenes":4,"claim":cfg["acceptance"]}
    (r/"audit.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(out)
if __name__ == "__main__": main()
