#!/usr/bin/env python3
"""Gate C3 Stage 3: isolate real JWST/NIRCam PSF 180-degree asymmetry.

Stage 1 used circular Gaussian PSFs and therefore could not test Yu et al.'s
reported small positive asymmetry bias for intrinsically symmetric galaxies.
This separate, noiseless synthetic-equivalent diagnostic uses the pinned STPSF
2.2.0 NIRCam F444W optical+distortion PSF already verified by Gate B.

The experiment compares the original STPSF OVERDIST kernel to a control formed
by averaging that same kernel with its 180-degree rotation about its measured
flux centroid.  This removes only the PSF component that is odd under 180-degree
rotation while retaining the same instrument/filter/field configuration and
nearly identical radial smoothing.  No PSF shape parameter is tuned to Yu et al.

The PSF is held fixed.  Instead, each intrinsic scene size is scaled so that
R_p,true/FWHM matches the seven frozen Yu et al. resolvedness levels.  No target
noise is added and no production acceptance threshold is defined.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates
from scipy.signal import fftconvolve

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_yu_2023_psf_only_resolvedness as stage1
from verification.yu_2023 import YU_RESOLUTION_LEVELS

FILTER = "F444W"
DETECTOR = "NRCA5"
DETECTOR_POSITION = (1024, 1024)
PSF_FOV_NATIVE_PIX = 31
PSF_OVERSAMPLE = 2
PSF_NLAMBDA = 3
STAMP = 257
SIZE_SOLVE_ITERATIONS = 3


def normalize(image: np.ndarray) -> np.ndarray:
    a = np.asarray(image, dtype=float)
    total = float(np.sum(a))
    if not np.isfinite(total) or total <= 0:
        raise RuntimeError("PSF/image has non-positive total flux")
    return a / total


def centroid(image: np.ndarray) -> tuple[float, float]:
    a = normalize(image)
    yy, xx = np.indices(a.shape, dtype=float)
    return float(np.sum(a * xx)), float(np.sum(a * yy))


def rotate_180_about(image: np.ndarray, center: tuple[float, float]) -> np.ndarray:
    yy, xx = np.indices(image.shape, dtype=float)
    x0, y0 = center
    return map_coordinates(
        np.asarray(image, dtype=float),
        [2.0 * y0 - yy, 2.0 * x0 - xx],
        order=1,
        mode="constant",
        cval=0.0,
        prefilter=False,
    )


def radial_fwhm(image: np.ndarray, center: tuple[float, float]) -> float:
    """Circular-mean half-maximum FWHM in the kernel's sampled-pixel units."""
    a = normalize(image)
    x0, y0 = center
    r = np.arange(0.0, 0.45 * min(a.shape), 0.025)
    th = np.linspace(0.0, 2.0 * np.pi, 720, endpoint=False)
    ct, st = np.cos(th), np.sin(th)
    prof = np.empty_like(r)
    for i, rr in enumerate(r):
        prof[i] = map_coordinates(
            a,
            [y0 + rr * st, x0 + rr * ct],
            order=1,
            mode="constant",
            cval=0.0,
            prefilter=False,
        ).mean()
    peak = float(prof[0])
    if not np.isfinite(peak) or peak <= 0:
        raise RuntimeError("invalid PSF radial-profile peak")
    half = 0.5 * peak
    hit = np.flatnonzero(prof <= half)
    hit = hit[hit > 0]
    if len(hit) == 0:
        raise RuntimeError("PSF half-maximum crossing not found")
    i = int(hit[0])
    y1, y2 = float(prof[i - 1]), float(prof[i])
    if y2 == y1:
        rh = float(r[i])
    else:
        f = (half - y1) / (y2 - y1)
        rh = float(r[i - 1] + f * (r[i] - r[i - 1]))
    return 2.0 * rh


