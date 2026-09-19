from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits

from scripts.audit_gate_d_cosmosweb_source_shot_covariance_preflight import (
    assess_exact_identifiability,
    inventory_fits,
    run,
)


def _write_bundle(path: Path, *, include_variance: bool = False) -> None:
    sci_header = fits.Header()
    sci_header["BUNIT"] = "MJy/sr"
    sci_header["PIXAR_SR"] = 2.1e-14
    sci_header["EXPTIME"] = 1000.0
    sci_header["PHOTMJSR"] = 1.23
    hdus = [
        fits.PrimaryHDU(),
        fits.ImageHDU(np.ones((8, 8)), header=sci_header, name="SCI"),
        fits.ImageHDU(np.ones((8, 8)), name="ERR"),
        fits.ImageHDU(np.ones((8, 8)), name="WHT"),
    ]
    if include_variance:
        for name in ("VAR_POISSON", "VAR_RNOISE", "VAR_FLAT"):
            hdus.append(fits.ImageHDU(np.ones((8, 8)), name=name))
    fits.HDUList(hdus).writeto(path)


def test_final_mosaic_scalars_do_not_make_exact_source_shot_identifiable(tmp_path: Path):
    path = tmp_path / "mosaic.fits"
    _write_bundle(path, include_variance=False)
    inv = inventory_fits(path)
    assessment = assess_exact_identifiability(
        inv,
        representation="drizzled_mosaic",
        per_exposure_resampling_replay_available=False,
    )

    assert inv["sci_header_fields"]["BUNIT"] == "MJy/sr"
    assert inv["sci_header_fields"]["EXPTIME"] == 1000.0
    assert not assessment["exact_l1_source_shot_and_covariance_identifiable"]
    assert not assessment["independent_output_pixel_poisson_is_exact_truth"]
    assert any("exposure/detector-level" in item for item in assessment["missing_requirements"])
    assert any("per-exposure" in item for item in assessment["missing_requirements"])
    assert any("VAR_POISSON" in item for item in assessment["missing_requirements"])


def test_exact_sufficiency_requires_exposure_representation_variances_and_replay(tmp_path: Path):
    path = tmp_path / "exposure_like.fits"
    _write_bundle(path, include_variance=True)
    inv = inventory_fits(path)
    assessment = assess_exact_identifiability(
        inv,
        representation="exposure_level",
        per_exposure_resampling_replay_available=True,
    )
    assert assessment["exact_l1_source_shot_and_covariance_identifiable"]
    assert assessment["missing_requirements"] == []


def test_run_is_non_stochastic_and_records_no_mutations(tmp_path: Path):
    path = tmp_path / "mosaic.fits"
    out = tmp_path / "summary.json"
    _write_bundle(path)
    before = path.read_bytes()

    summary = run(path, out, representation="drizzled_mosaic")

    assert path.read_bytes() == before
    assert summary["scientific_outcome"] == "exact_source_shot_not_identifiable_from_frozen_l1_bundle"
    assert all(value is False for value in summary["mutations"].values())
    assert json.loads(out.read_text())["scientific_outcome"] == summary["scientific_outcome"]


def test_checksum_mismatch_is_a_hard_failure(tmp_path: Path):
    path = tmp_path / "mosaic.fits"
    _write_bundle(path)
    with pytest.raises(ValueError, match="checksum mismatch"):
        run(
            path,
            tmp_path / "summary.json",
            representation="drizzled_mosaic",
            expected_sha256="0" * 64,
        )


def test_unknown_representation_is_rejected(tmp_path: Path):
    path = tmp_path / "mosaic.fits"
    _write_bundle(path)
    inv = inventory_fits(path)
    with pytest.raises(ValueError, match="representation"):
        assess_exact_identifiability(inv, representation="unknown")
