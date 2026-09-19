#!/usr/bin/env python3
"""Read-only completeness/algebra audit for C5p."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
from astropy.io import fits

sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_agn_imfit_optimizer_path as experiment


def read(path): return json.loads(path.read_text())


def audit(root,module):
    cfg=read(root/'config.json');summary=read(root/'summary.json')
    assert cfg==summary['config']==json.loads(json.dumps(experiment.configuration(module)))
    attempts=summary['attempts'];assert len(attempts)==2
    assert [x['solver'] for x in attempts]==['lm','nm']
    finite=[]; arrays=0
    for row in attempts:
        d=root/'fits'/row['solver'];assert read(d/'result.json')==row
        assert (d/'command.json').exists() and (d/'stdout.txt').exists() and (d/'stderr.txt').exists()
        command=read(d/'command.json')
        assert command[:3]==['/usr/bin/timeout','--kill-after=5s','180']
        assert ('--nm' in command)==(row['solver']=='nm')
        if row['finite']:
            assert row['returncode']==0 and row['products_complete'] and np.isfinite(row['sse'])
            parsed=experiment.c5o.parse_bestfit(d/'bestfit.dat')
            for key,value in parsed.items(): assert row[key]==value
            with np.load(d/'images.npz') as z: images={k:z[k].copy() for k in z.files}
            assert set(images)=={'data','model','residual','saved_residual'}
            for image in images.values(): assert image.shape==(201,201) and np.isfinite(image).all();arrays+=1
            calc=images['data']-images['model'];assert np.array_equal(calc,images['residual'])
            assert float(np.sum(calc**2))==row['sse']
            with fits.open(d/'model.fits',memmap=False) as h: assert np.array_equal(np.asarray(h[0].data,float),images['model'])
            finite.append(row['solver'])
        else:
            assert row['returncode']!=0 or not row['products_complete']
    assert not list(root.rglob('*.partial'))
    return dict(module=module,attempts=2,finite_solvers=finite,image_arrays=arrays,
        interpretation='complete optimizer-path audit; no convergence or physical-recovery claim')


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--module',choices=experiment.MODULES,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=audit(a.source,a.module);experiment.dump(a.output,result);print(result)


if __name__=='__main__':main()
