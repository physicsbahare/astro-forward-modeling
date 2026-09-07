#!/usr/bin/env python3
"""Audit whether Paulino-Afonso-style source->target PSF degradation is physically feasible.

This is a pre-image diagnostic for Gate C2.  It uses the paper anchors already
adopted by the verification suite: an SDSS-like local source PSF FWHM of about
1.3 arcsec, COSMOS/ACS F814W target PSF FWHM of about 0.09 arcsec, target
redshifts 0.40, 0.84, 1.47, 2.23, and the reported median local redshifts of the
CALIFA, SAMI, MaNGA, and NYU-VAGC source subsamples.

A source PSF with angular FWHM theta_s at z_s maps, after pure angular rescaling,
to an equivalent target-frame angular FWHM

    theta_equiv = theta_s * [kpc/arcsec(z_s)] / [kpc/arcsec(z_t)].

For Gaussian PSFs, pure degradation by convolution is possible only when

    theta_target >= theta_equiv,

in which case the required matching-kernel FWHM is

    sqrt(theta_target^2 - theta_equiv^2).

If theta_target < theta_equiv, the operation would require sharpening /
deconvolution.  This audit records that regime explicitly; it never substitutes
an imaginary Gaussian kernel and never changes a scientific tolerance.

The median-redshift calculation is a feasibility diagnostic, not a literal
reproduction of every source galaxy in Paulino-Afonso et al. (2017).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from verification.paulino_afonso_sersic_floor import (
    PSF_FWHM_ARCSEC,
    TARGET_REDSHIFTS,
    _kpc_per_arcsec,
)

SOURCE_PSF_FWHM_ARCSEC = 1.3
SOURCE_SUBSAMPLE_MEDIAN_REDSHIFTS = {
    "CALIFA": 0.015,
    "SAMI": 0.039,
    "MaNGA": 0.030,
    "NYU-VAGC": 0.041,
}


def main() -> None:
    out = Path("benchmark_output/paulino_afonso_2017/psf_feasibility")
    out.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for sample, z_source in SOURCE_SUBSAMPLE_MEDIAN_REDSHIFTS.items():
        source_scale = _kpc_per_arcsec(float(z_source))
        for z_target in TARGET_REDSHIFTS:
            target_scale = _kpc_per_arcsec(float(z_target))
            equiv = SOURCE_PSF_FWHM_ARCSEC * source_scale / target_scale
            feasible = bool(PSF_FWHM_ARCSEC >= equiv)
            if feasible:
                kernel = (PSF_FWHM_ARCSEC**2 - equiv**2) ** 0.5
            else:
                kernel = None
            rows.append(
                {
                    "source_sample": sample,
                    "source_median_redshift": float(z_source),
                    "target_redshift": float(z_target),
                    "source_psf_fwhm_arcsec": SOURCE_PSF_FWHM_ARCSEC,
                    "target_psf_fwhm_arcsec": PSF_FWHM_ARCSEC,
                    "source_kpc_per_arcsec": float(source_scale),
                    "target_kpc_per_arcsec": float(target_scale),
                    "source_psf_equivalent_at_target_arcsec": float(equiv),
                    "pure_convolution_feasible": feasible,
                    "required_gaussian_kernel_fwhm_arcsec": None if kernel is None else float(kernel),
                    "operation": "convolution" if feasible else "would_require_sharpening_or_deconvolution",
                }
            )

    with (out / "rows.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    n_feasible = sum(bool(r["pure_convolution_feasible"]) for r in rows)
    payload = {
        "experiment": "Paulino-Afonso C2 source-to-target PSF feasibility audit",
        "scientific_status": "diagnostic only; median source redshifts, not literal source-by-source reproduction",
        "source_psf_fwhm_arcsec": SOURCE_PSF_FWHM_ARCSEC,
        "target_psf_fwhm_arcsec": PSF_FWHM_ARCSEC,
        "n_combinations": len(rows),
        "n_pure_convolution_feasible": int(n_feasible),
        "n_requires_sharpening_or_deconvolution": int(len(rows) - n_feasible),
        "rows": rows,
        "decision_rule": (
            "Use a convolution-only source->target PSF benchmark only for combinations where the target PSF is broader than the angularly rescaled source PSF. For combinations requiring sharpening, do not fake a Gaussian degradation kernel; instead retain them as a feasibility limitation and move the controlled image-level benchmark to an intrinsic/latent source or to source-specific PSF treatment that reproduces the paper's actual procedure."
        ),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
