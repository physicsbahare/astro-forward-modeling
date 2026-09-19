"""
Consolidated GOLD403 Galight/Lenstronomy validation helpers.

This file records the validated notebook code used during the passive-disk
artificial-redshifting project as of 2026-09-19.

USAGE
-----
This is intentionally an integration helper for the existing project notebook,
not a standalone data-discovery pipeline. Run it after the normal notebook
setup/helper cells:

    %run -i scripts/gold403_validation_notebook_cells.py

The interactive namespace must already define the project-specific catalog,
PSF/context, and Galight helper functions listed in REQUIRED_NOTEBOOK_GLOBALS.

Why this file exists
--------------------
Earlier experiments used a homemade analytic Sersic renderer. A noiseless
closed-loop test showed that its numerical convention could disagree strongly
with Galight/Lenstronomy. The validated production direction is therefore:

    catalog structural parameters
      -> Lenstronomy ImageModel truth
      -> target PSF
      -> clean or real context
      -> Galight recovery

The functions below preserve the exact clean-validation logic that isolated
that issue and established the need for a native-clean baseline and explicit
B/T identifiability flags.
"""

from __future__ import annotations

import copy
import inspect
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
import galsim
from astropy.io import fits
from astropy.cosmology import Planck18
from lenstronomy.ImSim.image_model import ImageModel
from lenstronomy.Util import param_util


REQUIRED_NOTEBOOK_GLOBALS = (
    "FittingSpecify",
    "PIX",
    "MODEL_NPIX",
    "Z_TARGET",
    "NSERSIC_MAX",
    "BT_MAX",
    "mapped_source_wavelength_um",
    "choose_model_morphology",
    "source_theta_for_model",
    "target_psf_for_model_context",
    "build_galight_data_process",
    "one_component_params",
    "pack_source_params",
    "run_galight_model",
    "bd_condition",
    "choose_contexts_for_object",
    "get_master_initialization",
    "_get_galsim_psfex",
    "psf_file",
)


def validate_notebook_environment(namespace: dict | None = None) -> None:
    """Fail early if the notebook integration helpers are unavailable."""
    ns = globals() if namespace is None else namespace
    missing = [name for name in REQUIRED_NOTEBOOK_GLOBALS if name not in ns]
    if missing:
        raise RuntimeError(
            "Missing required notebook globals: " + ", ".join(missing)
        )


def _safe_image_model(fit_spec):
    """Construct ImageModel using only arguments supported by local lenstronomy."""
    init_parameters = inspect.signature(ImageModel.__init__).parameters

    candidates = {
        "data_class": fit_spec.data_class,
        "psf_class": fit_spec.psf_class,
        "lens_light_model_class": fit_spec.lightModel,
        "point_source_class": fit_spec.pointSource,
        "kwargs_numerics": fit_spec.kwargs_numerics,
    }

    if "likelihood_mask" in init_parameters:
        candidates["likelihood_mask"] = (
            fit_spec.kwargs_likelihood["image_likelihood_mask_list"][0]
        )

    return ImageModel(
        **{
            key: value
            for key, value in candidates.items()
            if key in init_parameters
        }
    )


def _safe_image_call(image_model, kwargs_lens_light):
    """Render lens light with only API arguments supported by local lenstronomy."""
    parameters = inspect.signature(image_model.image).parameters
    candidates = {
        "kwargs_lens": None,
        "kwargs_source": None,
        "kwargs_lens_light": kwargs_lens_light,
        "kwargs_ps": None,
        "kwargs_extinction": None,
        "kwargs_special": None,
        "unconvolved": False,
        "source_add": False,
        "lens_light_add": True,
        "point_source_add": False,
    }
    return image_model.image(
        **{
            key: value
            for key, value in candidates.items()
            if key in parameters
        }
    )


def _normalize_truth(image: np.ndarray, total_flux: float) -> np.ndarray:
    image = np.asarray(image, dtype=float)
    if not np.all(np.isfinite(image)):
        raise RuntimeError("NONFINITE_TRUTH_IMAGE")
    total = float(np.sum(image))
    if not np.isfinite(total) or total <= 0:
        raise RuntimeError("INVALID_TRUTH_IMAGE_FLUX")
    return image * (float(total_flux) / total)


def _inside_bounds(value, lower, upper, frac: float = 0.01) -> float:
    lower = float(lower)
    upper = float(upper)
    width = upper - lower
    if width <= 0:
        return float(value)
    return float(np.clip(value, lower + frac * width, upper - frac * width))


# ============================================================================
# EXACT SINGLE-SERSIC CLOSED LOOP
# ============================================================================


