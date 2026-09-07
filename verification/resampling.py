"""Resampling verification using exact pixel integrals of a 2D Gaussian.

The experiment distinguishes two operations:

1. Rendering a latent continuous scene directly into target pixel footprints.
2. Transferring an already-pixelized image by exact pixel-area overlap under a
   piecewise-constant assumption.

The former has access to the continuous truth; the latter cannot recover spatial
information already lost at the input pixelization stage.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import erf, sqrt

import numpy as np


@dataclass
class ResamplingMetrics:
    input_pixels: int
    output_pixels: int
    sigma_input_pixels: float
    output_to_input_pixel_width: float
    subpixel_phase_x: float
    subpixel_phase_y: float
    flux_relative_error: float
    l1_image_error: float
    centroid_error_in_output_pixels: float
    second_moment_relative_error: float

    def to_dict(self) -> dict:
        return asdict(self)


def _normal_cdf_interval(edges: np.ndarray, center: float, sigma: float) -> np.ndarray:
    z = (edges - center) / (sqrt(2.0) * sigma)
    cdf = 0.5 * (1.0 + np.array([erf(float(v)) for v in z]))
    return np.diff(cdf)


def integrated_gaussian_image(
    x_edges: np.ndarray,
    y_edges: np.ndarray,
    sigma: float,
    center_x: float,
    center_y: float,
) -> np.ndarray:
    px = _normal_cdf_interval(np.asarray(x_edges), center_x, sigma)
    py = _normal_cdf_interval(np.asarray(y_edges), center_y, sigma)
    return np.outer(py, px)


def overlap_matrix(output_edges: np.ndarray, input_edges: np.ndarray) -> np.ndarray:
    o0 = output_edges[:-1, None]
    o1 = output_edges[1:, None]
    i0 = input_edges[None, :-1]
    i1 = input_edges[None, 1:]
    return np.maximum(0.0, np.minimum(o1, i1) - np.maximum(o0, i0))


def resample_flux_by_exact_overlap(
    image_flux_per_pixel: np.ndarray,
    input_x_edges: np.ndarray,
    input_y_edges: np.ndarray,
    output_x_edges: np.ndarray,
    output_y_edges: np.ndarray,
) -> np.ndarray:
    image = np.asarray(image_flux_per_pixel, dtype=float)
    dx = np.diff(input_x_edges)
    dy = np.diff(input_y_edges)
    if not (np.allclose(dx, dx[0]) and np.allclose(dy, dy[0])):
        raise NotImplementedError("Reference test assumes constant input pixel size.")
    input_area = float(dx[0] * dy[0])
    ox = overlap_matrix(output_x_edges, input_x_edges)
    oy = overlap_matrix(output_y_edges, input_y_edges)
    return oy @ image @ ox.T / input_area


def _centroid_and_sigma(image: np.ndarray, x_edges: np.ndarray, y_edges: np.ndarray) -> tuple[float, float, float]:
    f = np.asarray(image, dtype=float)
    total = f.sum()
    xc = 0.5 * (x_edges[:-1] + x_edges[1:])
    yc = 0.5 * (y_edges[:-1] + y_edges[1:])
    xx, yy = np.meshgrid(xc, yc)
    cx = float(np.sum(f * xx) / total)
    cy = float(np.sum(f * yy) / total)
    varx = float(np.sum(f * (xx - cx) ** 2) / total)
    vary = float(np.sum(f * (yy - cy) ** 2) / total)
    sigma = sqrt(0.5 * (varx + vary))
    return cx, cy, sigma


def run_resampling_check(
    input_pixels: int = 101,
    output_pixels: int = 151,
    sigma_input_pixels: float = 4.0,
    subpixel_phase_x: float = 0.31,
    subpixel_phase_y: float = -0.27,
) -> ResamplingMetrics:
    half = input_pixels / 2.0
    in_edges = np.linspace(-half, half, input_pixels + 1)
    out_edges = np.linspace(-half, half, output_pixels + 1)
    out_width = out_edges[1] - out_edges[0]

    source = integrated_gaussian_image(in_edges, in_edges, sigma_input_pixels, subpixel_phase_x, subpixel_phase_y)
    transferred = resample_flux_by_exact_overlap(source, in_edges, in_edges, out_edges, out_edges)
    truth = integrated_gaussian_image(out_edges, out_edges, sigma_input_pixels, subpixel_phase_x, subpixel_phase_y)

    flux_err = abs(transferred.sum() - source.sum()) / source.sum()
    tnorm = truth / truth.sum()
    rnorm = transferred / transferred.sum()
    l1 = float(np.sum(np.abs(rnorm - tnorm)))

    cx_t, cy_t, sig_t = _centroid_and_sigma(tnorm, out_edges, out_edges)
    cx_r, cy_r, sig_r = _centroid_and_sigma(rnorm, out_edges, out_edges)
    centroid_world = np.hypot(cx_r - cx_t, cy_r - cy_t)
    centroid_pix = float(centroid_world / out_width)
    sigma_err = abs(sig_r - sig_t) / sig_t

    return ResamplingMetrics(input_pixels, output_pixels, sigma_input_pixels, float(out_width), subpixel_phase_x, subpixel_phase_y, float(flux_err), l1, centroid_pix, float(sigma_err))


def convergence_table() -> list[dict]:
    rows: list[dict] = []
    for sigma in (1.2, 2.0, 4.0, 8.0):
        for nout in (51, 81, 101, 151, 203):
            for phase_x, phase_y in ((0.0, 0.0), (0.23, -0.37), (0.49, 0.49)):
                rows.append(run_resampling_check(101, nout, sigma, phase_x, phase_y).to_dict())
    return rows


def sampling_density_table() -> list[dict]:
    rows: list[dict] = []
    half = 10.0
    sigma_physical = 1.0
    output_pixels = 157
    out_edges = np.linspace(-half, half, output_pixels + 1)
    for input_pixels in (21, 31, 51, 81, 101, 151, 201, 301, 401):
        in_edges = np.linspace(-half, half, input_pixels + 1)
        input_width = in_edges[1] - in_edges[0]
        for px, py in ((0.0, 0.0), (0.23 * input_width, -0.37 * input_width), (0.49 * input_width, 0.49 * input_width)):
            source = integrated_gaussian_image(in_edges, in_edges, sigma_physical, px, py)
            transferred = resample_flux_by_exact_overlap(source, in_edges, in_edges, out_edges, out_edges)
            truth = integrated_gaussian_image(out_edges, out_edges, sigma_physical, px, py)
            rnorm = transferred / transferred.sum()
            tnorm = truth / truth.sum()
            l1 = float(np.sum(np.abs(rnorm - tnorm)))
            cx_t, cy_t, sig_t = _centroid_and_sigma(tnorm, out_edges, out_edges)
            cx_r, cy_r, sig_r = _centroid_and_sigma(rnorm, out_edges, out_edges)
            out_width = out_edges[1] - out_edges[0]
            rows.append({
                "input_pixels": input_pixels,
                "input_sigma_pixels": sigma_physical / input_width,
                "output_pixels": output_pixels,
                "phase_fraction_x": px / input_width,
                "phase_fraction_y": py / input_width,
                "flux_relative_error": float(abs(transferred.sum() - source.sum()) / source.sum()),
                "l1_image_error": l1,
                "centroid_error_in_output_pixels": float(np.hypot(cx_r - cx_t, cy_r - cy_t) / out_width),
                "second_moment_relative_error": float(abs(sig_r - sig_t) / sig_t),
            })
    return rows
