#!/usr/bin/env python3
"""Gate C3 Stage 1: PSF-only/noiseless Yu et al. (2023) resolvedness sweep.

Controlled synthetic-equivalent only, not a literal DESI/CEERS reproduction.
The intrinsic scene is fixed and a circular Gaussian PSF is varied so that
R_p,true/FWHM is exactly the seven published resolution levels. No scientific
acceptance band is defined. A circular PSF isolates smoothing and therefore
cannot reproduce Yu et al.'s small positive A bias from JWST PSF asymmetry.
"""
from __future__ import annotations
import csv, json, sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
from scipy.optimize import minimize
from scipy.special import gammaincinv

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from verification.yu_2023 import (CONCENTRATION_COEFFICIENT,PETROSIAN_ETA,
    SERSIC_N_BOUNDS,TOTAL_LIGHT_APERTURE_RP,YU_RESOLUTION_LEVELS)

OVERSAMPLE=4; STAMP=129; RE0=16.0; PA0=0.37; DR=0.2; NTHETA=360
FIT_START_N=(1.0,2.5,5.0); FIT_RE_BOUNDS=(0.5,60.0); FIT_Q_BOUNDS=(0.15,1.0)
SCENES=(
 dict(scene="sersic_disk_n1",kind="sersic",n=1.0,re_pix=RE0,q=0.65,pa_rad=PA0),
 dict(scene="sersic_spheroid_n4",kind="sersic",n=4.0,re_pix=RE0,q=0.80,pa_rad=PA0),
 dict(scene="asymmetric_disk_clump",kind="disk_plus_clump",n=1.0,re_pix=RE0,q=0.65,pa_rad=PA0,
      clump_fraction=0.15,clump_x_re=1.25,clump_y_re=0.35,clump_sigma_re=0.18),)

def fine_xy(shape,f=OVERSAMPLE):
    o=(np.arange(f)+0.5)/f-0.5
    y=(np.arange(shape[0])[:,None]+o).reshape(-1); x=(np.arange(shape[1])[:,None]+o).reshape(-1)
    yy,xx=np.meshgrid(y,x,indexing="ij"); return xx,yy

