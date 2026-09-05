#!/usr/bin/env python3
"""Gate D1n-b: empirical point-source/effective-PSF support audit on frozen real mosaic."""
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np
from astropy.io import fits
from photutils.detection import DAOStarFinder
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("d1d",ROOT/"scripts"/"run_gate_d_cosmosweb_real_injection.py")
d1d=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(d1d)
PIXEL_SCALE=0.03; DETECTION_FWHM_PIX=0.145/PIXEL_SCALE; DETECTION_THRESHOLD_SIGMA=8.0
CORE_SNR_MIN=10.0; ISOLATION_RADIUS_PIX=3.0*DETECTION_FWHM_PIX; STAMP_SIZE=31; STAMP_HALF=15
BACKGROUND_ANNULUS_PIX=(11.0,15.0); STACK_MIN_CANDIDATES=3
STSCI_REFERENCE={"single_exposure_empirical_ee50_arcsec":0.085,"single_exposure_empirical_ee80_arcsec":0.276,"resampled_simulated_ee50_arcsec":0.113,"resampled_simulated_ee80_arcsec":0.291}

def robust_location_scale(values):
    x=np.asarray(values,dtype=float); x=x[np.isfinite(x)]
    if x.size==0:return float("nan"),float("nan")
    med=float(np.median(x)); return med,1.4826*float(np.median(np.abs(x-med)))

def crop_center(array,size=STAMP_SIZE):
    a=np.asarray(array,dtype=float)
    if a.ndim!=2 or size%2!=1: raise ValueError("array must be 2-D and crop size odd")
    iy=int(round((a.shape[0]-1)/2)); ix=int(round((a.shape[1]-1)/2)); h=size//2
    if iy-h<0 or ix-h<0 or iy+h>=a.shape[0] or ix+h>=a.shape[1]: raise ValueError("crop exceeds input")
    return np.array(a[iy-h:iy+h+1,ix-h:ix+h+1],copy=True)

def _positive_shape_metrics(image):
    arr=np.asarray(image,dtype=float); pos=np.maximum(arr,0.0); total=float(pos.sum())
    if not np.isfinite(total) or total<=0: raise ValueError("non-positive support")
    yy,xx=np.indices(arr.shape,dtype=float); cx=float((xx*pos).sum()/total); cy=float((yy*pos).sum()/total)
    dx=xx-cx; dy=yy-cy; mxx=float((dx*dx*pos).sum()/total); myy=float((dy*dy*pos).sum()/total); mxy=float((dx*dy*pos).sum()/total)
    ev=np.maximum(np.linalg.eigvalsh([[mxx,mxy],[mxy,myy]]),0.0); smin,smaj=np.sqrt(ev[0]),np.sqrt(ev[1]); rr=np.hypot(dx,dy)
    order=np.argsort(rr.ravel()); rs=rr.ravel()[order]; cs=np.cumsum(pos.ravel()[order])/total
    ee50=float(rs[min(np.searchsorted(cs,.5),rs.size-1)]); ee80=float(rs[min(np.searchsorted(cs,.8),rs.size-1)])
    asum=float(np.abs(arr).sum()); neg=float(np.abs(arr[arr<0]).sum())
    return {"positive_sum":total,"signed_sum":float(arr.sum()),"negative_absolute_fraction":neg/asum if asum>0 else None,"centroid_x_pix":cx,"centroid_y_pix":cy,"sigma_major_pix":float(smaj),"sigma_minor_pix":float(smin),"axis_ratio_moment":float(smin/smaj) if smaj>0 else None,"ee50_radius_pix":ee50,"ee80_radius_pix":ee80,"ee50_radius_arcsec":ee50*PIXEL_SCALE,"ee80_radius_arcsec":ee80*PIXEL_SCALE}

def _normalized_positive(image):
    a=np.maximum(np.asarray(image,dtype=float),0.0); s=float(a.sum())
    if s<=0 or not np.isfinite(s): raise ValueError("cannot normalize")
    return a/s

def normalized_l1(a,b):
    aa=_normalized_positive(a); bb=_normalized_positive(b)
    if aa.shape!=bb.shape: raise ValueError("shape mismatch")
    return float(np.abs(aa-bb).sum())