def make_exact_lenstronomy_single_truth(
    row,
    target_filter,
    context_row,
    *,
    total_flux: float = 1.0e4,
):
    """
    Generate a noiseless single-Sersic truth image with Lenstronomy itself.

    This is the canonical renderer/fitter-convention test. The truth parameter
    dictionary is copied directly from the same Galight source_params structure
    used by the fit, eliminating independent e1/e2/PA convention differences.
    """
    oid = int(row["id"])
    zs = float(row["z"])

    mapped_lambda = mapped_source_wavelength_um(target_filter, zs)
    morph = choose_model_morphology(row, mapped_lambda)

    angular_scale = float(
        Planck18.angular_diameter_distance(zs).value
        / Planck18.angular_diameter_distance(Z_TARGET).value
    )

    re_target = float(morph["single_re_arcsec"]) * angular_scale
    n_truth = float(morph["single_n"])
    q_truth = float(morph["single_q"])
    theta = float(source_theta_for_model(oid))

    radius_pix = max(40, int(np.ceil(6.0 * re_target / PIX)))
    npix = min(2 * radius_pix + 1, int(MODEL_NPIX))
    if npix % 2 == 0:
        npix -= 1
    center = npix // 2

    target_psf = target_psf_for_model_context(context_row, target_filter)

    blank = np.zeros((npix, npix), dtype=float)
    err = np.ones_like(blank)
    seg = np.zeros_like(blank, dtype=int)

    target_meta = {
        "label": -999999,
        "x": float(center),
        "y": float(center),
        "q": q_truth,
        "theta": theta,
        "re_pix": max(1.0, re_target / PIX),
        "npix": 1,
    }

    component = one_component_params(
        target_meta,
        npix,
        re_target,
        n_truth,
        q_truth,
        fixed_n=None,
    )
    source_params = pack_source_params([component])

    dp_blank, _ = build_galight_data_process(
        blank,
        err,
        seg,
        target_psf,
        target_meta,
        neighbour_metas=[],
        model_labels=[],
    )

    fit_spec = FittingSpecify(dp_blank, sersic_major_axis=True)
    fit_spec.prepare_fitting_seq(
        supersampling_factor=2,
        psf_data=dp_blank.PSF_list[0],
        extend_source_model=["SERSIC_ELLIPSE"],
        point_source_num=0,
        source_params=source_params,
        condition=None,
        mpi=False,
    )

    kwargs_truth = copy.deepcopy(source_params[0])
    kwargs_truth[0]["amp"] = 1.0

    image_model = _safe_image_model(fit_spec)
    truth_image = _normalize_truth(
        _safe_image_call(image_model, kwargs_truth),
        total_flux,
    )

    truth = {
        "mapped_source_wavelength_um": float(mapped_lambda),
        "angular_scale": angular_scale,
        "truth_n": n_truth,
        "truth_re": re_target,
        "truth_q": q_truth,
        "theta": theta,
        "npix": int(npix),
        "re_over_pixel": float(re_target / PIX),
        "re_over_f444w_psf": float(re_target / 0.145),
    }

    return truth_image, target_psf, target_meta, source_params, truth


def run_exact_lenstronomy_single_test(
    row,
    target_filter,
    context_row,
    *,
    pso_repeats: int = 1,
    total_flux: float = 1.0e4,
    savename=None,
):
    """Fit exact Lenstronomy truth with the same one-component Galight model."""
    image, psf, target_meta, source_params, truth = (
        make_exact_lenstronomy_single_truth(
            row,
            target_filter,
            context_row,
            total_flux=total_flux,
        )
    )

    dp, _ = build_galight_data_process(
        image,
        np.ones_like(image),
        np.zeros_like(image, dtype=int),
        psf,
        target_meta,
        neighbour_metas=[],
        model_labels=[],
    )

    fit = run_galight_model(
        dp,
        copy.deepcopy(source_params),
        n_components=1,
        savename=savename,
        condition=None,
        pso_repeats=int(pso_repeats),
    )

    result = fit.final_result_galaxy[0]
    fit_n = float(result["n_sersic"])
    fit_re = float(result["R_sersic"])
    fit_q = float(result["q"])

    return {
        "id": int(row["id"]),
        "z_source": float(row["z"]),
        "filter": str(target_filter),
        **truth,
        "fit_n": fit_n,
        "fit_re": fit_re,
        "fit_q": fit_q,
        "delta_n": fit_n - truth["truth_n"],
        "delta_re_frac": fit_re / truth["truth_re"] - 1.0,
        "delta_q": fit_q - truth["truth_q"],
        "chisq": float(fit.reduced_Chisq),
        "status": "OK",
    }


def make_perturbed_single_source_params(
    source_params,
    *,
    re_factor: float = 1.30,
    n_factor: float = 1.30,
    q_delta: float = 0.12,
    center_x_pix: float = 1.0,
    center_y_pix: float = -1.0,
):
    """Perturb only the initial guess while preserving fit bounds/fixed values."""
    p = copy.deepcopy(source_params)
    init = p[0][0]
    fixed = p[2][0]
    lower = p[3][0]
    upper = p[4][0]

    init["R_sersic"] = _inside_bounds(
        float(init["R_sersic"]) * re_factor,
        lower["R_sersic"],
        upper["R_sersic"],
    )

    if "n_sersic" not in fixed:
        init["n_sersic"] = _inside_bounds(
            float(init["n_sersic"]) * n_factor,
            lower["n_sersic"],
            upper["n_sersic"],
        )

    phi, q_old = param_util.ellipticity2phi_q(
        float(init["e1"]),
        float(init["e2"]),
    )
    q_new = q_old + q_delta if q_old <= 0.70 else q_old - q_delta
    q_new = float(np.clip(q_new, 0.15, 0.95))
    e1, e2 = param_util.phi_q2_ellipticity(phi, q_new)

    init["e1"] = _inside_bounds(e1, lower["e1"], upper["e1"])
    init["e2"] = _inside_bounds(e2, lower["e2"], upper["e2"])
    init["center_x"] = _inside_bounds(
        float(init["center_x"]) + center_x_pix * PIX,
        lower["center_x"],
        upper["center_x"],
    )
    init["center_y"] = _inside_bounds(
        float(init["center_y"]) + center_y_pix * PIX,
        lower["center_y"],
        upper["center_y"],
    )
    return p


