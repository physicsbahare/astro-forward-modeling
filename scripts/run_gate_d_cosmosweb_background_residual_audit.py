#!/usr/bin/env python3
"""Gate D1n-c: background/residual-context audit at all nine frozen AB=26 locations."""
from __future__ import annotations
import argparse,importlib.util,json,math
from pathlib import Path
import numpy as np
from astropy.io import fits
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("d1m",ROOT/"scripts"/"run_gate_d_cosmosweb_frozen_prefit_neighbour_scene.py"); d1m=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(d1m)
TRUTH_AB=26.0; TRUTH_RE_ARCSEC=.18; TRUTH_N=1.0; TRUTH_Q=.65; LOWFREQ_SIGMA_PIX=3.0

def robust_location_scale(values):
    x=np.asarray(values,dtype=float); x=x[np.isfinite(x)]
    if x.size==0:return float("nan"),float("nan")
    med=float(np.median(x)); return med,1.4826*float(np.median(np.abs(x-med)))

def pair_corr(z,valid,dy,dx):
    a=np.asarray(z,dtype=float); m=np.asarray(valid,dtype=bool); y0a,y1a=max(0,dy),a.shape[0]+min(0,dy); x0a,x1a=max(0,dx),a.shape[1]+min(0,dx); y0b,y1b=max(0,-dy),a.shape[0]+min(0,-dy); x0b,x1b=max(0,-dx),a.shape[1]+min(0,-dx); aa=a[y0a:y1a,x0a:x1a]; bb=a[y0b:y1b,x0b:x1b]; mm=m[y0a:y1a,x0a:x1a]&m[y0b:y1b,x0b:x1b]
    if int(mm.sum())<20:return None
    av=aa[mm]-aa[mm].mean(); bv=bb[mm]-bb[mm].mean(); den=float(np.linalg.norm(av)*np.linalg.norm(bv)); return float(np.dot(av,bv)/den) if den>0 else None

def quadratic_explained_fraction(residual,sigma,valid):
    yy,xx=np.indices(residual.shape,dtype=float); h=(residual.shape[0]-1)/2; x=(xx-h)/h; y=(yy-h)/h; m=valid&np.isfinite(residual)&np.isfinite(sigma)&(sigma>0); design=np.column_stack([np.ones(int(m.sum())),x[m],y[m],x[m]**2,x[m]*y[m],y[m]**2]); w=1.0/sigma[m]; coef,*_=np.linalg.lstsq(design*w[:,None],residual[m]*w,rcond=None); pred=design@coef; sse=float(np.sum(((pred-residual[m])/sigma[m])**2)); mean=np.average(residual[m],weights=1/sigma[m]**2); base=float(np.sum(((residual[m]-mean)/sigma[m])**2)); ex=1-sse/base if base>0 else None; return {"weighted_quadratic_coefficients_b0_bx_by_bxx_bxy_byy":[float(v) for v in coef],"weighted_variance_explained_fraction":float(ex) if ex is not None else None}

def low_frequency_variance_fraction(residual,valid):
    m=np.asarray(valid,dtype=float); num=ndimage.gaussian_filter(np.where(valid,residual,0.0),LOWFREQ_SIGMA_PIX,mode="constant"); den=ndimage.gaussian_filter(m,LOWFREQ_SIGMA_PIX,mode="constant"); good=valid&(den>.5)
    if int(good.sum())<20:return None
    low=num[good]/den[good]; raw=residual[good]; rv=float(np.var(raw)); return float(np.var(low)/rv) if rv>0 else None

def recovery_payload(row):
    dx=float(row["recovered_dx_pix"]); dy=float(row["recovered_dy_pix"]); ab=float(row["recovered_ab_mag"]); re=float(row["recovered_re_arcsec"]); n=float(row["recovered_n"]); q=float(row["recovered_q"])
    return {"optimizer_success":bool(row.get("optimizer_success")),"finite_solution":bool(row.get("finite_solution")),"target_bound_hits":list(row.get("target_bound_hits",[])),"any_target_bound_hit":bool(row.get("any_bound_hit")),"recovered_ab_mag":ab,"delta_mag":ab-TRUTH_AB,"recovered_re_arcsec":re,"re_error_arcsec":re-TRUTH_RE_ARCSEC,"re_ratio":re/TRUTH_RE_ARCSEC,"recovered_n":n,"n_error":n-TRUTH_N,"recovered_q":q,"q_error":q-TRUTH_Q,"centroid_excursion_pix":math.hypot(dx,dy),"reduced_chi2_proxy":float(row["reduced_chi2_proxy"]),"n_neighbour_models":int(row.get("n_neighbour_models",0)),"prefit_any_nuisance_bound_hit":bool(row.get("prefit_any_nuisance_bound_hit"))}

