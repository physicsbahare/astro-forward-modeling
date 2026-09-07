#!/usr/bin/env python3
"""Read-only C5k image/probe/fit audit; execution status is a separate receipt."""
import argparse
import json
from pathlib import Path
import numpy as np
import run_agn_fourier_grid as experiment
from audit_agn_imfit_renderer import csv_check


def audit(root,host_n,trace_rechecks=None):
    e=experiment.engine;p=experiment.parent;read=e.read
    summary=read(root/'summary.json');cfg=read(root/'config.json')
    expected=experiment.configuration(host_n)
    expected.update(github_run_id=cfg['github_run_id'],github_sha=cfg['github_sha'])
    assert summary['config']==cfg==json.loads(json.dumps(expected))
    assert summary['complete'] and not (root/'failure.json').exists()
    assert not list(root.rglob('*.partial'))
    workers=summary['workers'];rows=summary['results'];starts=summary['starts'];pairs=summary['pairwise']
    assert len(workers)==len(rows)==len(starts)==28 and len(pairs)==84
    assert read(root/'worker_progress.json')==workers
    csv_check(root/'metrics.csv',rows);csv_check(root/'fit_starts.csv',starts);csv_check(root/'pairwise.csv',pairs)
    manifest=read(root/'source_manifest.json')
    parent_record=next(a for a in read(e.AUDIT)['artifacts'] if a['host_n']==host_n)
    assert manifest['artifact_id']==parent_record['artifact_id']
    assert manifest['zip_sha256']==parent_record['zip_sha256']
    for rel,digest in manifest['selected_file_sha256'].items():
        assert digest==parent_record['file_sha256'][rel]==p.sha(root/'parent'/rel)
    historical=next(a for a in read(experiment.LOCAL_RECORD)['artifacts'] if a['host_n']==host_n)
    images={};warnings=[];runtimes=[];traces=[];errors=[];rechecks=[]
    for w in workers:
        directory=root/'renders'/w['name']
        assert read(directory/'process_result.json')==w and w['success'] and w['returncode']==0
        wc=read(directory/'worker_config.json');settings=experiment.arm_config(w['arm'])
        assert wc['arm_config']==json.loads(json.dumps(settings))
        assert wc['timeout_seconds']==120 and wc['address_space_bytes']==6*1024**3
        profiles=read(directory/'profiles.json')
        assert profiles==w['render']['profiles']
        expected_gsp=repr(experiment.galsim.GSParams(**settings['settings']))
        assert all(profile['gsparams']==expected_gsp for profile in profiles.values())
        trace=read(directory/'fft_trace.json')
        expected_trace_count=2 if host_n==1 else 1
        if len(trace)!=expected_trace_count:
            # Never overwrite or silently accept the incomplete original log.
            # Optional separate rechecks must reproduce every image and probe.
            assert trace_rechecks is not None, 'incomplete FFT trace without separate recheck'
            check=trace_rechecks/w['name']
            checked=read(check/'process_result.json')
            assert checked['success'] and checked['returncode']==0
            assert checked['render']==w['render']
            assert read(check/'profiles.json')==profiles
            assert not read(check/'warnings.json')
            check_cfg=read(check/'worker_config.json')
            assert {k:v for k,v in check_cfg.items() if k!='psf_path'}=={k:v for k,v in wc.items() if k!='psf_path'}
            for filename in ('images.npz','probes.npz'):
                with np.load(check/filename,allow_pickle=False) as a,np.load(directory/filename,allow_pickle=False) as b:
                    assert a.files==b.files
                    for key in a.files:np.testing.assert_array_equal(a[key],b[key])
            new_trace=read(check/'fft_trace.json')
            assert len(new_trace)==expected_trace_count and trace==new_trace[:len(trace)]
            rechecks.append(dict(worker=w['name'],original_fft_trace=trace,
                rechecked_fft_trace=new_trace,images_and_probes_bitwise_identical=True,
                file_sha256={str(f.relative_to(check)):p.sha(f) for f in sorted(check.rglob('*')) if f.is_file()}))
            trace=new_trace
        if w['arm']!='replay':
            key=w['case']['name']+'_'+w['module']+'_fine'
            inherited=next(r for r in historical['profiles'] if r['worker']==key)['psf']['maxk_inverse_arcsec']
            forced=inherited*settings['force_maxk_multiplier']
            assert w['render']['radius']['inherited_psf_maxk_inverse_arcsec']==inherited
            assert w['render']['radius']['forced_psf_maxk_inverse_arcsec']==forced
            assert profiles['psf']['maxk_inverse_arcsec']==forced
            assert all(t['wrap_size']>=settings['settings']['minimum_fft_size'] for t in trace)
        traces.append(dict(worker=w['name'],records=trace,profiles=profiles))
        warnings += [dict(worker=w['name'],**warning) for warning in read(directory/'warnings.json')]
        runtimes.append(dict(worker=w['name'],**read(directory/'runtime.json')))
        with np.load(directory/'images.npz',allow_pickle=False) as f:
            image=f['image'].copy();images[w['name']]=image
            assert image.shape==(201,201) and e.digest(image)==w['render']['image_sha256']
            assert p.image_stats(image)==w['render']['image_stats']
            if host_n==1:
                assert e.digest(f['gaussian'])==w['render']['gaussian_sha256']
                assert p.image_stats(f['gaussian'])==w['render']['gaussian_stats']
                assert p.comparison(image,f['gaussian'])==w['render']['gaussian_comparison']
                np.testing.assert_array_equal(f['gaussian_residual'],image-f['gaussian'])
        with np.load(directory/'probes.npz',allow_pickle=False) as f:
            x,y=e.probe_coordinates()
            np.testing.assert_array_equal(f['kx'],x);np.testing.assert_array_equal(f['ky'],y)
            np.testing.assert_array_equal(f['host']*f['psf'],f['product'])
            error=float(np.abs(f['convolution']-f['product']).max())
            assert error==w['render']['fourier_product_max_error'] and error<=1e-12
    for row,start in zip(rows,starts):
        assert start==dict(**row,start=0,start_type='one direct NNLS, not nonlinear multistart')
        assert row['success'] and row['amplitude']>=0
        assert row['hit_amplitude_zero']==(row['amplitude']==0)
        with np.load(root/'comparisons'/(row['case']+'.npz'),allow_pickle=False) as f:
            image,reference,prediction=f['template'],f['reference'],f['prediction']
            np.testing.assert_array_equal(image,images[row['case']])
            with np.load(root/f"parent/renders/{row['shape']}_{row['module']}_fine/nominal_hlr.npz") as r:
                np.testing.assert_array_equal(reference,r['sersic'])
            with np.load(root/f"parent/parent/renders/{row['shape']}_{row['module']}_s8/native.npz") as r:
                assert p.comparison(image,r['image'])==row['comparison_to_imfit8']
            assert e.digest(reference)==row['reference_sha256'] and e.digest(image)==row['template_sha256']
            error=float(np.abs(prediction-row['amplitude']*image).max());errors.append(error)
            assert error<=1e-12
            residual=prediction-reference;np.testing.assert_array_equal(residual,f['residual'])
            assert float(.5*np.sum(residual**2)/np.mean(reference**2))==row['cost']
            assert float(np.sum(image*residual))==row['gradient']
            assert row['gradient']>=-1e-12 and abs(row['amplitude']*row['gradient'])<=1e-12
            assert all(row[k]==v for k,v in p.comparison(image,reference).items())
            assert row['scaled_l1_over_reference_l1']==p.comparison(prediction,reference)['l1_over_reference_l1']
            if row['arm']=='replay':
                assert float(np.abs(image-reference).max())==row['replay_max_abs_error']<=1e-12
    for row in pairs:
        a=images[f"{row['shape']}_{row['module']}_{row['left']}"]
        b=images[f"{row['shape']}_{row['module']}_{row['right']}"]
        assert e.digest(a)==row['left_sha256'] and e.digest(b)==row['right_sha256']
        assert all(row[k]==v for k,v in p.comparison(a,b).items())
        with np.load(root/'pairwise'/(row['case']+'.npz'),allow_pickle=False) as f:
            np.testing.assert_array_equal(f['residual'],a-b)
    manifest=read(root/'image_manifest.json');count=0
    files=[f for f in root.rglob('*.npz') if f.relative_to(root).parts[0]!='parent']
    assert set(manifest)=={str(f.relative_to(root)) for f in files}
    for rel,m in manifest.items():
        assert p.sha(root/rel)==m['file_sha256']
        with np.load(root/rel,allow_pickle=False) as f:
            assert set(f.files)==set(m['arrays'])
            for key in f.files:
                assert np.isfinite(f[key]).all()
                assert m['arrays'][key]==dict(shape=list(f[key].shape),dtype=str(f[key].dtype),sha256=e.digest(f[key]))
                count+=1
    assert len(manifest)==168 and count==(504 if host_n==1 else 392)
    return dict(host_n=host_n,config=cfg,counts=dict(workers=28,renders=28,starts=28,
        gaussian_controls=28 if host_n==1 else 0,pairwise=84,new_arrays=count,
        failed_workers=0,zero_amplitudes=sum(r['hit_amplitude_zero'] for r in rows),
        incomplete_initial_fft_logs=len(rechecks),separate_bitwise_verified_trace_rechecks=len(rechecks)),
        trace_rechecks=rechecks,
        warnings=warnings,runtimes=runtimes,fft_traces=traces,
        max_prediction_reconstruction_error=max(errors),results=rows,pairwise=pairs,
        runtime=read(root/'runtime.json'),
        file_sha256={str(f.relative_to(root)):p.sha(f) for f in sorted(root.rglob('*')) if f.is_file()})


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--n1',type=Path,required=True);parser.add_argument('--n4',type=Path,required=True)
    parser.add_argument('--trace-rechecks',type=Path)
    parser.add_argument('--initial-producer-sha256')
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=dict(scope='Read-only product audit; not a GitHub execution-status confirmation',
        initial_producer_sha256=args.initial_producer_sha256,
        artifacts=[audit(args.n1,1,args.trace_rechecks),audit(args.n4,4,args.trace_rechecks)])
    experiment.engine.dump(args.output,result)
    for a in result['artifacts']:
        print(dict(host_n=a['host_n'],counts=a['counts'],warning_count=len(a['warnings']),runtime=a['runtime'],
            max_rss_kib=max(r['peak_rss_kib'] for r in a['runtimes'])))


if __name__=='__main__':main()
