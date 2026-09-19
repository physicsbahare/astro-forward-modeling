#!/usr/bin/env python3
"""Gate D1n-d: Gaia-vet the already frozen D1n-b compact-source support set."""
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS
import astropy.units as u

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "d1nb", ROOT / "scripts" / "run_gate_d_cosmosweb_empirical_psf_support.py"
)
d1nb = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(d1nb)

MATCH_RADIUS_ARCSEC = 0.15
TARGET_EPOCH_JYEAR = 2023.5
GAIA_TABLE = "gaiadr3.gaia_source"
GAIA_COLUMNS = (
    "source_id", "ra", "dec", "ref_epoch", "pmra", "pmdec", "parallax",
    "phot_g_mean_mag", "ruwe"
)

def candidate_skycoords(real_fits: Path, rows: list[dict]) -> SkyCoord:
    with fits.open(real_fits, mode="readonly") as h:
        w = WCS(h["SCI"].header).celestial
    x = np.asarray([r["xcentroid"] for r in rows], dtype=float)
    y = np.asarray([r["ycentroid"] for r in rows], dtype=float)
    return w.pixel_to_world(x, y)

def query_gaia_for_cutout(real_fits: Path):
    from astroquery.gaia import Gaia
    with fits.open(real_fits, mode="readonly") as h:
        data = h["SCI"].data
        w = WCS(h["SCI"].header).celestial
    ny, nx = data.shape
    center = w.pixel_to_world((nx - 1) / 2, (ny - 1) / 2)
    corners = w.pixel_to_world(
        np.asarray([0, nx - 1, 0, nx - 1], dtype=float),
        np.asarray([0, 0, ny - 1, ny - 1], dtype=float),
    )
    radius = float(np.max(center.separation(corners).arcsec) + 2.0) * u.arcsec
    job = Gaia.cone_search_async(
        center, radius=radius, table_name=GAIA_TABLE, columns=list(GAIA_COLUMNS)
    )
    return job.get_results(), center, radius

def _finite(v):
    try:
        return bool(np.isfinite(float(v)))
    except Exception:
        return False

def propagated_gaia_coords(table):
    coords = []
    records = []
    target_time = Time(TARGET_EPOCH_JYEAR, format="jyear")
    for row in table:
        ra, dec = float(row["ra"]), float(row["dec"])
        ref_epoch = float(row["ref_epoch"]) if _finite(row["ref_epoch"]) else 2016.0
        kwargs = dict(ra=ra*u.deg, dec=dec*u.deg, frame="icrs",
                      obstime=Time(ref_epoch, format="jyear"))
        pm_ok = _finite(row["pmra"]) and _finite(row["pmdec"])
        if pm_ok:
            kwargs["pm_ra_cosdec"] = float(row["pmra"]) * u.mas/u.yr
            kwargs["pm_dec"] = float(row["pmdec"]) * u.mas/u.yr
        c = SkyCoord(**kwargs)
        if pm_ok:
            c2 = c.apply_space_motion(new_obstime=target_time)
        else:
            c2 = SkyCoord(ra=c.ra, dec=c.dec, frame="icrs", obstime=target_time)
        coords.append(c2)
        records.append({
            "source_id": int(row["source_id"]),
            "ra_deg": ra, "dec_deg": dec, "ref_epoch": ref_epoch,
            "pmra_masyr": float(row["pmra"]) if _finite(row["pmra"]) else None,
            "pmdec_masyr": float(row["pmdec"]) if _finite(row["pmdec"]) else None,
            "parallax_mas": float(row["parallax"]) if _finite(row["parallax"]) else None,
            "phot_g_mean_mag": float(row["phot_g_mean_mag"]) if _finite(row["phot_g_mean_mag"]) else None,
            "ruwe": float(row["ruwe"]) if _finite(row["ruwe"]) else None,
            "propagated_ra_deg": float(c2.ra.deg),
            "propagated_dec_deg": float(c2.dec.deg),
            "target_epoch_jyear": TARGET_EPOCH_JYEAR,
            "proper_motion_propagated": pm_ok,
        })
    if coords:
        return SkyCoord(coords), records
    return SkyCoord(ra=[]*u.deg, dec=[]*u.deg), records

def nearest_matches(candidates: SkyCoord, gaia: SkyCoord, radius_arcsec=MATCH_RADIUS_ARCSEC):
    out = []
    if len(gaia) == 0:
        return [{"gaia_index": None, "separation_arcsec": None, "matched": False}
                for _ in range(len(candidates))]
    idx, sep, _ = candidates.match_to_catalog_sky(gaia)
    for i, s in zip(idx, sep.arcsec):
        out.append({"gaia_index": int(i), "separation_arcsec": float(s),
                    "matched": bool(s <= radius_arcsec)})
    return out