def make_psf_pair():
    import stpsf

    nrc = stpsf.NIRCam()
    nrc.filter = FILTER
    nrc.detector = DETECTOR
    nrc.detector_position = DETECTOR_POSITION
    hdul = nrc.calc_psf(
        fov_pixels=PSF_FOV_NATIVE_PIX,
        oversample=PSF_OVERSAMPLE,
        nlambda=PSF_NLAMBDA,
    )
    psf = normalize(np.asarray(hdul["OVERDIST"].data, dtype=float))
    cen = centroid(psf)
    rotated = rotate_180_about(psf, cen)
    sym = normalize(0.5 * (psf + rotated))
    sym_cen = centroid(sym)
    return {
        "original": psf,
        "sym180": sym,
        "centroid_original": cen,
        "centroid_sym180": sym_cen,
        "fwhm_original": radial_fwhm(psf, cen),
        "fwhm_sym180": radial_fwhm(sym, sym_cen),
        "kernel_asymmetry_180": float(np.sum(np.abs(psf - rotated)) / np.sum(np.abs(psf))),
    }


def scene_with_re(scene: dict[str, object], re_pix: float) -> dict[str, object]:
    out = dict(scene)
    out["re_pix"] = float(re_pix)
    return out


def intrinsic_at_resolvedness(
    scene: dict[str, object], requested: float, psf_fwhm: float
):
    """Scale Re without changing scene structure until intrinsic Rp/FWHM matches target."""
    base = scene_with_re(scene, float(scene["re_pix"]))
    base_m = stage1.morphology(stage1.render(base, 0.0))
    rp_per_re = float(base_m["rp"]) / float(base["re_pix"])
    re_pix = float(requested) * float(psf_fwhm) / rp_per_re

    for _ in range(SIZE_SOLVE_ITERATIONS):
        candidate = scene_with_re(scene, re_pix)
        intrinsic = stage1.render(candidate, 0.0)
        morph = stage1.morphology(intrinsic)
        constructed = float(morph["rp"]) / float(psf_fwhm)
        if not np.isfinite(constructed) or constructed <= 0:
            raise RuntimeError("invalid constructed resolvedness during size solve")
        re_pix *= float(requested) / constructed

    candidate = scene_with_re(scene, re_pix)
    intrinsic = stage1.render(candidate, 0.0)
    morph = stage1.morphology(intrinsic)
    return candidate, intrinsic, morph


