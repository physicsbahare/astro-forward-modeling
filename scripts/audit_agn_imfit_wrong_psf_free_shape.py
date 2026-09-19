#!/usr/bin/env python3
"""Read-only completeness and algebra audit for C5r."""
import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np
from astropy.io import fits

sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_agn_imfit_wrong_psf_free_shape as experiment


def read(path): return json.loads(path.read_text())


def audit(root,host_n):
    cfg=read(root/'config.json');summary=read(root/'summary.json')
    assert cfg==summary['config']==json.loads(json.dumps(experiment.configuration(host_n)))
    assert read(root/'binary.json')['sha256']==experiment.c5o.IMFIT_SHA
    manifest=read(root/'parent_manifest.json')
    assert manifest['run']==experiment.c5o.PARENT_RUN and manifest['artifact_id']==experiment.c5o.ARTIFACTS[host_n]
    attempts=summary['attempts'];winners=summary['results']
    assert len(attempts)==cfg['expected_attempts']==6 and len(winners)<=cfg['expected_cases']==2
    with (root/'fit_starts.csv').open(newline='') as handle: assert len(list(csv.DictReader(handle)))==6
    with (root/'metrics.csv').open(newline='') as handle: assert len(list(csv.DictReader(handle)))==len(winners)
    arrays=0;timeouts=[];boundary_winners=[]
    for row in attempts:
        assert row['fit_psf_module']==experiment.FIT_PSF[row['truth_module']]
        directory=root/'fits'/row['case']/row['label'];assert read(directory/'result.json')==row
        command=read(directory/'command.json')
        assert command[:3]==['/usr/bin/timeout','--kill-after=5s','180']
        assert command[command.index('--psf')+1].endswith(f"psf_{row['fit_psf_module']}.fits")
        assert '--no-normalize' in command and (directory/'stdout.txt').exists() and (directory/'stderr.txt').exists()
        if row['success']:
            assert row['returncode']==0 and np.isfinite(row['sse'])
            parsed=experiment.c5o.parse_bestfit(directory/'bestfit.dat')
            for key,value in parsed.items(): assert row[key]==value
            assert experiment.c5o.bound_hits(parsed)==row['bound_hits']
            with np.load(directory/'images.npz') as z: images={key:z[key].copy() for key in z.files}
            assert set(images)=={'data','model','residual','saved_residual'}
            for image in images.values(): assert image.shape==(201,201) and np.isfinite(image).all();arrays+=1
            calc=images['data']-images['model'];assert np.array_equal(calc,images['residual'])
            assert float(np.sum(calc**2))==row['sse']
            with fits.open(directory/'model.fits',memmap=False) as handle:
                assert np.array_equal(np.asarray(handle[0].data,float),images['model'])
        else:
            assert row['returncode']!=0;timeouts.append(row['case']+'/'+row['label'])
    for winner in winners:
        group=[row for row in attempts if row['case']==winner['case'] and row['success']]
        assert group and winner['sse']==min(row['sse'] for row in group)
        if winner['bound_hits']: boundary_winners.append(winner['case'])
    for truth_module in experiment.c5o.MODULES:
        group=[row for row in attempts if row['truth_module']==truth_module]
        finite=[row for row in group if row['success']]
        assert (not finite) or any(w['truth_module']==truth_module for w in winners)
    assert not list(root.rglob('*.partial'))
    return dict(host_n=host_n,counts=dict(cases=2,attempts=6,
        finite=len([x for x in attempts if x['success']]),image_arrays=arrays),
        timeouts=timeouts,boundary_winner_cases=boundary_winners,
        interpretation='complete wrong-PSF attempt/algebra audit; no recovery band')


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--host-n',type=int,choices=(1,4),required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=audit(a.source,a.host_n);experiment.dump(a.output,result);print(result)


if __name__=='__main__':main()