def block_sum(a,f=OVERSAMPLE):
    ny,nx=a.shape
    if ny%f or nx%f: raise RuntimeError("fine grid not divisible by oversampling")
    return a.reshape(ny//f,f,nx//f,f).sum(axis=(1,3))

def sersic_fine(shape,re,n,q,pa,x0,y0):
    xx,yy=fine_xy(shape); dx=xx-x0; dy=yy-y0; c,s=np.cos(pa),np.sin(pa)
    xp=c*dx+s*dy; yp=-s*dx+c*dy; r=np.sqrt(xp*xp+(yp/q)**2)
    b=float(gammaincinv(2*n,0.5)); a=np.exp(-b*((np.maximum(r,1e-12)/re)**(1/n)-1)); return a/a.sum()

def render(scene,fwhm):
    shape=(STAMP,STAMP); x0=y0=(STAMP-1)/2
    a=sersic_fine(shape,float(scene["re_pix"]),float(scene["n"]),float(scene["q"]),float(scene["pa_rad"]),x0,y0)
    if scene["kind"]=="disk_plus_clump":
        xx,yy=fine_xy(shape); re=float(scene["re_pix"]); pa=float(scene["pa_rad"]); c,s=np.cos(pa),np.sin(pa)
        dxg=float(scene["clump_x_re"])*re; dyg=float(scene["clump_y_re"])*re
        dx=c*dxg-s*dyg; dy=s*dxg+c*dyg; sig=float(scene["clump_sigma_re"])*re
        cl=np.exp(-0.5*((xx-(x0+dx))**2+(yy-(y0+dy))**2)/sig**2); cl/=cl.sum(); f=float(scene["clump_fraction"])
        a=(1-f)*a+f*cl
    d=block_sum(a)
    if fwhm>0: d=gaussian_filter(d,fwhm/2.3548200450309493,mode="constant",cval=0.0,truncate=6.0)
    return d/d.sum()

def moments(im,center=None):
    im=np.maximum(np.asarray(im,float),0); yy,xx=np.indices(im.shape,dtype=float); t=im.sum()
    if center is None: x0=float((im*xx).sum()/t); y0=float((im*yy).sum()/t)
    else: x0,y0=map(float,center)
    dx=xx-x0; dy=yy-y0; mxx=(im*dx*dx).sum()/t; myy=(im*dy*dy).sum()/t; mxy=(im*dx*dy).sum()/t
    vals,vecs=np.linalg.eigh([[mxx,mxy],[mxy,myy]]); k=np.argsort(vals)[::-1]; vals=vals[k]; v=vecs[:,k[0]]
    q=float(np.clip(np.sqrt(max(vals[1],1e-15)/max(vals[0],1e-15)),0.1,1.0)); pa=float(np.arctan2(v[1],v[0]))
    return x0,y0,q,pa

def radial(im,center,q,pa):
    r=np.arange(0,0.45*min(im.shape)+0.5*DR,DR); th=np.linspace(0,2*np.pi,NTHETA,endpoint=False)
    ct,st=np.cos(th),np.sin(th); c,s=np.cos(pa),np.sin(pa); x0,y0=center; I=np.empty_like(r)
    for i,rr in enumerate(r):
        xp=rr*ct; yp=q*rr*st; x=x0+c*xp-s*yp; y=y0+s*xp+c*yp
        I[i]=map_coordinates(im,[y,x],order=1,mode="constant",cval=0.0,prefilter=False).mean()
    cum=np.zeros_like(r); w=I*r; cum[1:]=np.cumsum(0.5*(w[1:]+w[:-1])*np.diff(r))
    mean=np.empty_like(r); mean[0]=I[0]; mean[1:]=2*cum[1:]/np.maximum(r[1:]**2,1e-30)
    eta=np.divide(I,mean,out=np.full_like(I,np.nan),where=mean>0); return r,cum,eta

def radii(im,center,q,pa):
    r,cum,eta=radial(im,center,q,pa); rp=None
    for i in range(2,len(r)):
        if np.isfinite(eta[i-1]) and np.isfinite(eta[i]) and eta[i-1]>PETROSIAN_ETA>=eta[i]:
            f=(PETROSIAN_ETA-eta[i-1])/(eta[i]-eta[i-1]); rp=float(r[i-1]+f*(r[i]-r[i-1])); break
    if rp is None: raise RuntimeError("Petrosian crossing not found")
    rt=TOTAL_LIGHT_APERTURE_RP*rp
    if rt>=r[-1]: raise RuntimeError("1.5 Rp exceeds radial grid")
    tot=float(np.interp(rt,r,cum)); r20=float(np.interp(.2*tot,cum,r)); r50=float(np.interp(.5*tot,cum,r)); r80=float(np.interp(.8*tot,cum,r))
    return dict(rp=rp,r20=r20,r50=r50,r80=r80,concentration=float(CONCENTRATION_COEFFICIENT*np.log10(r80/r20)))

def mask(shape,center,q,pa,rmax):
    yy,xx=np.indices(shape,dtype=float); x0,y0=center; dx=xx-x0; dy=yy-y0; c,s=np.cos(pa),np.sin(pa)
    xp=c*dx+s*dy; yp=-s*dx+c*dy; return np.sqrt(xp*xp+(yp/q)**2)<=rmax

def A_at(im,center,q,pa,rp):
    yy,xx=np.indices(im.shape,dtype=float); x0,y0=center
    rot=map_coordinates(im,[2*y0-yy,2*x0-xx],order=1,mode="constant",cval=0.0,prefilter=False)
    m=mask(im.shape,center,q,pa,TOTAL_LIGHT_APERTURE_RP*rp); return float(np.abs(im[m]-rot[m]).sum()/max(np.abs(im[m]).sum(),1e-30))

def morphology(im):
    x,y,q,pa=moments(im); pre=radii(im,(x,y),q,pa)
    o=minimize(lambda c:A_at(im,(float(c[0]),float(c[1])),q,pa,pre["rp"]),[x,y],method="Powell",
               bounds=[(x-1.5,x+1.5),(y-1.5,y+1.5)],options={"xtol":1e-4,"ftol":1e-10,"maxiter":80})
    x,y=map(float,o.x); _,_,q,pa=moments(im,(x,y)); rr=radii(im,(x,y),q,pa)
    o2=minimize(lambda c:A_at(im,(float(c[0]),float(c[1])),q,pa,rr["rp"]),[x,y],method="Powell",
                bounds=[(x-.75,x+.75),(y-.75,y+.75)],options={"xtol":1e-4,"ftol":1e-10,"maxiter":60})
    x,y=map(float,o2.x); rr=radii(im,(x,y),q,pa)
    return {**rr,"asymmetry":A_at(im,(x,y),q,pa,rr["rp"]),"center_x":x,"center_y":y,"moment_q":q,"moment_pa":pa,
            "asymmetry_min_success":bool(o.success and o2.success)}

def model(shape,re,n,q,pa,center,fwhm):
    a=sersic_fine(shape,re,n,q,pa,float(center[0]),float(center[1])); d=block_sum(a)
    if fwhm>0: d=gaussian_filter(d,fwhm/2.3548200450309493,mode="constant",cval=0.0,truncate=6.0)
    return d/d.sum()

def fit_sersic(im,fwhm,center,pa,q0,r500):
    data=np.asarray(im,float); scale=max(float(np.sqrt(np.mean(data*data))),1e-15); rlo,rhi=FIT_RE_BOUNDS; qlo,qhi=FIT_Q_BOUNDS; nlo,nhi=SERSIC_N_BOUNDS
    def cost(p):
        re,n,q=float(np.exp(p[0])),float(np.exp(p[1])),float(p[2]); m=model(data.shape,re,n,q,pa,center,fwhm)
        a=max(float(np.dot(m.ravel(),data.ravel())/max(np.dot(m.ravel(),m.ravel()),1e-30)),1e-15); r=(a*m-data)/scale
        return float(.5*np.dot(r.ravel(),r.ravel()))
    rows=[]
    for ns in FIT_START_N:
        p0=[np.log(np.clip(r500,rlo*1.1,rhi/1.1)),np.log(ns),np.clip(q0,qlo+1e-3,qhi-1e-3)]
        z=minimize(cost,p0,method="L-BFGS-B",bounds=[(np.log(rlo),np.log(rhi)),(np.log(nlo),np.log(nhi)),(qlo,qhi)],
                   options={"ftol":1e-10,"gtol":1e-7,"maxiter":160,"maxls":20})
        re,n,q=float(np.exp(z.x[0])),float(np.exp(z.x[1])),float(z.x[2]); m=model(data.shape,re,n,q,pa,center,fwhm); a=max(float(np.dot(m.ravel(),data.ravel())/max(np.dot(m.ravel(),m.ravel()),1e-30)),1e-15); c=cost(z.x)
        rows.append(dict(start_n=float(ns),success=bool(z.success),status=int(z.status),nit=int(z.nit),nfev=int(z.nfev),cost=c,re_pix=re,n=n,q=q,amplitude=a,
                         hit_re_lower_bound=bool(re<=rlo*(1+1e-5)),hit_re_upper_bound=bool(re>=rhi*(1-1e-5)),
                         hit_n_lower_bound=bool(n<=nlo*(1+1e-5)),hit_n_upper_bound=bool(n>=nhi*(1-1e-5)),
                         hit_q_lower_bound=bool(q<=qlo+1e-5),hit_q_upper_bound=bool(q>=qhi-1e-5)))
    return min(rows,key=lambda x:x["cost"]),rows

def row(scene,N,fw,t,m,ft,f):
    return dict(scene=scene["scene"],scene_kind=scene["kind"],rp_true_over_fwhm_requested=float(N),rp_true_over_fwhm_constructed=float(t["rp"])/fw,psf_fwhm_pix=fw,
      rp_true_pix=t["rp"],rp_measured_pix=m["rp"],rp_bias_pix=m["rp"]-t["rp"],r20_true_pix=t["r20"],r20_measured_pix=m["r20"],r20_bias_pix=m["r20"]-t["r20"],
      r50_true_pix=t["r50"],r50_measured_pix=m["r50"],r50_bias_pix=m["r50"]-t["r50"],r80_true_pix=t["r80"],r80_measured_pix=m["r80"],r80_bias_pix=m["r80"]-t["r80"],
      concentration_true=t["concentration"],concentration_measured=m["concentration"],concentration_bias=m["concentration"]-t["concentration"],
      asymmetry_true=t["asymmetry"],asymmetry_measured=m["asymmetry"],asymmetry_bias=m["asymmetry"]-t["asymmetry"],fit_re_true_pix=ft["re_pix"],fit_re_measured_pix=f["re_pix"],fit_re_ratio=f["re_pix"]/ft["re_pix"],
      fit_n_true=ft["n"],fit_n_measured=f["n"],fit_delta_n=f["n"]-ft["n"],fit_q_true=ft["q"],fit_q_measured=f["q"],fit_delta_q=f["q"]-ft["q"],fit_success=f["success"],fit_cost=f["cost"],
      fit_hit_re_lower_bound=f["hit_re_lower_bound"],fit_hit_re_upper_bound=f["hit_re_upper_bound"],fit_hit_n_lower_bound=f["hit_n_lower_bound"],fit_hit_n_upper_bound=f["hit_n_upper_bound"],fit_hit_q_lower_bound=f["hit_q_lower_bound"],fit_hit_q_upper_bound=f["hit_q_upper_bound"],asymmetry_center_minimization_success=m["asymmetry_min_success"])

def main():
    out=Path("benchmark_output/yu_2023/psf_only_noiseless"); out.mkdir(parents=True,exist_ok=True); rows=[]; starts=[]; truths=[]
    for scene in SCENES:
        im0=render(scene,0.0); t=morphology(im0); ft,ss=fit_sersic(im0,0.0,(t["center_x"],t["center_y"]),t["moment_pa"],t["moment_q"],t["r50"])
        truths.append(dict(scene=scene["scene"],scene_definition=scene,nonparametric_truth=t,single_sersic_intrinsic_fit=ft))
        starts += [dict(scene=scene["scene"],rp_true_over_fwhm_requested="intrinsic",**s) for s in ss]
        for N in YU_RESOLUTION_LEVELS:
            fw=t["rp"]/float(N); im=render(scene,fw); m=morphology(im); f,ss=fit_sersic(im,fw,(m["center_x"],m["center_y"]),m["moment_pa"],m["moment_q"],m["r50"])
            rows.append(row(scene,N,fw,t,m,ft,f)); starts += [dict(scene=scene["scene"],rp_true_over_fwhm_requested=float(N),**s) for s in ss]
    if len(rows)!=len(SCENES)*len(YU_RESOLUTION_LEVELS): raise RuntimeError("incomplete resolvedness matrix")
    if sorted({r["rp_true_over_fwhm_requested"] for r in rows})!=sorted(YU_RESOLUTION_LEVELS): raise RuntimeError("wrong resolvedness levels")
    with (out/"metrics.csv").open("w",newline="") as h: w=csv.DictWriter(h,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    with (out/"fit_starts.csv").open("w",newline="") as h: w=csv.DictWriter(h,fieldnames=list(starts[0])); w.writeheader(); w.writerows(starts)
    summary={}
    for scene in SCENES:
        s=[r for r in rows if r["scene"]==scene["scene"]]; summary[scene["scene"]]=dict(intrinsic=next(x for x in truths if x["scene"]==scene["scene"]),poorest_resolution=s[0],best_resolution=s[-1],mean_fit_delta_n=float(np.mean([x["fit_delta_n"] for x in s])),mean_fit_delta_q=float(np.mean([x["fit_delta_q"] for x in s])),n_fit_bound_hits=int(sum(x["fit_hit_n_lower_bound"] or x["fit_hit_n_upper_bound"] for x in s)))
    payload=dict(experiment="Yu et al. 2023 Gate C Stage 1 PSF-only/noiseless resolvedness sweep",scientific_status="controlled synthetic-equivalent; no production criterion; not literal survey reproduction",resolution_definition="R_p,true / FWHM",resolution_levels=list(YU_RESOLUTION_LEVELS),petrosian_eta=PETROSIAN_ETA,curve_of_growth_total_aperture_rp=TOTAL_LIGHT_APERTURE_RP,concentration_definition="5 log10(R80/R20)",asymmetry_aperture_rp=TOTAL_LIGHT_APERTURE_RP,asymmetry_center="minimized; no background term because Stage 1 is noiseless",psf_model="circular Gaussian on detector after 4x intrinsic pixel integration; isolates smoothing, not JWST PSF asymmetry",single_sersic_fit=dict(optimizer="L-BFGS-B scalar profiled-flux objective",n_bounds=list(SERSIC_N_BOUNDS),re_bounds_pix=list(FIT_RE_BOUNDS),q_bounds=list(FIT_Q_BOUNDS),start_n=list(FIT_START_N),winner_rule="lowest residual cost only; never closeness to truth or literature",center_and_pa="fixed to measured noiseless morphology center and moment PA"),scene_definitions=list(SCENES),matrix_rows=len(rows),descriptive_scene_summaries=summary,interpretation_rule="Do not tune scenes or introduce acceptance bands to force literature agreement; diagnose differences physically/numerically.")
    (out/"summary.json").write_text(json.dumps(payload,indent=2)+"\n"); print(json.dumps(payload,indent=2))
if __name__=="__main__": main()