def convolve_normalized(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    out = fftconvolve(np.asarray(image, float), np.asarray(kernel, float), mode="same")
    # FFT roundoff can create tiny negative values far below the physical scale.
    # Do not clip morphology-bearing pixels; only reject a numerically invalid total.
    return normalize(out)


def main() -> None:
    stage1.STAMP = STAMP
    out = Path("benchmark_output/yu_2023/stpsf_psf_asymmetry")
    out.mkdir(parents=True, exist_ok=True)

    psfs = make_psf_pair()
    rows: list[dict[str, object]] = []

    for scene in stage1.SCENES:
        for requested in YU_RESOLUTION_LEVELS:
            scaled, intrinsic, truth = intrinsic_at_resolvedness(
                scene, float(requested), float(psfs["fwhm_original"])
            )
            im_original = convolve_normalized(intrinsic, psfs["original"])
            im_sym = convolve_normalized(intrinsic, psfs["sym180"])
            mo = stage1.morphology(im_original)
            ms = stage1.morphology(im_sym)

            rows.append(
                {
                    "scene": scene["scene"],
                    "scene_kind": scene["kind"],
                    "rp_true_over_fwhm_requested": float(requested),
                    "rp_true_over_fwhm_constructed_original": float(truth["rp"])
                    / float(psfs["fwhm_original"]),
                    "rp_true_over_fwhm_constructed_sym180": float(truth["rp"])
                    / float(psfs["fwhm_sym180"]),
                    "scaled_re_pix": float(scaled["re_pix"]),
                    "psf_fwhm_original_pix": float(psfs["fwhm_original"]),
                    "psf_fwhm_sym180_pix": float(psfs["fwhm_sym180"]),
                    "asymmetry_true": float(truth["asymmetry"]),
                    "asymmetry_stpsf": float(mo["asymmetry"]),
                    "asymmetry_sym180_control": float(ms["asymmetry"]),
                    "delta_a_stpsf_vs_true": float(mo["asymmetry"] - truth["asymmetry"]),
                    "delta_a_sym180_vs_true": float(ms["asymmetry"] - truth["asymmetry"]),
                    "delta_a_odd_psf_component": float(mo["asymmetry"] - ms["asymmetry"]),
                    "concentration_true": float(truth["concentration"]),
                    "concentration_stpsf": float(mo["concentration"]),
                    "concentration_sym180_control": float(ms["concentration"]),
                    "rp_true_pix": float(truth["rp"]),
                    "rp_stpsf_pix": float(mo["rp"]),
                    "rp_sym180_control_pix": float(ms["rp"]),
                    "stpsf_center_min_success": bool(mo["asymmetry_min_success"]),
                    "sym180_center_min_success": bool(ms["asymmetry_min_success"]),
                }
            )

    expected = len(stage1.SCENES) * len(YU_RESOLUTION_LEVELS)
    if len(rows) != expected:
        raise RuntimeError(f"incomplete STPSF asymmetry matrix: {len(rows)} != {expected}")
    if sorted({r["rp_true_over_fwhm_requested"] for r in rows}) != sorted(YU_RESOLUTION_LEVELS):
        raise RuntimeError("resolvedness levels differ from frozen Yu et al. values")

    with (out / "metrics.csv").open("w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    symmetric = [r for r in rows if r["scene_kind"] == "sersic"]
    odd = np.array([float(r["delta_a_odd_psf_component"]) for r in symmetric])
    constructed_error = np.array(
        [
            abs(float(r["rp_true_over_fwhm_constructed_original"]) - float(r["rp_true_over_fwhm_requested"]))
            for r in rows
        ]
    )
    summary = {
        "experiment": "Yu et al. 2023 Gate C Stage 3 JWST/NIRCam PSF-asymmetry diagnostic",
        "scientific_status": (
            "noiseless synthetic-equivalent; actual pinned STPSF F444W PSF; "
            "not a literal CEERS reproduction; no production threshold"
        ),
        "instrument": "JWST/NIRCam",
        "filter": FILTER,
        "detector": DETECTOR,
        "detector_position": list(DETECTOR_POSITION),
        "stpsf_product": "OVERDIST",
        "psf_fov_native_pixels": PSF_FOV_NATIVE_PIX,
        "psf_oversample": PSF_OVERSAMPLE,
        "psf_nlambda": PSF_NLAMBDA,
        "psf_fwhm_original_sampled_pix": float(psfs["fwhm_original"]),
        "psf_fwhm_sym180_sampled_pix": float(psfs["fwhm_sym180"]),
        "psf_kernel_asymmetry_180": float(psfs["kernel_asymmetry_180"]),
        "control_definition": (
            "same normalized STPSF kernel averaged with its 180-degree rotation "
            "about the measured flux centroid"
        ),
        "resolution_levels": list(YU_RESOLUTION_LEVELS),
        "matrix_rows": len(rows),
        "max_abs_constructed_resolvedness_error": float(np.max(constructed_error)),
        "center_minimization_success_original": int(sum(bool(r["stpsf_center_min_success"]) for r in rows)),
        "center_minimization_success_sym180": int(sum(bool(r["sym180_center_min_success"]) for r in rows)),
        "descriptive_symmetric_scenes_only": {
            "median_delta_a_odd_psf_component": float(np.median(odd)),
            "min_delta_a_odd_psf_component": float(np.min(odd)),
            "max_delta_a_odd_psf_component": float(np.max(odd)),
            "positive_odd_psf_rows": int(np.count_nonzero(odd > 0.0)),
            "rows": int(len(odd)),
        },
        "interpretation_rule": (
            "Use the original-minus-sym180 difference only as a controlled diagnostic of "
            "the PSF component that is odd under 180-degree rotation. Do not tune the PSF, "
            "scene sizes, or acceptance criteria after seeing the result."
        ),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