def normalized_corr(a,b):
    aa=_normalized_positive(a).ravel(); bb=_normalized_positive(b).ravel(); aa-=aa.mean(); bb-=bb.mean(); den=float(np.linalg.norm(aa)*np.linalg.norm(bb))
    return float(np.dot(aa,bb)/den) if den>0 else float("nan")

def prepare_candidate_stamp(sci,x,y):
    h=STAMP_HALF; stamp=np.asarray(sci[y-h:y+h+1,x-h:x+h+1],dtype=float)
    if stamp.shape!=(STAMP_SIZE,STAMP_SIZE): raise ValueError("stamp truncated")
    yy,xx=np.indices(stamp.shape,dtype=float); r=np.hypot(xx-h,yy-h); ann=(r>=BACKGROUND_ANNULUS_PIX[0])&(r<=BACKGROUND_ANNULUS_PIX[1]); bkg,bs=robust_location_scale(stamp[ann]); sub=stamp-bkg
    core=np.maximum(sub,0.0); cs=float(core.sum())
    if cs<=0: raise ValueError("no positive support")
    cx=float((xx*core).sum()/cs); cy=float((yy*core).sum()/cs); shift=(h-cy,h-cx); centered=ndimage.shift(sub,shift=shift,order=3,mode="constant",cval=0.0,prefilter=True)
    return centered,{"local_background_median":bkg,"local_background_mad_sigma":bs,"precenter_centroid_x_in_stamp":cx,"precenter_centroid_y_in_stamp":cy,"applied_shift_yx_pix":[float(shift[0]),float(shift[1])]}

def _nearest_distances(x,y):
    if len(x)<=1:return np.full(len(x),np.inf)
    c=np.column_stack([x,y]).astype(float); d=c[:,None,:]-c[None,:,:]; r=np.sqrt(np.sum(d*d,axis=2)); np.fill_diagonal(r,np.inf); return np.min(r,axis=1)