def run_perturbed_lenstronomy_test(
    row,
    target_filter,
    context_row,
    *,
    pso_repeats: int = 2,
    total_flux: float = 1.0e4,
    savename=None,
):
    """Closed-loop single-Sersic test with deliberately wrong starting values."""
    image, psf, target_meta, source_params, truth = (
        make_exact_lenstronomy_single_truth(
            row,
            target_filter,
            context_row,
            total_flux=total_flux,
        )
    )

    start = make_perturbed_single_source_params(source_params)
    init = start[0][0]
    _, init_q = param_util.ellipticity2phi_q(init["e1"], init["e2"])

    dp, _ = build_galight_data_process(
        image,
        np.ones_like(image),
        np.zeros_like(image, dtype=int),
        psf,
        target_meta,
        neighbour_metas=[],
        model_labels=[],
    )

    fit = run_galight_model(
        dp,
        start,
        n_components=1,
        savename=savename,
        condition=None,
        pso_repeats=int(pso_repeats),
    )

    result = fit.final_result_galaxy[0]
    fit_n = float(result["n_sersic"])
    fit_re = float(result["R_sersic"])
    fit_q = float(result["q"])

    return {
        "id": int(row["id"]),
        "z_source": float(row["z"]),
        "filter": str(target_filter),
        **truth,
        "start_n": float(init["n_sersic"]),
        "start_re": float(init["R_sersic"]),
        "start_q": float(init_q),
        "start_center_x": float(init["center_x"]),
        "start_center_y": float(init["center_y"]),
        "fit_n": fit_n,
        "fit_re": fit_re,
        "fit_q": fit_q,
        "delta_n": fit_n - truth["truth_n"],
        "delta_re_frac": fit_re / truth["truth_re"] - 1.0,
        "delta_q": fit_q - truth["truth_q"],
        "chisq": float(fit.reduced_Chisq),
        "status": "OK",
    }


# ============================================================================
# EXACT B+D TRUTH
# ============================================================================


def _render_component(image_model, kwargs_components, component_index: int):
    kwargs_use = copy.deepcopy(kwargs_components)
    for comp in kwargs_use:
        comp["amp"] = 1.0

    parameters = inspect.signature(
        image_model.lens_surface_brightness
    ).parameters

    candidates = {
        "kwargs_lens_light": kwargs_use,
        "unconvolved": False,
        "k": int(component_index),
    }

    image = image_model.lens_surface_brightness(
        **{
            key: value
            for key, value in candidates.items()
            if key in parameters
        }
    )
    image = np.asarray(image, dtype=float)
    if not np.all(np.isfinite(image)):
        raise RuntimeError("NONFINITE_COMPONENT")
    total = float(np.sum(image))
    if not np.isfinite(total) or total <= 0:
        raise RuntimeError("INVALID_COMPONENT_FLUX")
    return image / total


