#!/usr/bin/env python3
"""Recover morphology from physically degraded CALIFA-like C2 images.

This stage follows the successful full artificial-redshifting chain assembly.
It asks the first morphology-level question on those images: after source pixel
integration, source PSF, angular resampling, positive target-PSF matching and
radiometric dimming/evolution have been applied, how much do recovered single-
Sersic parameters move even before stochastic target noise is added?

The fit uses the previously validated operational strategy: fixed generic
Sersic-n starts, Re starts expressed relative to the supplied perturbed input
estimate, a 3-point finite-difference Jacobian, x_scale='jac', and selection by
minimum residual cost only.  No start is selected using closeness to truth or
the Paulino-Afonso literature values, and no scientific tolerance is changed.

This remains a controlled synthetic-equivalent diagnostic, not a literal
reproduction of the original CALIFA galaxy images or GALFIT configuration.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

from scripts.run_paulino_afonso_full_chain_califa import CASES, TARGET_Z, transfer_to_target
from verification.paulino_afonso_sersic_floor import (
    PIXEL_SCALE_ARCSEC,
    _convolved_model,
    _kpc_per_arcsec,
    adaptive_stamp_size,
    flux_in_depth_units,
    mag_from_depth_units,
    pixel_noise_from_point_depth,
)

START_N = (1.0, 2.5, 5.5, 7.0)
START_RE_MULTIPLIER_OF_ESTIMATE = (0.8, 1.2)
INITIAL_RE_MULTIPLIER = 1.08
INITIAL_FLUX_MULTIPLIER = 0.93
INITIAL_Q_OFFSET = 0.04
MAX_NFEV = 1800


def _q_to_u(q: float) -> float:
    qmin, qmax = 0.15, 1.0
    t = np.clip((q - qmin) / (qmax - qmin), 1e-8, 1 - 1e-8)
    return float(np.log(t / (1 - t)))


def _u_to_q(u: float) -> float:
    qmin, qmax = 0.15, 1.0
    t = 1.0 / (1.0 + np.exp(-u))
    return float(qmin + (qmax - qmin) * t)


def _central_crop(image: np.ndarray, size: int) -> np.ndarray:
    size = min(size, image.shape[0], image.shape[1])
    if size % 2 == 0:
        size -= 1
    y0 = (image.shape[0] - size) // 2
    x0 = (image.shape[1] - size) // 2
    return np.asarray(image[y0:y0 + size, x0:x0 + size], dtype=float)


def main() -> None:
    out = Path("benchmark_output/paulino_afonso_2017/full_chain_morphology_recovery")
    out.mkdir(parents=True, exist_ok=True)
    sigma = pixel_noise_from_point_depth()
    all_rows: list[dict[str, object]] = []
    best_rows: list[dict[str, object]] = []

    for z0 in TARGET_Z:
        z = float(z0)
        kpc_arcsec = _kpc_per_arcsec(z)
        for case in CASES:
            source_flux = flux_in_depth_units(float(case["source_mag_ab"]))
            transferred, _, _, _, source_equiv, kernel_fwhm, flux_ratio = transfer_to_target(
                case, z, source_flux
            )
            true_re_pix = float(case["re_kpc"]) / kpc_arcsec / PIXEL_SCALE_ARCSEC
            fit_size = adaptive_stamp_size(true_re_pix)
            image = _central_crop(transferred, fit_size)
            ny, nx = image.shape
            center_x = 0.5 * (nx - 1)
            center_y = 0.5 * (ny - 1)
            true_flux_in_fit = float(np.sum(image))

            initial_re_estimate = true_re_pix * INITIAL_RE_MULTIPLIER
            initial_flux_estimate = true_flux_in_fit * INITIAL_FLUX_MULTIPLIER
            initial_q_estimate = min(0.95, max(0.2, float(case["q"]) + INITIAL_Q_OFFSET))

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
                    _u_to_q(float(p[3])), center_x + float(p[4]), center_y + float(p[5]),
                    float(p[6]) * sigma,
                )

            def residual(p: np.ndarray) -> np.ndarray:
                return ((_convolved_model(image.shape, *decode(p)) - image) / sigma).ravel()

            starts: list[dict[str, object]] = []
            for re_mult in START_RE_MULTIPLIER_OF_ESTIMATE:
                for n_start in START_N:
                    p0 = np.array([
                        np.log(max(initial_flux_estimate, 1e-12)),
                        np.log(max(initial_re_estimate * re_mult, 0.2)),
                        np.log(n_start),
                        _q_to_u(initial_q_estimate),
                        0.0, 0.0, 0.0,
                    ])
                    result = least_squares(
                        residual, p0, bounds=(lower, upper), method="trf",
                        jac="3-point", x_scale="jac", ftol=1e-9, xtol=1e-9,
                        gtol=1e-9, max_nfev=MAX_NFEV,
                    )
                    rec_flux, rec_re, rec_n, rec_q, rec_x, rec_y, rec_sky = decode(result.x)
                    row = {
                        "case": str(case["case"]),
                        "z_source": 0.015,
                        "z_target": z,
                        "input_re_kpc": float(case["re_kpc"]),
                        "input_n": float(case["n"]),
                        "input_q": float(case["q"]),
                        "source_mag_ab": float(case["source_mag_ab"]),
                        "fit_stamp_size": int(image.shape[0]),
                        "source_psf_equivalent_at_target_arcsec": float(source_equiv),
                        "matching_kernel_fwhm_arcsec": float(kernel_fwhm),
                        "flux_ratio_source_to_target": float(flux_ratio),
                        "start_re_multiplier_of_estimate": float(re_mult),
                        "start_n": float(n_start),
                        "success": bool(result.success),
                        "status": int(result.status),
                        "nfev": int(result.nfev),
                        "cost": float(result.cost),
                        "optimality": float(result.optimality),
                        "recovered_re_kpc": float(rec_re * PIXEL_SCALE_ARCSEC * kpc_arcsec),
                        "re_ratio": float(rec_re / true_re_pix),
                        "recovered_n": float(rec_n),
                        "n_ratio": float(rec_n / float(case["n"])),
                        "recovered_q": float(rec_q),
                        "q_difference": float(rec_q - float(case["q"])),
                        "recovered_flux_in_fit": float(rec_flux),
                        "flux_ratio_to_transferred_fit_flux": float(rec_flux / true_flux_in_fit),
                        "recovered_mag_from_fit_flux": float(mag_from_depth_units(rec_flux)),
                        "centroid_error_pixels": float(np.hypot(rec_x - center_x, rec_y - center_y)),
                        "sky_sigma_units": float(rec_sky / sigma),
                        "hit_re_lower_bound": bool(rec_re <= 0.15 * (1 + 5e-5)),
                        "hit_re_upper_bound": bool(rec_re >= 120.0 * (1 - 5e-5)),
                        "hit_n_lower_bound": bool(rec_n <= 0.2 * (1 + 5e-5)),
                        "hit_n_upper_bound": bool(rec_n >= 8.0 * (1 - 5e-5)),
                    }
                    all_rows.append(row)
                    starts.append(row)
            best_rows.append(min(starts, key=lambda r: float(r["cost"])))

    with (out / "all_starts.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0].keys()))
        writer.writeheader(); writer.writerows(all_rows)
    with (out / "best_rows.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(best_rows[0].keys()))
        writer.writeheader(); writer.writerows(best_rows)

    def any_bound(r: dict[str, object]) -> bool:
        return bool(r["hit_re_lower_bound"] or r["hit_re_upper_bound"] or r["hit_n_lower_bound"] or r["hit_n_upper_bound"])

    by_redshift = []
    for z0 in TARGET_Z:
        subset = [r for r in best_rows if float(r["z_target"]) == float(z0)]
        by_redshift.append({
            "z_target": float(z0),
            "n_cases": len(subset),
            "fit_success_fraction": float(np.mean([bool(r["success"]) for r in subset])),
            "any_re_or_n_bound_fraction": float(np.mean([any_bound(r) for r in subset])),
            "median_re_ratio": float(np.median([float(r["re_ratio"]) for r in subset])),
            "median_n_ratio": float(np.median([float(r["n_ratio"]) for r in subset])),
            "median_q_difference": float(np.median([float(r["q_difference"]) for r in subset])),
        })

    payload = {
        "experiment": "CALIFA full-chain noiseless morphology recovery",
        "scientific_status": "controlled synthetic-equivalent diagnostic; not literal survey reproduction",
        "n_cases": len(best_rows),
        "n_starts_per_case": len(START_N) * len(START_RE_MULTIPLIER_OF_ESTIMATE),
        "jacobian_scheme": "3-point",
        "x_scale": "jac",
        "max_nfev": MAX_NFEV,
        "selection_rule": "lowest residual cost only; never closeness to truth or literature",
        "noise_stage": "no target noise in this stage; isolates transfer-induced morphology bias",
        "by_redshift": by_redshift,
        "best_rows": best_rows,
        "next_decision_rule": (
            "Treat recovered offsets and bound hits as observables of the assembled degradation operator. "
            "Do not tune them toward Paulino-Afonso Table 2. If fits are numerically stable, add the declared "
            "target-noise ensemble on the same transferred images next; otherwise diagnose the failing cases first."
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
