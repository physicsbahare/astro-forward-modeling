#!/usr/bin/env python3
"""Noisy bulge+disk -> single-Sersic full-chain ensemble.

This stage follows the noiseless structural-model-mismatch benchmark and its
separate numerical-stability continuation audit.  It adds only the already
declared ACS-like white Gaussian target-noise model after the same physically
feasible CALIFA-like artificial-redshifting operator.

The structural cases, single-Sersic parameter bounds, 12 multistarts, 3-point
numerical Jacobian, x_scale='jac', convergence tolerances, MAX_NFEV, and winner
rule are inherited unchanged from the noiseless bulge+disk benchmark.  The
winner is always the lowest residual-cost start; non-convergence and bound hits
are recorded as scientific benchmark observables rather than filtered away.

Three deterministic target-noise realizations are pre-declared for every B/T
and target-redshift combination.  --z-target and --realization only shard this
fixed ensemble for CI runtime; they do not alter the scientific experiment.

This is a controlled synthetic-equivalent diagnostic, not a literal
CALIFA/Paulino-Afonso survey-data reproduction.
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
    START_N,
    START_RE_MULTIPLIER,
    _central_crop,
    _q_to_u,
    _u_to_q,
)
from scripts.run_paulino_afonso_full_chain_califa import TARGET_Z, transfer_to_target
from verification.paulino_afonso_sersic_floor import (
    PIXEL_SCALE_ARCSEC,
    POINT_DEPTH_AB_5SIGMA,
    _convolved_model,
    _kpc_per_arcsec,
    adaptive_stamp_size,
    flux_in_depth_units,
    mag_from_depth_units,
    pixel_noise_from_point_depth,
)

REALIZATIONS = 3
BASE_SEED = 92717


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--z-target",
        type=float,
        default=None,
        help="Run one member of the pre-declared TARGET_Z grid; default runs all.",
    )
    p.add_argument(
        "--realization",
        type=int,
        default=None,
        help="Run one of the pre-declared deterministic realizations 0,1,2; default runs all.",
    )
    return p.parse_args()


def _selected_redshifts(z_target):
    if z_target is None:
        return tuple((iz, float(z)) for iz, z in enumerate(TARGET_Z))
    matches = [
        (iz, float(z))
        for iz, z in enumerate(TARGET_Z)
        if np.isclose(float(z), float(z_target), rtol=0.0, atol=1e-10)
    ]
    if not matches:
        raise SystemExit(f"--z-target must be one of {tuple(float(z) for z in TARGET_Z)}")
    return tuple(matches)


def _selected_realizations(realization):
    if realization is None:
        return tuple(range(REALIZATIONS))
    if int(realization) not in range(REALIZATIONS):
        raise SystemExit(f"--realization must be one of {tuple(range(REALIZATIONS))}")
    return (int(realization),)


def _any_re_or_n_bound(row):
    return bool(
        row["hit_re_lower_bound"]
        or row["hit_re_upper_bound"]
        or row["hit_n_lower_bound"]
        or row["hit_n_upper_bound"]
    )


def main():
    args = _parse_args()
    selected_z = _selected_redshifts(args.z_target)
    selected_realizations = _selected_realizations(args.realization)

    z_suffix = "all" if args.z_target is None else f"z_{selected_z[0][1]:.2f}".replace(".", "p")
    r_suffix = "all" if args.realization is None else f"r_{selected_realizations[0]}"
    out = Path("benchmark_output/paulino_afonso_2017/bulge_disk_noisy_ensemble") / z_suffix / r_suffix
    out.mkdir(parents=True, exist_ok=True)

    sigma = pixel_noise_from_point_depth()
    all_rows = []
    best_rows = []

    for iz, z in selected_z:
        kpc_arcsec = _kpc_per_arcsec(z)
        for icase, cfg in enumerate(COMPOSITES):
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

            disk, _, _, _, source_equiv, kernel_fwhm, flux_ratio = transfer_to_target(
                disk_case, z, disk_flux
            )
            bulge, _, _, _, _, _, _ = transfer_to_target(bulge_case, z, bulge_flux)
            composite = disk + bulge

            disk_re_pix = cfg["disk_re_kpc"] / kpc_arcsec / PIXEL_SCALE_ARCSEC
            noiseless = _central_crop(composite, adaptive_stamp_size(disk_re_pix))
            ny, nx = noiseless.shape
            cx = 0.5 * (nx - 1)
            cy = 0.5 * (ny - 1)

            # Preserve the noiseless benchmark's initialization rather than
            # allowing one noise realization to redefine the multistart grid.
            fit_flux = max(float(np.sum(noiseless)), 1e-12)
            initial_q = (1.0 - cfg["bt"]) * cfg["disk_q"] + cfg["bt"] * cfg["bulge_q"]

            expected_target_flux = float(total_source_flux * flux_ratio)
            target_mag = float(mag_from_depth_units(expected_target_flux))
            point_source_equivalent_snr = float(
                5.0 * 10.0 ** (-0.4 * (target_mag - POINT_DEPTH_AB_5SIGMA))
            )
            known_template_matched_snr = float(np.sqrt(np.sum(noiseless**2)) / sigma)
            peak_pixel_snr = float(np.max(noiseless) / sigma)
            whole_stamp_sum_snr = float(np.sum(noiseless) / (sigma * np.sqrt(noiseless.size)))

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

            for realization in selected_realizations:
                seed = int(BASE_SEED + iz * 100000 + icase * 1000 + realization)
                rng = np.random.default_rng(seed)
                image = noiseless + rng.normal(0.0, sigma, size=noiseless.shape)

                def residual(p):
                    return ((_convolved_model(image.shape, *decode(p)) - image) / sigma).ravel()

                starts = []
                for rm in START_RE_MULTIPLIER:
                    for ns in START_N:
                        p0 = np.array(
                            [
                                np.log(fit_flux * 0.95),
                                np.log(max(disk_re_pix * rm, 0.2)),
                                np.log(ns),
                                _q_to_u(initial_q),
                                0.0,
                                0.0,
                                0.0,
                            ]
                        )
                        result = least_squares(
                            residual,
                            p0,
                            bounds=(lower, upper),
                            method="trf",
                            jac="3-point",
                            x_scale="jac",
                            ftol=1e-9,
                            xtol=1e-9,
                            gtol=1e-9,
                            max_nfev=MAX_NFEV,
                        )
                        rf, rr, rn, rq, rx, ry, rsky = decode(result.x)
                        row = {
                            "case": cfg["case"],
                            "z_target": float(z),
                            "bt": float(cfg["bt"]),
                            "realization": int(realization),
                            "seed": seed,
                            "total_source_mag_ab": float(cfg["total_source_mag_ab"]),
                            "target_mag_ab": target_mag,
                            "disk_re_kpc": float(cfg["disk_re_kpc"]),
                            "disk_n": 1.0,
                            "disk_q": float(cfg["disk_q"]),
                            "bulge_re_kpc": float(cfg["bulge_re_kpc"]),
                            "bulge_n": 4.0,
                            "bulge_q": float(cfg["bulge_q"]),
                            "flux_weighted_input_q": float(initial_q),
                            "fit_stamp_size": int(image.shape[0]),
                            "pixel_noise_sigma_depth_units": float(sigma),
                            "point_source_equivalent_snr": point_source_equivalent_snr,
                            "known_template_matched_snr": known_template_matched_snr,
                            "peak_pixel_snr": peak_pixel_snr,
                            "whole_stamp_sum_snr": whole_stamp_sum_snr,
                            "source_psf_equivalent_at_target_arcsec": float(source_equiv),
                            "matching_kernel_fwhm_arcsec": float(kernel_fwhm),
                            "expected_target_flux": expected_target_flux,
                            "noiseless_flux_in_fit_stamp": float(np.sum(noiseless)),
                            "noisy_flux_in_fit_stamp": float(np.sum(image)),
                            "start_re_multiplier_of_disk_re": float(rm),
                            "start_n": float(ns),
                            "success": bool(result.success),
                            "status": int(result.status),
                            "nfev": int(result.nfev),
                            "cost": float(result.cost),
                            "optimality": float(result.optimality),
                            "recovered_re_kpc": float(rr * PIXEL_SCALE_ARCSEC * kpc_arcsec),
                            "recovered_re_over_disk_re": float(rr / disk_re_pix),
                            "recovered_n": float(rn),
                            "recovered_q": float(rq),
                            "q_minus_flux_weighted_input": float(rq - initial_q),
                            "recovered_flux": float(rf),
                            "recovered_mag": float(mag_from_depth_units(rf)),
                            "centroid_error_pixels": float(np.hypot(rx - cx, ry - cy)),
                            "sky_sigma_units": float(rsky / sigma),
                            "hit_re_lower_bound": bool(rr <= 0.15 * (1 + 5e-5)),
                            "hit_re_upper_bound": bool(rr >= 120.0 * (1 - 5e-5)),
                            "hit_n_lower_bound": bool(rn <= 0.2 * (1 + 5e-5)),
                            "hit_n_upper_bound": bool(rn >= 8.0 * (1 - 5e-5)),
                        }
                        all_rows.append(row)
                        starts.append(row)

                # Preserve the declared truth-independent winner rule even when
                # the lowest-cost start is non-converged or boundary-limited.
                best_rows.append(min(starts, key=lambda r: float(r["cost"])))

    for name, rows in (("all_starts.csv", all_rows), ("best_rows.csv", best_rows)):
        with (out / name).open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    summary_rows = []
    for row in best_rows:
        summary_rows.append(
            {
                key: row[key]
                for key in (
                    "case",
                    "z_target",
                    "bt",
                    "realization",
                    "seed",
                    "success",
                    "status",
                    "nfev",
                    "recovered_re_kpc",
                    "recovered_re_over_disk_re",
                    "recovered_n",
                    "recovered_q",
                    "centroid_error_pixels",
                    "sky_sigma_units",
                    "hit_re_lower_bound",
                    "hit_re_upper_bound",
                    "hit_n_lower_bound",
                    "hit_n_upper_bound",
                    "point_source_equivalent_snr",
                    "known_template_matched_snr",
                    "peak_pixel_snr",
                )
            }
        )

    payload = {
        "experiment": "noisy bulge+disk model mismatch through CALIFA-feasible full chain",
        "scientific_status": "controlled synthetic-equivalent diagnostic; not literal survey reproduction",
        "noise_model": "declared ACS-like white Gaussian noise derived from AB=27.2 at 5 sigma point-source depth",
        "realizations_per_case_redshift": REALIZATIONS,
        "base_seed": BASE_SEED,
        "execution_shard_redshifts": [float(z) for _, z in selected_z],
        "execution_shard_realizations": list(selected_realizations),
        "bt_values": [float(c["bt"]) for c in COMPOSITES],
        "n_starts_per_image": len(START_N) * len(START_RE_MULTIPLIER),
        "max_nfev": MAX_NFEV,
        "selection_rule": "lowest residual cost only; never proximity to truth or literature",
        "fit_success_fraction": float(np.mean([bool(r["success"]) for r in best_rows])),
        "any_re_or_n_bound_fraction": float(np.mean([_any_re_or_n_bound(r) for r in best_rows])),
        "summary_rows": summary_rows,
        "interpretation_rule": "Treat non-convergence, Re/n bound hits, centroid excursions, and morphology loss as benchmark observables. Do not widen bounds or tune tolerances to recover the noiseless or published values. Compare the noisy results with the noiseless structural-mismatch floor and extended-source information content.",
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
