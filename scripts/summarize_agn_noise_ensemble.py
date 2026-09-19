#!/usr/bin/env python3
"""Descriptive statistics for all twelve frozen CI shards; no exclusions."""
import argparse
import json
from pathlib import Path
import numpy as np


def summarize(root):
    rows=[];starts=[]
    for snr in (100,20,5):
        for block in range(4):
            p=root/f'agn-noise-ensemble-snr{snr}-block{block}'
            if (p/'commit.txt').read_text().strip()!='8ad412ec5de6cec80bf90ee5189aaacf79f6431c':
                raise ValueError('wrong provenance')
            s=json.loads((p/'summary.json').read_text())
            if len(s['results'])!=18 or len(s['starts'])!=54:
                raise ValueError('incomplete shard')
            rows+=s['results'];starts+=s['starts']
    result=dict(source_run=33691443555,source_commit='8ad412ec5de6cec80bf90ee5189aaacf79f6431c',
                winner_count=len(rows),start_count=len(starts),failed_starts=sum(not s['success'] for s in starts),
                interpretation='all outcomes included; paired across cases; descriptive, no confidence or acceptance bands',cases=[])
    for snr in (100,20,5):
        for ratio in (.1,1,10):
            for label in ('initial_unweighted','estimated_weight'):
                a=[x for x in rows if x['host_snr']==snr and x['agn_to_host']==ratio and x['pass_name']==label]
                if len(a)!=12 or {x['seed'] for x in a}!=set(range(20261001,20261013)):
                    raise ValueError('wrong ensemble membership')
                r=dict(host_snr=snr,agn_to_host=ratio,pass_name=label,count=12,
                       bound_winners=sum(any(v for k,v in x.items() if k.startswith('hit_')) for x in a),
                       failed_winners=sum(not x['success'] for x in a),errors={})
                arrays={'re_fraction':[x['re_pix']/16-1 for x in a], 'n':[x['n']-4 for x in a],
                        'q':[x['q']-.6 for x in a], 'host_flux_fraction':[x['host_flux']-1 for x in a],
                        'nuclear_flux_fraction':[x['nuclear_flux']/ratio-1 for x in a]}
                for k,v in arrays.items():
                    v=np.asarray(v)
                    if not np.isfinite(v).all():raise ValueError('nonfinite result; do not discard')
                    r['errors'][k]=dict(mean=float(v.mean()),median=float(np.median(v)),rms=float(np.sqrt(np.mean(v*v))))
                result['cases'].append(r)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path)
    print(json.dumps(summarize(p.parse_args().root),indent=2))