def make_exact_lenstronomy_bd_truth(
    row,
    target_filter,
    context_row,
    *,
    total_flux: float = 1.0e4,
):
    """Build exact z=target B+D truth with disk n=1 and bulge n=4."""
    oid = int(row["id"])
    zs = float(row["z"])
    mapped_lambda = mapped_source_wavelength_um(target_filter, zs)
    morph = choose_model_morphology(row, mapped_lambda)

    angular_scale = float(
        Planck18.angular_diameter_distance(zs).value
        / Planck18.angular_diameter_distance(Z_TARGET).value
    )

    rd = float(morph["disk_re_arcsec"]) * angular_scale
    rb = float(morph["bulge_re_arcsec"]) * angular_scale
    single_re = float(morph["single_re_arcsec"]) * angular_scale
    bt_truth = float(morph["bt"])
    disk_q = float(morph["disk_q"])
    bulge_q = float(morph["bulge_q"])
    theta = float(source_theta_for_model(oid))

    npix = int(MODEL_NPIX)
    if npix % 2 == 0:
        npix -= 1
    center = npix // 2

    psf = target_psf_for_model_context(context_row, target_filter)
    blank = np.zeros((npix, npix), dtype=float)
    err = np.ones_like(blank)
    seg = np.zeros_like(blank, dtype=int)

    target_meta = {
        "label": -999999,
        "x": float(center),
        "y": float(center),
        "q": disk_q,
        "theta": theta,
        "re_pix": max(1.0, rd / PIX),
        "npix": 1,
    }

    disk_component = one_component_params(
        target_meta, npix, rd, 1.0, disk_q, fixed_n=1.0
    )
    bulge_component = one_component_params(
        target_meta, npix, rb, 4.0, bulge_q, fixed_n=4.0
    )
    source_params = pack_source_params([disk_component, bulge_component])

    dp_blank, _ = build_galight_data_process(
        blank,
        err,
        seg,
        psf,
        target_meta,
        neighbour_metas=[],
        model_labels=[],
    )

    fit_spec = FittingSpecify(dp_blank, sersic_major_axis=True)
    fit_spec.prepare_fitting_seq(
        supersampling_factor=2,
        psf_data=dp_blank.PSF_list[0],
        extend_source_model=["SERSIC_ELLIPSE", "SERSIC_ELLIPSE"],
        point_source_num=0,
        source_params=source_params,
        condition=None,
        mpi=False,
    )

    image_model = _safe_image_model(fit_spec)
    kwargs_components = copy.deepcopy(source_params[0])

    disk_image = _render_component(image_model, kwargs_components, 0)
    bulge_image = _render_component(image_model, kwargs_components, 1)

    truth_image = (1.0 - bt_truth) * disk_image + bt_truth * bulge_image
    truth_image = _normalize_truth(truth_image, total_flux)

    truth = {
        "mapped_source_wavelength_um": float(mapped_lambda),
        "angular_scale": angular_scale,
        "published_single_n": float(morph["single_n"]),
        "published_single_re_arcsec": float(morph["single_re_arcsec"]),
        "target_single_re_arcsec": single_re,
        "truth_bt": bt_truth,
        "truth_disk_re": rd,
        "truth_bulge_re": rb,
        "truth_disk_q": disk_q,
        "truth_bulge_q": bulge_q,
        "theta": theta,
        "npix": int(npix),
        "disk_re_over_pixel": float(rd / PIX),
        "bulge_re_over_pixel": float(rb / PIX),
        "disk_re_over_psf": float(rd / 0.145),
        "bulge_re_over_psf": float(rb / 0.145),
        "catalog_disk_classification": bool(
            float(morph["single_n"]) < NSERSIC_MAX and bt_truth < BT_MAX
        ),
    }

    return truth_image, psf, target_meta, source_params, truth


def perturb_bd_source_params(source_params):
    """Perturb B+D start: disk Re high, bulge Re low, q and centers offset."""
    p = copy.deepcopy(source_params)
    factors = [1.30, 0.70]
    q_changes = [+0.10, -0.10]

    for i in range(2):
        init = p[0][i]
        lower = p[3][i]
        upper = p[4][i]

        init["R_sersic"] = _inside_bounds(
            float(init["R_sersic"]) * factors[i],
            lower["R_sersic"],
            upper["R_sersic"],
        )

        phi, q = param_util.ellipticity2phi_q(
            float(init["e1"]), float(init["e2"])
        )
        q_new = float(np.clip(q + q_changes[i], 0.15, 0.95))
        e1, e2 = param_util.phi_q2_ellipticity(phi, q_new)
        init["e1"] = _inside_bounds(e1, lower["e1"], upper["e1"])
        init["e2"] = _inside_bounds(e2, lower["e2"], upper["e2"])
        init["center_x"] = _inside_bounds(
            float(init["center_x"]) + PIX,
            lower["center_x"],
            upper["center_x"],
        )
        init["center_y"] = _inside_bounds(
            float(init["center_y"]) - PIX,
            lower["center_y"],
            upper["center_y"],
        )
    return p


def make_single_start_for_bd_truth(row, truth, target_meta, npix):
    mapped_lambda = float(truth["mapped_source_wavelength_um"])
    morph = choose_model_morphology(row, mapped_lambda)

    component = one_component_params(
        target_meta,
        npix,
        float(truth["target_single_re_arcsec"]),
        float(truth["published_single_n"]),
        float(morph["single_q"]),
        fixed_n=None,
    )
    p = pack_source_params([component])

    init = p[0][0]
    lower = p[3][0]
    upper = p[4][0]

    init["R_sersic"] = _inside_bounds(
        float(init["R_sersic"]) * 1.30,
        lower["R_sersic"],
        upper["R_sersic"],
    )
    init["n_sersic"] = _inside_bounds(
        float(init["n_sersic"]) * 1.30,
        lower["n_sersic"],
        upper["n_sersic"],
    )
    init["center_x"] = _inside_bounds(
        float(init["center_x"]) + PIX,
        lower["center_x"],
        upper["center_x"],
    )
    init["center_y"] = _inside_bounds(
        float(init["center_y"]) - PIX,
        lower["center_y"],
        upper["center_y"],
    )
    return p