def location_audit(orig,err,wht,labels,catalog,x,y,psf,pixar_sr,row):
    pre=d1m.prefit_neighbour_scene(orig,err,labels,catalog,x,y,psf,pixar_sr); data=d1m.rec._crop(orig,x,y); sig=d1m.rec._crop(err,x,y); wp=d1m.rec._crop(wht,x,y); cm=np.asarray(pre.get("_child_mask",np.zeros_like(data,dtype=bool)),dtype=bool); valid=np.isfinite(data)&np.isfinite(sig)&(sig>0)&~cm; rm,rs=robust_location_scale(data[valid]); out={"x":int(x),"y":int(y),"class":row["class"],"index":int(row["index"]),"valid_fraction":float(valid.mean()),"masked_child_pixels":int(cm.sum()),"selected_neighbour_labels":list(pre.get("selected_neighbour_labels",[])),"masked_child_labels":list(pre.get("masked_child_labels",[])),"prefit_optimizer_success":bool(pre.get("optimizer_success")),"prefit_finite_solution":bool(pre.get("finite_solution")),"prefit_any_nuisance_bound_hit":bool(pre.get("any_nuisance_bound_hit")),"raw_sci":{"median":rm,"mad_sigma":rs},"ERR":{"median":float(np.median(sig[valid])),"p05":float(np.percentile(sig[valid],5)),"p95":float(np.percentile(sig[valid],95)),"coefficient_of_variation":float(np.std(sig[valid])/np.mean(sig[valid]))},"WHT":{"median":float(np.median(wp[valid])),"p05":float(np.percentile(wp[valid],5)),"p95":float(np.percentile(wp[valid],95)),"coefficient_of_variation":float(np.std(wp[valid])/np.mean(wp[valid]))},"d1m_ab26_recovery":recovery_payload(row)}
    if not pre.get("finite_solution"): out["residual_available"]=False; out["prefit_failure_reason"]=pre.get("reason"); return out
    bp=pre["background_prefit"]; residual=data-np.asarray(pre["_frozen_source"],dtype=float)-d1m._plane(np.array([bp["b0"],bp["bx"],bp["by"]])); z=residual/sig; med,mad=robust_location_scale(residual[valid]); zm,zs=robust_location_scale(z[valid]); out["residual_available"]=True; out["prefit_background_plane"]=dict(bp); out["residual"]={"median":med,"mad_sigma":mad,"standardized_median":zm,"standardized_mad_sigma":zs,"standardized_mean":float(np.mean(z[valid])),"standardized_std":float(np.std(z[valid])),"lag_correlations":{"x1":pair_corr(z,valid,0,1),"y1":pair_corr(z,valid,1,0),"x2":pair_corr(z,valid,0,2),"y2":pair_corr(z,valid,2,0),"diag1":pair_corr(z,valid,1,1)},"low_frequency_gaussian_sigma_pix":LOWFREQ_SIGMA_PIX,"low_frequency_variance_fraction":low_frequency_variance_fraction(residual,valid),"quadratic_structure":quadratic_explained_fraction(residual,sig,valid)}; return out

def run(injected_fits,injection_summary,d1m_summary,out_json):
    inj=json.loads(injection_summary.read_text()); prior=json.loads(d1m_summary.read_text()); rows26=[r for r in prior["experiments"] if float(r["ab_mag"])==TRUTH_AB]
    if len(rows26)!=9: raise ValueError(f"expected 9 D1m AB=26 rows, got {len(rows26)}")
    psf,prov=d1m.rec.inj.build_stpsf(inj["matrix"],float(inj["matrix"]["pixel_scale_arcsec"]))
    with fits.open(injected_fits,mode="readonly") as h: orig=np.asarray(h["SCI_ORIG"].data,dtype=float); err=np.asarray(h["ERR"].data,dtype=float); wht=np.asarray(h["WHT"].data,dtype=float)
    labels,bg,sm,dm=d1m.d1k.deblend_scene_components(orig,err); cat=d1m.d1l.build_child_catalog(orig,labels,bg); results=[location_audit(orig,err,wht,labels,cat,int(r["x"]),int(r["y"]),psf,float(inj["pixar_sr"]),r) for r in sorted(rows26,key=lambda r:(r["class"],int(r["index"])))]; rank=sorted(results,key=lambda r:abs(float(r["d1m_ab26_recovery"]["delta_mag"])),reverse=True); top=[{"class":r["class"],"index":r["index"],"x":r["x"],"y":r["y"],"abs_delta_mag":abs(float(r["d1m_ab26_recovery"]["delta_mag"]))} for r in rank[:2]]
    out={"claim":"background/residual-context audit at all nine frozen AB=26 Gate-D positions; D1m recovery outcomes are attached but no new target recovery or post-hoc acceptance criterion is performed","parent_d1m":{"run_id":33978251853,"summary_path":str(d1m_summary),"all_ab26_locations_audited":True},"psf_provenance":prov,"scene_components":{"same_detection_and_deblending_as_d1m":True,"global_background_median":float(bg),"global_scene_mask_fraction":float(sm.mean()),"deblending":dm,"child_catalog_count":len(cat)},"truth":{"ab_mag":TRUTH_AB,"re_arcsec":TRUTH_RE_ARCSEC,"n":TRUTH_N,"q":TRUTH_Q},"locations":results,"most_extreme_two_by_absolute_delta_mag_for_navigation_only":top,"semantics":{"all_nine_ab26_locations_retained":True,"target_refit_performed":False,"target_bounds_changed":False,"segmentation_tuned":False,"noise_added":False,"err_or_wht_modified":False,"psf_sharpening_performed":False,"tolman_factor_applied":False,"acceptance_threshold_defined":False,"low_snr_or_bad_recoveries_discarded":False}}
    out_json.parent.mkdir(parents=True,exist_ok=True); out_json.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); return out

def main():
    p=argparse.ArgumentParser(); p.add_argument("--injected-fits",type=Path,required=True); p.add_argument("--injection-summary",type=Path,required=True); p.add_argument("--d1m-summary",type=Path,required=True); p.add_argument("--out-json",type=Path,required=True); a=p.parse_args(); out=run(a.injected_fits,a.injection_summary,a.d1m_summary,a.out_json); print(json.dumps({"n_locations":len(out["locations"]),"residual_available":sum(bool(r["residual_available"]) for r in out["locations"]),"most_extreme_two_by_absolute_delta_mag_for_navigation_only":out["most_extreme_two_by_absolute_delta_mag_for_navigation_only"]},indent=2))
if __name__=="__main__": main()
