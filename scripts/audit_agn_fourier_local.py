#!/usr/bin/env python3
"""Retain the complete local C5j diagnostic, including its resource failure.

This is explicitly not a GitHub success receipt or a changed completeness rule.
"""
import argparse
from pathlib import Path
import numpy as np
import run_agn_fourier_controls as experiment
from audit_agn_imfit_renderer import csv_check


def audit(root, host_n):
    read, digest = experiment.read, experiment.digest
    summary = read(root/'summary.json'); cfg = read(root/'config.json')
    assert cfg == summary['config']
    assert cfg['github_run_id'] is None and cfg['github_sha'] is None
    assert cfg['protocol_sha256'] == experiment.parent.sha(experiment.PROTOCOL)
    assert cfg['parent_audit_sha256'] == experiment.parent.sha(experiment.AUDIT)
    assert cfg['pins'] == cfg['runtime_versions']
    workers = summary['workers']; rows = summary['results']; starts = summary['starts']
    assert len(workers) == 36 and read(root/'worker_progress.json') == workers
    assert summary['complete'] == all(w['success'] for w in workers)
    assert (root/'failure.json').exists() == (not summary['complete'])
    csv_check(root/'metrics.csv',rows); csv_check(root/'fit_starts.csv',starts)
    source = read(root/'source_manifest.json')
    record = next(a for a in read(experiment.AUDIT)['artifacts'] if a['host_n']==host_n)
    for rel,sha in source['selected_file_sha256'].items():
        assert sha == record['file_sha256'][rel] == experiment.parent.sha(root/'parent'/rel)
    warnings = []; failures = []; profiles = []; traces = []; errors = []; runtimes = []
    for w in workers:
        d = root/'renders'/w['name']
        assert read(d/'process_result.json') == w
        wc = read(d/'worker_config.json')
        assert wc['arm_config'] == experiment.arm_config(w['arm'])
        assert wc['address_space_bytes'] == 6*1024**3 and wc['timeout_seconds'] == 120
        warnings += [dict(worker=w['name'],**a) for a in read(d/'warnings.json')]
        profiles.append(dict(worker=w['name'],**read(d/'profiles.json')))
        traces.append(dict(worker=w['name'],records=read(d/'fft_trace.json')))
        runtimes.append(dict(worker=w['name'],**read(d/'runtime.json')))
        if not w['success']:
            assert w['returncode'] != 0
            failures.append(dict(**w,stderr=(d/'stderr.txt').read_text(),warnings=read(d/'warnings.json')))
            continue
        assert w['returncode'] == 0
        with np.load(d/'images.npz',allow_pickle=False) as f:
            assert digest(f['image']) == w['render']['image_sha256']
            assert experiment.parent.image_stats(f['image']) == w['render']['image_stats']
            if host_n == 1:
                np.testing.assert_array_equal(f['image']-f['gaussian'],f['gaussian_residual'])
                assert digest(f['gaussian']) == w['render']['gaussian_sha256']
                assert experiment.parent.comparison(f['image'],f['gaussian']) == w['render']['gaussian_comparison']
        with np.load(d/'probes.npz',allow_pickle=False) as f:
            x,y = experiment.probe_coordinates()
            np.testing.assert_array_equal(f['kx'],x); np.testing.assert_array_equal(f['ky'],y)
            np.testing.assert_array_equal(f['host']*f['psf'],f['product'])
            assert float(np.abs(f['convolution']-f['product']).max()) == w['render']['fourier_product_max_error']
    for row,start in zip(rows,starts):
        assert start == dict(**row,start=0,start_type='one direct NNLS, not nonlinear multistart')
        assert row['success'] and row['amplitude']>=0
        assert row['hit_amplitude_zero'] == (row['amplitude']==0)
        with np.load(root/'comparisons'/(row['case']+'.npz'),allow_pickle=False) as f:
            image = f['template']; reference = f['reference']; prediction = f['prediction']
            with np.load(root/'renders'/row['case']/'images.npz') as r:
                np.testing.assert_array_equal(image,r['image'])
            for level in ('coarse','fine'):
                path=root/f"parent/renders/{row['shape']}_{row['module']}_{level}/nominal_hlr.npz"
                with np.load(path) as r:
                    if level=='fine':
                        np.testing.assert_array_equal(reference,r['sersic'])
                    else:
                        assert experiment.parent.comparison(image,r['sersic'])==row['comparison_to_coarse']
            with np.load(root/f"parent/parent/renders/{row['shape']}_{row['module']}_s8/native.npz") as r:
                assert experiment.parent.comparison(image,r['image'])==row['comparison_to_imfit8']
            residual=prediction-reference
            np.testing.assert_array_equal(residual,f['residual'])
            error=float(np.abs(prediction-row['amplitude']*image).max())
            assert error<=1e-12; errors.append(error)
            assert float(.5*np.sum(residual**2)/np.mean(reference**2))==row['cost']
            assert float(np.sum(image*residual))==row['gradient']
            assert abs(row['amplitude']*row['gradient'])<=1e-12 and row['gradient']>=-1e-12
            assert all(row[k]==v for k,v in experiment.parent.comparison(image,reference).items())
    manifest=read(root/'image_manifest.json'); count=0
    for rel,m in manifest.items():
        assert experiment.parent.sha(root/rel)==m['file_sha256']
        with np.load(root/rel,allow_pickle=False) as f:
            assert set(f.files)==set(m['arrays'])
            for key in f.files:
                assert np.isfinite(f[key]).all()
                assert m['arrays'][key]==dict(shape=list(f[key].shape),dtype=str(f[key].dtype),sha256=digest(f[key]))
                count+=1
    assert len(rows)==sum(w['success'] for w in workers)==len(starts)
    assert count==(540 if host_n==1 else 352)
    return dict(host_n=host_n,config=cfg,complete=summary['complete'],
        counts=dict(attempts=len(workers),renders=len(rows),starts=len(starts),
            gaussian_images=36 if host_n==1 else 0,failed_workers=len(failures),new_arrays=count),
        failures=failures,warnings=warnings,profiles=profiles,fft_traces=traces,runtimes=runtimes,
        max_prediction_reconstruction_error=max(errors),results=rows,
        source_manifest=source,runtime=read(root/'runtime.json'),
        file_sha256={str(p.relative_to(root)):experiment.parent.sha(p) for p in sorted(root.rglob('*')) if p.is_file()})


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=dict(scope='LOCAL ONLY: C5j is incomplete, not CI success',date='2026-09-03',
        github_parent_run=experiment.PARENT_RUN,github_parent_commit=experiment.PARENT_COMMIT,
        source_sha256={p:experiment.parent.sha(experiment.ROOT/p) for p in (
            'scripts/run_agn_fourier_controls.py','tests/test_agn_fourier_controls.py',
            'benchmarks/zhuang_shen_2024/C5J_PROTOCOL.md')},
        artifacts=[audit(args.root/f'local_c5j_n{n}',n) for n in (1,4)],
        decision='Retain all results and four resource failures; do not dispatch a known deterministic failing C5j run or alter its settings/completeness')
    experiment.dump(args.output,result)
    print({a['host_n']:a['counts'] for a in result['artifacts']})


if __name__=='__main__':main()