def run_exact_bd_validation(
    row,
    target_filter,
    context_row,
    *,
    pso_repeats: int = 2,
    total_flux: float = 1.0e4,
    diag_root: str | Path | None = None,
):
    """Fit exact z=target B+D truth with B+D and single-Sersic models."""
    image, psf, target_meta, bd_source_params, truth = (
        make_exact_lenstronomy_bd_truth(
            row,
            target_filter,
            context_row,
            total_flux=total_flux,
        )
    )

    dp, _ = build_galight_data_process(
        image,
        np.ones_like(image),
        np.zeros_like(image, dtype=int),
        psf,
        target_meta,
        neighbour_metas=[],
        model_labels=[],
    )

    oid = int(row["id"])
    diag_root = Path(diag_root) if diag_root is not None else None
    if diag_root is not None:
        diag_root.mkdir(parents=True, exist_ok=True)

    fit_bd = run_galight_model(
        dp,
        perturb_bd_source_params(bd_source_params),
        n_components=2,
        savename=(
            diag_root / f"ID{oid}_{target_filter}_BD"
            if diag_root is not None
            else None
        ),
        condition=bd_condition,
        pso_repeats=int(pso_repeats),
    )

    disk = fit_bd.final_result_galaxy[0]
    bulge = fit_bd.final_result_galaxy[1]
    fd = float(disk["flux_sersic_model"])
    fb = float(bulge["flux_sersic_model"])
    recovered_bt = fb / (fb + fd)

    fit_single = run_galight_model(
        dp,
        make_single_start_for_bd_truth(row, truth, target_meta, image.shape[0]),
        n_components=1,
        savename=(
            diag_root / f"ID{oid}_{target_filter}_single_on_BD"
            if diag_root is not None
            else None
        ),
        condition=None,
        pso_repeats=int(pso_repeats),
    )

    single = fit_single.final_result_galaxy[0]
    clean_single_n = float(single["n_sersic"])
    clean_single_re = float(single["R_sersic"])

    clean_model_disk = bool(
        clean_single_n < NSERSIC_MAX and recovered_bt < BT_MAX
    )

    return {
        "id": oid,
        "z_source": float(row["z"]),
        "filter": str(target_filter),
        **truth,
        "recovered_bt": recovered_bt,
        "delta_bt": recovered_bt - truth["truth_bt"],
        "recovered_disk_re": float(disk["R_sersic"]),
        "delta_disk_re_frac": (
            float(disk["R_sersic"]) / truth["truth_disk_re"] - 1.0
        ),
        "recovered_bulge_re": float(bulge["R_sersic"]),
        "delta_bulge_re_frac": (
            float(bulge["R_sersic"]) / truth["truth_bulge_re"] - 1.0
        ),
        "bd_chisq": float(fit_bd.reduced_Chisq),
        "clean_single_n_from_bd": clean_single_n,
        "delta_clean_n_vs_published": (
            clean_single_n - truth["published_single_n"]
        ),
        "clean_single_re_from_bd": clean_single_re,
        "single_chisq": float(fit_single.reduced_Chisq),
        "clean_model_disk_classification": clean_model_disk,
        "classification_same_as_catalog": bool(
            clean_model_disk == truth["catalog_disk_classification"]
        ),
        "status": "OK",
    }


# ============================================================================
# NATIVE CLEAN BASELINE
# ============================================================================


def native_psf_for_object(row, source_filter):
    """Evaluate the native/source-band PSF at the object's actual position."""
    oid = int(row["id"])
    info = get_master_initialization(row)
    tile = str(info["tile"])
    filt = str(source_filter)

    if filt == "F814W":
        if "source_psf_for_position" not in globals():
            raise RuntimeError("F814W native PSF helper unavailable")
        psf = source_psf_for_position(
            tile,
            filt,
            float(info["ra"]),
            float(info["dec"]),
        )
        return _normalize_truth(psf, 1.0)

    model = _get_galsim_psfex(tile, filt)
    pos = galsim.PositionD(
        float(info["x_image_0"]) + 1.0,
        float(info["y_image_0"]) + 1.0,
    )
    psf_obj = model.getPSF(pos)

    path = psf_file(tile, filt)
    with fits.open(path, memmap=False) as hdul:
        hdr = hdul[1].header
        axis = int(hdr["PSFAXIS1"])
        samp = float(hdr["PSF_SAMP"])

    native_side = int(np.ceil(axis * samp))
    if native_side % 2 == 0:
        native_side += 1

    image = psf_obj.drawImage(
        nx=native_side,
        ny=native_side,
        scale=1.0,
        method="no_pixel",
    )
    return _normalize_truth(np.asarray(image.array, dtype=float), 1.0)


