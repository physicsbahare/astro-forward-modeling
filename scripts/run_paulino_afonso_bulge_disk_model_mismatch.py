#!/usr/bin/env python3
"""Gate-C2 source-complexity diagnostic: bulge+disk -> single-Sersic recovery.

The full-chain information audit showed that noisy morphology failures are
consistent with extended-source identifiability loss rather than a reason to
widen fitter bounds. The next controlled question is therefore model mismatch:
what single-Sersic morphology is recovered from a composite bulge+disk galaxy
when the same physically feasible CALIFA-like artificial-redshifting operator is
used, before adding target noise?

This is deliberately a synthetic-equivalent diagnostic, not literal CALIFA or
Paulino-Afonso survey reproduction. The transfer is linear, so separately
redshifted disk and bulge components are summed. No acceptance band is imposed
and no result is tuned toward the published Table-2 ratios.

The optional --z-target argument only shards the pre-declared redshift grid for
CI runtime. It does not change the scientific setup, starts, bounds, optimizer,
or selection rule.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_paulino_afonso_full_chain_califa import TARGET_Z, transfer_to_target
from verification.paulino_afonso_sersic_floor import (
    PIXEL_SCALE_ARCSEC,
    _convolved_model,
    _kpc_per_arcsec,
    adaptive_stamp_size,
    flux_in_depth_units,
    mag_from_depth_units,
    pixel_noise_from_point_depth,
)

COMPOSITES = (
    {"case":"bd_bt010","bt":0.10,"total_source_mag_ab":17.0,"disk_re_kpc":5.0,"disk_q":0.65,"bulge_re_kpc":1.0,"bulge_q":0.90},
    {"case":"bd_bt030","bt":0.30,"total_source_mag_ab":17.0,"disk_re_kpc":5.0,"disk_q":0.65,"bulge_re_kpc":1.0,"bulge_q":0.90},
    {"case":"bd_bt050","bt":0.50,"total_source_mag_ab":17.0,"disk_re_kpc":5.0,"disk_q":0.65,"bulge_re_kpc":1.0,"bulge_q":0.90},
)
START_N=(1.0,2.5,5.5,7.0)
START_RE_MULTIPLIER=(0.6,1.0,1.4)
MAX_NFEV=1800

def _q_to_u(q):
    qmin,qmax=.15,1.; t=np.clip((q-qmin)/(qmax-qmin),1e-8,1-1e-8); return float(np.log(t/(1-t)))

def _u_to_q(u):
    qmin,qmax=.15,1.; t=1/(1+np.exp(-u)); return float(qmin+(qmax-qmin)*t)

def _central_crop(image,size):
    size=min(int(size),image.shape[0],image.shape[1]); size-=int(size%2==0)
    y0=(image.shape[0]-size)//2; x0=(image.shape[1]-size)//2
    return np.asarray(image[y0:y0+size,x0:x0+size],dtype=float)

def _parse_args():
    p=argparse.ArgumentParser()
    p.add_argument('--z-target',type=float,default=None,
                   help='Run one member of the pre-declared TARGET_Z grid; default runs all.')
    return p.parse_args()

def _selected_redshifts(z_target):
    if z_target is None:
        return tuple(float(z) for z in TARGET_Z)
    matches=[float(z) for z in TARGET_Z if np.isclose(float(z),float(z_target),rtol=0.0,atol=1e-10)]
    if not matches:
        raise SystemExit(f'--z-target must be one of {tuple(float(z) for z in TARGET_Z)}')
    return tuple(matches)

def main():
    args=_parse_args()
    selected_z=_selected_redshifts(args.z_target)
    suffix='all' if args.z_target is None else f'z_{selected_z[0]:.2f}'.replace('.','p')
    out=Path('benchmark_output/paulino_afonso_2017/bulge_disk_model_mismatch')/suffix
    out.mkdir(parents=True,exist_ok=True)
    sigma=pixel_noise_from_point_depth()
    all_rows=[]; best_rows=[]

    for z in selected_z:
        kpc_arcsec=_kpc_per_arcsec(z)
        for cfg in COMPOSITES:
            total_source_flux=flux_in_depth_units(cfg['total_source_mag_ab'])
            disk_flux=total_source_flux*(1.0-cfg['bt'])
            bulge_flux=total_source_flux*cfg['bt']
            disk_case={'case':cfg['case']+'_disk','re_kpc':cfg['disk_re_kpc'],'n':1.0,'q':cfg['disk_q'],'source_mag_ab':cfg['total_source_mag_ab']}
            bulge_case={'case':cfg['case']+'_bulge','re_kpc':cfg['bulge_re_kpc'],'n':4.0,'q':cfg['bulge_q'],'source_mag_ab':cfg['total_source_mag_ab']}
            disk,_,_,_,_,_,flux_ratio=transfer_to_target(disk_case,z,disk_flux)
            bulge,_,_,_,_,_,_=transfer_to_target(bulge_case,z,bulge_flux)
            composite=disk+bulge

            disk_re_pix=cfg['disk_re_kpc']/kpc_arcsec/PIXEL_SCALE_ARCSEC
            image=_central_crop(composite,adaptive_stamp_size(disk_re_pix))
            ny,nx=image.shape; cx=.5*(nx-1); cy=.5*(ny-1)
            fit_flux=max(float(np.sum(image)),1e-12)
            initial_q=(1-cfg['bt'])*cfg['disk_q']+cfg['bt']*cfg['bulge_q']
            lower=np.array([np.log(1e-8),np.log(.15),np.log(.2),-12.,-2.,-2.,-5.])
            upper=np.array([np.log(1e8),np.log(120.),np.log(8.),12.,2.,2.,5.])

            def decode(p):
                return float(np.exp(p[0])),float(np.exp(p[1])),float(np.exp(p[2])),_u_to_q(float(p[3])),cx+float(p[4]),cy+float(p[5]),float(p[6])*sigma
            def residual(p):
                return ((_convolved_model(image.shape,*decode(p))-image)/sigma).ravel()

            starts=[]
            for rm in START_RE_MULTIPLIER:
                for ns in START_N:
                    p0=np.array([np.log(fit_flux*.95),np.log(max(disk_re_pix*rm,.2)),np.log(ns),_q_to_u(initial_q),0.,0.,0.])
                    result=least_squares(residual,p0,bounds=(lower,upper),method='trf',jac='3-point',x_scale='jac',ftol=1e-9,xtol=1e-9,gtol=1e-9,max_nfev=MAX_NFEV)
                    rf,rr,rn,rq,rx,ry,rsky=decode(result.x)
                    row={
                        'case':cfg['case'],'z_target':z,'bt':cfg['bt'],'total_source_mag_ab':cfg['total_source_mag_ab'],
                        'disk_re_kpc':cfg['disk_re_kpc'],'bulge_re_kpc':cfg['bulge_re_kpc'],'disk_n':1.0,'bulge_n':4.0,
                        'start_re_multiplier_of_disk_re':rm,'start_n':ns,'success':bool(result.success),'status':int(result.status),
                        'nfev':int(result.nfev),'cost':float(result.cost),'optimality':float(result.optimality),
                        'recovered_re_kpc':float(rr*PIXEL_SCALE_ARCSEC*kpc_arcsec),'recovered_re_over_disk_re':float(rr/disk_re_pix),
                        'recovered_n':float(rn),'recovered_q':float(rq),'recovered_flux':float(rf),'recovered_mag':float(mag_from_depth_units(rf)),
                        'centroid_error_pixels':float(np.hypot(rx-cx,ry-cy)),'sky_sigma_units':float(rsky/sigma),
                        'hit_re_lower_bound':bool(rr<=.15*(1+5e-5)),'hit_re_upper_bound':bool(rr>=120*(1-5e-5)),
                        'hit_n_lower_bound':bool(rn<=.2*(1+5e-5)),'hit_n_upper_bound':bool(rn>=8*(1-5e-5)),
                        'expected_target_flux':float(total_source_flux*flux_ratio),
                    }
                    all_rows.append(row); starts.append(row)
            best_rows.append(min(starts,key=lambda r:float(r['cost'])))

    for name,rows in [('all_starts.csv',all_rows),('best_rows.csv',best_rows)]:
        with (out/name).open('w',newline='') as h:
            w=csv.DictWriter(h,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    summary=[]
    for z in selected_z:
        for cfg in COMPOSITES:
            r=next(x for x in best_rows if x['case']==cfg['case'] and float(x['z_target'])==float(z))
            summary.append({k:r[k] for k in ('case','z_target','bt','success','recovered_re_kpc','recovered_re_over_disk_re','recovered_n','recovered_q','centroid_error_pixels','hit_re_lower_bound','hit_re_upper_bound','hit_n_lower_bound','hit_n_upper_bound')})

    payload={
        'experiment':'noiseless bulge+disk model-mismatch through CALIFA-feasible full chain',
        'scientific_status':'controlled synthetic-equivalent diagnostic; not literal survey reproduction',
        'execution_shard_redshifts':list(selected_z),
        'n_composites':len(COMPOSITES),'n_target_redshifts':len(selected_z),'n_best_rows':len(best_rows),
        'source_structure':'co-centered exponential disk (n=1) + compact bulge (n=4), common transfer operator; single-Sersic recovery',
        'bt_values':[c['bt'] for c in COMPOSITES],
        'selection_rule':'lowest residual cost only; no truth/literature proximity criterion',
        'noise_stage':'no target noise; isolates structural model mismatch from identifiability loss',
        'summary_rows':summary,
        'next_decision_rule':'If the noiseless composite fits are numerically stable, add target noise to quantify the interaction of bulge+disk structure with the already-measured extended-source information loss. Do not tune toward Paulino-Afonso Table 2.'
    }
    (out/'summary.json').write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps(payload,indent=2))

if __name__=='__main__':
    main()