def run(real_fits,matrix_path,out_json,out_npz):
    matrix=json.loads(matrix_path.read_text())
    with fits.open(real_fits,mode="readonly") as h: sci=np.asarray(h["SCI"].data,dtype=float); err=np.asarray(h["ERR"].data,dtype=float); wht=np.asarray(h["WHT"].data,dtype=float)
    if sci.shape!=err.shape or sci.shape!=wht.shape: raise ValueError("shape mismatch")
    if not (np.isfinite(sci).all() and np.isfinite(err).all() and np.isfinite(wht).all() and np.all(err>0) and np.all(wht>0)): raise ValueError("invalid cutout")
    bg,bgs=robust_location_scale(sci); finder=DAOStarFinder(threshold=DETECTION_THRESHOLD_SIGMA*bgs,fwhm=DETECTION_FWHM_PIX); table=finder(sci-bg); detections=[]
    if table is not None:
        xs=np.asarray(table["xcentroid"],dtype=float); ys=np.asarray(table["ycentroid"],dtype=float); nearest=_nearest_distances(xs,ys)
        for i,row in enumerate(table):
            x=float(row["xcentroid"]); y=float(row["ycentroid"]); ix,iy=int(round(x)),int(round(y)); edge=float(min(ix,iy,sci.shape[1]-1-ix,sci.shape[0]-1-iy)); snr=float((sci[iy,ix]-bg)/err[iy,ix])
            item={"id":int(row["id"]),"xcentroid":x,"ycentroid":y,"ix":ix,"iy":iy,"peak":float(row["peak"]),"flux":float(row["flux"]),"sharpness":float(row["sharpness"]),"roundness1":float(row["roundness1"]),"roundness2":float(row["roundness2"]),"nearest_detection_distance_pix":float(nearest[i]),"edge_distance_pix":edge,"peak_snr_using_err":snr}
            item["support_selected"]=bool(edge>=STAMP_HALF+1 and nearest[i]>=ISOLATION_RADIUS_PIX and snr>=CORE_SNR_MIN); detections.append(item)
    selected=[r for r in detections if r["support_selected"]]; psf,prov=d1d.build_stpsf(matrix,PIXEL_SCALE); psf_stamp=crop_center(psf,STAMP_SIZE); stamps=[]; rows=[]
    for rec in selected:
        centered,meta=prepare_candidate_stamp(sci,rec["ix"],rec["iy"]); r=dict(rec); r.update(meta); r["metrics"]=_positive_shape_metrics(centered); r["normalized_l1_to_declared_stpsf"]=normalized_l1(centered,psf_stamp); r["normalized_cross_correlation_to_declared_stpsf"]=normalized_corr(centered,psf_stamp); rows.append(r); stamps.append(centered)
    stack=None; sm=None; sc=None
    if len(stamps)>=STACK_MIN_CANDIDATES:
        stack=_normalized_positive(np.median(np.stack([_normalized_positive(v) for v in stamps]),axis=0)); sm=_positive_shape_metrics(stack); sc={"normalized_l1_to_declared_stpsf":normalized_l1(stack,psf_stamp),"normalized_cross_correlation_to_declared_stpsf":normalized_corr(stack,psf_stamp)}
    out={"claim":"empirical point-source-like support audit on the frozen real COSMOS-Web F444W mosaic cutout; compact detections are not asserted to be stars and the empirical stack is not adopted as an effective-PSF ground truth","real_cutout":str(real_fits),"shape":list(sci.shape),"pixel_scale_arcsec":PIXEL_SCALE,"background":{"median":bg,"mad_sigma":bgs},"selection_frozen_before_data_inspection":{"finder":"photutils.detection.DAOStarFinder","finder_fwhm_pix":DETECTION_FWHM_PIX,"finder_threshold_sigma":DETECTION_THRESHOLD_SIGMA,"peak_snr_min_using_ERR":CORE_SNR_MIN,"isolation_radius_pix":ISOLATION_RADIUS_PIX,"stamp_size_pix":STAMP_SIZE,"background_annulus_pix":list(BACKGROUND_ANNULUS_PIX),"stack_min_candidates":STACK_MIN_CANDIDATES},"n_detections":len(detections),"n_support_selected":len(selected),"detections":detections,"selected_candidate_diagnostics":rows,"declared_stpsf":{"provenance":prov,"metrics_on_common_stamp":_positive_shape_metrics(psf_stamp)},"empirical_positive_median_stack":{"constructed":stack is not None,"n_candidates":len(stamps),"metrics":sm,"comparison_to_declared_stpsf":sc,"interpretation_limit":"diagnostic positive-flux median stack after local-background subtraction and centroid interpolation; not a Photutils EPSFBuilder model and not a calibrated survey effective PSF"},"stscI_reference_context":STSCI_REFERENCE,"epsf_builder":{"attempted":False,"reason":"This 512x512 support audit does not pre-certify a sufficiently large, clean, visually vetted stellar sample; forcing EPSFBuilder would overstate the evidence."},"semantics":{"source_injection_performed":False,"morphology_recovery_performed":False,"psf_sharpening_performed":False,"acceptance_threshold_defined":False,"empirical_psf_claimed_ground_truth":False,"compact_detections_claimed_stars":False,"sci_err_wht_modified":False,"tolman_factor_applied":False}}
    out_json.parent.mkdir(parents=True,exist_ok=True); out_json.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); arrays={"declared_stpsf_common_stamp":psf_stamp}; arrays.update({f"candidate_{i:02d}_centered_stamp":s for i,s in enumerate(stamps)}); 
    if stack is not None: arrays["empirical_positive_median_stack"]=stack
    np.savez_compressed(out_npz,**arrays); return out

def main():
    p=argparse.ArgumentParser(); p.add_argument("--real-fits",type=Path,required=True); p.add_argument("--matrix",type=Path,required=True); p.add_argument("--out-json",type=Path,required=True); p.add_argument("--out-npz",type=Path,required=True); a=p.parse_args(); out=run(a.real_fits,a.matrix,a.out_json,a.out_npz); print(json.dumps({"n_detections":out["n_detections"],"n_support_selected":out["n_support_selected"],"empirical_stack_constructed":out["empirical_positive_median_stack"]["constructed"],"stack_comparison":out["empirical_positive_median_stack"]["comparison_to_declared_stpsf"]},indent=2))
if __name__=="__main__": main()