def make_native_clean_bd_truth(
    row,
    *,
    target_filter_for_mapping: str = "F444W",
    total_flux: float = 1.0e4,
):
    """Create the same chosen B+D structural model at its native angular size."""
    oid = int(row["id"])
    zs = float(row["z"])

    mapped_lambda = mapped_source_wavelength_um(
        target_filter_for_mapping, zs
    )
    morph = choose_model_morphology(row, mapped_lambda)
    morph_filter = str(morph["morph_filter"])

    rd = float(morph["disk_re_arcsec"])
    rb = float(morph["bulge_re_arcsec"])
    single_re = float(morph["single_re_arcsec"])
    published_n = float(morph["single_n"])
    published_q = float(morph["single_q"])
    bt_truth = float(morph["bt"])
    disk_q = float(morph["disk_q"])
    bulge_q = float(morph["bulge_q"])
    theta = float(source_theta_for_model(oid))

    npix = int(MODEL_NPIX)
    if npix % 2 == 0:
        npix -= 1
    center = npix // 2

    psf = native_psf_for_object(row, morph_filter)

    blank = np.zeros((npix, npix), dtype=float)
    err = np.ones_like(blank)
    seg = np.zeros_like(blank, dtype=int)

    target_meta = {
        "label": -999999,
        "x": float(center),
        "y": float(center),
        "q": disk_q,
        "theta": theta,
        "re_pix": max(1.0, rd / PIX),
        "npix": 1,
    }

    disk_component = one_component_params(
        target_meta, npix, rd, 1.0, disk_q, fixed_n=1.0
    )
    bulge_component = one_component_params(
        target_meta, npix, rb, 4.0, bulge_q, fixed_n=4.0
    )
    source_params = pack_source_params([disk_component, bulge_component])

    dp_blank, _ = build_galight_data_process(
        blank,
        err,
        seg,
        psf,
        target_meta,
        neighbour_metas=[],
        model_labels=[],
    )

    fit_spec = FittingSpecify(dp_blank, sersic_major_axis=True)
    fit_spec.prepare_fitting_seq(
        supersampling_factor=2,
        psf_data=dp_blank.PSF_list[0],
        extend_source_model=["SERSIC_ELLIPSE", "SERSIC_ELLIPSE"],
        point_source_num=0,
        source_params=source_params,
        condition=None,
        mpi=False,
    )

    image_model = _safe_image_model(fit_spec)
    kwargs_components = copy.deepcopy(source_params[0])

    disk_image = _render_component(image_model, kwargs_components, 0)
    bulge_image = _render_component(image_model, kwargs_components, 1)

    truth_image = _normalize_truth(
        (1.0 - bt_truth) * disk_image + bt_truth * bulge_image,
        total_flux,
    )

    truth = {
        "morph_filter": morph_filter,
        "mapped_source_wavelength_um": float(mapped_lambda),
        "published_single_n": published_n,
        "published_single_re": single_re,
        "published_single_q": published_q,
        "truth_bt": bt_truth,
        "truth_disk_re": rd,
        "truth_bulge_re": rb,
        "truth_disk_q": disk_q,
        "truth_bulge_q": bulge_q,
        "theta": theta,
        "npix": int(npix),
        "native_disk_re_over_pixel": float(rd / PIX),
        "native_bulge_re_over_pixel": float(rb / PIX),
    }

    return truth_image, psf, target_meta, source_params, truth


def make_native_single_start(truth, target_meta, npix):
    component = one_component_params(
        target_meta,
        npix,
        float(truth["published_single_re"]),
        float(truth["published_single_n"]),
        float(truth["published_single_q"]),
        fixed_n=None,
    )
    p = pack_source_params([component])
    init = p[0][0]
    lower = p[3][0]
    upper = p[4][0]

    init["R_sersic"] = _inside_bounds(
        float(init["R_sersic"]) * 1.30,
        lower["R_sersic"],
        upper["R_sersic"],
    )
    init["n_sersic"] = _inside_bounds(
        float(init["n_sersic"]) * 1.30,
        lower["n_sersic"],
        upper["n_sersic"],
    )
    init["center_x"] = _inside_bounds(
        float(init["center_x"]) + PIX,
        lower["center_x"],
        upper["center_x"],
    )
    init["center_y"] = _inside_bounds(
        float(init["center_y"]) - PIX,
        lower["center_y"],
        upper["center_y"],
    )
    return p


def run_native_clean_baseline(
    row,
    *,
    pso_repeats: int = 2,
    total_flux: float = 1.0e4,
    diag_root: str | Path | None = None,
):
    """Fit the chosen structural model at native angular size before redshifting."""
    image, psf, target_meta, source_params, truth = make_native_clean_bd_truth(
        row,
        total_flux=total_flux,
    )

    dp, _ = build_galight_data_process(
        image,
        np.ones_like(image),
        np.zeros_like(image, dtype=int),
        psf,
        target_meta,
        neighbour_metas=[],
        model_labels=[],
    )

    oid = int(row["id"])
    diag_root = Path(diag_root) if diag_root is not None else None
    if diag_root is not None:
        diag_root.mkdir(parents=True, exist_ok=True)

    fit_bd = run_galight_model(
        dp,
        perturb_bd_source_params(source_params),
        n_components=2,
        savename=(
            diag_root / f"ID{oid}_{truth['morph_filter']}_native_BD"
            if diag_root is not None
            else None
        ),
        condition=bd_condition,
        pso_repeats=int(pso_repeats),
    )

    disk = fit_bd.final_result_galaxy[0]
    bulge = fit_bd.final_result_galaxy[1]
    fd = float(disk["flux_sersic_model"])
    fb = float(bulge["flux_sersic_model"])
    recovered_bt = fb / (fb + fd)

    fit_single = run_galight_model(
        dp,
        make_native_single_start(truth, target_meta, image.shape[0]),
        n_components=1,
        savename=(
            diag_root / f"ID{oid}_{truth['morph_filter']}_native_single_on_BD"
            if diag_root is not None
            else None
        ),
        condition=None,
        pso_repeats=int(pso_repeats),
    )

    single = fit_single.final_result_galaxy[0]
    native_single_n = float(single["n_sersic"])

    return {
        "id": oid,
        "z_source": float(row["z"]),
        **truth,
        "native_recovered_bt": recovered_bt,
        "native_delta_bt": recovered_bt - truth["truth_bt"],
        "native_recovered_disk_re": float(disk["R_sersic"]),
        "native_recovered_bulge_re": float(bulge["R_sersic"]),
        "native_single_n_from_bd": native_single_n,
        "native_single_re_from_bd": float(single["R_sersic"]),
        "native_delta_n_vs_published": (
            native_single_n - truth["published_single_n"]
        ),
        "native_clean_disk_classification": bool(
            native_single_n < NSERSIC_MAX and recovered_bt < BT_MAX
        ),
        "native_bd_chisq": float(fit_bd.reduced_Chisq),
        "native_single_chisq": float(fit_single.reduced_Chisq),
        "status": "OK",
    }


