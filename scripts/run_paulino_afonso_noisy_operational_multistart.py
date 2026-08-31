#!/usr/bin/env python3
"""Run the controlled C2 noisy ensemble with the operational robust fitter.

This is the next step after the truth-independent noiseless floor.  It keeps the
same controlled single-Sersic truth scenes, target PSF, sampling, radiometric
mapping, white-noise depth model, physical parameter bounds and deterministic
seeds used by the existing Paulino-Afonso measurement-floor experiment.  The
only numerical change is the fitter strategy that passed the operational
noiseless floor:

* central finite-difference Jacobian (jac='3-point');
* x_scale='jac';
* fixed generic n starts (1.0, 2.5, 5.5, 7.0);
* Re starts at 0.8 and 1.2 times the supplied Re estimate;
* dimensionless sky/sigma coordinate with the same decoded +/-5 sigma bound;
* choose the solution with the lowest residual cost only.

No literature-matching tolerance, correction factor, or morphology acceptance
criterion is introduced.  The purpose is to measure the bias that remains once
the known optimizer-basin pathology is removed.  Three realizations per
case/redshift remain a diagnostic ensemble, not a claim of stochastic
convergence.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

from verification.paulino_afonso_sersic_floor import (
    PIXEL_SCALE_ARCSEC,
    PSF_FWHM_ARCSEC,
    POINT_DEPTH_AB_5SIGMA,
    SOURCE_REDSHIFT,
    TARGET_REDSHIFTS,
    TRUTH_CASES,
    _convolved_model,
    _kpc_per_arcsec,
    adaptive_stamp_size,
    flux_in_depth_units,
    mag_from_depth_units,
    pixel_noise_from_point_depth,
    target_mag_from_source_mag,
)

START_N = (1.0, 2.5, 5.5, 7.0)
START_RE_MULTIPLIER_OF_ESTIMATE = (0.8, 1.2)
MAX_NFEV = 1800
REALIZATIONS = 3
BASE_SEED = 2717


def _q_to_u(q: float) -> float:
    qmin, qmax = 0.15, 1.0
    t = np.clip((q - qmin) / (qmax - qmin), 1e-8, 1 - 1e-8)
    return float(np.log(t / (1 - t)))


def _u_to_q(u: float) -> float:
    qmin, qmax = 0.15, 1.0
    t = 1.0 / (1.0 + np.exp(-u))
    return float(qmin + (qmax - qmin) * t)


def _fit_multistart(
    image: np.ndarray,
    sigma: float,
    initial_re_pix: float,
    initial_q: float,
    initial_flux: float,
):
    ny, nx = image.shape
    xmid = 0.5 * (nx - 1)
    ymid = 0.5 * (ny - 1)

    lower = np.array([
        np.log(1e-8), np.log(0.15), np.log(0.2), -12.0,
        -2.0, -2.0, -5.0,
    ])
    upper = np.array([
        np.log(1e8), np.log(120.0), np.log(8.0), 12.0,
        2.0, 2.0, 5.0,
    ])

    def decode(p: np.ndarray):
        return (
            float(np.exp(p[0])), float(np.exp(p[1])), float(np.exp(p[2])),
            _u_to_q(float(p[3])), xmid + float(p[4]), ymid + float(p[5]),
            float(p[6]) * sigma,
        )

    def residual(p: np.ndarray) -> np.ndarray:
        return ((_convolved_model(image.shape, *decode(p)) - image) / sigma).ravel()

    attempts = []
    for re_mult in START_RE_MULTIPLIER_OF_ESTIMATE:
        for n_start in START_N:
            p0 = np.array([
                np.log(max(initial_flux, 1e-12)),
                np.log(max(initial_re_pix * re_mult, 0.2)),
                np.log(n_start),
                _q_to_u(initial_q),
                0.0, 0.0, 0.0,
            ])
            result = least_squares(
                residual, p0, bounds=(lower, upper), method="trf",
                jac="3-point", x_scale="jac",
                ftol=1e-9, xtol=1e-9, gtol=1e-9, max_nfev=MAX_NFEV,
            )
            attempts.append((float(result.cost), re_mult, n_start, result))

    _, re_mult, n_start, best = min(attempts, key=lambda item: item[0])
    return decode(best.x), best, float(re_mult), float(n_start), lower, upper


def _near_bound(value: float, bound: float, scale: float = 5e-5) -> bool:
    return bool(abs(value - bound) <= scale * max(1.0, abs(bound)))


def main() -> None:
    out = Path("benchmark_output/paulino_afonso_2017/noisy_operational_multistart")
    out.mkdir(parents=True, exist_ok=True)
    sigma = pixel_noise_from_point_depth()
    rows: list[dict[str, object]] = []

    for iz, z0 in enumerate(TARGET_REDSHIFTS):
        z = float(z0)
        kpc_arcsec = _kpc_per_arcsec(z)
        for icase, truth in enumerate(TRUTH_CASES):
            re_arcsec = float(truth["re_kpc"]) / kpc_arcsec
            re_pix = re_arcsec / PIXEL_SCALE_ARCSEC
            stamp_size = adaptive_stamp_size(re_pix)
            center = 0.5 * (stamp_size - 1)
            target_mag = target_mag_from_source_mag(float(truth["source_mag_ab"]), z)
            flux = flux_in_depth_units(target_mag)
            noiseless = _convolved_model(
                (stamp_size, stamp_size), flux, re_pix, float(truth["n"]),
                float(truth["q"]), center, center, 0.0,
            )

            initial_re = re_pix * 1.08
            initial_flux = flux * 0.93
            initial_q = min(0.95, max(0.2, float(truth["q"]) + 0.04))

            for realization in range(REALIZATIONS):
                seed = int(BASE_SEED + iz * 100_000 + icase * 1_000 + realization)
                rng = np.random.default_rng(seed)
                image = noiseless + rng.normal(0.0, sigma, size=noiseless.shape)

                fit, result, best_re_mult, best_n_start, lower, upper = _fit_multistart(
                    image, sigma, initial_re, initial_q, initial_flux,
                )
                rec_flux, rec_re_pix, rec_n, rec_q, x0, y0, sky = fit
                rec_re_kpc = rec_re_pix * PIXEL_SCALE_ARCSEC * kpc_arcsec
                rec_mag = mag_from_depth_units(rec_flux)

                rows.append({
                    "case": str(truth["case"]),
                    "z_source": SOURCE_REDSHIFT,
                    "z_target": z,
                    "realization": realization,
                    "seed": seed,
                    "input_re_kpc": float(truth["re_kpc"]),
                    "input_n": float(truth["n"]),
                    "input_q": float(truth["q"]),
                    "source_mag_ab": float(truth["source_mag_ab"]),
                    "target_mag_ab": target_mag,
                    "target_re_pixels": re_pix,
                    "stamp_size": stamp_size,
                    "psf_fwhm_pixels": PSF_FWHM_ARCSEC / PIXEL_SCALE_ARCSEC,
                    "point_source_depth_ab_5sigma": POINT_DEPTH_AB_5SIGMA,
                    "pixel_noise_sigma_depth_units": sigma,
                    "best_start_re_multiplier_of_estimate": best_re_mult,
                    "best_start_n": best_n_start,
                    "fit_success": bool(result.success),
                    "fit_status": int(result.status),
                    "nfev": int(result.nfev),
                    "fit_cost": float(result.cost),
                    "optimality": float(result.optimality),
                    "hit_re_lower_bound": _near_bound(float(result.x[1]), float(lower[1])),
                    "hit_re_upper_bound": _near_bound(float(result.x[1]), float(upper[1])),
                    "hit_n_lower_bound": _near_bound(float(result.x[2]), float(lower[2])),
                    "hit_n_upper_bound": _near_bound(float(result.x[2]), float(upper[2])),
                    "recovered_re_kpc": float(rec_re_kpc),
                    "recovered_n": float(rec_n),
                    "recovered_q": float(rec_q),
                    "recovered_mag_ab": float(rec_mag),
                    "recovered_sky": float(sky),
                    "centroid_error_pixels": float(np.hypot(x0 - center, y0 - center)),
                    "re_ratio": float(rec_re_kpc / float(truth["re_kpc"])),
                    "n_ratio": float(rec_n / float(truth["n"])),
                    "q_difference": float(rec_q - float(truth["q"])),
                    "mag_difference": float(rec_mag - target_mag),
                })

    with (out / "rows.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summaries: list[dict[str, object]] = []
    for z0 in TARGET_REDSHIFTS:
        z = float(z0)
        for truth in TRUTH_CASES:
            subset = [r for r in rows if r["z_target"] == z and r["case"] == truth["case"]]
            item: dict[str, object] = {
                "case": str(truth["case"]),
                "z_target": z,
                "n_realizations": len(subset),
                "fit_success_fraction": float(np.mean([bool(r["fit_success"]) for r in subset])),
                "any_parameter_bound_fraction": float(np.mean([
                    bool(r["hit_re_lower_bound"] or r["hit_re_upper_bound"] or r["hit_n_lower_bound"] or r["hit_n_upper_bound"])
                    for r in subset
                ])),
            }
            for key in ("re_ratio", "n_ratio", "q_difference", "mag_difference"):
                vals = np.asarray([float(r[key]) for r in subset])
                item[f"{key}_p16"] = float(np.percentile(vals, 16))
                item[f"{key}_median"] = float(np.median(vals))
                item[f"{key}_p84"] = float(np.percentile(vals, 84))
            summaries.append(item)

    with (out / "summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0].keys()))
        writer.writeheader()
        writer.writerows(summaries)

    by_z = []
    for z0 in TARGET_REDSHIFTS:
        z = float(z0)
        subset = [r for r in rows if r["z_target"] == z]
        by_z.append({
            "z_target": z,
            "n_measurements": len(subset),
            "fit_success_fraction": float(np.mean([bool(r["fit_success"]) for r in subset])),
            "median_re_ratio_all_cases": float(np.median([float(r["re_ratio"]) for r in subset])),
            "median_n_ratio_all_cases": float(np.median([float(r["n_ratio"]) for r in subset])),
        })

    payload = {
        "experiment": "controlled noisy C2 floor with truth-independent operational multistart fitter",
        "scientific_status": "diagnostic only; not full Paulino-Afonso reproduction and not a production correction",
        "realizations_per_case_redshift": REALIZATIONS,
        "n_rows": len(rows),
        "jacobian_scheme": "3-point",
        "x_scale": "jac",
        "max_nfev_per_start": MAX_NFEV,
        "start_n": list(START_N),
        "start_re_multiplier_of_estimate": list(START_RE_MULTIPLIER_OF_ESTIMATE),
        "selection_rule": "minimum residual cost only",
        "by_redshift": by_z,
        "next_decision_rule": (
            "Interpret the remaining recovery offsets as the controlled PSF/sampling/white-noise measurement floor only if fit success is adequate and no parameter-bound pathology dominates. Do not compare a three-realization synthetic floor to the published Table-2 medians as if it were a literal reproduction. The next physical C2 step is source-to-target PSF transformation plus source complexity and real-background insertion."
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
