#!/usr/bin/env python3
"""Twelve new paired realizations; descriptive ensemble, no recovery cuts."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from run_agn_shot_noise import source_noise, weighted_fit, HOST_ELECTRONS, RATIOS
from run_agn_estimated_weights import estimated_sigma
from run_agn_nuclear_fraction_noiseless import Renderer, fit, write_csv

SOURCE_COMMIT='335b76bdf6b83f1d0374252affe5ebcf4c29995c'
SOURCE_RUN=33680659156
SEEDS=tuple(range(20261001,20261013))


def block_seeds(block):
    if block not in range(4):
        raise ValueError('invalid block')
    return SEEDS[3*block:3*block+3]


def background_field(shape,seed):
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed,4,311])))
    return rng.standard_normal(shape)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--block',type=int,choices=range(4),required=True)
    p.add_argument('--output',type=Path,default=Path('benchmark_output/agn_noise_ensemble'))
    args=p.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    config=dict(stage='3e predeclared expanded noise ensemble',source_run=SOURCE_RUN,
                source_commit=SOURCE_COMMIT,seeds=SEEDS,block=args.block,block_seeds=block_seeds(args.block),
                host_n=4,ratios=RATIOS,host_electrons=HOST_ELECTRONS,fit_factor=8,
                background_rng='PCG64 SeedSequence([seed,4,311])',
                shot_rng='PCG64 SeedSequence([seed,4,ratio_index,310])',
                pairing='background shared across ratios/SNRs; shot shared across SNRs only',
                estimator='unweighted initial fit, then exactly one model variance update; inherited bounds/starts/tolerances',
                acceptance='complete finite matrix only, no morphology recovery bands',
                reporting='per-SNR/ratio mean, median, RMS truth error and bound/failure counts over all 12 new seeds; no exclusions',
                limitations='n=4 only; twelve replicates descriptive, not precise tail rates or calibrated coverage',
                exclusions='no oracle fit, new PSF mismatch, free center/PA, fitted background or resampling')
    (out/'config.json').write_text(json.dumps(config,indent=2)+'\n')
    if (args.input/'commit.txt').read_text().strip()!=SOURCE_COMMIT:
        raise RuntimeError('wrong source commit')
    source=json.loads((args.input/'summary.json').read_text())
    ancestor=json.loads((args.input/'source_record.json').read_text())
    (out/'source_record.json').write_text(json.dumps(dict(source=source,ancestor=ancestor),indent=2)+'\n')
    template=next(r for r in ancestor['results'] if r['seed']==20260903 and r['agn_to_host']==.1)
    bg=template['pixel_sigma'];snr=template['host_snr']
    if template['true_n']!=4 or snr not in (100,20,5):
        raise RuntimeError('wrong template scene')
    z=np.load(args.input/'seed20260903_ratio0.1_background_plus_shot.npz')
    archived=next(r for r in source['results'] if r['seed']==20260903 and r['agn_to_host']==.1 and r['arm']=='background_plus_shot')
    if hashlib.sha256(z['data'].tobytes()).hexdigest()!=archived['data_sha256']:
        raise RuntimeError('source template bundle hash mismatch')
    host=z['host_reference'];renderer=Renderer(oversample=8);rows=[];starts=[]
    for seed in block_seeds(args.block):
        background=bg*background_field(host.shape,seed)
        for i,ratio in enumerate(RATIOS):
            truth=host+ratio*renderer.point
            counts,shot=source_noise(truth,seed,i)
            data=truth+background+shot
            first,fs,ip=fit(data,renderer,True)
            sigma=estimated_sigma(ip,bg)
            final,ss,pred=weighted_fit(data,renderer,sigma)
            common=dict(seed=seed,host_snr=snr,agn_to_host=ratio,true_n=4,true_re_pix=16,true_q=.6,
                        true_host_flux=1.,true_nuclear_flux=ratio,background_sigma=bg,
                        data_sha256=hashlib.sha256(data.tobytes()).hexdigest(),
                        background_sha256=hashlib.sha256(background.tobytes()).hexdigest(),
                        shot_sha256=hashlib.sha256(shot.tobytes()).hexdigest())
            for label,win,all_rows in [('initial_unweighted',first,fs),('estimated_weight',final,ss)]:
                for row in all_rows:
                    row.setdefault('residual_l1_over_data_l1',None)
                    row.setdefault('whitened_residual_l1_over_whitened_data_l1',None)
                rows.append(dict(**common,pass_name=label,**win))
                starts.extend(dict(**common,pass_name=label,**s) for s in all_rows)
            write_csv(out/'metrics.csv',rows);write_csv(out/'fit_starts.csv',starts)
            np.savez_compressed(out/f'seed{seed}_ratio{ratio:g}.npz',data=data,host_reference=host,
                                nuclear_reference=ratio*renderer.point,noiseless=truth,background=background,
                                source_counts=counts,shot_noise=shot,initial_prediction=ip,
                                estimated_sigma=sigma,prediction=pred,residual=pred-data)
            print(json.dumps(rows[-1]),flush=True)
    if len(rows)!=18 or len(starts)!=54 or not all(np.isfinite(s['cost']) for s in starts):
        raise RuntimeError('incomplete/nonfinite output; retain partial results')
    (out/'summary.json').write_text(json.dumps(dict(config=config,results=rows,starts=starts),indent=2)+'\n')


if __name__=='__main__':
    main()
