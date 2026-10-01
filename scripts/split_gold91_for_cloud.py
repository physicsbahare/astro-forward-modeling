#!/usr/bin/env python3
"""Create deterministic GOLD91 redshift-bin chunks for remote/cloud fitting."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path,
                        help="GOLD403 CSV containing id and z")
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--z-min", type=float, default=0.75)
    parser.add_argument("--z-max", type=float, default=1.00)
    parser.add_argument("--chunks", type=int, default=3)
    parser.add_argument("--expected-count", type=int, default=91)
    args = parser.parse_args()

    frame = pd.read_csv(args.input)
    if "id" not in frame.columns or "z" not in frame.columns:
        raise KeyError("input must contain id and z columns")

    z = pd.to_numeric(frame["z"], errors="coerce")
    subset = frame.loc[
        (z >= float(args.z_min)) & (z < float(args.z_max))
    ].copy()
    subset["id"] = pd.to_numeric(subset["id"], errors="raise").astype("int64")
    subset = subset.sort_values("id").reset_index(drop=True)

    if args.expected_count is not None and len(subset) != int(args.expected_count):
        raise RuntimeError(
            f"Expected {args.expected_count} objects in "
            f"{args.z_min:.2f} <= z < {args.z_max:.2f}; found {len(subset)}"
        )
    if args.chunks < 1:
        raise ValueError("--chunks must be >= 1")

    args.outdir.mkdir(parents=True, exist_ok=True)
    subset.to_csv(args.outdir / "GOLD91_all.csv", index=False)

    edges = [
        round(i * len(subset) / args.chunks)
        for i in range(args.chunks + 1)
    ]
    for i in range(args.chunks):
        part = subset.iloc[edges[i]:edges[i + 1]].copy()
        path = args.outdir / f"GOLD91_chunk_{i + 1:02d}_of_{args.chunks:02d}.csv"
        part.to_csv(path, index=False)
        print(path, len(part), int(part["id"].min()), int(part["id"].max()))

    print("TOTAL", len(subset))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