# ============================================================================
# CLEAN IDENTIFIABILITY SWEEP
# ============================================================================


def select_clean_sweep_ids(
    gold,
    *,
    n_sample: int = 30,
    target_filter: str = "F444W",
    force_ids=(751217, 322095, 162363),
):
    """
    Select a deterministic sample spanning source z and predicted z=3 disk size.

    This intentionally avoids random sampling so the validation set is stable.
    """
    rows = []
    for _, row in gold.iterrows():
        try:
            zs = float(row["z"])
            mapped_lambda = mapped_source_wavelength_um(target_filter, zs)
            morph = choose_model_morphology(row, mapped_lambda)
            angular_scale = float(
                Planck18.angular_diameter_distance(zs).value
                / Planck18.angular_diameter_distance(Z_TARGET).value
            )
            rows.append(
                {
                    "id": int(row["id"]),
                    "z": zs,
                    "z3_disk_re_pix": (
                        float(morph["disk_re_arcsec"]) * angular_scale / PIX
                    ),
                    "z3_bulge_re_pix": (
                        float(morph["bulge_re_arcsec"]) * angular_scale / PIX
                    ),
                }
            )
        except Exception:
            continue

    frame = pd.DataFrame(rows)
    frame["rank_z"] = frame["z"].rank(pct=True)
    frame["rank_size"] = frame["z3_disk_re_pix"].rank(pct=True)

    # Interleave the two ranks to avoid selecting only along one monotonic axis.
    frame["selection_key"] = 0.5 * frame["rank_z"] + 0.5 * frame["rank_size"]
    frame = frame.sort_values(
        ["selection_key", "rank_z", "rank_size", "id"]
    ).reset_index(drop=True)

    idx = np.unique(
        np.linspace(0, len(frame) - 1, int(n_sample)).astype(int)
    )
    ids = frame.iloc[idx]["id"].astype(int).tolist()

    available = set(gold["id"].astype(int).tolist())
    for oid in force_ids:
        if int(oid) in available and int(oid) not in ids:
            ids.append(int(oid))

    return list(dict.fromkeys(ids))


def run_clean_identifiability_sweep(
    gold,
    *,
    output_csv,
    n_sample: int = 30,
    target_filter: str = "F444W",
    bt_identify_tol: float = 0.10,
    native_n_consistency_tol: float = 0.50,
    pso_repeats: int = 2,
    diag_root: str | Path | None = None,
):
    """
    Run native-clean -> z=3-clean structural identifiability sweep.

    The B/T tolerance here is a diagnostic flag only. It must not silently
    become the final paper threshold without reviewing the sweep.
    """
    ids = select_clean_sweep_ids(
        gold,
        n_sample=n_sample,
        target_filter=target_filter,
    )

    rows = []
    for number, oid in enumerate(ids, start=1):
        match = gold.loc[gold["id"].astype(int) == int(oid)]
        if len(match) == 0:
            continue
        row = match.iloc[0]

        print(
            f"\n{'=' * 72}\n"
            f"CLEAN SWEEP {number}/{len(ids)} ID {oid}\n"
            f"{'=' * 72}"
        )

        try:
            native = run_native_clean_baseline(
                row,
                pso_repeats=pso_repeats,
                diag_root=(
                    Path(diag_root) / "native"
                    if diag_root is not None
                    else None
                ),
            )

            context = choose_contexts_for_object(int(oid), 1).iloc[0]
            z3 = run_exact_bd_validation(
                row,
                target_filter,
                context,
                pso_repeats=pso_repeats,
                diag_root=(
                    Path(diag_root) / "z3"
                    if diag_root is not None
                    else None
                ),
            )

            bt_native_error = abs(
                float(native["native_recovered_bt"])
                - float(native["truth_bt"])
            )
            bt_z3_error = abs(
                float(z3["recovered_bt"])
                - float(z3["truth_bt"])
            )

            native_disk = bool(native["native_clean_disk_classification"])
            z3_disk = bool(z3["clean_model_disk_classification"])

            record = {
                "id": int(oid),
                "z_source": float(row["z"]),
                "morph_filter": native["morph_filter"],
                "published_n": float(native["published_single_n"]),
                "native_clean_n": float(native["native_single_n_from_bd"]),
                "z3_clean_n": float(z3["clean_single_n_from_bd"]),
                "delta_n_catalog_to_native": (
                    float(native["native_single_n_from_bd"])
                    - float(native["published_single_n"])
                ),
                "delta_n_native_to_z3": (
                    float(z3["clean_single_n_from_bd"])
                    - float(native["native_single_n_from_bd"])
                ),
                "native_model_n_consistent": bool(
                    abs(
                        float(native["native_single_n_from_bd"])
                        - float(native["published_single_n"])
                    )
                    <= native_n_consistency_tol
                ),
                "input_bt": float(native["truth_bt"]),
                "native_recovered_bt": float(
                    native["native_recovered_bt"]
                ),
                "z3_recovered_bt": float(z3["recovered_bt"]),
                "bt_native_abs_error": float(bt_native_error),
                "bt_z3_abs_error": float(bt_z3_error),
                "bt_native_identifiable": bool(
                    bt_native_error <= bt_identify_tol
                ),
                "bt_z3_identifiable": bool(
                    bt_z3_error <= bt_identify_tol
                ),
                "native_disk_re_pix": float(
                    native["native_disk_re_over_pixel"]
                ),
                "native_bulge_re_pix": float(
                    native["native_bulge_re_over_pixel"]
                ),
                "z3_disk_re_pix": float(z3["disk_re_over_pixel"]),
                "z3_bulge_re_pix": float(z3["bulge_re_over_pixel"]),
                "native_clean_disk": native_disk,
                "z3_clean_disk": z3_disk,
                "resolution_classification_flip": bool(
                    native_disk != z3_disk
                ),
                "native_single_chisq": float(
                    native["native_single_chisq"]
                ),
                "native_bd_chisq": float(native["native_bd_chisq"]),
                "z3_single_chisq": float(z3["single_chisq"]),
                "z3_bd_chisq": float(z3["bd_chisq"]),
                "status": "OK",
            }

            print(
                "n:",
                round(record["native_clean_n"], 3),
                "->",
                round(record["z3_clean_n"], 3),
                "| B/T identifiable native/z3:",
                record["bt_native_identifiable"],
                record["bt_z3_identifiable"],
                "| flip:",
                record["resolution_classification_flip"],
            )

        except Exception as exc:
            traceback.print_exc()
            record = {
                "id": int(oid),
                "z_source": float(row["z"]),
                "status": "ERROR",
                "error": repr(exc),
            }

        rows.append(record)

    frame = pd.DataFrame(rows)
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_csv, index=False)
    return frame


