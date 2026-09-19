#!/usr/bin/env python3
"""Summarize whether the controlled noisy C2 floor is information-limited.

This is a descriptive follow-up to the operational noisy multistart experiment.
It does not change fitting bounds, optimizer tolerances, scientific acceptance
criteria, or the simulated data.  The purpose is to separate numerical success
from measurement identifiability before adding further physical complexity.

For every already-generated recovery row we report two directly interpretable
observables available before fitting:

* an equivalent point-source S/N implied by the declared 5-sigma depth and the
  target apparent magnitude; and
* target effective radius divided by target PSF FWHM, a simple resolvedness
  coordinate.

We then tabulate parameter-bound incidence and recovery offsets against those
observables.  No S/N or resolvedness cut is declared here; doing so after seeing
these results would turn a diagnostic into a post-hoc acceptance criterion.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path("benchmark_output/paulino_afonso_2017/noisy_operational_multistart")
ROWS = ROOT / "rows.csv"
OUT = ROOT / "identifiability"

BOUND_COLUMNS = (
    "hit_re_lower_bound",
    "hit_re_upper_bound",
    "hit_n_lower_bound",
    "hit_n_upper_bound",
)


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def main() -> None:
    if not ROWS.exists():
        raise FileNotFoundError(f"Run the noisy operational ensemble first: {ROWS}")

    with ROWS.open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    enriched: list[dict[str, object]] = []
    for row in rows:
        target_mag = float(row["target_mag_ab"])
        depth = float(row["point_source_depth_ab_5sigma"])
        re_pix = float(row["target_re_pixels"])
        psf_fwhm_pix = float(row["psf_fwhm_pixels"])
        any_bound = any(_as_bool(row[name]) for name in BOUND_COLUMNS)
        enriched.append({
            "case": row["case"],
            "z_target": float(row["z_target"]),
            "realization": int(row["realization"]),
            "target_mag_ab": target_mag,
            "point_source_equivalent_snr": float(5.0 * 10.0 ** (-0.4 * (target_mag - depth))),
            "re_over_psf_fwhm": float(re_pix / psf_fwhm_pix),
            "fit_success": _as_bool(row["fit_success"]),
            "any_re_or_n_bound": any_bound,
            "re_ratio": float(row["re_ratio"]),
            "n_ratio": float(row["n_ratio"]),
            "q_difference": float(row["q_difference"]),
            "mag_difference": float(row["mag_difference"]),
            "centroid_error_pixels": float(row["centroid_error_pixels"]),
        })

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "rows.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(enriched[0].keys()))
        writer.writeheader()
        writer.writerows(enriched)

    by_z: list[dict[str, object]] = []
    for z in sorted({float(r["z_target"]) for r in enriched}):
        sub = [r for r in enriched if float(r["z_target"]) == z]
        by_z.append({
            "z_target": z,
            "n": len(sub),
            "fit_success_fraction": float(np.mean([bool(r["fit_success"]) for r in sub])),
            "parameter_bound_fraction": float(np.mean([bool(r["any_re_or_n_bound"]) for r in sub])),
            "point_source_equivalent_snr_min": float(min(float(r["point_source_equivalent_snr"]) for r in sub)),
            "point_source_equivalent_snr_median": float(np.median([float(r["point_source_equivalent_snr"]) for r in sub])),
            "point_source_equivalent_snr_max": float(max(float(r["point_source_equivalent_snr"]) for r in sub)),
            "re_over_psf_fwhm_min": float(min(float(r["re_over_psf_fwhm"]) for r in sub)),
            "re_over_psf_fwhm_median": float(np.median([float(r["re_over_psf_fwhm"]) for r in sub])),
            "re_over_psf_fwhm_max": float(max(float(r["re_over_psf_fwhm"]) for r in sub)),
            "median_re_ratio": float(np.median([float(r["re_ratio"]) for r in sub])),
            "median_n_ratio": float(np.median([float(r["n_ratio"]) for r in sub])),
        })

    by_case_redshift: list[dict[str, object]] = []
    keys = sorted({(str(r["case"]), float(r["z_target"])) for r in enriched}, key=lambda x: (x[1], x[0]))
    for case, z in keys:
        sub = [r for r in enriched if str(r["case"]) == case and float(r["z_target"]) == z]
        by_case_redshift.append({
            "case": case,
            "z_target": z,
            "n": len(sub),
            "target_mag_ab": float(sub[0]["target_mag_ab"]),
            "point_source_equivalent_snr": float(sub[0]["point_source_equivalent_snr"]),
            "re_over_psf_fwhm": float(sub[0]["re_over_psf_fwhm"]),
            "parameter_bound_fraction": float(np.mean([bool(r["any_re_or_n_bound"]) for r in sub])),
            "median_re_ratio": float(np.median([float(r["re_ratio"]) for r in sub])),
            "median_n_ratio": float(np.median([float(r["n_ratio"]) for r in sub])),
        })

    payload = {
        "experiment": "descriptive identifiability audit of controlled noisy C2 floor",
        "scientific_status": "diagnostic only; no post-hoc S/N or resolvedness acceptance cut declared",
        "n_rows": len(enriched),
        "observables": {
            "point_source_equivalent_snr": "5 * 10^[-0.4 * (target_mag - 5sigma_depth_mag)]",
            "re_over_psf_fwhm": "target effective radius in pixels / target PSF FWHM in pixels",
        },
        "by_redshift": by_z,
        "by_case_redshift": by_case_redshift,
        "decision_rule": (
            "If parameter-bound incidence grows where the pre-fit information coordinates degrade, treat those catastrophic recoveries as an identifiability limitation of the declared depth/resolution floor, not as residual optimizer bias. Do not hide them by widening bounds or inventing a post-hoc quality cut. Document the regime, then proceed to the physical source-to-target degradation benchmark with these failure modes retained as observables. If bound incidence is not associated with information loss, continue numerical diagnosis instead."
        ),
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
