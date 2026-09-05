#!/usr/bin/env python3
"""Run the C2 target-noise single-Sersic ensemble with the validated 4x fitter.

The phase-corrected noiseless transfer and the full 20-case noiseless structural
benchmark have established that detector-pixel-integrated 4x model rendering
removes the large point-sampling floor without changing fit bounds, optimizer
settings, or winner selection.  This diagnostic now adds only the previously
declared ACS-like white Gaussian target noise and reuses the same deterministic
realizations as the historical point-sampled noisy benchmark.

Each invocation covers five pre-declared single-Sersic cases at one target
redshift and one deterministic realization.  The workflow shards the full
4 redshifts x 3 realizations into 12 independent jobs.  Low-S/N non-convergence,
bound hits, centroid excursions, and morphology offsets are observables; no
acceptance band is introduced or widened here.
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

from scripts.run_paulino_afonso_full_chain_califa import (
    CASES,
    TARGET_PIXEL_SCALE,
    TARGET_Z,
    transfer_to_target,
)
from scripts.run_paulino_afonso_pixel_integrated_structural_fitter import (
    START_N,
    START_RE_MULTIPLIER_OF_ESTIMATE,
    INITIAL_RE_MULTIPLIER,
    INITIAL_FLUX_MULTIPLIER,
    INITIAL_Q_OFFSET,
    MAX_NFEV,
    _q_to_u,
    _u_to_q,
    _central_crop,
    _model,
)
from verification.paulino_afonso_sersic_floor import (
    POINT_DEPTH_AB_5SIGMA,
    PSF_FWHM_ARCSEC,
    _kpc_per_arcsec,
    adaptive_stamp_size,
    flux_in_depth_units,
    mag_from_depth_units,
    pixel_noise_from_point_depth,
)

REALIZATIONS = 3
BASE_SEED = 92717


def _any_bound(row: dict) -> bool:
    return bool(
        row["hit_re_lower_bound"]
        or row["hit_re_upper_bound"]
        or row["hit_n_lower_bound"]
        or row["hit_n_upper_bound"]
    )


def fit_noisy_case(case: dict, z: float, realization: int, case_index: int, z_index: int):
    sigma = pixel_noise_from_point_depth()
    kpc_arcsec = _kpc_per_arcsec(z)
    source_flux = flux_in_depth_units(float(case["source_mag_ab"]))
    transferred, _, _, _, source_equiv, kernel_fwhm, flux_ratio = transfer_to_target(case, z, source_flux)

    true_re_pix = float(case["re_kpc"]) / kpc_arcsec / TARGET_PIXEL_SCALE
    base = _central_crop(transferred, adaptive_stamp_size(true_re_pix))
    ny, nx = base.shape
    cx = 0.5 * (nx - 1)
    cy = 0.5 * (ny - 1)
    transferred_flux = float(np.sum(base))

    seed = int(BASE_SEED + z_index * 100000 + case_index * 1000 + realization)
    rng = np.random.default_rng(seed)
    image = base + rng.normal(0.0, sigma, size=base.shape)

    target_flux = source_flux * flux_ratio
    target_mag = float(mag_from_depth_units(target_flux))
    point_source_equivalent_snr = float(
        5.0 * 10.0 ** (-0.4 * (target_mag - POINT_DEPTH_AB_5SIGMA))
    )
    known_template_matched_snr = float(np.sqrt(np.sum(base**2)) / sigma)
    peak_pixel_snr = float(np.max(base) / sigma)
    whole_stamp_sum_snr = float(np.sum(base) / (sigma * np.sqrt(base.size)))
    re_over_psf_fwhm = float(
        true_re_pix / (PSF_FWHM_ARCSEC / TARGET_PIXEL_SCALE)
    )

    ire = true_re_pix * INITIAL_RE_MULTIPLIER
    iflux = max(transferred_flux, 1e-12) * INITIAL_FLUX_MULTIPLIER
    iq = min(0.95, max(0.2, float(case["q"]) + INITIAL_Q_OFFSET))

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
        return ((_model(image.shape, *decode(p)) - image) / sigma).ravel()

    starts = []
    for rm in START_RE_MULTIPLIER_OF_ESTIMATE:
        for ns in START_N:
            p0 = np.array([
                np.log(max(iflux, 1e-12)),
                np.log(max(ire * rm, 0.2)),
                np.log(ns),
                _q_to_u(iq),
                0.0,
                0.0,
                0.0,
            ])
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
            starts.append({
                "case": str(case["case"]),
                "z_source": 0.015,
                "z_target": z,
                "realization": int(realization),
                "seed": seed,
                "input_re_kpc": float(case["re_kpc"]),
                "input_n": float(case["n"]),
                "input_q": float(case["q"]),
                "source_mag_ab": float(case["source_mag_ab"]),
                "target_mag_ab": target_mag,
                "point_source_equivalent_snr": point_source_equivalent_snr,
                "known_template_matched_snr": known_template_matched_snr,
                "peak_pixel_snr": peak_pixel_snr,
                "whole_stamp_sum_snr": whole_stamp_sum_snr,
                "re_over_psf_fwhm": re_over_psf_fwhm,
                "fit_stamp_size": int(image.shape[0]),
                "source_psf_equivalent_at_target_arcsec": float(source_equiv),
                "matching_kernel_fwhm_arcsec": float(kernel_fwhm),
                "start_re_multiplier_of_estimate": float(rm),
                "start_n": float(ns),
                "success": bool(result.success),
                "status": int(result.status),
                "nfev": int(result.nfev),
                "cost": float(result.cost),
                "optimality": float(result.optimality),
                "recovered_re_kpc": float(rr * TARGET_PIXEL_SCALE * kpc_arcsec),
                "re_ratio": float(rr / true_re_pix),
                "recovered_n": float(rn),
                "n_ratio": float(rn / float(case["n"])),
                "recovered_q": float(rq),
                "q_difference": float(rq - float(case["q"])),
                "recovered_flux": float(rf),
                "recovered_mag": float(mag_from_depth_units(rf)),
                "centroid_error_pixels": float(np.hypot(rx - cx, ry - cy)),
                "sky_sigma_units": float(rsky / sigma),
                "hit_re_lower_bound": bool(rr <= 0.15 * (1 + 5e-5)),
                "hit_re_upper_bound": bool(rr >= 120.0 * (1 - 5e-5)),
                "hit_n_lower_bound": bool(rn <= 0.2 * (1 + 5e-5)),
                "hit_n_upper_bound": bool(rn >= 8.0 * (1 - 5e-5)),
            })

    return starts, min(starts, key=lambda row: float(row["cost"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--z-target", type=float, required=True, choices=list(TARGET_Z))
    parser.add_argument("--realization", type=int, required=True, choices=list(range(REALIZATIONS)))
    args = parser.parse_args()

    z = float(args.z_target)
    realization = int(args.realization)
    z_index = list(map(float, TARGET_Z)).index(z)

    all_rows = []
    best_rows = []
    for case_index, case in enumerate(CASES):
        starts, best = fit_noisy_case(case, z, realization, case_index, z_index)
        all_rows.extend(starts)
        best_rows.append(best)

    out = Path("benchmark_output/paulino_afonso_2017/pixel_integrated_noisy_single_sersic") / (
        "z_" + str(z).replace(".", "p") + f"/realization_{realization}"
    )
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in (("all_starts.csv", all_rows), ("best_rows.csv", best_rows)):
        with (out / name).open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    payload = {
        "experiment": "C2 target-noise single-Sersic recovery with 4x pixel-integrated fitter",
        "scientific_status": "controlled synthetic-equivalent diagnostic; not literal survey reproduction",
        "z_target": z,
        "realization": realization,
        "n_images": len(best_rows),
        "n_starts_per_image": len(START_N) * len(START_RE_MULTIPLIER_OF_ESTIMATE),
        "base_seed": BASE_SEED,
        "noise_model": "declared ACS-like white Gaussian depth model; AB=27.2 at 5 sigma point source",
        "selection_rule": "lowest residual cost only; non-convergence and bound hits retained as observables",
        "bounds": "unchanged from established full-chain structural benchmark",
        "fit_success_fraction": float(np.mean([bool(row["success"]) for row in best_rows])),
        "any_re_or_n_bound_fraction": float(np.mean([_any_bound(row) for row in best_rows])),
        "median_re_ratio": float(np.median([float(row["re_ratio"]) for row in best_rows])),
        "median_n_ratio": float(np.median([float(row["n_ratio"]) for row in best_rows])),
        "median_abs_q_difference": float(np.median([abs(float(row["q_difference"])) for row in best_rows])),
        "median_centroid_error_pixels": float(np.median([float(row["centroid_error_pixels"]) for row in best_rows])),
        "median_point_source_equivalent_snr": float(np.median([float(row["point_source_equivalent_snr"]) for row in best_rows])),
        "median_known_template_matched_snr": float(np.median([float(row["known_template_matched_snr"]) for row in best_rows])),
        "median_peak_pixel_snr": float(np.median([float(row["peak_pixel_snr"]) for row in best_rows])),
        "best_rows": best_rows,
        "decision_rule": (
            "Do not widen bounds or tune morphology tolerances. Compare these same-seed outcomes with the historical "
            "point-sampled noisy benchmark and with the noiseless pixel-integrated floor. If sampling-driven pathologies "
            "disappear but low-known-template-S/N cases remain unstable, classify the remainder as information/identifiability "
            "loss. If high-known-template-S/N cases remain pathological, investigate another fitter/model issue before literature comparison."
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
