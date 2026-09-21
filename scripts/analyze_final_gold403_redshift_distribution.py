#!/usr/bin/env python3
"""Summarize the final 403-object GOLD403 catalog by fixed redshift bins.

This intentionally reads only the final GOLD403 catalog supplied with
``--input``.  It does not use the earlier parent-candidate catalog as a
denominator or as an additional source population.

The script writes compact tables, provenance, a short interpretation, and
four diagnostic figures.  It is deliberately lightweight: it does not access
the artificial-redshifting production runner or any imaging data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


FINAL_REQUIRED_COLUMNS = {"id", "z", "logM", "mag_model_f444w"}
AGN_COLUMNS = ("known_xray_agn", "verified_xray_agn")
MASS_COLUMN = "logM"
LUMINOSITY_COLUMN = "mag_model_f444w"
LUMINOSITY_DESCRIPTION = "Observed F444W model AB magnitude (mag_model_f444w)"
MIN_N_FOR_NARROW_BIN = 20
MIN_MASS_COVERAGE_FOR_NARROW_BIN = 0.90


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Final GOLD403 CSV")
    parser.add_argument("--outdir", required=True, type=Path, help="New or empty output directory")
    parser.add_argument(
        "--expected-n",
        type=int,
        default=403,
        help="Expected number of final-catalog rows (default: 403)",
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_text(path: Path, text: str) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def atomic_csv(table: pd.DataFrame, path: Path) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        table.to_csv(handle, index=False)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def validate_final_catalog(table: pd.DataFrame, expected_n: int) -> None:
    missing = FINAL_REQUIRED_COLUMNS - set(table.columns)
    if missing:
        raise ValueError(f"Final catalog is missing required columns: {sorted(missing)}")
    if len(table) != expected_n:
        raise ValueError(
            f"Expected {expected_n} final GOLD403 rows, found {len(table)}. "
            "Refusing to mix or substitute a different population."
        )
    if table["id"].isna().any() or table["id"].duplicated().any():
        raise ValueError("Final catalog must have one non-null unique id per row.")
    for column in ("z", MASS_COLUMN, LUMINOSITY_COLUMN):
        values = pd.to_numeric(table[column], errors="coerce")
        if not np.isfinite(values).all():
            raise ValueError(f"{column} must be finite for every final-catalog object.")
        table[column] = values
    if (table["z"] < 0).any():
        raise ValueError("Redshifts must be non-negative.")


def percentile_summary(values: pd.Series) -> tuple[int, float, float, float]:
    finite = pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if finite.empty:
        return 0, np.nan, np.nan, np.nan
    q16, median, q84 = np.percentile(finite, [16, 50, 84])
    return int(len(finite)), float(median), float(q16), float(q84)


def fixed_edges(zmax: float, width: float) -> np.ndarray:
    top = np.ceil(zmax / width) * width
    # The final edge is nudged upward so an object exactly at ``top`` remains in
    # the final reported bin while all labels retain their conventional bounds.
    return np.append(np.arange(0.0, top, width), np.nextafter(top, np.inf))


def summarize_bins(table: pd.DataFrame, width: float, env_note: str) -> pd.DataFrame:
    edges = fixed_edges(float(table["z"].max()), width)
    rows: list[dict[str, object]] = []
    agn_available = all(column in table.columns for column in AGN_COLUMNS)
    if agn_available:
        agn_flag = table[list(AGN_COLUMNS)].fillna(False).astype(bool).any(axis=1)
        agn_coverage = table[list(AGN_COLUMNS)].notna().any(axis=1)
    else:
        agn_flag = pd.Series(False, index=table.index)
        agn_coverage = pd.Series(False, index=table.index)

    for lo, hi in zip(edges[:-1], edges[1:]):
        in_bin = (table["z"] >= lo) & (table["z"] < hi)
        subset = table.loc[in_bin]
        mass_n, mass_median, mass_p16, mass_p84 = percentile_summary(subset[MASS_COLUMN])
        lum_n, lum_median, lum_p16, lum_p84 = percentile_summary(subset[LUMINOSITY_COLUMN])
        n_total = int(len(subset))
        n_agn_covered = int(agn_coverage.loc[subset.index].sum())
        n_agn = int(agn_flag.loc[subset.index].sum()) if n_agn_covered else 0
        rows.append(
            {
                "bin_width": width,
                "z_lo": float(lo),
                "z_hi": float(hi),
                "z_interval": f"[{lo:.2f}, {hi:.2f})",
                "N_total": n_total,
                "median_z": float(subset["z"].median()) if n_total else np.nan,
                "N_mass": mass_n,
                "mass_coverage_fraction": mass_n / n_total if n_total else np.nan,
                "logM_median": mass_median,
                "logM_p16": mass_p16,
                "logM_p84": mass_p84,
                "luminosity_metric": LUMINOSITY_DESCRIPTION,
                "N_luminosity": lum_n,
                "luminosity_coverage_fraction": lum_n / n_total if n_total else np.nan,
                "F444W_model_ABmag_median": lum_median,
                "F444W_model_ABmag_p16": lum_p16,
                "F444W_model_ABmag_p84": lum_p84,
                "N_agn_coverage": n_agn_covered,
                "N_agn": n_agn,
                "agn_fraction_of_covered": n_agn / n_agn_covered if n_agn_covered else np.nan,
                "N_environment_density_coverage": 0,
                "environment_density_coverage_fraction": 0.0 if n_total else np.nan,
                "environment_note": env_note,
            }
        )
    return pd.DataFrame(rows)


def choose_narrow_bin(narrow: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, str]:
    """Choose before inspecting science outcomes: N first, then mass coverage."""
    result = narrow.copy()
    eligible = (
        (result["N_total"] >= MIN_N_FOR_NARROW_BIN)
        & (result["mass_coverage_fraction"] >= MIN_MASS_COVERAGE_FOR_NARROW_BIN)
    )
    result["meets_predeclared_narrow_criterion"] = eligible
    if not eligible.any():
        pool = result[result["N_total"] > 0]
        selection_rule = (
            "Fallback: no Δz=0.25 bin met the predeclared N≥20 and mass-coverage≥90% criterion; "
            "selected the largest non-empty bin."
        )
    else:
        pool = result.loc[eligible]
        selection_rule = (
            "Predeclared descriptive rule: among Δz=0.25 bins with N≥20 and logM coverage≥90%, "
            "select the largest N; break any tie by lower redshift. No morphology/redshifting outcome was used."
        )
    selected_index = pool.sort_values(["N_total", "z_lo"], ascending=[False, True]).index[0]
    result["selected_best_narrow_bin"] = result.index == selected_index
    return result, result.loc[selected_index], selection_rule


def save_figure(figure: plt.Figure, path: Path) -> None:
    temporary = path.with_name(f".{path.stem}.tmp{path.suffix}")
    figure.savefig(temporary, dpi=180, bbox_inches="tight")
    plt.close(figure)
    os.replace(temporary, path)


def plot_products(table: pd.DataFrame, broad: pd.DataFrame, narrow: pd.DataFrame, selected: pd.Series, outdir: Path) -> None:
    selected_lo, selected_hi = float(selected.z_lo), float(selected.z_hi)
    selected_label = str(selected.z_interval)
    blue, gold, charcoal, grid = "#1f4e79", "#c58b00", "#202124", "#d9d9d9"

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for axis, width, title in zip(axes, (0.25, 0.5), ("Δz = 0.25", "Δz = 0.50")):
        edges = fixed_edges(float(table.z.max()), width)
        axis.hist(table.z, bins=edges, color=blue, edgecolor="white", linewidth=0.8)
        axis.set_title(title)
        axis.set_xlabel("Redshift z")
        axis.grid(axis="y", color=grid, linewidth=0.7)
        axis.set_axisbelow(True)
    axes[0].set_ylabel("GOLD403 candidate count")
    fig.suptitle("Final GOLD403 redshift distribution (N = 403)", y=1.02, color=charcoal)
    save_figure(fig, outdir / "GOLD403_final_redshift_histogram.png")

    fig, axis = plt.subplots(figsize=(7.4, 4.8))
    axis.scatter(table.z, table.logM, s=18, color=blue, alpha=0.72, linewidths=0)
    axis.axvspan(selected_lo, selected_hi, color=gold, alpha=0.16, label=f"selected {selected_label}")
    axis.set_xlabel("Redshift z")
    axis.set_ylabel(r"log stellar mass [$M_\odot$]")
    axis.set_title("Final GOLD403 stellar mass versus redshift")
    axis.grid(color=grid, linewidth=0.7)
    axis.set_axisbelow(True)
    axis.legend(frameon=False)
    save_figure(fig, outdir / "GOLD403_final_stellar_mass_vs_redshift.png")

    fig, axes = plt.subplots(2, 1, figsize=(9.2, 7.2), sharex=False)
    for axis, summary, title in zip(axes, (narrow, broad), ("Candidate counts: Δz = 0.25", "Candidate counts: Δz = 0.50")):
        centers = (summary.z_lo.to_numpy() + summary.z_hi.to_numpy()) / 2
        axis.bar(centers, summary.N_total, width=summary.bin_width.iloc[0] * 0.88, color=blue, edgecolor="white")
        for x, y in zip(centers, summary.N_total):
            if y:
                axis.text(x, y + 1.5, str(int(y)), ha="center", va="bottom", fontsize=8)
        axis.set_title(title, pad=12)
        axis.set_ylabel("N")
        axis.set_xlabel("Redshift z")
        axis.grid(axis="y", color=grid, linewidth=0.7)
        axis.set_axisbelow(True)
    fig.subplots_adjust(top=0.93, bottom=0.09, hspace=0.82)
    save_figure(fig, outdir / "GOLD403_final_candidate_counts_per_redshift_bin.png")

    best = table[(table.z >= selected_lo) & (table.z < selected_hi)]
    fig, axis = plt.subplots(figsize=(7.4, 4.8))
    axis.hist(best.logM, bins="fd", color=blue, edgecolor="white", linewidth=0.8)
    axis.axvline(selected.logM_median, color=gold, linewidth=2, label=f"median = {selected.logM_median:.2f}")
    axis.axvspan(selected.logM_p16, selected.logM_p84, color=gold, alpha=0.16, label="16th–84th percentile")
    axis.set_xlabel(r"log stellar mass [$M_\odot$]")
    axis.set_ylabel("GOLD403 candidate count")
    axis.set_title(f"Mass distribution: {selected_label}, N = {int(selected.N_total)}")
    axis.grid(axis="y", color=grid, linewidth=0.7)
    axis.set_axisbelow(True)
    axis.legend(frameon=False)
    save_figure(fig, outdir / "GOLD403_final_best_narrow_bin_mass_distribution.png")


def markdown_summary(broad: pd.DataFrame, narrow: pd.DataFrame, selected: pd.Series, selection_rule: str, source: Path) -> str:
    def rows(summary: pd.DataFrame) -> str:
        body = []
        for item in summary.itertuples():
            body.append(
                f"| {item.z_interval} | {item.N_total} | {item.median_z:.4f} | "
                f"{item.logM_median:.3f} [{item.logM_p16:.3f}, {item.logM_p84:.3f}] | "
                f"{item.F444W_model_ABmag_median:.3f} [{item.F444W_model_ABmag_p16:.3f}, {item.F444W_model_ABmag_p84:.3f}] |"
            )
        return "\n".join(body)

    return f"""# Final GOLD403 redshift-distribution receipt

