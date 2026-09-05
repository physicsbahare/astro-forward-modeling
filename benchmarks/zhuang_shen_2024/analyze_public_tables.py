#!/usr/bin/env python3
"""Quantitatively inspect the public Zhuang & Shen (2024) mock-AGN tables.

This script is a literature-benchmark analyzer, not production framework code.
It operates on the immutable public products fetched by
``scripts/fetch_zhuang_shen_benchmark.py`` and produces machine-readable
summaries of the published PSF-mismatch experiment.

Reference
---------
Zhuang & Shen, ApJ 962, 139 (2024), arXiv:2304.13776.

Important conventions
---------------------
* ``ratio`` in the public table is the Sérsic axis ratio q, not AGN/host flux
  ratio.  The AGN/host flux ratio is derived from input magnitudes as
  10**[-0.4 * (m_AGN - m_host)].
* Re is in pixels.  The paper's mosaics use 0.03 arcsec/pixel.
* Parameter "success" follows the paper's stated measurement/error >= 3
  convention where it is used below.  Zero tabulated formal errors are treated
  as infinite formal significance rather than divided numerically.
* The centroid-offset significance implemented here uses a transparent
  quadrature approximation from the tabulated x/y uncertainties.  It is kept
  explicitly named and must be compared with the paper before becoming a
  frozen reproduction statistic.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
from astropy.table import Table

PIXEL_SCALE_ARCSEC = 0.03
F150W_SB_DEPTH_MAG_ARCSEC2 = 25.28  # paper Table 2, 3-sigma SB depth
F150W_POINT_DEPTH_MAG = 26.83  # paper Table 2, 5-sigma point-source depth

SCENARIOS = {
    "fiducial": "mock_AGN_results_F150W_fiducial_PSF.ipac",
    "broader": "mock_AGN_results_F150W_broader_PSF.ipac",
    "narrower": "mock_AGN_results_F150W_narrower_PSF.ipac",
}
CENTER_FREE_FILE = "mock_AGN_results_F150W_fiducial_PSF_center_not_tied.ipac"
INPUT_FILE = "mock_AGN_input_values.ipac"


def _array(table: Table, name: str) -> np.ndarray:
    return np.asarray(table[name], dtype=float)


def _names(table: Table) -> np.ndarray:
    return np.asarray(table["Name"], dtype=str)


def _finite_percentile(values: np.ndarray, q: float) -> float | None:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return None
    return float(np.percentile(values, q))


def _finite_median(values: np.ndarray) -> float | None:
    return _finite_percentile(values, 50.0)


def _summary_distribution(values: np.ndarray) -> dict[str, float | int | None]:
    values = np.asarray(values, dtype=float)
    finite = values[np.isfinite(values)]
    return {
        "n": int(finite.size),
        "p16": _finite_percentile(finite, 16.0),
        "median": _finite_median(finite),
        "p84": _finite_percentile(finite, 84.0),
    }


def _formal_significance(value: np.ndarray, error: np.ndarray) -> np.ndarray:
    value = np.asarray(value, dtype=float)
    error = np.asarray(error, dtype=float)
    out = np.full(value.shape, np.nan, dtype=float)
    finite = np.isfinite(value) & np.isfinite(error)
    positive = finite & (error > 0)
    out[positive] = np.abs(value[positive]) / error[positive]
    exact_zero = finite & (error == 0)
    out[exact_zero] = np.inf
    return out


def agn_to_host_flux_ratio(input_table: Table) -> np.ndarray:
    return 10.0 ** (-0.4 * (_array(input_table, "Mag_psf") - _array(input_table, "Mag_sersic")))


def mean_host_surface_brightness(input_table: Table) -> np.ndarray:
    """Return input mean host SB within Re in mag/arcsec^2.

    Implements the paper's equation
    mu_Sersic = m_Sersic + 2.5 log10(2 q pi Re^2),
    with Re converted from pixels to arcsec.
    """

    m = _array(input_table, "Mag_sersic")
    q = _array(input_table, "ratio")
    re_arcsec = _array(input_table, "Re") * PIXEL_SCALE_ARCSEC
    area_factor = 2.0 * q * np.pi * re_arcsec**2
    return m + 2.5 * np.log10(area_factor)


def validate_row_identity(input_table: Table, result_tables: Iterable[Table]) -> None:
    input_names = _names(input_table)
    if len(np.unique(input_names)) != len(input_names):
        raise RuntimeError("Input mock names are not unique; row identity is ambiguous.")
    for table in result_tables:
        names = _names(table)
        if len(names) != len(input_names):
            raise RuntimeError(f"Row count mismatch: {len(names)} != {len(input_names)}")
        if not np.array_equal(names, input_names):
            mismatch = np.flatnonzero(names != input_names)
            first = int(mismatch[0]) if mismatch.size else -1
            raise RuntimeError(f"Row identity/order mismatch at row {first}.")


def parameter_biases(input_table: Table, result_table: Table) -> dict[str, np.ndarray]:
    mhost_in = _array(input_table, "Mag_sersic")
    magn_in = _array(input_table, "Mag_psf")
    re_in = _array(input_table, "Re")
    n_in = _array(input_table, "n")
    q_in = _array(input_table, "ratio")

    mhost = _array(result_table, "Mag_sersic")
    magn = _array(result_table, "Mag_psf")
    re = _array(result_table, "Re")
    n = _array(result_table, "n")
    q = _array(result_table, "ratio")

    with np.errstate(divide="ignore", invalid="ignore"):
        log_re_ratio = np.log10(re / re_in)
        log_n_ratio = np.log10(n / n_in)

    return {
        "delta_m_host": mhost - mhost_in,
        "host_flux_recovered_over_true": 10.0 ** (-0.4 * (mhost - mhost_in)),
        "delta_m_agn": magn - magn_in,
        "agn_flux_recovered_over_true": 10.0 ** (-0.4 * (magn - magn_in)),
        "log10_recovered_over_true_Re": log_re_ratio,
        "log10_recovered_over_true_n": log_n_ratio,
        "delta_q": q - q_in,
        "recovered_agn_to_host_flux_ratio": 10.0 ** (-0.4 * (magn - mhost)),
    }


def success_masks(result_table: Table) -> dict[str, np.ndarray]:
    return {
        "host_mag": _formal_significance(_array(result_table, "Mag_sersic"), _array(result_table, "Mag_sersic_e")) >= 3,
        "agn_mag": _formal_significance(_array(result_table, "Mag_psf"), _array(result_table, "Mag_psf_e")) >= 3,
        "Re": _formal_significance(_array(result_table, "Re"), _array(result_table, "Re_e")) >= 3,
        "n": _formal_significance(_array(result_table, "n"), _array(result_table, "n_e")) >= 3,
        "q": _formal_significance(_array(result_table, "ratio"), _array(result_table, "ratio_e")) >= 3,
    }


def summarize_scenario(input_table: Table, result_table: Table) -> dict[str, object]:
    biases = parameter_biases(input_table, result_table)
    successes = success_masks(result_table)
    mhost = _array(input_table, "Mag_sersic")
    display_range = (mhost >= 19.0) & (mhost <= 27.5)

    result: dict[str, object] = {
        "n_total": int(len(input_table)),
        "n_paper_display_range_19_to_27p5": int(np.count_nonzero(display_range)),
        "success_fraction_display_range": {
            name: float(np.mean(mask[display_range])) for name, mask in successes.items()
        },
        "bias_distribution_display_range": {},
    }
    for name, values in biases.items():
        result["bias_distribution_display_range"][name] = _summary_distribution(values[display_range])
    return result


def ratio_grid_at_mhost_24(input_table: Table, scenario_tables: dict[str, Table]) -> list[dict[str, object]]:
    input_ratio = agn_to_host_flux_ratio(input_table)
    mhost = _array(input_table, "Mag_sersic")
    target_ratios = (0.1, 1.0, 10.0)
    rows: list[dict[str, object]] = []

    for scenario, table in scenario_tables.items():
        biases = parameter_biases(input_table, table)
        successes = success_masks(table)
        for ratio_target in target_ratios:
            mask = np.isclose(mhost, 24.0, atol=1e-8) & np.isclose(
                np.log10(input_ratio), np.log10(ratio_target), atol=1e-8
            )
            if not np.any(mask):
                raise RuntimeError(f"Expected m_host=24, AGN/host={ratio_target} grid point is absent.")

            row: dict[str, object] = {
                "scenario": scenario,
                "input_agn_to_host": ratio_target,
                "n": int(np.count_nonzero(mask)),
            }
            for parameter, values in biases.items():
                row[f"{parameter}_median"] = _finite_median(values[mask])
                row[f"{parameter}_p16"] = _finite_percentile(values[mask], 16)
                row[f"{parameter}_p84"] = _finite_percentile(values[mask], 84)
            for parameter, success in successes.items():
                row[f"success_fraction_{parameter}"] = float(np.mean(success[mask]))
            rows.append(row)
    return rows


def centroid_offset_summary(input_table: Table, center_table: Table) -> dict[str, object]:
    x0 = _array(input_table, "x")
    y0 = _array(input_table, "y")
    xagn = _array(center_table, "x_AGN")
    yagn = _array(center_table, "y_AGN")
    xhost = _array(center_table, "x_sersic")
    yhost = _array(center_table, "y_sersic")

    d_host = np.hypot(xhost - x0, yhost - y0)
    d_agn = np.hypot(xagn - x0, yagn - y0)
    d_host_agn = np.hypot(xhost - xagn, yhost - yagn)

    # Transparent conservative quadrature from the four independent coordinate
    # errors.  This is a provisional reproduction statistic until the exact
    # offset-error convention in the original analysis is independently matched.
    sigma_quad = np.sqrt(
        _array(center_table, "x_AGN_e") ** 2
        + _array(center_table, "y_AGN_e") ** 2
        + _array(center_table, "x_sersic_e") ** 2
        + _array(center_table, "y_sersic_e") ** 2
    )
    significance = np.divide(
        d_host_agn,
        sigma_quad,
        out=np.full_like(d_host_agn, np.nan),
        where=sigma_quad > 0,
    )
    significance[(sigma_quad == 0) & (d_host_agn > 0)] = np.inf
    significance[(sigma_quad == 0) & (d_host_agn == 0)] = 0.0

    mhost = _array(input_table, "Mag_sersic")
    mu = mean_host_surface_brightness(input_table)
    ratio = agn_to_host_flux_ratio(input_table)
    paper_mag_range = (mhost >= 19.0) & (mhost <= 27.5)
    above_sb_limit = mu <= F150W_SB_DEPTH_MAG_ARCSEC2

    out: dict[str, object] = {
        "surface_brightness_equation": "m_host + 2.5*log10(2*q*pi*(Re_pix*0.03_arcsec)^2)",
        "f150w_3sigma_sb_depth_mag_arcsec2": F150W_SB_DEPTH_MAG_ARCSEC2,
        "offset_error_convention": "sqrt(xAGN_e^2+yAGN_e^2+xSersic_e^2+ySersic_e^2); provisional",
        "all_paper_mag_range": {},
        "above_sb_limit": {},
        "offset_distributions_pixels": {
            "host_to_truth": _summary_distribution(d_host[paper_mag_range]),
            "agn_to_truth": _summary_distribution(d_agn[paper_mag_range]),
            "host_to_agn": _summary_distribution(d_host_agn[paper_mag_range]),
        },
    }

    for label, base in (("all_paper_mag_range", paper_mag_range), ("above_sb_limit", paper_mag_range & above_sb_limit)):
        for ratio_target in (0.1, 1.0, 10.0):
            mask = base & np.isclose(np.log10(ratio), np.log10(ratio_target), atol=1e-8)
            valid = mask & np.isfinite(significance)
            key = f"agn_to_host_{ratio_target:g}"
            out[label][key] = {
                "n": int(np.count_nonzero(valid)),
                "fraction_gt_1sigma_provisional": float(np.mean(significance[valid] > 1.0)) if np.any(valid) else None,
                "fraction_gt_2sigma_provisional": float(np.mean(significance[valid] > 2.0)) if np.any(valid) else None,
                "fraction_gt_3sigma_provisional": float(np.mean(significance[valid] > 3.0)) if np.any(valid) else None,
                "median_offset_over_Re": _finite_median(
                    d_host_agn[valid] / _array(input_table, "Re")[valid]
                ) if np.any(valid) else None,
            }
    return out


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise RuntimeError("No rows to write.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("external_data/zhuang_shen_2024/mock_AGN_results"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("benchmark_output/zhuang_shen_2024"),
    )
    args = parser.parse_args()

    input_table = Table.read(args.data_root / INPUT_FILE, format="ascii.ipac")
    scenario_tables = {
        name: Table.read(args.data_root / filename, format="ascii.ipac")
        for name, filename in SCENARIOS.items()
    }
    center_table = Table.read(args.data_root / CENTER_FREE_FILE, format="ascii.ipac")
    validate_row_identity(input_table, [*scenario_tables.values(), center_table])

    summary = {
        "reference": "Zhuang & Shen 2024, ApJ 962, 139, arXiv:2304.13776",
        "filter": "F150W",
        "pixel_scale_arcsec": PIXEL_SCALE_ARCSEC,
        "point_source_depth_5sigma_mag": F150W_POINT_DEPTH_MAG,
        "surface_brightness_depth_3sigma_mag_arcsec2": F150W_SB_DEPTH_MAG_ARCSEC2,
        "n_input": int(len(input_table)),
        "input_grid": {
            "m_agn_min": float(np.min(_array(input_table, "Mag_psf"))),
            "m_agn_max": float(np.max(_array(input_table, "Mag_psf"))),
            "m_host_min": float(np.min(_array(input_table, "Mag_sersic"))),
            "m_host_max": float(np.max(_array(input_table, "Mag_sersic"))),
            "Re_pixels": sorted(float(x) for x in np.unique(_array(input_table, "Re"))),
            "sersic_n": sorted(float(x) for x in np.unique(_array(input_table, "n"))),
            "axis_ratio_q": sorted(float(x) for x in np.unique(_array(input_table, "ratio"))),
            "agn_to_host_flux_ratio": sorted(
                float(x) for x in np.unique(np.round(agn_to_host_flux_ratio(input_table), 12))
            ),
        },
        "scenarios": {
            name: summarize_scenario(input_table, table) for name, table in scenario_tables.items()
        },
        "centroid_offsets": centroid_offset_summary(input_table, center_table),
    }

    ratio_rows = ratio_grid_at_mhost_24(input_table, scenario_tables)
    args.output_root.mkdir(parents=True, exist_ok=True)
    json_path = args.output_root / "summary_f150w.json"
    csv_path = args.output_root / "figure11_like_mhost24.csv"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_csv(csv_path, ratio_rows)

    print(f"ROW_IDENTITY: PASS ({len(input_table)} rows match exactly in all tables)")
    print("INPUT AGN/HOST GRID:", summary["input_grid"]["agn_to_host_flux_ratio"])
    print("F150W m_host=24 benchmark medians:")
    for row in ratio_rows:
        print(
            row["scenario"],
            "AGN/host=", row["input_agn_to_host"],
            "dmag_host=", f"{row['delta_m_host_median']:.4f}",
            "logRe=", f"{row['log10_recovered_over_true_Re_median']:.4f}",
            "logn=", f"{row['log10_recovered_over_true_n_median']:.4f}",
            "q_delta=", f"{row['delta_q_median']:.4f}",
        )
    print("CENTER OFFSET PROVISIONAL SIGNIFICANCE (above F150W SB limit):")
    for key, record in summary["centroid_offsets"]["above_sb_limit"].items():
        print(key, record)
    print(f"WROTE {json_path}")
    print(f"WROTE {csv_path}")


if __name__ == "__main__":
    main()
