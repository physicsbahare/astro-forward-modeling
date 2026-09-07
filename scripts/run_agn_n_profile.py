#!/usr/bin/env python3
"""Profile-grid diagnostic on archived noise-pilot data; never changes old fits."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from run_agn_nuclear_fraction_noiseless import Renderer, profile_flux, write_csv, RE_BOUNDS, Q_BOUNDS, MAX_NFEV

SOURCE_RUN = 33668364723
SOURCE_COMMIT = '46c7af879cb0c27432c2a34352b37dcada9d1be3'
N_GRID = (.5,1.,2.,3.,4.,5.,6.)
START_RE = (4.,12.,36.)


def profile_at_n(data, renderer, fixed_n, sigma):
    scale = float(np.sqrt(np.mean(data**2)))
    lo=[np.log(RE_BOUNDS[0]),Q_BOUNDS[0]]
    hi=[np.log(RE_BOUNDS[1]),Q_BOUNDS[1]]
    def evaluate(p):
        return profile_flux(data,renderer.host(np.exp(p[0]),fixed_n,p[1]),renderer.point)
    def residual(p):
        return ((evaluate(p)[1]-data)/scale).ravel()
    rows, predictions=[],[]
    for re_start in START_RE:
        result=least_squares(residual,[np.log(re_start),.75],bounds=(lo,hi),
                             method='trf',max_nfev=MAX_NFEV,ftol=1e-10,xtol=1e-10,gtol=1e-7)
        flux,pred=evaluate(result.x)
        re,q=float(np.exp(result.x[0])),float(result.x[1])
        row=dict(fixed_n=fixed_n,start_re=re_start,success=bool(result.success),
                 status=int(result.status),message=result.message,nfev=int(result.nfev),
                 optimality=float(result.optimality),cost=float(result.cost),
                 chi2=float(np.sum(((pred-data)/sigma)**2)),re_pix=re,q=q,
                 host_flux=float(flux[0]),nuclear_flux=float(flux[1]),
                 hit_host_flux_zero=bool(flux[0]==0),hit_nuclear_flux_zero=bool(flux[1]==0))
        for name,value,bounds in [('re',re,RE_BOUNDS),('q',q,Q_BOUNDS)]:
            row[f'hit_{name}_lower_bound']=bool(value<=bounds[0]*(1+1e-5))
            row[f'hit_{name}_upper_bound']=bool(value>=bounds[1]*(1-1e-5))
        rows.append(row);predictions.append(pred)
    best=min(range(len(rows)),key=lambda i:rows[i]['cost'])
    return rows[best],rows,predictions[best]


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,default=Path('benchmark_output/agn_n_profile'))
    args=p.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    config=dict(stage='3b n profile grid',source_run=SOURCE_RUN,source_commit=SOURCE_COMMIT,
                selection='all n=4 ratio=1 cases; all three seeds in supplied SNR shard',
                n_grid=N_GRID,start_re=START_RE,start_q=.75,re_bounds=RE_BOUNDS,q_bounds=Q_BOUNDS,
                fit_factor=8,max_nfev=MAX_NFEV,ftol=1e-10,xtol=1e-10,gtol=1e-7,
                fixed='n at each grid node, center, PA, zero sky; original data unchanged',
                acceptance='finite complete grid only; raw delta chi-square, no confidence bands',
                interpretation='negative delta vs original winner may expose missed optimum; preserve it')
    (out/'config.json').write_text(json.dumps(config,indent=2)+'\n')
    if (args.input/'commit.txt').read_text().strip()!=SOURCE_COMMIT:
        raise RuntimeError('wrong input commit')
    source=json.loads((args.input/'summary.json').read_text())
    originals=[r for r in source['results'] if r['true_n']==4 and r['agn_to_host']==1.]
    if len(originals)!=3 or {r['seed'] for r in originals}!={20260903,20260904,20260905}:
        raise RuntimeError('wrong source cases')
    (out/'source_record.json').write_text(json.dumps(dict(config=source['config'],results=originals),indent=2)+'\n')
    renderer=Renderer(oversample=8);rows=[];starts=[]
    for old in originals:
        z=np.load(args.input/f"seed{old['seed']}_ratio1.npz")
        data=z['data'];sigma=old['pixel_sigma']
        if hashlib.sha256(data.tobytes()).hexdigest()!=old['data_sha256']:
            raise RuntimeError('input data hash mismatch')
        common=dict(seed=old['seed'],host_snr=old['host_snr'],data_sha256=old['data_sha256'],
                    original_n=old['n'],original_chi2=old['chi2'])
        for n in N_GRID:
            winner,all_rows,pred=profile_at_n(data,renderer,n,sigma)
            rows.append(dict(**common,**winner,delta_chi2_vs_original=winner['chi2']-old['chi2']))
            starts.extend(dict(**common,**s,delta_chi2_vs_original=s['chi2']-old['chi2']) for s in all_rows)
            write_csv(out/'metrics.csv',rows);write_csv(out/'fit_starts.csv',starts)
            np.savez_compressed(out/f"seed{old['seed']}_n{n:g}.npz",data=data,prediction=pred,
                                residual=pred-data,original_prediction=z['prediction'])
            print(json.dumps(rows[-1]),flush=True)
    if len(rows)!=21 or len(starts)!=63 or not all(np.isfinite(r['chi2']) for r in starts):
        raise RuntimeError('incomplete/nonfinite grid; preserve partial outputs')
    (out/'summary.json').write_text(json.dumps(dict(config=config,results=rows,starts=starts),indent=2)+'\n')


if __name__=='__main__':
    main()
