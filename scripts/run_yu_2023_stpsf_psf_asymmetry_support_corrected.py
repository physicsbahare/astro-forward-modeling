#!/usr/bin/env python3
"""Support-corrected rerun of the Yu et al. (2023) STPSF asymmetry diagnostic.

The first Stage-3 implementation used a fixed 257x257 detector stamp while
scaling intrinsic galaxies across the full frozen Yu resolvedness range.  The
run failed before producing morphology metrics because the exact 1.5 Rp
measurement aperture exceeded the numerical radial support at high
resolvedness.

This separate diagnostic preserves that failed run and changes numerical
support only.  The stamp size is derived before any morphology measurement from
(1) the largest frozen Rp,true/FWHM value, (2) the measured FWHM of the pinned
STPSF F444W kernels, (3) Yu's exact 1.5 Rp aperture, and (4) the full sampled
PSF half-width needed to keep the convolution support inside the image.  The
radial sampler is the same detector-edge-supported implementation already used
by the Stage-2 support-corrected diagnostic.  PSF configuration, scenes,
resolvedness values, center minimization, and all morphology definitions remain
unchanged.  No acceptance threshold is introduced or tuned.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path as _Path

import numpy as np

ROOT = _Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_yu_2023_stpsf_psf_asymmetry as original
from scripts.run_yu_2023_noisy_resolvedness_support_corrected import (
    EDGE_MARGIN_PIX,
    radial_edge_supported,
)
from verification.yu_2023 import TOTAL_LIGHT_APERTURE_RP, YU_RESOLUTION_LEVELS

LEGACY_OUTPUT_ROOT = "benchmark_output/yu_2023/stpsf_psf_asymmetry"
CORRECTED_OUTPUT_ROOT = "benchmark_output/yu_2023/stpsf_psf_asymmetry_support_corrected"
LEGACY_STAMP = 257


def redirected_path(value="."):
    """Redirect only the Stage-3 output directory to a separate record."""
    if str(value) == LEGACY_OUTPUT_ROOT:
        return _Path(CORRECTED_OUTPUT_ROOT)
    return _Path(value)


def derive_stamp(psfs: dict[str, object]) -> tuple[int, dict[str, float]]:
    """Derive an odd stamp size from frozen measurement and PSF support."""
    max_fwhm = max(float(psfs["fwhm_original"]), float(psfs["fwhm_sym180"]))
    max_resolvedness = max(float(x) for x in YU_RESOLUTION_LEVELS)
    max_rp_true = max_resolvedness * max_fwhm

    kernel = np.asarray(psfs["original"])
    kernel_half_width = max((float(n) - 1.0) / 2.0 for n in kernel.shape)
    measurement_radius = float(TOTAL_LIGHT_APERTURE_RP) * max_rp_true
    required_half_extent = measurement_radius + kernel_half_width + float(EDGE_MARGIN_PIX)

    half_extent_pix = int(np.ceil(required_half_extent))
    stamp = 2 * half_extent_pix + 1
    return stamp, {
        "max_psf_fwhm_sampled_pix": max_fwhm,
        "max_frozen_resolvedness": max_resolvedness,
        "max_constructed_rp_true_pix": max_rp_true,
        "measurement_aperture_factor_rp": float(TOTAL_LIGHT_APERTURE_RP),
        "max_measurement_radius_pix": measurement_radius,
        "psf_kernel_half_width_pix": kernel_half_width,
        "interpolation_edge_margin_pix": float(EDGE_MARGIN_PIX),
        "required_half_extent_pix": required_half_extent,
    }


def main() -> None:
    # Generate the pinned PSF once, then derive numerical support from it before
    # any morphology is measured.  Cache the pair so original.main() does not
    # regenerate a slightly different or separately timed PSF product.
    psfs = original.make_psf_pair()
    stamp, support = derive_stamp(psfs)

    original.STAMP = stamp
    original.stage1.radial = radial_edge_supported
    original.Path = redirected_path
    original.make_psf_pair = lambda: psfs
    original.main()

    summary_path = _Path(CORRECTED_OUTPUT_ROOT) / "summary.json"
    payload = json.loads(summary_path.read_text())
    payload["numerical_support_correction"] = {
        "record_semantics": (
            "separate support-corrected diagnostic; the initial fixed-257-pixel "
            "failed run is preserved and not overwritten"
        ),
        "legacy_stamp_pixels": LEGACY_STAMP,
        "corrected_stamp_pixels": stamp,
        "stamp_derivation": support,
        "radial_support_rule": (
            "center-dependent detector-edge clearance minus 0.5 pixel, identical "
            "to the Stage-2 support-corrected diagnostic"
        ),
        "changed_quantities": [
            "detector stamp numerical support",
            "radial numerical support ceiling",
        ],
        "unchanged": [
            "pinned STPSF 2.2.0 NIRCam F444W PSF configuration",
            "original versus 180-degree-symmetrized PSF control",
            "scene definitions",
            "seven frozen Rp,true/FWHM values",
            "Yu 1.5 Rp measurement aperture",
            "concentration and asymmetry definitions",
            "asymmetry center minimization",
            "noiseless design",
        ],
    }
    payload["scientific_status"] = (
        "support-corrected noiseless synthetic-equivalent STPSF diagnostic; "
        "initial finite-support failure preserved; not a literal CEERS reproduction; "
        "no production threshold"
    )
    summary_path.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
