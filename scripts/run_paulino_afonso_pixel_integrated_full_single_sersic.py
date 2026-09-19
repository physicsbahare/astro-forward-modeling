#!/usr/bin/env python3
"""Run the phase-corrected C2 noiseless single-Sersic set with a 4x pixel-integrated fitter.

This expands the previously isolated concentrated-n=4 pixel-integrated structural
fit to all five pre-declared synthetic single-Sersic cases at one target redshift.
The transfer operator, physical bounds, generic multistart locations, 3-point
Jacobian, x_scale='jac', MAX_NFEV, and lowest-cost winner rule are unchanged from
the established noiseless full-chain benchmark. Only the fit renderer is changed
to detector-pixel-integrated 4x sampling, matching the validated truth semantics.

This is a verification diagnostic, not production code and not a literal survey
reproduction. No morphology acceptance threshold is introduced here.
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
from scripts.run_paulino_afonso_high_n_pixel_integration_surface import (
    _pixel_integrated_unit_template,
    _profile_flux_and_sky,
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
    _kpc_per_arcsec,
    adaptive_stamp_size,
    flux_in_depth_units,
    mag_from_depth_units,
    pixel_noise_from_point_depth,
)


def fit_case(case: dict, z: float) -> tuple[list[dict], dict, dict]:
    sigma = pixel_noise_from_point_depth()
    kpc_arcsec = _kpc_per_arcsec(z)
    source_flux = flux_in_depth_units(float(case["source_mag_ab"]))
    transferred, _, _, _, source_equiv, kernel_fwhm, flux_ratio = transfer_to_target(case, z, source_flux)

    true_re_pix = float(case["re_kpc"]) / kpc_arcsec / TARGET_PIXEL_SCALE
    image = _central_crop(transferred, adaptive_stamp_size(true_re_pix))
    ny, nx = image.shape
    cx = 0.5 * (nx - 1)
    cy = 0.5 * (ny - 1)
    transferred_flux = float(np.sum(image))

    truth_template = _pixel_integrated_unit_template(
        image.shape, true_re_pix, float(case["n"]), float(case["q"]), cx, cy
    )
    truth_amp, truth_sky, truth_cost, truth_l1 = _profile_flux_and_sky(truth_template, image, sigma)

    ire = true_re_pix * INITIAL_RE_MULTIPLIER
    iflux = max(transferred_flux, 1e-12) * INITIAL_FLUX_MULTIPLIER
    iq = min(0.95, max(0.2, float(case["q"]) + INITIAL_Q_OFFSET))

    lower = np.array([np.log(1e-8), np.log(0.15), np.log(0.2), -12.0, -2.0, -2.0, -5.0])
    upper = np.array([np.log(1e8), np.log(120.0), np.log(8.0), 12.0, 2.0, 2.0, 5.0])

    def decode(p):
        return (
            float(np.exp(p[0])), float(np.exp(p[1])), float(np.exp(p[2])), _u_to_q(float(p[3])),
            cx + float(p[4]), cy + float(p[5]), float(p[6]) * sigma,
        )

    def residual(p):
        return ((_model(image.shape, *decode(p)) - image) / sigma).ravel()

    rows = []
    for rm in START_RE_MULTIPLIER_OF_ESTIMATE:
        for ns in START_N:
            p0 = np.array([
                np.log(max(iflux, 1e-12)), np.log(max(ire * rm, 0.2)), np.log(ns),
                _q_to_u(iq), 0.0, 0.0, 0.0,
            ])
            result = least_squares(
                residual, p0, bounds=(lower, upper), method="trf", jac="3-point", x_scale="jac",
                ftol=1e-9, xtol=1e-9, gtol=1e-9, max_nfev=MAX_NFEV,
            )
            rf, rr, rn, rq, rx, ry, rsky = decode(result.x)
            rows.append({
                "case": str(case["case"]), "z_target": z,
                "start_re_multiplier_of_estimate": float(rm), "start_n": float(ns),
                "success": bool(result.success), "status": int(result.status), "nfev": int(result.nfev),
                "cost": float(result.cost), "optimality": float(result.optimality),
                "input_re_kpc": float(case["re_kpc"]), "input_n": float(case["n"]), "input_q": float(case["q"]),
                "source_mag_ab": float(case["source_mag_ab"]), "fit_stamp_size": int(image.shape[0]),
                "source_psf_equivalent_at_target_arcsec": float(source_equiv),
                "matching_kernel_fwhm_arcsec": float(kernel_fwhm), "flux_ratio_source_to_target": float(flux_ratio),
                "recovered_re_kpc": float(rr * TARGET_PIXEL_SCALE * kpc_arcsec), "re_ratio": float(rr / true_re_pix),
                "recovered_n": float(rn), "n_ratio": float(rn / float(case["n"])),
                "recovered_q": float(rq), "q_difference": float(rq - float(case["q"])),
                "centroid_error_pixels": float(np.hypot(rx - cx, ry - cy)),
                "recovered_flux": float(rf), "recovered_mag": float(mag_from_depth_units(rf)),
                "sky_sigma_units": float(rsky / sigma),
                "hit_re_lower_bound": bool(rr <= 0.15 * (1 + 5e-5)),
                "hit_re_upper_bound": bool(rr >= 120.0 * (1 - 5e-5)),
                "hit_n_lower_bound": bool(rn <= 0.2 * (1 + 5e-5)),
                "hit_n_upper_bound": bool(rn >= 8.0 * (1 - 5e-5)),
            })

    best = min(rows, key=lambda r: float(r["cost"]))
    truth = {
        "case": str(case["case"]), "z_target": z, "profiled_flux": float(truth_amp),
        "sky_sigma_units": float(truth_sky / sigma), "cost": float(truth_cost),
        "normalized_l1": float(truth_l1),
    }
    return rows, best, truth


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--z-target", type=float, required=True, choices=list(TARGET_Z))
    args = parser.parse_args()
    z = float(args.z_target)

    all_rows: list[dict] = []
    best_rows: list[dict] = []
    truth_rows: list[dict] = []
    for case in CASES:
        rows, best, truth = fit_case(case, z)
        all_rows.extend(rows); best_rows.append(best); truth_rows.append(truth)

    def any_bound(r):
        return bool(r["hit_re_lower_bound"] or r["hit_re_upper_bound"] or r["hit_n_lower_bound"] or r["hit_n_upper_bound"])

    out = Path("benchmark_output/paulino_afonso_2017/pixel_integrated_full_single_sersic") / (
        "z_" + str(z).replace(".", "p")
    )
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in (("all_starts.csv", all_rows), ("best_rows.csv", best_rows), ("truth_objectives.csv", truth_rows)):
        with (out / name).open("w", newline="") as h:
            w = csv.DictWriter(h, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    payload = {
        "experiment": "C2 full noiseless single-Sersic recovery with 4x pixel-integrated fitter",
        "scientific_status": "controlled synthetic-equivalent diagnostic; not literal survey reproduction",
        "z_target": z, "n_cases": len(best_rows), "n_starts_per_case": len(START_N) * len(START_RE_MULTIPLIER_OF_ESTIMATE),
        "jacobian_scheme": "3-point", "x_scale": "jac", "max_nfev": MAX_NFEV,
        "selection_rule": "lowest residual cost only; never closeness to truth or literature",
        "bounds": "unchanged from established noiseless full-chain benchmark",
        "fit_success_fraction": float(np.mean([bool(r["success"]) for r in best_rows])),
        "any_re_or_n_bound_fraction": float(np.mean([any_bound(r) for r in best_rows])),
        "median_re_ratio": float(np.median([float(r["re_ratio"]) for r in best_rows])),
        "median_n_ratio": float(np.median([float(r["n_ratio"]) for r in best_rows])),
        "median_abs_q_difference": float(np.median([abs(float(r["q_difference"])) for r in best_rows])),
        "max_centroid_error_pixels": float(max(float(r["centroid_error_pixels"]) for r in best_rows)),
        "best_rows": best_rows, "truth_structure_profiled_objectives": truth_rows,
        "next_decision_rule": (
            "Do not invent morphology acceptance bands from these results. If the five lowest-cost fits are numerically stable "
            "and no structural blocker remains, proceed to a target-noise ensemble using the same pixel-integrated renderer. "
            "If a case is nonconverged or boundary-limited, diagnose it before adding noise."
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