def run(real_fits: Path, d1nb_summary: Path, d1nb_npz: Path, out_json: Path, out_npz: Path):
    parent = json.loads(d1nb_summary.read_text())
    rows = list(parent["selected_candidate_diagnostics"])
    cand_sky = candidate_skycoords(real_fits, rows)
    gaia_table, center, query_radius = query_gaia_for_cutout(real_fits)
    gaia_sky, gaia_records = propagated_gaia_coords(gaia_table)
    matches = nearest_matches(cand_sky, gaia_sky)

    candidate_rows = []
    matched_stamps = []
    with np.load(d1nb_npz) as bundle:
        stpsf = np.asarray(bundle["declared_stpsf_common_stamp"], dtype=float)
        for i, (src, sky, match) in enumerate(zip(rows, cand_sky, matches)):
            item = {
                "d1nb_selected_index": i,
                "d1nb_detection_id": int(src["id"]),
                "candidate_ra_deg": float(sky.ra.deg),
                "candidate_dec_deg": float(sky.dec.deg),
                "gaia_match_radius_arcsec": MATCH_RADIUS_ARCSEC,
                **match,
                "d1nb_metrics": src["metrics"],
                "d1nb_l1_to_declared_stpsf": src["normalized_l1_to_declared_stpsf"],
                "d1nb_corr_to_declared_stpsf": src["normalized_cross_correlation_to_declared_stpsf"],
            }
            item["nearest_gaia"] = gaia_records[match["gaia_index"]] if match["gaia_index"] is not None else None
            candidate_rows.append(item)
            if match["matched"]:
                matched_stamps.append(np.asarray(bundle[f"candidate_{i:02d}_centered_stamp"], dtype=float))

    stack = None
    stack_metrics = None
    stack_compare = None
    if len(matched_stamps) >= 3:
        stack = d1nb._normalized_positive(np.median(
            np.stack([d1nb._normalized_positive(v) for v in matched_stamps]), axis=0
        ))
        stack_metrics = d1nb._positive_shape_metrics(stack)
        stack_compare = {
            "normalized_l1_to_declared_stpsf": d1nb.normalized_l1(stack, stpsf),
            "normalized_cross_correlation_to_declared_stpsf": d1nb.normalized_corr(stack, stpsf),
        }

    out = {
        "claim": "Gaia-DR3 vetting of the exact D1n-b compact-source support set; not an ePSF construction and not morphology recovery",
        "parent_d1nb": {
            "run_id": 33994133478,
            "artifact_id": 9977535930,
            "artifact_sha256": "8ce56143f3dceef0bf77b286ed12a3b7a2d38ea0018a5eddee4e302943746e69",
            "n_support_selected": len(rows),
        },
        "gaia_query": {
            "table": GAIA_TABLE,
            "columns": list(GAIA_COLUMNS),
            "center_ra_deg": float(center.ra.deg),
            "center_dec_deg": float(center.dec.deg),
            "radius_arcsec": float(query_radius.to_value(u.arcsec)),
            "n_rows": len(gaia_records),
            "target_epoch_jyear": TARGET_EPOCH_JYEAR,
            "match_radius_arcsec": MATCH_RADIUS_ARCSEC,
        },
        "n_gaia_matched_d1nb_candidates": int(sum(m["matched"] for m in matches)),
        "candidate_matches": candidate_rows,
        "gaia_query_records": gaia_records,
        "gaia_vetted_positive_median_stack": {
            "constructed": stack is not None,
            "n_candidates": len(matched_stamps),
            "metrics": stack_metrics,
            "comparison_to_declared_stpsf": stack_compare,
            "interpretation_limit": "Gaia-vetted diagnostic median of archived D1n-b centered stamps; not EPSFBuilder, not a calibrated survey PSF, and not ground truth",
        },
        "semantics": {
            "d1nb_candidate_selection_changed": False,
            "match_radius_changed_after_inspection": False,
            "epsf_builder_attempted": False,
            "source_injection_performed": False,
            "morphology_recovery_performed": False,
            "psf_sharpening_performed": False,
            "sci_err_wht_modified": False,
            "noise_added": False,
            "tolman_factor_applied": False,
            "acceptance_threshold_defined": False,
        },
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    arrays = {"declared_stpsf_common_stamp": stpsf}
    if stack is not None:
        arrays["gaia_vetted_positive_median_stack"] = stack
    np.savez_compressed(out_npz, **arrays)
    return out

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--real-fits", type=Path, required=True)
    p.add_argument("--d1nb-summary", type=Path, required=True)
    p.add_argument("--d1nb-npz", type=Path, required=True)
    p.add_argument("--out-json", type=Path, required=True)
    p.add_argument("--out-npz", type=Path, required=True)
    a = p.parse_args()
    out = run(a.real_fits, a.d1nb_summary, a.d1nb_npz, a.out_json, a.out_npz)
    print(json.dumps({
        "n_gaia_rows": out["gaia_query"]["n_rows"],
        "n_gaia_matched_d1nb_candidates": out["n_gaia_matched_d1nb_candidates"],
        "gaia_vetted_stack_constructed": out["gaia_vetted_positive_median_stack"]["constructed"],
        "stack_comparison": out["gaia_vetted_positive_median_stack"]["comparison_to_declared_stpsf"],
    }, indent=2))

if __name__ == "__main__":
    main()
