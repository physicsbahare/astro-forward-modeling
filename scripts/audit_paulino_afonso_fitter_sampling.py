#!/usr/bin/env python3
"""Audit detector-pixel integration in the Paulino-Afonso C2 fitter renderer.

This is a diagnostic only. It does not replace or retune the established C2
benchmarks. The current operational fitter evaluates a Sersic profile at
coarse detector-pixel centres before PSF convolution, while the full-chain
source/target truth renderers use detector-pixel integration via supersampling.
This script isolates that rendering choice by comparing the existing
point-sampled PSF-convolved model with a 4x pixel-integrated version at identical
physical/model parameters.

No pass/fail morphology tolerance is introduced. The output is intended to
show where detector sampling is negligible and where it can become part of the
model-mismatch floor, especially for compact/high-n structure.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

from verification.paulino_afonso_sersic_floor import (
    _bn,
    _convolved_model,
    _psf_sigma_pix,
    _sersic_total_normalization,
)

OUT = Path("benchmark_output/paulino_afonso_2017/fitter_sampling_audit")
SHAPE = (129, 129)
TOTAL_FLUX = 1.0
OVERSAMPLE = 4
RE_PIX = (0.5, 1.0, 2.0, 5.0, 10.0, 20.0)
N_VALUES = (1.0, 2.0, 4.0, 8.0)
Q_VALUES = (0.65, 0.90)
OFFSETS = ((0.0, 0.0), (0.37, -0.29))
PA_RAD = 0.37


def pixel_integrated_convolved_model(
    shape: tuple[int, int],
    total_flux: float,
    re_pix: float,
    n: float,
    q: float,
    x0: float,
    y0: float,
    sky: float = 0.0,
    oversample: int = OVERSAMPLE,
) -> np.ndarray:
    """Render a Sersic model integrated over detector pixels before binning."""
    ny, nx = shape
    f = int(oversample)
    xf = (np.arange(nx * f, dtype=float) + 0.5) / f - 0.5
    yf = (np.arange(ny * f, dtype=float) + 0.5) / f - 0.5
    yy, xx = np.meshgrid(yf, xf, indexing="ij")

    dx = xx - float(x0)
    dy = yy - float(y0)
    c = np.cos(PA_RAD)
    s = np.sin(PA_RAD)
    xp = c * dx + s * dy
    yp = -s * dx + c * dy
    r = np.sqrt(xp**2 + (yp / float(q)) ** 2)

    b = _bn(float(n))
    ie = float(total_flux) / _sersic_total_normalization(float(re_pix), float(n), float(q))
    fine = ie * np.exp(-b * ((r / float(re_pix)) ** (1.0 / float(n)) - 1.0)) / (f * f)

    fine = gaussian_filter(
        fine,
        _psf_sigma_pix() * f,
        mode="constant",
        cval=0.0,
        truncate=7.0,
    )
    coarse = fine.reshape(ny, f, nx, f).sum(axis=(1, 3))
    return coarse + float(sky)


def moments(image: np.ndarray) -> tuple[float, float, float]:
    image = np.asarray(image, dtype=float)
    flux = float(np.sum(image))
    if not np.isfinite(flux) or flux <= 0:
        return float("nan"), float("nan"), float("nan")
    y, x = np.indices(image.shape, dtype=float)
    cx = float(np.sum(image * x) / flux)
    cy = float(np.sum(image * y) / flux)
    trace = float(np.sum(image * ((x - cx) ** 2 + (y - cy) ** 2)) / flux)
    return cx, cy, trace


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ny, nx = SHAPE
    cx = 0.5 * (nx - 1)
    cy = 0.5 * (ny - 1)
    rows: list[dict[str, object]] = []

    for re_pix in RE_PIX:
        for n in N_VALUES:
            for q in Q_VALUES:
                for dx, dy in OFFSETS:
                    x0 = cx + dx
                    y0 = cy + dy
                    point = _convolved_model(
                        SHAPE, TOTAL_FLUX, re_pix, n, q, x0, y0, 0.0
                    )
                    integ = pixel_integrated_convolved_model(
                        SHAPE, TOTAL_FLUX, re_pix, n, q, x0, y0, 0.0
                    )

                    sum_p = float(np.sum(point))
                    sum_i = float(np.sum(integ))
                    denom = max(float(np.sum(np.abs(integ))), 1e-300)
                    l1 = float(np.sum(np.abs(point - integ)) / denom)
                    flux_rel = float((sum_p - sum_i) / max(abs(sum_i), 1e-300))
                    peak_rel = float(
                        np.max(np.abs(point - integ)) / max(float(np.max(np.abs(integ))), 1e-300)
                    )
                    cpx, cpy, trp = moments(point)
                    cix, ciy, tri = moments(integ)
                    cent = float(np.hypot(cpx - cix, cpy - ciy))
                    trace_rel = float((trp - tri) / max(abs(tri), 1e-300))

                    rows.append(
                        {
                            "re_pix": float(re_pix),
                            "n": float(n),
                            "q": float(q),
                            "x_offset_pix": float(dx),
                            "y_offset_pix": float(dy),
                            "point_sampled_flux": sum_p,
                            "pixel_integrated_flux": sum_i,
                            "point_minus_integrated_flux_relative": flux_rel,
                            "normalized_l1_point_vs_integrated": l1,
                            "max_pixel_difference_over_integrated_peak": peak_rel,
                            "centroid_difference_pix": cent,
                            "second_moment_trace_relative_difference": trace_rel,
                        }
                    )

    with (OUT / "rows.csv").open("w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    def subset(predicate):
        s = [r for r in rows if predicate(r)]
        return {
            "n_rows": len(s),
            "median_normalized_l1": float(np.median([r["normalized_l1_point_vs_integrated"] for r in s])),
            "max_normalized_l1": float(np.max([r["normalized_l1_point_vs_integrated"] for r in s])),
            "median_abs_flux_relative_difference": float(
                np.median([abs(r["point_minus_integrated_flux_relative"]) for r in s])
            ),
            "max_abs_flux_relative_difference": float(
                np.max([abs(r["point_minus_integrated_flux_relative"]) for r in s])
            ),
            "max_centroid_difference_pix": float(np.max([r["centroid_difference_pix"] for r in s])),
            "max_abs_second_moment_trace_relative_difference": float(
                np.max([abs(r["second_moment_trace_relative_difference"]) for r in s])
            ),
        }

    payload = {
        "experiment": "Paulino-Afonso C2 fitter detector-sampling audit",
        "scientific_status": "diagnostic only; no production tolerance and no retroactive benchmark retuning",
        "existing_renderer": "coarse detector-pixel centre sampling, then target Gaussian PSF convolution",
        "comparison_renderer": f"{OVERSAMPLE}x detector-pixel integration, target Gaussian PSF on fine grid, then block sum",
        "shape": list(SHAPE),
        "psf_sigma_pixels": float(_psf_sigma_pix()),
        "grid": {
            "re_pix": list(RE_PIX),
            "n": list(N_VALUES),
            "q": list(Q_VALUES),
            "offsets_pix": [list(x) for x in OFFSETS],
        },
        "n_rows": len(rows),
        "all_cases": subset(lambda r: True),
        "resolved_disk_like": subset(lambda r: r["re_pix"] >= 5.0 and r["n"] <= 2.0),
        "compact_high_n": subset(lambda r: r["re_pix"] <= 2.0 and r["n"] >= 4.0),
        "decision_rule": (
            "Use the observed discrepancy scale to decide whether a separate pixel-integrated fitter comparison is required. "
            "Do not alter the established structural/noisy benchmark outputs, parameter bounds, optimizer tolerances, or "
            "literature anchors in response to this audit."
        ),
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