def summarize_clean_sweep(frame: pd.DataFrame) -> None:
    """Print a compact diagnostic summary without inventing science thresholds."""
    print("\nSTATUS")
    print(frame["status"].value_counts(dropna=False))

    good = frame.loc[frame["status"] == "OK"].copy()
    if len(good) == 0:
        return

    print("\nNative B/T identifiable")
    print(good["bt_native_identifiable"].value_counts(dropna=False))

    print("\nz=3 B/T identifiable")
    print(good["bt_z3_identifiable"].value_counts(dropna=False))

    print("\nResolution-only classification flips")
    print(good["resolution_classification_flip"].value_counts(dropna=False))

    print("\nNative synthetic n consistent with catalog")
    print(good["native_model_n_consistent"].value_counts(dropna=False))

    print(
        "\nMedian |native -> z3 delta n| =",
        np.nanmedian(np.abs(good["delta_n_native_to_z3"])),
    )

    print("\nLargest |native -> z3 delta n| cases")
    cols = [
        "id",
        "z_source",
        "morph_filter",
        "native_disk_re_pix",
        "native_bulge_re_pix",
        "z3_disk_re_pix",
        "z3_bulge_re_pix",
        "published_n",
        "native_clean_n",
        "z3_clean_n",
        "delta_n_native_to_z3",
        "input_bt",
        "native_recovered_bt",
        "z3_recovered_bt",
        "bt_native_identifiable",
        "bt_z3_identifiable",
        "resolution_classification_flip",
    ]
    show = good[cols].copy()
    show["abs_delta_n"] = np.abs(show["delta_n_native_to_z3"])
    print(show.sort_values("abs_delta_n", ascending=False).head(15).to_string(index=False))


# ============================================================================
# KNOWN DIAGNOSTIC RECEIPTS
# ============================================================================


KNOWN_DIAGNOSTICS = {
    751217: {
        "z_source": 0.1009,
        "published_n": 2.254607,
        "native_clean_n": 1.525468,
        "z3_clean_n": 8.797613,
        "input_bt": 0.268124,
        "native_bt": 0.077148,
        "z3_bt": 0.092379,
        "native_disk_re_pix": 1.716355,
        "z3_disk_re_pix": 0.418394,
        "native_bulge_re_pix": 0.333353,
        "z3_bulge_re_pix": 0.081261,
    },
    322095: {
        "z_source": 0.8709,
        "published_n": 1.413573,
        "native_clean_n": 1.459759,
        "z3_clean_n": 1.431337,
        "input_bt": 0.303099,
        "native_bt": 0.312616,
        "z3_bt": 0.311619,
    },
    162363: {
        "z_source": 2.9478,
        "published_n": 0.774276,
        "native_clean_n": 1.049920,
        "z3_clean_n": 1.049680,
        "input_bt": 0.011345,
        "native_bt": 0.008410,
        "z3_bt": 0.005877,
    },
}
