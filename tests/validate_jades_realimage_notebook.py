"""Synthetic, public-data-free regression for the JADES real-image notebook.

This is NOT a substitute for end-to-end validation on actual JADES DR5 data.
It checks catalog FITS HDUs, WCS/memmap cutouts, real pixels and PSF matching,
throughput interpolation, flux accounting, noise, output, and MAP refitting.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

HERE = Path(__file__).resolve().parent.parent
NB_PATH = HERE / "JADES_realimage_artificial_redshifting_batch.ipynb"


def load_engine():
    nb = json.loads(NB_PATH.read_text())
    ns = {"__name__": "__main__"}
    # 2 dependency check, 4 imports, 6 settings, 8/10/12/14/16 helpers.
    # Do NOT execute the last Run All cell, which expects real JADES paths.
    for i in (2, 4, 6, 8, 10, 12, 14, 16):
        code = "".join(nb["cells"][i]["source"])
        exec(compile(code, f"notebook_cell_{i}", "exec"), ns)
    return ns


def write_mosaic(path, data, sigma, segmentation=False):
    ny, nx = data.shape
    w = WCS(naxis=2)
    w.wcs.crpix = [(nx + 1) / 2, (ny + 1) / 2]
    w.wcs.crval = [53.0, -27.8]
    w.wcs.cdelt = np.array([-0.03 / 3600, 0.03 / 3600])
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    header = w.to_header()
    header["BUNIT"] = "MJy/sr"
    if segmentation:
        # Simulate a segmentation pixel grid that is shifted relative to SCI,
        # as when a full-field mosaic is paired with a JADES submosaic.
        header["CRPIX1"] = float(header["CRPIX1"]) + 0.3
        header["CRPIX2"] = float(header["CRPIX2"]) - 0.6
        fits.PrimaryHDU(np.asarray(data, np.int32), header=header).writeto(path)
    else:
        err_h = header.copy()
        err_h["BUNIT"] = "MJy/sr"
        # Actual JADES DR5 products repeat EXTNAME SCI on the no-data
        # primary HDU and on the 2-D SCI image extension.
        primary = fits.PrimaryHDU(header=fits.Header({"EXTNAME": "SCI", "BUNIT": "MJy/sr"}))
        fits.HDUList([
            primary,
            fits.ImageHDU(np.asarray(data, np.float32), header=header, name="SCI"),
            fits.ImageHDU(np.full(data.shape, sigma, np.float32), header=err_h, name="ERR"),
        ]).writeto(path)


def write_psf(path, sigma):
    n = 35
    yy, xx = np.indices((n, n), dtype=float)
    r2 = (xx-(n-1)/2)**2 + (yy-(n-1)/2)**2
    p = np.exp(-r2 / (2.0 * float(sigma)**2))
    p /= p.sum()
    fits.PrimaryHDU(p.astype(np.float32), header=fits.Header({"PIXSCALE": 0.03})).writeto(path)


def make_throughput(path, center, spread):
    wave = np.linspace(center-4*spread, center+4*spread, 161)
    trans = np.exp(-0.5 * ((wave-center)/spread)**2)
    np.savetxt(path, np.column_stack([wave, trans]), fmt="%.12g")


def run():
    ns = load_engine()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ns["OUTPUT_DIR"] = str(root/"out")
        ns["THROUGHPUT_CACHE_DIR"] = str(root/"cache")
        ns["INPUT_CATALOG_PATH"] = str(root/"jades_catalog.fits")
        ns["CATALOG_FORMAT"] = "JADES_DR5"
        ns["JADES_REDSHIFT_HDU"] = "PHOTOZ_KRON"
        ns["JADES_REDSHIFT_COL"] = "z_a"
        ns["SOURCE_Z_RANGE"] = None
        ns["AUTO_SELECT_TARGET_FOOTPRINT"] = False
        ns["RUN_NATIVE_REFIT"] = False
        ns["REFIT_MODE"] = "MAP"
        ns["PYSERSIC_WARMUP"] = 10
        ns["PYSERSIC_SAMPLES"] = 10
        ns["SOURCE_NOISE_MC_DRAWS"] = 3
        ns["MAX_FIT_IMAGE_PIX"] = 71
        ns["FLUX_CONSERVATION_TOLERANCE"] = 0.15
        ns["SOURCE_CUTOUT_ARCSEC"] = 3.0
        ns["TARGET_CUTOUT_ARCSEC"] = 3.0
        ns["SOURCE_MASK_DILATION_PIX"] = 0
        ns["FIT_MASK_DILATION_PIX"] = 2
        ns["TARGET_PLAN"] = [{"z": 4.0, "filter": "F444W"}]
        ns["INJECTION_MODE"] = "CATALOG"
        ns["INJECTION_RA_COL"] = "injection_ra"
        ns["INJECTION_DEC_COL"] = "injection_dec"

        # DR5-format FITS catalog contains separate coordinate/PHOTOZ HDUs.
        cols = fits.ColDefs([
            fits.Column(name="ID", array=np.array([42], np.int32), format="J"),
            fits.Column(name="RA", array=np.array([53.0]), format="D"),
            fits.Column(name="DEC", array=np.array([-27.8]), format="D"),
        ])
        photo = fits.ColDefs([
            fits.Column(name="ID", array=np.array([42], np.int32), format="J"),
            fits.Column(name="z_a", array=np.array([0.95]), format="D"),
        ])
        flag = fits.ColDefs([
            fits.Column(name="ID", array=np.array([42], np.int32), format="J"),
            fits.Column(name="FLAG_BN", array=np.array([0], np.int32), format="J"),
        ])
        fits.HDUList([
            fits.PrimaryHDU(),
            fits.BinTableHDU.from_columns(cols, name="SIZE"),
            fits.BinTableHDU.from_columns(photo, name="PHOTOZ_KRON"),
            fits.BinTableHDU.from_columns(flag, name="FLAG"),
        ]).writeto(root/"jades_catalog.fits")
        cat = ns["load_catalog"](str(root/"jades_catalog.fits"))
        assert len(cat) == 1
        assert cat.iloc[0]["ID"] == 42
        assert abs(float(cat.iloc[0]["z_source"]) - 0.95) < 1e-10

        yy, xx = np.indices((101, 101), dtype=float)
        cx = cy = 50.0
        ell_r2 = ((xx-cx)/8.0)**2 + ((yy-cy)/6.0)**2
        src = np.exp(-0.5 * ell_r2) + 0.15*np.exp(-((xx-cx-10)**2+(yy-cy+3)**2)/(2*3**2))
        seg = np.where(((xx-cx)/26.0)**2+((yy-cy)/22.0)**2<1, 42, 0).astype(np.int32)
        write_mosaic(root/"seg.fits", seg, 1, segmentation=True)

        bands = {}
        for band, amp, sigma, lam, width in (
            ("F115W", 6.0, 1.2, 1.15, 0.06),
            ("F200W", 8.0, 1.9, 1.99, 0.09),
        ):
            write_mosaic(root/f"{band}.fits", 0.02+amp*src, 0.06)
            write_psf(root/f"psf_{band}.fits", sigma)
            make_throughput(root/f"{band}.dat", lam, width)
            bands[band] = {
                "sci_path": str(root/f"{band}.fits"),
                "err_path": "SAME_AS_SCI", "seg_path": str(root/"seg.fits"),
                "psf_path": str(root/f"psf_{band}.fits"),
                "sci_ext": "SCI", "err_ext": "ERR", "seg_ext": 0, "psf_ext": 0,
                "err_kind": "STDDEV", "psf_pixel_scale_arcsec": 0.03,
                "throughput_file": str(root/f"{band}.dat"),
                "throughput_wavelength_unit": "um", "svo_id": None,
            }
        ns["SOURCE_BANDS"] = bands

        # The real audit observed only five HDUs in the still-downloading
        # F200W mosaic. The runner must refuse to use partial DR5 products.
        try:
            ns["validate_mosaic_file_integrity"](
                str(root/"F115W.fits"), expected_min_hdus=6)
        except ns["PipelineFailure"] as exc:
            assert exc.code == "INCOMPLETE_FITS_DOWNLOAD"
        else:
            raise AssertionError("Incomplete DR5-FITS guard did not fire")

        write_mosaic(root/"F444W.fits", np.full((101, 101), 0.02), 0.04)
        write_psf(root/"psf_F444W.fits", 4.5)
        write_mosaic(root/"target_seg.fits", np.zeros((101, 101), np.int32), 1, segmentation=True)
        make_throughput(root/"F444W.dat", 4.44, 0.18)
        ns["TARGET_PRODUCTS"] = {
            "F444W": {
                "sci_path": str(root/"F444W.fits"),
                "err_path": "SAME_AS_SCI", "seg_path": str(root/"target_seg.fits"),
                "psf_path": str(root/"psf_F444W.fits"),
                "sci_ext": "SCI", "err_ext": "ERR", "seg_ext": 0, "psf_ext": 0,
                "err_kind": "STDDEV", "psf_pixel_scale_arcsec": 0.03,
                "throughput_file": str(root/"F444W.dat"),
                "throughput_wavelength_unit": "um", "svo_id": None,
            }
        }

        # Geometry/units/PSF/SED tests independent of the optimizer.
        crv = {b: ns["curve_for"](b, q) for b, q in bands.items()}
        target_crv = ns["curve_for"]("F444W", ns["TARGET_PRODUCTS"]["F444W"])
        plan = ns["choose_sed_plan"](crv, ns["mapped_curve"](target_crv, .95, 4.0))
        assert plan["bands"] == ["F115W", "F200W"]
        assert np.isfinite(plan["weights"]).all()

        # Ingestion of source/target FITS must use memmapped small WCS cutouts.
        row = cat.iloc[0].copy()
        row["injection_ra"] = 53.0
        row["injection_dec"] = -27.8
        assert isinstance(ns["resolve_product"](bands["F115W"], row, "F115W")["seg_ext"], int)
        sci, err, sg, prod = ns["read_science_err_seg"](
            bands["F115W"], row, "F115W", 53.0, -27.8, 3.0)
        assert sci.bunit == "MJy/sr"
        assert 42 in sg
        assert sci.data.shape == err.shape == sg.shape

        # Confirm the handoff metadata preflight on synthetic DR5-like
        # source/target/segmentation products, without whole-mosaic reads.
        ns["PREFLIGHT_SAMPLE_ROWS"] = 1
        ns["PREFLIGHT_CHECK_SPECTRAL_SUPPORT"] = True
        ns["INPUT_CATALOG_PATH"] = str(root/"jades_catalog.fits")
        preflight = ns["run_preflight"]()
        assert "FAIL" not in preflight.status.values, (
            preflight[preflight.status=="FAIL"].to_string(index=False)
        )
        assert (root/"out"/"data_preflight.md").exists()
        print("SYNTHETIC JADES HANDOFF PREFLIGHT: PASS")

        # Test full real-image redshifting, noise, and PySersic MAP recovery.
        result = ns["run_case"](row, 4.0, "F444W", "42__z4__F444W", root/"out"/"cases"/"42__z4__F444W")
        assert result["status"] == "OK", result
        assert result["analytic_source_model_used"] is False
        assert result["source_real_pixels"] is True
        assert result["flux_conservation"]["relative_signed_flux_residual"] < .15
        assert "recovered_n" in result["refit"]
        assert (root/"out"/"cases"/"42__z4__F444W"/"04_target_injected_mjy_sr.fits").exists()
        print("SYNTHETIC JADES FITS + REAL-PIXEL + PySersic MAP TEST: PASS")

        # Separate science-mode smoke test. Small sample counts are used only
        # to exercise both NUTS output serialization and the native reference
        # fit; they are NOT suitable science posterior settings.
        ns["REFIT_MODE"] = "NUTS"
        ns["RUN_NATIVE_REFIT"] = True
        ns["PYSERSIC_WARMUP"] = 30
        ns["PYSERSIC_SAMPLES"] = 30
        result_nuts = ns["run_case"](
            row, 4.0, "F444W", "42__z4__F444W_NUTS",
            root/"out"/"cases"/"42__z4__F444W_NUTS",
        )
        assert result_nuts["status"] == "OK"
        assert result_nuts["native_wavelength_matched_reference_fit"] is not None
        assert "recovered_n" in result_nuts["refit"]
        assert "recovered_re_arcsec" in result_nuts["refit"]
        assert "recovered_q" in result_nuts["refit"]
        assert result_nuts["refit"].get("difference_from_native_reference") is not None
        print("SYNTHETIC JADES NUTS + NATIVE REFERENCE FIT TEST: PASS")


if __name__ == "__main__":
    run()
