#!/usr/bin/env python3
"""Targeted numerical stability audit for the noiseless bulge+disk benchmark.

Run 33482286026 completed successfully at the workflow level, but the
lowest-cost B/T=0.10 single-Sersic solutions at z=1.47 and z=2.23 exhausted the
pre-declared MAX_NFEV=1800 budget.  This audit diagnoses that numerical fact
without changing the scientific model, bounds, tolerances, Jacobian, scaling,
or winner rule of the parent benchmark.

For each unresolved redshift, the exact start that produced the lowest-cost
non-converged solution is first rerun with MAX_NFEV=1800.  The optimizer is then
restarted from that endpoint with an additional 5400 evaluations.  This is a
numerical continuation diagnostic only; it does not redefine the parent
benchmark and introduces no new acceptance band.

The B/T=0.30 and B/T=0.50 parent solutions are not refit here: their radius/n
bound hits were highly reproducible across multistarts and are retained as
scientific observables of single-Sersic model mismatch rather than hidden by
widening the established bounds.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_paulino_afonso_bulge_disk_model_mismatch import (
    COMPOSITES,
    MAX_NFEV,
    _central_crop,
    _q_to_u,
    _u_to_q,
)
from scripts.run_paulino_afonso_full_chain_califa import transfer_to_target
from verification.paulino_afonso_sersic_floor import (
    PIXEL_SCALE_ARCSEC,
    _convolved_model,
    _kpc_per_arcsec,
    adaptive_stamp_size,
    flux_in_depth_units,
    pixel_noise_from_point_depth,
)

# These are the two lowest-cost non-converged winners observed in run
# 33482286026.  Selection is based only on optimizer outcome/cost, never on
# closeness to truth or to literature.
UNRESOLVED_STARTS = {
    1.47: {"start_re_multiplier": 1.0, "start_n": 2.5},
    2.23: {"start_re_multiplier": 1.4, "start_n": 1.0},
}
CONTINUATION_NFEV = 5400


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--z-target",
        type=float,
        required=True,
        help="Target redshift for one unresolved B/T=0.10 numerical audit.",
    )
    return p.parse_args()


def _match_redshift(value: float) -> float:
    for z in UNRESOLVED_STARTS:
        if np.isclose(float(value), float(z), rtol=0.0, atol=1e-10):
            return float(z)
    raise SystemExit(f"--z-target must be one of {tuple(UNRESOLVED_STARTS)}")


def _fit_record(result, decode, cx, cy, sigma, kpc_arcsec):
    rf, rr, rn, rq, rx, ry, rsky = decode(result.x)
    return {
        "success": bool(result.success),
        "status": int(result.status),
        "nfev": int(result.nfev),
        "cost": float(result.cost),
        "optimality": float(result.optimality),
        "recovered_re_kpc": float(rr * PIXEL_SCALE_ARCSEC * kpc_arcsec),
        "recovered_n": float(rn),
        "recovered_q": float(rq),
        "centroid_error_pixels": float(np.hypot(rx - cx, ry - cy)),
        "sky_sigma_units": float(rsky / sigma),
        "recovered_flux": float(rf),
        "hit_re_lower_bound": bool(rr <= 0.15 * (1 + 5e-5)),
        "hit_re_upper_bound": bool(rr >= 120.0 * (1 - 5e-5)),
        "hit_n_lower_bound": bool(rn <= 0.2 * (1 + 5e-5)),
        "hit_n_upper_bound": bool(rn >= 8.0 * (1 - 5e-5)),
    }


def main():
    args = _parse_args()
    z = _match_redshift(args.z_target)
    start = UNRESOLVED_STARTS[z]
    cfg = next(c for c in COMPOSITES if np.isclose(float(c["bt"]), 0.10))

    out = Path("benchmark_output/paulino_afonso_2017/bulge_disk_stability") / f"z_{z:.2f}".replace(".", "p")
    out.mkdir(parents=True, exist_ok=True)

    sigma = pixel_noise_from_point_depth()
    kpc_arcsec = _kpc_per_arcsec(z)
    total_source_flux = flux_in_depth_units(cfg["total_source_mag_ab"])
    disk_flux = total_source_flux * (1.0 - cfg["bt"])
    bulge_flux = total_source_flux * cfg["bt"]

    disk_case = {
        "case": cfg["case"] + "_disk",
        "re_kpc": cfg["disk_re_kpc"],
        "n": 1.0,
        "q": cfg["disk_q"],
        "source_mag_ab": cfg["total_source_mag_ab"],
    }
    bulge_case = {
        "case": cfg["case"] + "_bulge",
        "re_kpc": cfg["bulge_re_kpc"],
        "n": 4.0,
        "q": cfg["bulge_q"],
        "source_mag_ab": cfg["total_source_mag_ab"],
    }
    disk, _, _, _, _, _, _ = transfer_to_target(disk_case, z, disk_flux)
    bulge, _, _, _, _, _, _ = transfer_to_target(bulge_case, z, bulge_flux)
    composite = disk + bulge

    disk_re_pix = cfg["disk_re_kpc"] / kpc_arcsec / PIXEL_SCALE_ARCSEC
    image = _central_crop(composite, adaptive_stamp_size(disk_re_pix))
    ny, nx = image.shape
    cx = 0.5 * (nx - 1)
    cy = 0.5 * (ny - 1)
    fit_flux = max(float(np.sum(image)), 1e-12)
    initial_q = (1 - cfg["bt"]) * cfg["disk_q"] + cfg["bt"] * cfg["bulge_q"]

    lower = np.array([np.log(1e-8), np.log(0.15), np.log(0.2), -12.0, -2.0, -2.0, -5.0])
    upper = np.array([np.log(1e8), np.log(120.0), np.log(8.0), 12.0, 2.0, 2.0, 5.0])

    def decode(p):
        return (
            float(np.exp(p[0])),
            float(np.exp(p[1])),
            float(np.exp(p[2])),
            _u_to_q(float(p[3])),
            cx + float(p[4]),
            cy + float(p[5]),
            float(p[6]) * sigma,
        )

    def residual(p):
        return ((_convolved_model(image.shape, *decode(p)) - image) / sigma).ravel()

    p0 = np.array(
        [
            np.log(fit_flux * 0.95),
            np.log(max(disk_re_pix * start["start_re_multiplier"], 0.2)),
            np.log(start["start_n"]),
            _q_to_u(initial_q),
            0.0,
            0.0,
            0.0,
        ]
    )

    common = dict(
        bounds=(lower, upper),
        method="trf",
        jac="3-point",
        x_scale="jac",
        ftol=1e-9,
        xtol=1e-9,
        gtol=1e-9,
    )

    baseline = least_squares(residual, p0, max_nfev=MAX_NFEV, **common)
    continued = least_squares(residual, baseline.x, max_nfev=CONTINUATION_NFEV, **common)

    baseline_row = _fit_record(baseline, decode, cx, cy, sigma, kpc_arcsec)
    continuation_row = _fit_record(continued, decode, cx, cy, sigma, kpc_arcsec)

    comparison = {
        "cost_fractional_change": float((continuation_row["cost"] - baseline_row["cost"]) / max(abs(baseline_row["cost"]), 1e-300)),
        "re_fractional_change": float((continuation_row["recovered_re_kpc"] - baseline_row["recovered_re_kpc"]) / max(abs(baseline_row["recovered_re_kpc"]), 1e-300)),
        "n_fractional_change": float((continuation_row["recovered_n"] - baseline_row["recovered_n"]) / max(abs(baseline_row["recovered_n"]), 1e-300)),
        "q_change": float(continuation_row["recovered_q"] - baseline_row["recovered_q"]),
        "centroid_error_change_pixels": float(continuation_row["centroid_error_pixels"] - baseline_row["centroid_error_pixels"]),
    }

    rows = []
    for stage, record in (("baseline_1800", baseline_row), ("restart_continuation_5400", continuation_row)):
        rows.append({
            "stage": stage,
            "z_target": z,
            "case": cfg["case"],
            "bt": cfg["bt"],
            "start_re_multiplier_of_disk_re": start["start_re_multiplier"],
            "start_n": start["start_n"],
            **record,
        })

    with (out / "stability_rows.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    payload = {
        "experiment": "targeted noiseless bulge+disk numerical stability continuation",
        "scientific_status": "controlled synthetic-equivalent diagnostic; not literal survey reproduction",
        "parent_run_id": 33482286026,
        "parent_experiment": "noiseless bulge+disk model mismatch through CALIFA-feasible full chain",
        "case": cfg["case"],
        "bt": cfg["bt"],
        "z_target": z,
        "selection_basis": "exact start of the parent run's lowest-cost non-converged winner; no truth/literature proximity criterion",
        "unchanged_scientific_setup": [
            "same composite galaxy",
            "same full-chain transfer operator",
            "same single-Sersic model",
            "same parameter bounds",
            "same ftol/xtol/gtol",
            "same 3-point numerical Jacobian",
            "same x_scale=jac",
        ],
        "baseline_max_nfev": MAX_NFEV,
        "continuation_max_nfev": CONTINUATION_NFEV,
        "baseline": baseline_row,
        "continuation": continuation_row,
        "comparison": comparison,
        "decision_rule": "Use this only to diagnose whether the parent max-NFEV winners were iteration-budget effects. Do not widen bounds or invent an acceptance band. If the low-B/T solutions become converged and numerically stationary, proceed to the declared noisy bulge+disk ensemble while retaining B/T=0.30 and 0.50 bound hits as structural model-mismatch observables.",
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
