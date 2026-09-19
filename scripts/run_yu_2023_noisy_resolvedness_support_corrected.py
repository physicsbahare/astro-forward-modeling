#!/usr/bin/env python3
"""Separate support-corrected diagnostic for Yu et al. (2023) Stage 2.

The historical Stage-2 noisy-resolvedness workflow is preserved unchanged.  Its
non-parametric radial sampler inherited the Stage-1 fixed radial ceiling
``0.45 * min(image_shape)``.  At the poorest resolvedness the PSF-only 1.5 Rp
aperture already lies very close to that numerical ceiling, so small noisy Rp
excursions can produce ``1.5 Rp exceeds radial grid`` even when the requested
ellipse is still contained by the detector stamp.

This diagnostic changes only that numerical support convention: the radial
profile extends to the largest center-dependent radius that remains inside the
existing detector stamp (with a half-pixel interpolation margin).  The same
scenes, seven Rp,true/FWHM values, S/N values, random seeds, Eq. (28), Sérsic
bounds, optimizer settings, and winner rule are retained.  It writes to a new
output directory and therefore cannot overwrite the historical Stage-2 record.

This is controlled synthetic-equivalent verification, not production code and
not a literal CEERS reproduction.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path as _Path

import numpy as np
from scipy.ndimage import map_coordinates

ROOT = _Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.run_yu_2023_noisy_resolvedness as legacy
from scripts import run_yu_2023_psf_only_resolvedness as stage1

LEGACY_OUTPUT_ROOT = "benchmark_output/yu_2023/noisy_resolvedness"
CORRECTED_OUTPUT_ROOT = "benchmark_output/yu_2023/noisy_resolvedness_support_corrected"
EDGE_MARGIN_PIX = 0.5


def radial_edge_supported(im: np.ndarray, center, q: float, pa: float):
    """Stage-1 radial estimator with an edge-safe, center-dependent rmax.

    For q<=1 the Euclidean displacement of every sampled point on an ellipse of
    semi-major radius r is <=r.  Limiting r by the minimum Cartesian distance
    from the adopted center to the detector edges therefore keeps all samples
    inside the stamp.  The half-pixel margin avoids relying on interpolation
    exactly on the outer pixel boundary.
    """
    image = np.asarray(im, dtype=float)
    ny, nx = image.shape
    x0, y0 = map(float, center)
    edge_clearance = min(x0, y0, (nx - 1.0) - x0, (ny - 1.0) - y0)
    rmax = float(edge_clearance - EDGE_MARGIN_PIX)
    dr = float(stage1.DR)
    if not np.isfinite(rmax) or rmax <= 2.0 * dr:
        raise RuntimeError("insufficient detector support for radial profile")

    r = np.arange(0.0, rmax + 0.5 * dr, dr)
    th = np.linspace(0.0, 2.0 * np.pi, int(stage1.NTHETA), endpoint=False)
    ct, st = np.cos(th), np.sin(th)
    c, s = np.cos(float(pa)), np.sin(float(pa))
    q = float(q)
    I = np.empty_like(r)
    for i, rr in enumerate(r):
        xp = rr * ct
        yp = q * rr * st
        x = x0 + c * xp - s * yp
        y = y0 + s * xp + c * yp
        I[i] = map_coordinates(
            image,
            [y, x],
            order=1,
            mode="constant",
            cval=0.0,
            prefilter=False,
        ).mean()

    cum = np.zeros_like(r)
    w = I * r
    cum[1:] = np.cumsum(0.5 * (w[1:] + w[:-1]) * np.diff(r))
    mean = np.empty_like(r)
    mean[0] = I[0]
    mean[1:] = 2.0 * cum[1:] / np.maximum(r[1:] ** 2, 1e-30)
    eta = np.divide(I, mean, out=np.full_like(I, np.nan), where=mean > 0)
    return r, cum, eta


def redirected_path(value="."):
    """Redirect only the legacy Stage-2 output root to a new record."""
    if str(value) == LEGACY_OUTPUT_ROOT:
        return _Path(CORRECTED_OUTPUT_ROOT)
    return _Path(value)


def _requested_snr() -> int:
    try:
        i = sys.argv.index("--aperture-snr")
        return int(float(sys.argv[i + 1]))
    except Exception as exc:
        raise RuntimeError("--aperture-snr is required") from exc


def main() -> None:
    # Monkey-patch only the two implementation seams needed for this diagnostic.
    # The historical module and its default output remain unchanged in Git.
    legacy.radial = radial_edge_supported
    legacy.Path = redirected_path
    legacy.main()

    snr = _requested_snr()
    summary_path = _Path(CORRECTED_OUTPUT_ROOT) / f"snr_{snr}" / "summary.json"
    payload = json.loads(summary_path.read_text())
    payload["radial_support_correction"] = {
        "record_semantics": "separate corrected diagnostic; historical Stage-2 outputs are not overwritten",
        "legacy_rule": "fixed rmax = 0.45 * min(image_shape)",
        "corrected_rule": "center-dependent detector-edge clearance minus 0.5 pixel",
        "changed_quantity": "radial numerical support only",
        "unchanged": [
            "scene definitions",
            "Rp,true/FWHM levels",
            "S/N levels",
            "random seeds",
            "noise model",
            "Yu Eq. (28) and f1/f2",
            "Sersic bounds",
            "optimizer settings",
            "winner rule",
        ],
    }
    payload["scientific_status"] = (
        "support-corrected synthetic-equivalent diagnostic; historical Stage 2 preserved; "
        "no production criterion; not literal CEERS depth"
    )
    summary_path.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
