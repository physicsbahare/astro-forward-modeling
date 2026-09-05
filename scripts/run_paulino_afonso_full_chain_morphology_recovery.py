#!/usr/bin/env python3
"""Recover morphology from physically degraded CALIFA-like C2 images.

This stage follows the successful full artificial-redshifting chain assembly.
It asks the first morphology-level question on those images: after source pixel
integration, source PSF, angular resampling, positive target-PSF matching and
radiometric dimming/evolution have been applied, how much do recovered single-
Sersic parameters move even before stochastic target noise is added?

The fit uses the previously validated operational strategy: fixed generic
Sersic-n starts, Re starts expressed relative to the supplied perturbed input
estimate, a 3-point finite-difference Jacobian, x_scale='jac', and selection by
minimum residual cost only. No scientific tolerance is changed.
"""
from __future__ import annotations
import csv, json, sys
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

# Running `python scripts/<name>.py` puts scripts/ rather than the repository
# root on sys.path in GitHub Actions. Add the root explicitly so this diagnostic
# can reuse the already-audited full-chain transfer helper without packaging
# verification-stage scripts as production modules.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_paulino_afonso_full_chain_califa import CASES, TARGET_Z, transfer_to_target
from verification.paulino_afonso_sersic_floor import (
    PIXEL_SCALE_ARCSEC, _convolved_model, _kpc_per_arcsec, adaptive_stamp_size,
    flux_in_depth_units, mag_from_depth_units, pixel_noise_from_point_depth,
)
START_N=(1.0,2.5,5.5,7.0); START_RE_MULTIPLIER_OF_ESTIMATE=(0.8,1.2)
INITIAL_RE_MULTIPLIER=1.08; INITIAL_FLUX_MULTIPLIER=0.93; INITIAL_Q_OFFSET=0.04; MAX_NFEV=1800

def _q_to_u(q):
    qmin,qmax=.15,1.; t=np.clip((q-qmin)/(qmax-qmin),1e-8,1-1e-8); return float(np.log(t/(1-t)))
def _u_to_q(u):
    qmin,qmax=.15,1.; t=1/(1+np.exp(-u)); return float(qmin+(qmax-qmin)*t)
def _central_crop(image,size):
    size=min(size,image.shape[0],image.shape[1]); size-=int(size%2==0)
    y0=(image.shape[0]-size)//2; x0=(image.shape[1]-size)//2
    return np.asarray(image[y0:y0+size,x0:x0+size],dtype=float)

