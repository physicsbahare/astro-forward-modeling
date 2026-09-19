#!/usr/bin/env python3
"""Gate C3 Stage 2: add controlled Gaussian noise across Yu et al. resolvedness.

This is a synthetic-equivalent diagnostic, not a literal DESI/CEERS reproduction.
Stage 1 remains the immutable PSF-only/noiseless record.  This script compares
each noisy realization to the PSF-only image at the *same* constructed
R_p,true/FWHM, so noise and resolution effects are not conflated.

Noise is parameterized by a predeclared integrated S/N inside the PSF-only
1.5 R_p elliptical aperture.  No acceptance band is defined.  Low-S/N
Petrosian/radius failures, optimizer failures, and parameter-bound hits are
recorded as observables and are not repaired by changing bounds.

The Yu et al. Eq. (28) asymmetry estimator is evaluated with both the
Wen & Zheng (2016) thresholds (f1=1, f2=sqrt(2)) and Yu et al.'s published
improved values (f1=2.25, f2=2.1).  These values are literature anchors, not
tuned on this synthetic ensemble.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_yu_2023_psf_only_resolvedness import (
    SCENES,
    A_at,
    fit_sersic,
    mask,
    morphology,
    radial,
    render,
)
from verification.yu_2023 import (
    ASYMMETRY_NOISE_F1,
    ASYMMETRY_NOISE_F2,
    TOTAL_LIGHT_APERTURE_RP,
    YU_RESOLUTION_LEVELS,
    asymmetry_noise_corrected_from_terms,
)

APERTURE_SN_LEVELS = (10.0, 30.0, 100.0)
REALIZATIONS = (0, 1, 2)
BASE_SEED = 20230902
WZ16_F1 = 1.0
WZ16_F2 = math.sqrt(2.0)


def first_upward_crossing(x: np.ndarray, y: np.ndarray, target: float, stop_x: float) -> float:
    """Return the first upward crossing of y=target before stop_x."""
    valid = np.flatnonzero(x <= float(stop_x))
    for i in valid[1:]:
        if y[i - 1] < target <= y[i]:
            dy = float(y[i] - y[i - 1])
            if dy == 0:
                return float(x[i])
            f = (target - float(y[i - 1])) / dy
            return float(x[i - 1] + f * (x[i] - x[i - 1]))
    raise RuntimeError("curve-of-growth fraction has no upward crossing")


def noisy_radii(im: np.ndarray, center, q: float, pa: float) -> dict[str, float]:
    """Petrosian/curve-of-growth radii using first crossings for noisy curves.

    Stage-1 history is not changed.  This separate Stage-2 implementation avoids
    assuming that a background-subtracted noisy cumulative curve is strictly
    monotonic, while retaining the same eta=0.2 and 1.5 Rp definitions.
    """
    r, cum, eta = radial(im, center, q, pa)
    rp = None
    for i in range(2, len(r)):
        if (
            np.isfinite(eta[i - 1])
            and np.isfinite(eta[i])
            and eta[i - 1] > 0.20 >= eta[i]
        ):
            d = float(eta[i] - eta[i - 1])
            f = 0.0 if d == 0 else (0.20 - float(eta[i - 1])) / d
            rp = float(r[i - 1] + f * (r[i] - r[i - 1]))
            break
    if rp is None:
        raise RuntimeError("Petrosian crossing not found")

    rtot = TOTAL_LIGHT_APERTURE_RP * rp
    if rtot >= r[-1]:
        raise RuntimeError("1.5 Rp exceeds radial grid")
    total = float(np.interp(rtot, r, cum))
    if not np.isfinite(total) or total <= 0:
        raise RuntimeError("non-positive 1.5 Rp curve-of-growth total")

    r20 = first_upward_crossing(r, cum, 0.20 * total, rtot)
    r50 = first_upward_crossing(r, cum, 0.50 * total, rtot)
    r80 = first_upward_crossing(r, cum, 0.80 * total, rtot)
    if not (0 < r20 <= r50 <= r80 <= rtot):
        raise RuntimeError("nonparametric radii ordering failed")
    return {
        "rp": rp,
        "r20": r20,
        "r50": r50,
        "r80": r80,
        "concentration": float(5.0 * np.log10(r80 / r20)),
    }


def noisy_morphology(im: np.ndarray, reference: dict[str, float]) -> dict[str, float | bool]:
    """Measure noisy non-parametric morphology with PSF-only ellipse geometry.

    q and PA are held to the PSF-only values to isolate target-noise effects
    from a separate noisy moment/shape estimator.  The asymmetry center is still
    re-minimized on each noisy realization, as required by the paper.
    """
    q = float(reference["moment_q"])
    pa = float(reference["moment_pa"])
    x0 = float(reference["center_x"])
    y0 = float(reference["center_y"])

    pre = noisy_radii(im, (x0, y0), q, pa)
    o1 = minimize(
        lambda c: A_at(im, (float(c[0]), float(c[1])), q, pa, pre["rp"]),
        [x0, y0],
        method="Powell",
        bounds=[(x0 - 1.5, x0 + 1.5), (y0 - 1.5, y0 + 1.5)],
        options={"xtol": 1e-4, "ftol": 1e-10, "maxiter": 80},
    )
    x1, y1 = map(float, o1.x)
    rr = noisy_radii(im, (x1, y1), q, pa)
    o2 = minimize(
        lambda c: A_at(im, (float(c[0]), float(c[1])), q, pa, rr["rp"]),
        [x1, y1],
        method="Powell",
        bounds=[(x1 - 0.75, x1 + 0.75), (y1 - 0.75, y1 + 0.75)],
        options={"xtol": 1e-4, "ftol": 1e-10, "maxiter": 60},
    )
    x2, y2 = map(float, o2.x)
    rr = noisy_radii(im, (x2, y2), q, pa)
    return {
        **rr,
        "asymmetry": A_at(im, (x2, y2), q, pa, rr["rp"]),
        "center_x": x2,
        "center_y": y2,
        "moment_q": q,
        "moment_pa": pa,
        "asymmetry_min_success": bool(o1.success and o2.success),
    }


def rotate_180(im: np.ndarray, center) -> np.ndarray:
    yy, xx = np.indices(im.shape, dtype=float)
    x0, y0 = map(float, center)
    return map_coordinates(
        im,
        [2.0 * y0 - yy, 2.0 * x0 - xx],
        order=1,
        mode="constant",
        cval=0.0,
        prefilter=False,
    )


def residual_sum(im: np.ndarray, center, q: float, pa: float, rp: float) -> float:
    rot = rotate_180(im, center)
    m = mask(im.shape, center, q, pa, TOTAL_LIGHT_APERTURE_RP * rp)
    return float(np.abs(im[m] - rot[m]).sum())


def minimize_residual_sum(
    im: np.ndarray,
    start_center,
    q: float,
    pa: float,
    rp: float,
    half_width: float,
):
    x0, y0 = map(float, start_center)
    o = minimize(
        lambda c: residual_sum(im, (float(c[0]), float(c[1])), q, pa, rp),
        [x0, y0],
        method="Powell",
        bounds=[(x0 - half_width, x0 + half_width), (y0 - half_width, y0 + half_width)],
        options={"xtol": 1e-4, "ftol": 1e-10, "maxiter": 80},
    )
    center = tuple(map(float, o.x))
    return center, float(o.fun), bool(o.success)


def equation28_from_images(
    noisy: np.ndarray,
    background: np.ndarray,
    center,
    q: float,
    pa: float,
    rp: float,
    sigma_bkg: float,
    f1_threshold: float,
    f2_threshold: float,
) -> dict[str, float | bool]:
    """Evaluate Yu et al. Eq. (28) on one noisy image/background pair."""
    gcenter, gnum, gok = minimize_residual_sum(noisy, center, q, pa, rp, 0.75)
    b0 = ((background.shape[1] - 1) / 2.0, (background.shape[0] - 1) / 2.0)
    bcenter, bnum, bok = minimize_residual_sum(background, b0, q, pa, rp, 1.5)

    gm = mask(noisy.shape, gcenter, q, pa, TOTAL_LIGHT_APERTURE_RP * rp)
    bm = mask(background.shape, bcenter, q, pa, TOTAL_LIGHT_APERTURE_RP * rp)
    grot = rotate_180(noisy, gcenter)

    gden = float(np.abs(noisy[gm]).sum())
    bden = float(np.abs(background[bm]).sum())
    nall = int(np.count_nonzero(gm))
    if nall <= 0:
        raise RuntimeError("empty Eq. 28 aperture")

    F1 = float(np.count_nonzero(noisy[gm] < f1_threshold * sigma_bkg) / nall)
    F2 = float(
        np.count_nonzero(np.abs(noisy[gm] - grot[gm]) < f2_threshold * sigma_bkg)
        / nall
    )
    try:
        aval = asymmetry_noise_corrected_from_terms(gnum, bnum, gden, bden, F1, F2)
        valid = True
    except ValueError:
        aval = float("nan")
        valid = False

    return {
        "asymmetry_corrected": float(aval),
        "F1_noise_fraction": F1,
        "F2_noise_fraction": F2,
        "galaxy_residual_min": gnum,
        "background_residual_min": bnum,
        "galaxy_abs_flux_sum": gden,
        "background_abs_flux_sum": bden,
        "galaxy_min_success": gok,
        "background_min_success": bok,
        "correction_denominator_positive": valid,
    }


def nan_fit_row() -> dict[str, float | bool]:
    return {
        "success": False,
        "cost": float("nan"),
        "re_pix": float("nan"),
        "n": float("nan"),
        "q": float("nan"),
        "hit_re_lower_bound": False,
        "hit_re_upper_bound": False,
        "hit_n_lower_bound": False,
        "hit_n_upper_bound": False,
        "hit_q_lower_bound": False,
        "hit_q_upper_bound": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aperture-snr", type=float, required=True, choices=list(APERTURE_SN_LEVELS))
    args = parser.parse_args()
    snr_target = float(args.aperture_snr)

    out = Path("benchmark_output/yu_2023/noisy_resolvedness") / f"snr_{int(snr_target)}"
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    fit_starts = []

    for si, scene in enumerate(SCENES):
        intrinsic = render(scene, 0.0)
        truth = morphology(intrinsic)
        for ri, resolvedness in enumerate(YU_RESOLUTION_LEVELS):
            fwhm = float(truth["rp"]) / float(resolvedness)
            psf_only = render(scene, fwhm)
            psf_morph = morphology(psf_only)
            psf_fit, psf_starts = fit_sersic(
                psf_only,
                fwhm,
                (psf_morph["center_x"], psf_morph["center_y"]),
                psf_morph["moment_pa"],
                psf_morph["moment_q"],
                psf_morph["r50"],
            )
            fit_starts += [
                {
                    "stage": "psf_only_reference",
                    "aperture_snr_target": snr_target,
                    "scene": scene["scene"],
                    "resolvedness": float(resolvedness),
                    "realization": -1,
                    **s,
                }
                for s in psf_starts
            ]

            reference_mask = mask(
                psf_only.shape,
                (psf_morph["center_x"], psf_morph["center_y"]),
                psf_morph["moment_q"],
                psf_morph["moment_pa"],
                TOTAL_LIGHT_APERTURE_RP * psf_morph["rp"],
            )
            npix_ref = int(np.count_nonzero(reference_mask))
            signal_ref = float(psf_only[reference_mask].sum())
            sigma_bkg = signal_ref / (snr_target * math.sqrt(npix_ref))

            for realization in REALIZATIONS:
                seed = (
                    BASE_SEED
                    + int(snr_target) * 10000
                    + si * 1000
                    + ri * 10
                    + int(realization)
                )
                rng = np.random.default_rng(seed)
                noisy = psf_only + rng.normal(0.0, sigma_bkg, size=psf_only.shape)
                background = rng.normal(0.0, sigma_bkg, size=psf_only.shape)

                measurement_error = ""
                try:
                    nm = noisy_morphology(noisy, psf_morph)
                    morphology_success = True
                except Exception as exc:
                    nm = {
                        "rp": float("nan"),
                        "r20": float("nan"),
                        "r50": float("nan"),
                        "r80": float("nan"),
                        "concentration": float("nan"),
                        "asymmetry": float("nan"),
                        "center_x": float("nan"),
                        "center_y": float("nan"),
                        "moment_q": float(psf_morph["moment_q"]),
                        "moment_pa": float(psf_morph["moment_pa"]),
                        "asymmetry_min_success": False,
                    }
                    morphology_success = False
                    measurement_error = f"{type(exc).__name__}: {exc}"

                wz = {
                    "asymmetry_corrected": float("nan"),
                    "F1_noise_fraction": float("nan"),
                    "F2_noise_fraction": float("nan"),
                    "correction_denominator_positive": False,
                    "galaxy_min_success": False,
                    "background_min_success": False,
                }
                improved = dict(wz)
                if morphology_success:
                    wz = equation28_from_images(
                        noisy,
                        background,
                        (nm["center_x"], nm["center_y"]),
                        float(nm["moment_q"]),
                        float(nm["moment_pa"]),
                        float(nm["rp"]),
                        sigma_bkg,
                        WZ16_F1,
                        WZ16_F2,
                    )
                    improved = equation28_from_images(
                        noisy,
                        background,
                        (nm["center_x"], nm["center_y"]),
                        float(nm["moment_q"]),
                        float(nm["moment_pa"]),
                        float(nm["rp"]),
                        sigma_bkg,
                        ASYMMETRY_NOISE_F1,
                        ASYMMETRY_NOISE_F2,
                    )

                nf = nan_fit_row()
                if morphology_success:
                    try:
                        nf, starts = fit_sersic(
                            noisy,
                            fwhm,
                            (nm["center_x"], nm["center_y"]),
                            float(psf_morph["moment_pa"]),
                            float(psf_morph["moment_q"]),
                            float(nm["r50"]),
                        )
                        fit_starts += [
                            {
                                "stage": "noisy",
                                "aperture_snr_target": snr_target,
                                "scene": scene["scene"],
                                "resolvedness": float(resolvedness),
                                "realization": int(realization),
                                **s,
                            }
                            for s in starts
                        ]
                    except Exception as exc:
                        if measurement_error:
                            measurement_error += " | "
                        measurement_error += f"fit {type(exc).__name__}: {exc}"

                def diff(value, ref):
                    return float(value - ref) if np.isfinite(value) else float("nan")

                rows.append(
                    {
                        "scene": scene["scene"],
                        "scene_kind": scene["kind"],
                        "rp_true_over_fwhm_requested": float(resolvedness),
                        "rp_true_over_fwhm_constructed": float(truth["rp"]) / fwhm,
                        "psf_fwhm_pix": fwhm,
                        "aperture_snr_target": snr_target,
                        "realization": int(realization),
                        "seed": int(seed),
                        "reference_aperture_npix": npix_ref,
                        "reference_aperture_signal": signal_ref,
                        "sigma_bkg": sigma_bkg,
                        "morphology_success": morphology_success,
                        "measurement_error": measurement_error,
                        "rp_psf_only": psf_morph["rp"],
                        "rp_noisy": nm["rp"],
                        "rp_noise_delta": diff(nm["rp"], psf_morph["rp"]),
                        "r50_psf_only": psf_morph["r50"],
                        "r50_noisy": nm["r50"],
                        "r50_noise_delta": diff(nm["r50"], psf_morph["r50"]),
                        "concentration_psf_only": psf_morph["concentration"],
                        "concentration_noisy": nm["concentration"],
                        "concentration_noise_delta": diff(
                            nm["concentration"], psf_morph["concentration"]
                        ),
                        "asymmetry_psf_only": psf_morph["asymmetry"],
                        "asymmetry_noisy_raw": nm["asymmetry"],
                        "asymmetry_raw_noise_delta": diff(
                            nm["asymmetry"], psf_morph["asymmetry"]
                        ),
                        "asymmetry_wz16": wz["asymmetry_corrected"],
                        "asymmetry_wz16_noise_delta": diff(
                            wz["asymmetry_corrected"], psf_morph["asymmetry"]
                        ),
                        "asymmetry_improved": improved["asymmetry_corrected"],
                        "asymmetry_improved_noise_delta": diff(
                            improved["asymmetry_corrected"], psf_morph["asymmetry"]
                        ),
                        "wz16_F1_noise_fraction": wz["F1_noise_fraction"],
                        "wz16_F2_noise_fraction": wz["F2_noise_fraction"],
                        "improved_F1_noise_fraction": improved["F1_noise_fraction"],
                        "improved_F2_noise_fraction": improved["F2_noise_fraction"],
                        "wz16_correction_denominator_positive": wz[
                            "correction_denominator_positive"
                        ],
                        "improved_correction_denominator_positive": improved[
                            "correction_denominator_positive"
                        ],
                        "eq28_galaxy_min_success": improved["galaxy_min_success"],
                        "eq28_background_min_success": improved["background_min_success"],
                        "fit_re_psf_only": psf_fit["re_pix"],
                        "fit_re_noisy": nf["re_pix"],
                        "fit_re_noise_ratio": (
                            float(nf["re_pix"] / psf_fit["re_pix"])
                            if np.isfinite(nf["re_pix"])
                            else float("nan")
                        ),
                        "fit_n_psf_only": psf_fit["n"],
                        "fit_n_noisy": nf["n"],
                        "fit_delta_n_noise": diff(nf["n"], psf_fit["n"]),
                        "fit_q_psf_only": psf_fit["q"],
                        "fit_q_noisy": nf["q"],
                        "fit_delta_q_noise": diff(nf["q"], psf_fit["q"]),
                        "fit_success": bool(nf["success"]),
                        "fit_cost": nf["cost"],
                        "fit_hit_re_lower_bound": bool(nf["hit_re_lower_bound"]),
                        "fit_hit_re_upper_bound": bool(nf["hit_re_upper_bound"]),
                        "fit_hit_n_lower_bound": bool(nf["hit_n_lower_bound"]),
                        "fit_hit_n_upper_bound": bool(nf["hit_n_upper_bound"]),
                        "fit_hit_q_lower_bound": bool(nf["hit_q_lower_bound"]),
                        "fit_hit_q_upper_bound": bool(nf["hit_q_upper_bound"]),
                    }
                )

    expected = len(SCENES) * len(YU_RESOLUTION_LEVELS) * len(REALIZATIONS)
    if len(rows) != expected:
        raise RuntimeError(f"incomplete noisy matrix: {len(rows)} != {expected}")

    with (out / "metrics.csv").open("w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with (out / "fit_starts.csv").open("w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=list(fit_starts[0].keys()))
        w.writeheader()
        w.writerows(fit_starts)

    finite_improved = [
        r["asymmetry_improved_noise_delta"]
        for r in rows
        if np.isfinite(r["asymmetry_improved_noise_delta"])
    ]
    finite_raw = [
        r["asymmetry_raw_noise_delta"]
        for r in rows
        if np.isfinite(r["asymmetry_raw_noise_delta"])
    ]
    summary = {
        "experiment": "Yu et al. 2023 Gate C Stage 2 controlled target-noise x resolvedness",
        "scientific_status": (
            "synthetic-equivalent; PSF-only Stage 1 preserved; no production criterion; "
            "not literal CEERS depth"
        ),
        "aperture_snr_definition": (
            "integrated PSF-only signal divided by sigma_bkg*sqrt(Npix) inside "
            "the PSF-only 1.5 Rp ellipse"
        ),
        "aperture_snr_target": snr_target,
        "declared_aperture_snr_levels": list(APERTURE_SN_LEVELS),
        "realizations": list(REALIZATIONS),
        "base_seed": BASE_SEED,
        "resolution_levels": list(YU_RESOLUTION_LEVELS),
        "matrix_rows": len(rows),
        "noise_model": "independent zero-mean Gaussian source/background fields",
        "nonparametric_geometry": (
            "PSF-only q and PA held fixed; asymmetry center re-minimized in every noisy realization"
        ),
        "curve_of_growth_noise_rule": (
            "first upward crossings are used because noisy background-subtracted cumulative "
            "curves need not be monotonic; Stage-1 noiseless implementation is unchanged"
        ),
        "asymmetry_noise_correction": {
            "equation": "Yu et al. 2023 Eq. (28)",
            "wen_zheng_2016": {"f1": WZ16_F1, "f2": WZ16_F2},
            "yu_improved": {"f1": ASYMMETRY_NOISE_F1, "f2": ASYMMETRY_NOISE_F2},
        },
        "counts": {
            "morphology_success": int(sum(bool(r["morphology_success"]) for r in rows)),
            "fit_success": int(sum(bool(r["fit_success"]) for r in rows)),
            "improved_asymmetry_valid": int(
                sum(bool(r["improved_correction_denominator_positive"]) for r in rows)
            ),
            "n_bound_hits": int(
                sum(
                    bool(r["fit_hit_n_lower_bound"] or r["fit_hit_n_upper_bound"])
                    for r in rows
                )
            ),
            "q_bound_hits": int(
                sum(
                    bool(r["fit_hit_q_lower_bound"] or r["fit_hit_q_upper_bound"])
                    for r in rows
                )
            ),
        },
        "descriptive_only": {
            "median_raw_asymmetry_noise_delta": (
                float(np.median(finite_raw)) if finite_raw else None
            ),
            "median_improved_asymmetry_noise_delta": (
                float(np.median(finite_improved)) if finite_improved else None
            ),
        },
        "interpretation_rule": (
            "Do not tune noise levels, bounds, scenes, or correction factors after seeing results. "
            "Failures and bound hits are retained as observables. Compare noisy quantities to the "
            "PSF-only reference at identical resolvedness before combining effects."
        ),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
