#!/usr/bin/env python3
"""Run Passive Spiral P2 against the frozen real COSMOS-Web cutout."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import scipy
from astropy.io import fits

from verification.passive_spiral_real_context import P2_TARGET_Z, run_p2_grid


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def aggregate(rows: list[dict]) -> list[dict]:
    groups: dict[tuple[str, float], list[dict]] = {}
    for row in rows:
        key = (str(row["crowding_class"]), float(row["ab_mag"]))
        groups.setdefault(key, []).append(row)

    out: list[dict] = []
    for (crowding_class, mag), members in sorted(groups.items()):
        arm = np.asarray([m["injected_fit"]["arm_coefficient"] for m in members], dtype=float)
        smooth = np.asarray([m["injected_fit"]["smooth_coefficient"] for m in members], dtype=float)
        background_arm = np.asarray([m["background_arm_equivalent"] for m in members], dtype=float)
        paired_arm = np.asarray([m["paired_difference_fit"]["arm_coefficient"] for m in members], dtype=float)
        out.append(
            {
                "crowding_class": crowding_class,
                "ab_mag": mag,
                "n": len(members),
                "raw_arm_coefficient_median": float(np.median(arm)),
                "raw_arm_coefficient_min": float(np.min(arm)),
                "raw_arm_coefficient_max": float(np.max(arm)),
                "raw_arm_abs_bias_median": float(np.median(np.abs(arm - 1.0))),
                "raw_smooth_coefficient_median": float(np.median(smooth)),
                "background_arm_equivalent_median": float(np.median(background_arm)),
                "paired_arm_coefficient_median": float(np.median(paired_arm)),
            }
        )
    return out


def make_figure(rows: list[dict], out_png: Path) -> None:
    classes = ["near_source_2_5", "intermediate_8_20", "relatively_isolated_ge30"]
    class_labels = ["near source\n2–5 px", "intermediate\n8–20 px", "isolated\n≥30 px"]
    xbase = {name: i for i, name in enumerate(classes)}
    marker_by_mag = {26.0: "o", 29.0: "s"}
    offset_by_mag = {26.0: -0.08, 29.0: 0.08}

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for mag in (26.0, 29.0):
        selected = [r for r in rows if float(r["ab_mag"]) == mag]
        xs = [xbase[str(r["crowding_class"])] + offset_by_mag[mag] for r in selected]
        ys = [float(r["injected_fit"]["arm_coefficient"]) for r in selected]
        ax.scatter(xs, ys, marker=marker_by_mag[mag], s=55, label=f"AB={mag:.0f}")

    ax.axhline(1.0, linestyle="--", linewidth=1.2, label="injected arm truth = 1")
    ax.set_xticks(range(len(classes)), class_labels)
    ax.set_ylabel("Recovered signed arm-template coefficient")
    ax.set_xlabel("Frozen real-context crowding class")
    ax.set_title("Passive Spiral P2 — z=2 spiral in real COSMOS-Web F444W context")
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_png, dpi=180)
    plt.close(fig)


def run(real_fits: Path, matrix_path: Path, out_dir: Path) -> dict:
    matrix = json.loads(matrix_path.read_text())
    with fits.open(real_fits, mode="readonly", memmap=True) as hdul:
        sci = np.array(hdul["SCI"].data, dtype=float, copy=True)
        err = np.array(hdul["ERR"].data, dtype=float, copy=True)
        wht = np.array(hdul["WHT"].data, dtype=float, copy=True)
        sci_header = hdul["SCI"].header.copy()

    if not (sci.shape == err.shape == wht.shape):
        raise ValueError("frozen real SCI/ERR/WHT shapes differ")
    if str(sci_header.get("BUNIT", "")).strip().lower() != "mjy/sr":
        raise ValueError(f"expected SCI BUNIT=MJy/sr, got {sci_header.get('BUNIT')!r}")
    pixar_sr = float(sci_header["PIXAR_SR"])
    if not np.isfinite(pixar_sr) or pixar_sr <= 0:
        raise ValueError("SCI PIXAR_SR must be positive and finite")
    if np.any(~np.isfinite(err)) or np.any(err <= 0):
        raise ValueError("P2 requires finite positive ERR over the frozen cutout")

    rows = run_p2_grid(sci, err, matrix, pixar_sr)
    if len(rows) != 18:
        raise RuntimeError(f"frozen P2 matrix must produce 18 cases, got {len(rows)}")

    out_dir.mkdir(parents=True, exist_ok=True)
    figure_path = out_dir / "p2_arm_coefficient_real_context.png"
    make_figure(rows, figure_path)

    payload = {
        "benchmark": "Passive Spiral P2 real COSMOS-Web context arm-recovery stress test",
        "scope": (
            "Deterministic P1 z=2 spiral morphology injected into the frozen real COSMOS-Web "
            "SCI context. This is not literal exposure-space survey reproduction and not a classifier."
        ),
        "target_redshift": P2_TARGET_Z,
        "input_real_fits": real_fits.name,
        "input_real_fits_sha256": sha256(real_fits),
        "matrix": matrix,
        "pixar_sr": pixar_sr,
        "bunit": sci_header["BUNIT"],
        "n_cases": len(rows),
        "results": rows,
        "aggregate_descriptive": aggregate(rows),
        "figure": figure_path.name,
        "measurement_semantics": {
            "fit": "unbounded diagonal-ERR weighted plane + smooth-template + signed arm-residual template",
            "diagonal_err_is_independence_claim": False,
            "paired_difference_is_independent_crosscode_validation": False,
            "scientific_detection_threshold_applied": False,
        },
        "mutations": {
            "science_input_modified_in_place": False,
            "err_modified": False,
            "wht_modified": False,
            "background_noise_added": False,
            "source_shot_noise_generated": False,
            "psf_sharpening_applied": False,
            "extra_tolman_factor_applied": False,
        },
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
    }
    json_path = out_dir / "p2_real_context_metrics.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--real-fits", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.real_fits, args.matrix, args.out)


if __name__ == "__main__":
    main()
