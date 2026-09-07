#!/usr/bin/env python3
"""B9a: pinned PyAutoGalaxy/PyAutoArray morphology convention preflight."""
from __future__ import annotations
import argparse, importlib.metadata, json, math
from pathlib import Path
import numpy as np
from scipy.signal import convolve2d
from scipy.special import gammaincinv
import autogalaxy as ag

AG_VERSION = "2026.8.14.1"
AA_VERSION = "2026.8.14.1"
SHAPE = (101, 101)
PIXEL_SCALE = 1.0
RE = 8.0
INTENSITY = 0.03
PSF_SIGMA = 1.2
PSF_SIZE = 9
CROP = PSF_SIZE // 2
SCENES = (
    {"name": "n1_q1_a0", "n": 1.0, "q": 1.0, "angle": 0.0},
    {"name": "n1_q06_a37", "n": 1.0, "q": 0.6, "angle": 37.0},
    {"name": "n4_q1_a0", "n": 4.0, "q": 1.0, "angle": 0.0},
    {"name": "n4_q06_a37", "n": 4.0, "q": 0.6, "angle": 37.0},
)


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def config():
    return {
        "stage": "B9a PyAutoGalaxy/PyAutoArray morphology convention preflight",
        "autogalaxy_version": AG_VERSION,
        "autoarray_version": AA_VERSION,
        "shape": list(SHAPE), "pixel_scale": PIXEL_SCALE,
        "effective_radius": RE, "intensity_at_re": INTENSITY,
        "psf_sigma_pixels": PSF_SIGMA, "psf_size": PSF_SIZE,
        "over_sample_size": 1, "convolution": "PyAutoArray real-space vs scipy.signal.convolve2d",
        "geometry": "documented PyAutoGalaxy eccentric radius sqrt(q)*sqrt(x_major^2 + y_minor^2/q^2)",
        "acceptance": "artifact completeness/finiteness/kernel normalization only; no morphology band",
        "scenes": list(SCENES),
    }


def gaussian_psf():
    ax = np.arange(PSF_SIZE, dtype=float) - PSF_SIZE // 2
    yy, xx = np.meshgrid(ax, ax, indexing="ij")
    p = np.exp(-0.5 * (xx * xx + yy * yy) / PSF_SIGMA**2)
    return p / p.sum()


def analytic_sersic(grid_native, n, q, angle):
    y = np.asarray(grid_native[..., 0], dtype=float)
    x = np.asarray(grid_native[..., 1], dtype=float)
    phi = math.radians(angle)
    x_major = x * math.cos(phi) + y * math.sin(phi)
    y_minor = -x * math.sin(phi) + y * math.cos(phi)
    r = math.sqrt(q) * np.sqrt(x_major**2 + (y_minor / q) ** 2)
    bn = float(gammaincinv(2.0 * n, 0.5))
    return INTENSITY * np.exp(-bn * ((r / RE) ** (1.0 / n) - 1.0))


def centroid_and_moments(img):
    w = np.asarray(img, dtype=float)
    yy, xx = np.indices(w.shape, dtype=float)
    total = w.sum()
    cy = float((w * yy).sum() / total); cx = float((w * xx).sum() / total)
    dy, dx = yy - cy, xx - cx
    mxx = float((w * dx * dx).sum() / total); myy = float((w * dy * dy).sum() / total)
    mxy = float((w * dx * dy).sum() / total)
    cov = np.array([[mxx, mxy], [mxy, myy]])
    vals, vecs = np.linalg.eigh(cov); vals = np.maximum(vals, 0.0)
    order = np.argsort(vals)[::-1]; vals = vals[order]; vec = vecs[:, order[0]]
    qmom = float(math.sqrt(vals[1] / vals[0])) if vals[0] > 0 else None
    angle = float(math.degrees(math.atan2(vec[1], vec[0])) % 180.0)
    return {"centroid_y": cy, "centroid_x": cx, "mxx": mxx, "myy": myy, "mxy": mxy, "moment_q": qmom, "moment_angle_deg": angle}


def diff(a, b):
    d = np.asarray(a) - np.asarray(b)
    denom = float(np.sum(np.abs(a)))
    return {"max_abs": float(np.max(np.abs(d))), "l1_over_reference_l1": float(np.sum(np.abs(d)) / denom)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", type=Path, required=True); args = ap.parse_args()
    assert importlib.metadata.version("autogalaxy") == AG_VERSION
    assert importlib.metadata.version("autoarray") == AA_VERSION
    out = args.out; out.mkdir(parents=True, exist_ok=True); dump(out / "config.json", config())
    psf = gaussian_psf(); kernel = ag.Array2D.no_mask(values=psf, pixel_scales=PIXEL_SCALE)
    convolver = ag.Convolver(kernel=kernel, use_fft=False, normalize=False)
    grid = ag.Grid2D.uniform(shape_native=SHAPE, pixel_scales=PIXEL_SCALE, over_sample_size=1)
    grid_native = np.asarray(grid.native)
    arrays = {"psf": psf, "grid_native": grid_native}; rows = []
    for s in SCENES:
        profile = ag.lp.Sersic(centre=(0.0, 0.0), ell_comps=ag.convert.ell_comps_from(axis_ratio=s["q"], angle=s["angle"]), intensity=INTENSITY, effective_radius=RE, sersic_index=s["n"])
        ag_raw = np.asarray(profile.image_2d_from(grid=grid).native, dtype=float)
        ref_raw = analytic_sersic(grid_native, s["n"], s["q"], s["angle"])
        ag_conv = np.asarray(profile.unmasked_blurred_image_2d_from(grid=grid, psf=convolver).native, dtype=float)
        ref_conv = convolve2d(ref_raw, psf, mode="same", boundary="fill", fillvalue=0.0)
        sl = (slice(CROP, -CROP), slice(CROP, -CROP))
        row = {"scene": s["name"], "raw_diff": diff(ref_raw, ag_raw), "conv_global_diff": diff(ref_conv, ag_conv), "conv_interior_diff": diff(ref_conv[sl], ag_conv[sl]), "ref_raw_sum": float(ref_raw.sum()), "ag_raw_sum": float(ag_raw.sum()), "ref_conv_sum": float(ref_conv.sum()), "ag_conv_sum": float(ag_conv.sum()), "ref_raw_moments": centroid_and_moments(ref_raw), "ag_raw_moments": centroid_and_moments(ag_raw), "ref_conv_moments": centroid_and_moments(ref_conv), "ag_conv_moments": centroid_and_moments(ag_conv)}
        rows.append(row)
        for key, val in (("ref_raw", ref_raw), ("ag_raw", ag_raw), ("ref_conv", ref_conv), ("ag_conv", ag_conv)):
            arrays[f"{s['name']}__{key}"] = val
    np.savez_compressed(out / "arrays.npz", **arrays)
    summary = {"config": config(), "psf_sum": float(psf.sum()), "psf_min": float(psf.min()), "results": rows}
    dump(out / "summary.json", summary)
    print(json.dumps(summary, indent=2))

if __name__ == "__main__": main()
