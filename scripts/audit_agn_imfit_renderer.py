#!/usr/bin/env python3
"""Read-only C5h artifact audit; no optimizer or scientific recovery cut.

GitHub execution conclusions are queried separately from this file audit.
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
from astropy.io import fits
import run_agn_imfit_renderer as experiment

RUN = 33759931812
COMMIT = '391efc236c440e76ed5dcd7c7b7e71e444fea012'
ARTIFACTS = {1:9895134048, 4:9895141857}
ZIP_HASHES = {1:'7fb1f2f443eb34e44811793b2703f80fe0ee1a4b881cc09b80e4efb43479d171',
              4:'545ab085d3e4039cc2fef2827832f7d2a27ad0b02c217871a8e3a64bd1142315'}


def csv_check(path, rows):
    with path.open() as handle:
        actual = list(csv.DictReader(handle))
    assert actual == [{k:'' if v is None else str(v) for k,v in r.items()} for r in rows]


def audit(root, host_n):
    summary = json.loads((root/'summary.json').read_text())
    cfg = json.loads((root/'config.json').read_text())
    expected = experiment.configuration(host_n)
    expected.update(github_run_id=str(RUN), github_sha=COMMIT)
    assert summary['config'] == cfg == json.loads(json.dumps(expected))
    assert cfg['pins'] == cfg['runtime_versions']
    assert (root/'commit.txt').read_text().strip() == COMMIT
    assert summary['complete']
    c5g = json.loads(experiment.AUDIT.read_text())
    parent = next(a for a in c5g['artifacts'] if a['host_n'] == host_n)
    manifest = json.loads((root/'c5g_manifest.json').read_text())
    assert manifest == dict(run=c5g['run_id'], commit=c5g['commit'],
        artifact_id=parent['artifact_id'], file_sha256=parent['file_sha256'])
    c5d = json.loads((root/'source_manifest.json').read_text())
    c5d_record = next(a for a in json.loads((experiment.ROOT/
        'benchmarks/zhuang_shen_2024/empirical_transfer_33717899427.json').read_text())['artifacts']
        if a['artifact_id'] == c5d['artifact_id'])
    assert c5d['run'] == 33717899427 and c5d['file_sha256'] == c5d_record['file_sha256']
    for rel, value in c5d['file_sha256'].items():
        assert experiment.sha(root/'parent'/rel) == value, rel
    binary = json.loads((root/'binary.json').read_text())
    assert binary['sha256'] == experiment.IMFIT_BINARY_SHA
    assert 'version 1.9.0' in binary['stdout']
    for name, value in json.loads((root/'software/manifest.json').read_text()).items():
        assert experiment.sha(root/'software'/name) == value
    renders, rows, starts = summary['renders'], summary['results'], summary['starts']
    assert len(renders) == len(rows) == len(starts) == len(summary['refinement']) == 36
    assert len({r['name'] for r in renders}) == len({r['case'] for r in rows}) == 36
    csv_check(root/'metrics.csv', rows)
    csv_check(root/'fit_starts.csv', starts)
    assert json.loads((root/'render_progress.json').read_text()) == renders
    native = {}
    npz_count = fits_count = 0
    with np.load(root/'parent/templates.npz') as f:
        points = {m:f[m+'_fine_quintic_point'].copy() for m in ('A','B')}
        hosts = {m:f[m+'_fine_quintic_host'].copy() for m in ('A','B')}
    for row in renders:
        directory = root/'renders'/row['name']
        saved = json.loads((directory/'result.json').read_text())
        assert all(row[k] == v for k,v in saved.items())
        assert row['success'] and row['peak_child_rss_kib'] > 0
        assert (directory/'model.dat').read_text() == experiment.model_text(row['case'],row['sampling'])
        command = json.loads((directory/'command.json').read_text())
        assert '--no-normalize' in command and '--no-subsampling' not in command
        assert '--print-fluxes' not in command and '--overpsf' not in command
        assert experiment.sha(directory/'fine.fits') == row['fine_sha256']
        with fits.open(directory/'fine.fits', memmap=False) as f:
            assert f[0].header['BITPIX'] == row['fits_bitpix']
            fine = np.asarray(f[0].data, dtype=float)
        fits_count += 1
        with np.load(directory/'native.npz') as f:
            image = f['image'].copy()
            npz_count += len(f.files)
        np.testing.assert_array_equal(image,experiment.native_from_fine(fine,row['sampling']))
        assert experiment.digest(image) == row['native_sha256']
        assert all(row[k] == v for k,v in experiment.image_stats(image).items())
        native[row['case']['name'],row['module'],row['sampling']] = image
        if (directory/'comparison.npz').exists():
            with np.load(directory/'comparison.npz') as f:
                npz_count += len(f.files)
                assert all(np.isfinite(f[k]).all() for k in f.files)
                np.testing.assert_array_equal(image,f['image'])
                np.testing.assert_array_equal(image-f['reference'],f['residual'])
                key = 'comparison_to_C5d' if row['case']['name']=='truth' else 'comparison_to_exact'
                assert row[key] == experiment.comparison(image,f['reference'])
                if key == 'comparison_to_C5d':
                    np.testing.assert_array_equal(f['reference'],hosts[row['module']])
                else:
                    sigma = np.hypot(row['case']['sigma_arcsec'],
                        row['case']['psf_fwhm']/np.sqrt(8*np.log(2)))
                    expected = experiment.gaussian_effective_samples(sigma,201,.03)
                    np.testing.assert_array_equal(f['reference'],expected)
    for row in summary['refinement']:
        key = (row['case']['name'],row['module'])
        actual = experiment.comparison(native[*key,row['coarse']],native[*key,row['fine']])
        assert all(row[k] == v for k,v in actual.items())
    kernels = json.loads((root/'kernel_manifest.json').read_text())
    assert len(kernels) == 12
    for row in kernels:
        path = root/'kernels'/f"{row['label']}_s{row['sampling']}.fits"
        assert experiment.sha(path) == row['sha256']
        with fits.open(path,memmap=False) as f:
            kernel = np.asarray(f[0].data,dtype=float)
        fits_count += 1
        assert list(kernel.shape) == row['shape'] and np.isfinite(kernel).all()
        assert kernel.sum() == row['signed_sum']
        assert np.abs(kernel).sum() == row['absolute_sum']
        assert int((kernel<0).sum()) == row['negative_pixels']
    max_cost = max_prediction = max_kkt = max_singular = 0.
    for row,start in zip(rows,starts):
        assert start == dict(**row,start=0,start_type='one direct NNLS, not nonlinear multistart')
        with np.load(root/(row['case']+'.npz')) as f:
            npz_count += len(f.files)
            assert len(f.files) == 5 and all(np.isfinite(f[k]).all() for k in f.files)
            data,host,point = f['data'],f['host'],f['point']
            assert experiment.digest(data) == row['data_sha256']
            np.testing.assert_array_equal(host,native['truth',row['fit_module'],row['sampling']])
            np.testing.assert_array_equal(point,points[row['fit_module']])
            prediction = row['host_flux']*host+row['nuclear_flux']*point
            max_prediction = max(max_prediction,float(np.abs(prediction-f['prediction']).max()))
            np.testing.assert_allclose(prediction,f['prediction'],rtol=0,atol=1e-12)
            residual = f['prediction']-data
            np.testing.assert_array_equal(residual,f['residual'])
            cost = float(.5*np.sum(residual**2)/np.mean(data**2))
            max_cost = max(max_cost,abs(cost-row['cost']))
            assert abs(cost-row['cost']) <= 1e-12*max(1.,cost)
            singular = np.linalg.svd(np.column_stack((host.ravel(),point.ravel())),compute_uv=False)
            for key,value in [('template_singular_max',singular[0]),('template_singular_min',singular[-1])]:
                max_singular = max(max_singular,abs(float(value)-row[key]))
                assert abs(float(value)-row[key]) < 1e-12
            for label,template in [('host',host),('nuclear',point)]:
                assert row[label+'_flux'] >= 0
                assert row['hit_'+label+'_flux_zero'] == (row[label+'_flux']==0)
                difference = abs(float(np.sum(template*residual))-row['kkt_'+label+'_gradient'])
                max_kkt = max(max_kkt,difference)
                assert difference < 1e-12
                assert row[label+'_flux_change_from_C5d'] == row[label+'_flux']-row['parent_'+label+'_flux']
    assert npz_count == 252 and fits_count == 48
    return dict(host_n=host_n,artifact_id=ARTIFACTS[host_n],zip_sha256=ZIP_HASHES[host_n],config=cfg,
        counts=dict(renders=36,direct_fits=36,starts=36,npz_arrays=npz_count,fits_arrays=fits_count,
            render_failures=sum(not r['success'] for r in renders),
            unsuccessful_fits=sum(not r['success'] for r in rows),
            zero_host=sum(r['hit_host_flux_zero'] for r in rows),
            zero_nucleus=sum(r['hit_nuclear_flux_zero'] for r in rows)),
        bookkeeping_errors=dict(prediction=max_prediction,cost=max_cost,kkt=max_kkt,singular=max_singular),
        max_render_seconds=max(r['wall_seconds'] for r in renders),
        max_child_rss_kib=max(r['peak_child_rss_kib'] for r in renders),
        fits_precision=sorted({r['fits_bitpix'] for r in renders}),
        runtime=json.loads((root/'runtime.json').read_text()),
        warnings=json.loads((root/'warnings.json').read_text()),
        kernels=kernels,renders=renders,refinements=summary['refinement'],results=rows,
        file_sha256={str(p.relative_to(root)):experiment.sha(p) for p in sorted(root.rglob('*')) if p.is_file()})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--n1',type=Path,required=True)
    parser.add_argument('--n4',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    result = dict(run_id=RUN,commit=COMMIT,
        github_confirmation=dict(observed_date='2026-09-03',status='completed',conclusion='success',
            updated_at='2026-09-03T13:18:02Z',
            jobs=[dict(id=i,status='completed',conclusion='success')
                  for i in (100663437845,100663438269)],
            regression_run=33759932043,regression_conclusion='success',
            source='GitHub connector run and jobs queries; receipt recorded after direct inspection'),
        evidence='Actual downloaded C5h CI artifacts; no image or optimizer rerun',
        artifacts=[audit(args.n1,1),audit(args.n4,4)],
        limitations='Shared signed PSF interpolation; not global convergence, morphology recovery, or photon-ready PSF')
    if args.output:
        experiment.dump(args.output,result)
        print(json.dumps(dict(run_id=RUN,commit=COMMIT,
            artifacts=[dict(host_n=a['host_n'],counts=a['counts'],
                bookkeeping_errors=a['bookkeeping_errors']) for a in result['artifacts']],
            output=str(args.output)),indent=2,allow_nan=False))
    else:
        print(json.dumps(result,indent=2,allow_nan=False))


if __name__=='__main__':
    main()
