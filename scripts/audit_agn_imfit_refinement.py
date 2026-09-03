#!/usr/bin/env python3
"""Read-only C5m algebra, all-array and FITS/native reduction audit."""
import argparse
import json
from pathlib import Path
import numpy as np
from astropy.io import fits
import run_agn_imfit_refinement as m
from audit_agn_imfit_renderer import csv_check


def audit(root,n):
    read=m.c.e.read;cfg=read(root/'config.json');s=read(root/'summary.json')
    expected=m.configuration(n);expected.update(github_run_id=cfg['github_run_id'],github_sha=cfg['github_sha'])
    assert cfg==s['config']==json.loads(json.dumps(expected))
    assert s['complete'] and not (root/'failure.json').exists()
    assert len(s['workers'])==8 and len(s['results'])==len(s['starts'])==16 and len(s['pairwise'])==4
    assert read(root/'worker_progress.json')==s['workers']
    assert read(root/'binary.json')['sha256']==m.h.IMFIT_BINARY_SHA
    for rel,digest in read(root/'source_manifest.json').items():assert m.h.sha(root/'parent'/rel)==digest
    images={}
    for w in s['workers']:
        d=root/'renders'/w['name'];assert read(d/'process_result.json')==w
        assert w['success'] and w['returncode']==0 and w['sampling'] in m.SAMPLES
        assert m.h.sha(d/'imfit/fine.fits')==w['fine_sha256']
        with fits.open(d/'imfit/fine.fits') as hdus:
            assert hdus[0].header['BITPIX']==w['fits_bitpix']
            with m.sampling_scope():native=m.h.native_from_fine(np.asarray(hdus[0].data,dtype=float),w['sampling'])
        with np.load(d/'imfit/native.npz') as f:np.testing.assert_array_equal(native,f['image'])
        images[w['name']]=native
        assert m.c.e.digest(native)==w['native_sha256']
        assert all(w[k]==v for k,v in m.h.image_stats(native).items())
        with fits.open(d/'kernel.fits') as hdus,np.load(d/'kernel.npz') as f:
            np.testing.assert_array_equal(hdus[0].data,f['image'])
            assert m.c.e.digest(f['image'])==w['kernel_sha256']
            assert list(f['image'].shape)==w['kernel_stats']['shape']==[208*w['sampling']+1]*2
        if w['sampling']==8:
            with np.load(root/f"parent/parent/imfit/parent/renders/{w['case']['name']}_{w['module']}_s8/native.npz") as f:
                np.testing.assert_allclose(native,f['image'],rtol=0,atol=1e-12)
    for name,data in [('metrics',s['results']),('fit_starts',s['starts']),('pairwise',s['pairwise'])]:csv_check(root/(name+'.csv'),data)
    for row,start in zip(s['results'],s['starts']):
        assert start==dict(**row,start=0,start_type='direct NNLS projection') and row['success']
        with np.load(root/'comparisons'/(row['case']+'.npz')) as f:
            image,ref,pred=f['template'],f['reference'],f['prediction']
            np.testing.assert_array_equal(image,images[row['render']])
            shape=row['render'].rsplit('_s',1)[0]
            refpath=(root/f'parent/parent/imfit/parent/renders/{shape}_s8/native.npz' if row['reference']=='imfit8'
                     else root/f'parent/renders/{shape}_no_cell/images.npz')
            with np.load(refpath) as parent:np.testing.assert_array_equal(ref,parent['image'])
            np.testing.assert_array_equal(pred,row['amplitude']*image)
            res=pred-ref;np.testing.assert_array_equal(res,f['residual'])
            assert row['template_sha256']==m.c.e.digest(image) and row['reference_sha256']==m.c.e.digest(ref)
            assert float(.5*np.sum(res**2)/np.mean(ref**2))==row['cost']
            assert float(np.sum(image*res))==row['gradient']
            assert row['amplitude']>=0 and row['gradient']>=-1e-12 and abs(row['amplitude']*row['gradient'])<=1e-12
            assert all(row[k]==v for k,v in m.h.comparison(image,ref).items())
    for pair in s['pairwise']:
        a,b=images[pair['left']],images[pair['right']]
        assert all(pair[k]==v for k,v in m.h.comparison(a,b).items())
        with np.load(root/'pairwise'/(pair['case']+'.npz')) as f:np.testing.assert_array_equal(f['residual'],a-b)
    manifest=read(root/'image_manifest.json');count=0
    actual={str(f.relative_to(root)) for f in root.rglob('*.npz') if f.relative_to(root).parts[0]!='parent'}
    assert set(manifest)==actual and not list(root.rglob('*.partial'))
    for rel,record in manifest.items():
        assert m.h.sha(root/rel)==record['file_sha256']
        with np.load(root/rel,allow_pickle=False) as f:
            assert set(f.files)==set(record['arrays'])
            for key in f.files:
                a=f[key];assert np.isfinite(a).all()
                assert record['arrays'][key]==dict(shape=list(a.shape),dtype=str(a.dtype),sha256=m.c.e.digest(a))
                count+=1
    assert count==84
    return dict(host_n=n,config=cfg,workers=s['workers'],results=s['results'],pairwise=s['pairwise'],
        counts=dict(workers=8,starts=16,pairs=4,new_arrays=count,fits_outputs=8),
        file_sha256={str(p.relative_to(root)):m.h.sha(p) for p in sorted(root.rglob('*')) if p.is_file()})


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--host-n',type=int,choices=(1,4),required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();r=audit(args.source,args.host_n)
    m.c.e.dump(args.output,r);print(r['counts'])


if __name__=='__main__':main()