## Scope

This analysis uses only the final 403-row GOLD403 catalog: `{source}`. It does
not use the earlier 1,163/1,158 parent-candidate sample as a source or a
denominator.

## Recommended narrow starting bin

**{selected.z_interval}, N = {int(selected.N_total)}**, with median
z = {selected.median_z:.4f} and log stellar mass = {selected.logM_median:.3f}
[ {selected.logM_p16:.3f}, {selected.logM_p84:.3f} ] (16th–84th percentile;
N_mass = {int(selected.N_mass)}).

Selection rule: {selection_rule}

## Fixed Δz = 0.25 bins

| z interval | N | median z | logM median [p16, p84] | F444W model AB mag median [p16, p84] |
|---|---:|---:|---:|---:|
{rows(narrow)}

## Fixed Δz = 0.50 bins

| z interval | N | median z | logM median [p16, p84] | F444W model AB mag median [p16, p84] |
|---|---:|---:|---:|---:|
{rows(broad)}

## AGN and environment scope

The direct final-catalog flags `known_xray_agn` and `verified_xray_agn` are
available for all 403 rows and are false for all of them. Thus each bin's
catalog-flag AGN count is zero, but this is selection-censored and must not be
interpreted as a field AGN incidence measurement.

No per-object, documented tracer-density estimate is present in the final
catalog or existing compact local products. An existing master-catalog schema
inventory lists `group_id`, which is not a calibrated environment/density
measurement; density coverage is therefore reported as 0/ N rather than
manufactured from the selected sample.

