#!/usr/bin/env python3
"""Noiseless width-only mismatch; not a literal NIRCam PSF reproduction."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.special import erf
from run_agn_nuclear_fraction_noiseless import Renderer, fit, write_csv, TRUNCATE

FACTORS=(.97,1.,1.03)
SOURCE_RUN=33661985266
SOURCE_COMMIT='94fc982e17b248b0227230554d6b47c5e1d40de8'


class WidthRenderer(Renderer):
    def __init__(self,fwhm,stamp=129,oversample=8):
        if not np.isfinite(fwhm) or fwhm<=0:raise ValueError('invalid width')
        self.stamp,self.f=stamp,oversample
        self.sigma=fwhm/np.sqrt(8*np.log(2))
        self.pad=int(np.ceil(TRUNCATE*self.sigma))+1
        side=stamp+2*self.pad
        offsets=(np.arange(self.f)+.5)/self.f-.5
        coord=(np.arange(side)[:,None]+offsets).ravel()-(side-1)/2
        yy,xx=np.meshgrid(coord,coord,indexing='ij');pa=np.deg2rad(45)
        self.xp2=(np.cos(pa)*xx+np.sin(pa)*yy)**2
        self.yp2=(-np.sin(pa)*xx+np.cos(pa)*yy)**2
        edges=np.arange(stamp+1)-stamp/2
        one=np.diff(.5*(1+erf(edges/(np.sqrt(2)*self.sigma))))
        self.point=np.outer(one,one)


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True)
    p.add_argument('--host-n',type=int,choices=(1,4),required=True)
    p.add_argument('--output',type=Path,default=Path('benchmark_output/agn_psf_width'))
    args=p.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    config=dict(stage='C5a Gaussian PSF width isolation',source_run=SOURCE_RUN,source_commit=SOURCE_COMMIT,
                host_n=args.host_n,true_fwhm=3.,fit_factors=FACTORS,fit_factor=8,
                ratios=(.1,1.,10.),reference='archived independent GalSim host + exact Gaussian nucleus',
                fixed='true center and PA, zero sky; no noise',
                optimizer='inherited three starts, bounds, tolerances and max_nfev=160 unchanged',
                acceptance='finite complete matrix only; signs of bias are observations, not pass criteria',
                limitations='width-only Gaussian diagnostic; no core/wing, empirical, chromatic or centroid reproduction')
    (out/'config.json').write_text(json.dumps(config,indent=2)+'\n')
    if (args.input/'commit.txt').read_text().strip()!=SOURCE_COMMIT:raise RuntimeError('wrong source commit')
    source=json.loads((args.input/'summary.json').read_text())
    (out/'source_record.json').write_text(json.dumps(source,indent=2)+'\n')
    rows=[];starts=[]
    for ratio in (.1,1.,10.):
        z=np.load(args.input/f'ratio{ratio:g}.npz');data=z['data']
        old=next(r for r in source['results'] if r['agn_to_host']==ratio)
        if old['true_n']!=args.host_n or hashlib.sha256(data.tobytes()).hexdigest()!=old['data_sha256']:
            raise RuntimeError('wrong source scene/hash')
        for factor in FACTORS:
            renderer=WidthRenderer(3*factor)
            winner,all_rows,pred=fit(data,renderer,True)
            common=dict(true_n=args.host_n,agn_to_host=ratio,fit_fwhm=3*factor,psf_width_factor=factor,
                        data_sha256=old['data_sha256'],reference_re=old['re_pix'],reference_n=old['n'])
            rows.append(dict(**common,**winner,re_fraction_error=winner['re_pix']/16-1,
                             delta_n=winner['n']-args.host_n,delta_q=winner['q']-.6,
                             host_flux_fraction_error=winner['host_flux']-1,
                             nuclear_flux_fraction_error=winner['nuclear_flux']/ratio-1))
            starts.extend(dict(**common,**r) for r in all_rows)
            write_csv(out/'metrics.csv',rows);write_csv(out/'fit_starts.csv',starts)
            np.savez_compressed(out/f'ratio{ratio:g}_width{factor:g}.npz',data=data,
                                host_reference=z['host_reference'],fit_point=renderer.point,
                                prediction=pred,residual=pred-data)
            print(json.dumps(rows[-1]),flush=True)
    if len(rows)!=9 or len(starts)!=27 or not all(np.isfinite(s['cost']) for s in starts):
        raise RuntimeError('incomplete/nonfinite output; preserve partial results')
    (out/'summary.json').write_text(json.dumps(dict(config=config,results=rows,starts=starts),indent=2)+'\n')


if __name__=='__main__':main()