def main():
    out=Path('benchmark_output/paulino_afonso_2017/full_chain_morphology_recovery'); out.mkdir(parents=True,exist_ok=True)
    sigma=pixel_noise_from_point_depth(); all_rows=[]; best_rows=[]
    for z0 in TARGET_Z:
      z=float(z0); kpc_arcsec=_kpc_per_arcsec(z)
      for case in CASES:
        source_flux=flux_in_depth_units(float(case['source_mag_ab']))
        transferred,_,_,_,source_equiv,kernel_fwhm,flux_ratio=transfer_to_target(case,z,source_flux)
        true_re_pix=float(case['re_kpc'])/kpc_arcsec/PIXEL_SCALE_ARCSEC
        image=_central_crop(transferred,adaptive_stamp_size(true_re_pix)); ny,nx=image.shape
        cx=.5*(nx-1); cy=.5*(ny-1); true_flux=float(np.sum(image))
        ire=true_re_pix*INITIAL_RE_MULTIPLIER; iflux=true_flux*INITIAL_FLUX_MULTIPLIER
        iq=min(.95,max(.2,float(case['q'])+INITIAL_Q_OFFSET))
        lower=np.array([np.log(1e-8),np.log(.15),np.log(.2),-12.,-2.,-2.,-5.])
        upper=np.array([np.log(1e8),np.log(120.),np.log(8.),12.,2.,2.,5.])
        def decode(p): return float(np.exp(p[0])),float(np.exp(p[1])),float(np.exp(p[2])),_u_to_q(float(p[3])),cx+float(p[4]),cy+float(p[5]),float(p[6])*sigma
        def residual(p): return ((_convolved_model(image.shape,*decode(p))-image)/sigma).ravel()
        starts=[]
        for rm in START_RE_MULTIPLIER_OF_ESTIMATE:
          for ns in START_N:
            p0=np.array([np.log(max(iflux,1e-12)),np.log(max(ire*rm,.2)),np.log(ns),_q_to_u(iq),0.,0.,0.])
            result=least_squares(residual,p0,bounds=(lower,upper),method='trf',jac='3-point',x_scale='jac',ftol=1e-9,xtol=1e-9,gtol=1e-9,max_nfev=MAX_NFEV)
            rf,rr,rn,rq,rx,ry,rsky=decode(result.x)
            row={'case':str(case['case']),'z_source':.015,'z_target':z,'input_re_kpc':float(case['re_kpc']),'input_n':float(case['n']),'input_q':float(case['q']),'source_mag_ab':float(case['source_mag_ab']),'fit_stamp_size':int(image.shape[0]),'source_psf_equivalent_at_target_arcsec':float(source_equiv),'matching_kernel_fwhm_arcsec':float(kernel_fwhm),'flux_ratio_source_to_target':float(flux_ratio),'start_re_multiplier_of_estimate':float(rm),'start_n':float(ns),'success':bool(result.success),'status':int(result.status),'nfev':int(result.nfev),'cost':float(result.cost),'optimality':float(result.optimality),'recovered_re_kpc':float(rr*PIXEL_SCALE_ARCSEC*kpc_arcsec),'re_ratio':float(rr/true_re_pix),'recovered_n':float(rn),'n_ratio':float(rn/float(case['n'])),'recovered_q':float(rq),'q_difference':float(rq-float(case['q'])),'recovered_flux_in_fit':float(rf),'flux_ratio_to_transferred_fit_flux':float(rf/true_flux),'recovered_mag_from_fit_flux':float(mag_from_depth_units(rf)),'centroid_error_pixels':float(np.hypot(rx-cx,ry-cy)),'sky_sigma_units':float(rsky/sigma),'hit_re_lower_bound':bool(rr<=.15*(1+5e-5)),'hit_re_upper_bound':bool(rr>=120*(1-5e-5)),'hit_n_lower_bound':bool(rn<=.2*(1+5e-5)),'hit_n_upper_bound':bool(rn>=8*(1-5e-5))}
            all_rows.append(row); starts.append(row)
        best_rows.append(min(starts,key=lambda r:float(r['cost'])))
    for name,rows in [('all_starts.csv',all_rows),('best_rows.csv',best_rows)]:
      with (out/name).open('w',newline='') as h:
        w=csv.DictWriter(h,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    def any_bound(r): return bool(r['hit_re_lower_bound'] or r['hit_re_upper_bound'] or r['hit_n_lower_bound'] or r['hit_n_upper_bound'])
    by=[]
    for z0 in TARGET_Z:
      s=[r for r in best_rows if float(r['z_target'])==float(z0)]
      by.append({'z_target':float(z0),'n_cases':len(s),'fit_success_fraction':float(np.mean([bool(r['success']) for r in s])),'any_re_or_n_bound_fraction':float(np.mean([any_bound(r) for r in s])),'median_re_ratio':float(np.median([float(r['re_ratio']) for r in s])),'median_n_ratio':float(np.median([float(r['n_ratio']) for r in s])),'median_q_difference':float(np.median([float(r['q_difference']) for r in s]))})
    payload={'experiment':'CALIFA full-chain noiseless morphology recovery','scientific_status':'controlled synthetic-equivalent diagnostic; not literal survey reproduction','n_cases':len(best_rows),'n_starts_per_case':8,'jacobian_scheme':'3-point','x_scale':'jac','max_nfev':MAX_NFEV,'selection_rule':'lowest residual cost only; never closeness to truth or literature','noise_stage':'no target noise in this stage; isolates transfer-induced morphology bias','by_redshift':by,'best_rows':best_rows,'next_decision_rule':'Treat recovered offsets and bound hits as observables. Do not tune them toward Paulino-Afonso Table 2. If fits are numerically stable, add the declared target-noise ensemble next; otherwise diagnose failing cases first.'}
    (out/'summary.json').write_text(json.dumps(payload,indent=2)+'\n'); print(json.dumps(payload,indent=2))
if __name__=='__main__': main()