## Luminosity convention

No rest-frame luminosity column is present in the final catalog. The reported
photometric distribution is the complete observed `mag_model_f444w` AB
magnitude. It is appropriate as an observed brightness diagnostic within a
narrow z bin, but it is not a rest-frame luminosity or a completeness limit.
"""


def main() -> None:
    args = parse_args()
    if not args.input.is_file():
        raise FileNotFoundError(f"Final GOLD403 catalog not found: {args.input}")
    args.outdir.mkdir(parents=True, exist_ok=True)
    table = pd.read_csv(args.input)
    validate_final_catalog(table, args.expected_n)

    env_note = (
        "No documented per-object density product available locally; schema inventory's group_id is not a density metric."
    )
    broad = summarize_bins(table, 0.50, env_note)
    narrow = summarize_bins(table, 0.25, env_note)
    narrow, selected, selection_rule = choose_narrow_bin(narrow)
    broad["meets_predeclared_narrow_criterion"] = False
    broad["selected_best_narrow_bin"] = False
    summary = pd.concat([broad, narrow], ignore_index=True)

    plot_products(table, broad, narrow, selected, args.outdir)
    atomic_csv(summary, args.outdir / "GOLD403_final_redshift_bin_summary.csv")
    atomic_csv(narrow, args.outdir / "GOLD403_final_narrow_bin_candidates.csv")
    atomic_csv(
        table.loc[(table.z >= selected.z_lo) & (table.z < selected.z_hi), ["id", "z", "logM", "mag_model_f444w"]],
        args.outdir / "GOLD403_final_best_narrow_bin_members.csv",
    )
    atomic_text(
        args.outdir / "GOLD403_final_redshift_distribution_interpretation.md",
        markdown_summary(broad, narrow, selected, selection_rule, args.input),
    )
    provenance = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "input_catalog": str(args.input.resolve()),
        "input_catalog_sha256": sha256(args.input),
        "population_definition": "All and only rows in the final 403-object GOLD403 catalog; no parent-candidate catalog used.",
        "N_rows": int(len(table)),
        "N_unique_ids": int(table.id.nunique()),
        "redshift_column": "z",
        "mass_column": MASS_COLUMN,
        "luminosity_metric": LUMINOSITY_DESCRIPTION,
        "agn_definition": "known_xray_agn OR verified_xray_agn",
        "environment_density_coverage": "No documented per-object density product available locally; reported as zero coverage.",
        "bin_convention": "Fixed bins anchored at z=0, closed on the left and open on the right: [z_lo, z_hi).",
        "narrow_bin_selection_rule": selection_rule,
        "selected_narrow_bin": selected.to_dict(),
        "files_written": sorted(path.name for path in args.outdir.iterdir()),
    }
    atomic_text(
        args.outdir / "GOLD403_final_redshift_distribution_provenance.json",
        json.dumps(provenance, indent=2, default=str) + "\n",
    )
    print(f"SELECTED_NARROW_BIN {selected.z_interval} N={int(selected.N_total)}")
    print(f"OUTPUT_DIR {args.outdir}")


if __name__ == "__main__":
    main()
