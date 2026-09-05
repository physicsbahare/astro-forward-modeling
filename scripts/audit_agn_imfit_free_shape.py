#!/usr/bin/env python3
"""Read-only completeness and algebra audit for C5o."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
from astropy.io import fits

import run_agn_imfit_free_shape as experiment


def read(path): return json.loads(path.read_text())


def audit(root,host_n):
    cfg=read(root/'config.json'); summary=read(root/'summary.json')
    expected=json.loads(json.dumps(experiment.configuration(host_n)))
    assert cfg==summary['config']==expected
    assert read(root/'binary.json')['sha256']==experiment.IMFIT_SHA
    manifest=read(root/'parent_manifest.json')
    assert manifest['run']==experiment.PARENT_RUN and manifest['artifact_id']==experiment.ARTIFACTS[host_n]
    starts=summary['starts']; winners=summary['results']
    assert len(starts)==cfg['expected_starts']==12 and len(winners)==cfg['expected_cases']==4
    with (root/'fit_starts.csv').open(newline='') as f: csv_starts=list(csv.DictReader(f))
    with (root/'metrics.csv').open(newline='') as f: csv_winners=list(csv.DictReader(f))
    assert len(csv_starts)==12 and len(csv_winners)==4
    arrays=0; maximum_saved_residual_error=0.; boundary_winners=[]
    for row in starts:
        assert row['success'] and row['returncode']==0 and np.isfinite(row['sse'])
        d=root/'fits'/row['case']/row['label']
        saved=read(d/'result.json')
        for key in ('label','returncode','success','sse','pa','q','n','ie','re','point_flux','bound_hits'):
            assert saved[key]==row[key]
        parsed=experiment.parse_bestfit(d/'bestfit.dat')
        for key,value in parsed.items(): assert value==row[key]
        assert experiment.bound_hits(parsed)==row['bound_hits']
        with np.load(d/'images.npz') as z:
            images={k:z[k].copy() for k in z.files}
        assert set(images)=={'data','model','residual','saved_residual'}
        for value in images.values(): assert value.shape==(201,201) and np.isfinite(value).all(); arrays+=1
        calc=images['data']-images['model']
        assert np.array_equal(calc,images['residual'])
        assert float(np.sum(calc**2))==row['sse']
        error=float(np.max(np.abs(calc-images['saved_residual'])))
        assert error==row['saved_residual_max_abs_error']; maximum_saved_residual_error=max(maximum_saved_residual_error,error)
        with fits.open(d/'model.fits',memmap=False) as h: assert np.array_equal(np.asarray(h[0].data,float),images['model'])
        with fits.open(d/'residual.fits',memmap=False) as h: assert np.array_equal(np.asarray(h[0].data,float),images['saved_residual'])
    for winner in winners:
        group=[x for x in starts if x['case']==winner['case']]
        assert winner['sse']==min(x['sse'] for x in group)
        assert any(x['label']==winner['label'] and x['sse']==winner['sse'] for x in group)
        if winner['bound_hits']: boundary_winners.append(winner['case'])
    assert not list(root.rglob('*.partial'))
    return dict(host_n=host_n,counts=dict(cases=4,starts=12,image_arrays=arrays),
        maximum_saved_residual_error=maximum_saved_residual_error,boundary_winner_cases=boundary_winners,
        interpretation='algebra/completeness audit; no numerical recovery band')


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--host-n',type=int,choices=(1,4),required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=audit(a.source,a.host_n);experiment.dump(a.output,result);print(result)


if __name__=='__main__':main()
