#!/usr/bin/env python3
"""Read-only C5l output audit; no rendering or optimizer calls."""
import argparse
import json
from pathlib import Path
import numpy as np
import run_agn_cell_response as c
from audit_agn_imfit_renderer import csv_check


def audit(root,n):
    read=c.e.read;summary=read(root/'summary.json');cfg=read(root/'config.json')
    expected=c.configuration(n)
    expected.update(github_run_id=cfg['github_run_id'],github_sha=cfg['github_sha'])
    assert cfg==summary['config']==json.loads(json.dumps(expected))
    assert summary['complete'] and not (root/'failure.json').exists()
    workers,rows,starts,pairs=(summary[k] for k in ('workers','results','starts','pairwise'))
    assert len(workers)==16 and len(rows)==len(starts)==48 and len(pairs)==24
    assert read(root/'worker_progress.json')==workers
    for name,data in [('metrics',rows),('fit_starts',starts),('pairwise',pairs)]:csv_check(root/(name+'.csv'),data)
    for key,record in read(root/'source_manifest.json').items():
        for rel,digest in record['selected_file_sha256'].items():assert c.p.sha(root/'parent'/key/rel)==digest
    images={};warnings=[];runtimes=[]
    for w in workers:
        directory=root/'renders'/w['name']
        assert w['success'] and w['returncode']==0 and read(directory/'process_result.json')==w
        assert read(directory/'worker_config.json')['arm_config']==c.arm_config(w['arm'])
        assert len(read(directory/'fft_trace.json'))==(2 if n==1 else 1)
        assert read(directory/'profiles.json')==w['render']['profiles']
        warnings.extend(dict(worker=w['name'],**x) for x in read(directory/'warnings.json'))
        runtimes.append(dict(worker=w['name'],**read(directory/'runtime.json')))
        with np.load(directory/'images.npz',allow_pickle=False) as f:
            image=f['image'].copy();images[w['name']]=image
            assert c.e.digest(image)==w['render']['image_sha256']
            assert c.p.image_stats(image)==w['render']['image_stats']
            if n==1:
                assert c.e.digest(f['gaussian'])==w['render']['gaussian_sha256']
                np.testing.assert_array_equal(f['gaussian_residual'],image-f['gaussian'])
            if w['arm']=='no_cell':
                with np.load(root/f"parent/grid/renders/{w['case']['name']}_{w['module']}_grid1536_k4/images.npz") as ref:
                    np.testing.assert_allclose(image,ref['image'],rtol=0,atol=1e-12)
        with np.load(directory/'probes.npz',allow_pickle=False) as f:
            np.testing.assert_array_equal(f['host']*f['psf'],f['product'])
            assert float(np.abs(f['convolution']-f['product']).max())==w['render']['fourier_product_max_error']<=1e-12
    for row,start in zip(rows,starts):
        assert row['success'] and start==dict(**row,start=0,start_type='one direct NNLS projection')
        assert row['matched_cell']==(row['arm']==f"cell{row['imfit_sampling']}")
        with np.load(root/'comparisons'/(row['case']+'.npz'),allow_pickle=False) as f:
            image,ref,pred=f['template'],f['reference'],f['prediction']
            np.testing.assert_array_equal(image,images[row['render']])
            with np.load(root/f"parent/imfit/parent/renders/{row['shape']}_{row['module']}_s{row['imfit_sampling']}/native.npz") as parent:
                np.testing.assert_array_equal(ref,parent['image'])
            assert row['template_sha256']==c.e.digest(image) and row['reference_sha256']==c.e.digest(ref)
            np.testing.assert_array_equal(pred,row['amplitude']*image)
            residual=pred-ref;np.testing.assert_array_equal(residual,f['residual'])
            assert float(.5*np.sum(residual**2)/np.mean(ref**2))==row['cost']
            assert float(np.sum(image*residual))==row['gradient']
            assert row['amplitude']>=0 and row['gradient']>=-1e-12 and abs(row['amplitude']*row['gradient'])<=1e-12
            assert all(row[k]==v for k,v in c.p.comparison(image,ref).items())
    for pair in pairs:
        a=images[f"{pair['shape']}_{pair['module']}_{pair['left']}"]
        b=images[f"{pair['shape']}_{pair['module']}_{pair['right']}"]
        assert pair['left_sha256']==c.e.digest(a) and pair['right_sha256']==c.e.digest(b)
        assert all(pair[k]==v for k,v in c.p.comparison(a,b).items())
        with np.load(root/'pairwise'/(pair['case']+'.npz')) as f:np.testing.assert_array_equal(f['residual'],a-b)
    manifest=read(root/'image_manifest.json');count=0
    actual={str(f.relative_to(root)) for f in root.rglob('*.npz') if f.relative_to(root).parts[0]!='parent'}
    assert set(manifest)==actual and not list(root.rglob('*.partial'))
    for rel,m in manifest.items():
        assert c.p.sha(root/rel)==m['file_sha256']
        with np.load(root/rel,allow_pickle=False) as f:
            assert set(f.files)==set(m['arrays'])
            for key in f.files:
                a=f[key];assert np.isfinite(a).all()
                assert m['arrays'][key]==dict(shape=list(a.shape),dtype=str(a.dtype),sha256=c.e.digest(a))
                count+=1
    assert count==(392 if n==1 else 328)
    return dict(host_n=n,config=cfg,counts=dict(workers=16,starts=48,pairwise=24,new_arrays=count,
        gaussian_controls=16 if n==1 else 0,failed_workers=0,zero_amplitudes=sum(r['hit_amplitude_zero'] for r in rows)),
        warnings=warnings,runtimes=runtimes,runtime=read(root/'runtime.json'),results=rows,pairwise=pairs,
        file_sha256={str(f.relative_to(root)):c.p.sha(f) for f in sorted(root.rglob('*')) if f.is_file()})


def main():
    p=argparse.ArgumentParser();p.add_argument('--n1',type=Path,required=True);p.add_argument('--n4',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    records=[audit(a.n1,1),audit(a.n4,4)]
    c.e.dump(a.output,dict(scope='Read-only product audit; NOT a GitHub success receipt',artifacts=records))
    print([(x['host_n'],x['counts'],len(x['warnings'])) for x in records])


if __name__=='__main__':main()
