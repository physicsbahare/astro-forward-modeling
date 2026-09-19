#!/usr/bin/env python3
"""Run the standalone pre-implementation numerical verification suite.

This suite is intentionally independent of the future production package. It
exists to establish numerical behavior and acceptance criteria before production
implementation begins.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from verification import chromatic, noise, psf, radiometry, resampling, spectral_support

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"


def write_json(name: str, payload) -> None:
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_csv(name: str, rows: list[dict]) -> None:
    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / name
    if not rows:
        path.write_text("")
        return
    keys = list(rows[0].keys())
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def plot_radiometry(rows: list[dict]) -> None:
    FIGURES.mkdir(exist_ok=True)
    n = np.array([r["grid_points"] for r in rows])
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for key, label in [
        ("fnu_bolometric_relative_error", r"$F_\nu$ bolometric"),
        ("flambda_bolometric_relative_error", r"$F_\lambda$ bolometric"),
        ("photon_rate_relative_disagreement", "photon-rate representation"),
        ("tolman_relative_error", "Tolman integral"),
    ]:
        y = np.maximum([r[key] for r in rows], np.finfo(float).tiny)
        ax.loglog(n, y, marker="o", label=label)
    ax.set_xlabel("Spectral grid points")
    ax.set_ylabel("Relative error")
    ax.set_title("Radiometry convergence")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES / "radiometry_convergence.png", dpi=180)
    plt.close(fig)


def plot_psf(rows: list[dict]) -> None:
    FIGURES.mkdir(exist_ok=True)
    selected = [
        r for r in rows
        if r["method"] == "wiener_scalar_tikhonov"
        and r["shape"] == 101
        and r["sigma_source_pix"] == 2.5
        and r["sigma_target_pix"] == 5.0
    ]
    regs = np.array([r["regularization"] for r in selected])
    D = np.array([r["l1_reconstruction_error_D"] for r in selected])
    W = np.array([r["negative_kernel_weight_Wminus"] for r in selected])
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.loglog(regs, D, marker="o", label="L1 PSF reconstruction error D")
    ax.loglog(regs, np.maximum(W, 1e-18), marker="s", label=r"negative weight $W_-$")
    ax.set_xlabel("Wiener regularization")
    ax.set_ylabel("Metric")
    ax.set_title("PSF matching trade-off: Gaussian reference")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES / "psf_wiener_tradeoff.png", dpi=180)
    plt.close(fig)


def plot_resampling(rows: list[dict]) -> None:
    FIGURES.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    x = np.array([r["output_to_input_pixel_width"] for r in rows])
    y = np.array([r["l1_image_error"] for r in rows])
    ax.scatter(x, y, s=13, alpha=0.6)
    ax.set_yscale("log")
    ax.set_xlabel("Output pixel width / input pixel width")
    ax.set_ylabel("L1 image error vs continuous truth")
    ax.set_title("Already-pixelized image transfer: discretization limits")
    fig.tight_layout()
    fig.savefig(FIGURES / "resampling_discretization.png", dpi=180)
    plt.close(fig)


def plot_chromatic(rows: list[dict]) -> None:
    FIGURES.mkdir(exist_ok=True)
    n = np.array([r["wavelength_samples"] for r in rows])
    y = np.array([r["l1_normalized_image_difference"] for r in rows])
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.semilogx(n, y, marker="o")
    ax.set_xlabel("Wavelength samples")
    ax.set_ylabel("L1 difference: chromatic truth vs one global PSF")
    ax.set_title("Chromatic PSF effect converges to a real modeling difference")
    fig.tight_layout()
    fig.savefig(FIGURES / "chromatic_psf_difference.png", dpi=180)
    plt.close(fig)


def main() -> None:
    rad_rows = radiometry.convergence_table()
    psf_rows = psf.convergence_table()
    res_rows = resampling.convergence_table()
    res_density_rows = resampling.sampling_density_table()
    chr_rows = chromatic.convergence_table()
    noise_result = noise.run_noise_check().to_dict()
    spectral_result = spectral_support.run_spectral_support_check().to_dict()

    write_csv("radiometry_convergence.csv", rad_rows)
    write_csv("psf_convergence.csv", psf_rows)
    write_csv("resampling_convergence.csv", res_rows)
    write_csv("resampling_input_sampling_convergence.csv", res_density_rows)
    write_csv("chromatic_convergence.csv", chr_rows)
    write_json("noise_ordering.json", noise_result)
    write_json("spectral_support.json", spectral_result)
    write_json("psf_impossible_case.json", {"detected": psf.impossible_case_is_detected()})

    plot_radiometry(rad_rows)
    plot_psf(psf_rows)
    plot_resampling(res_rows)
    plot_chromatic(chr_rows)

    summary = {
        "radiometry_finest": rad_rows[-1],
        "analytic_psf_reference": psf.run_gaussian_reference().to_dict(),
        "noise_ordering": noise_result,
        "spectral_support": spectral_result,
        "chromatic_finest": chr_rows[-1],
        "psf_impossible_case_detected": psf.impossible_case_is_detected(),
    }
    write_json("summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
