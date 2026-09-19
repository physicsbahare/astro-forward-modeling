#!/usr/bin/env python3
"""Read-only audit of C5i CI products; no re-render, fit, or recovery cut."""
import argparse
import json
from pathlib import Path

import numpy as np
from astropy.io import fits

import run_agn_compact_renderer as experiment
from audit_agn_imfit_renderer import csv_check

RUN = 33766246396
COMMIT = '169018474ae502a537bc736a64ead778f24e42cd'
ARTIFACTS = {1:9898810716, 4:9898833104}
ZIP_HASHES = {
    1:'49f76606fb0087dd37b3ae60fdd5c7e2fddf0e5af0ebd584029116613f9515c7',
    4:'5768ef50ccd0276501f4fda22e83a5b0c2c0a11fa6953f13d0c4fe80fbcd014a'}


def read(path):
    return json.loads(path.read_text())


def audit(root, host_n):
    summary, cfg = read(root/'summary.json'), read(root/'config.json')
    expected = experiment.configuration(host_n)
    expected.update(github_run_id=str(RUN), github_sha=COMMIT)
    assert summary['config'] == cfg == json.loads(json.dumps(expected))
    assert cfg['pins'] == cfg['runtime_versions']
    assert (root/'commit.txt').read_text().strip() == COMMIT
    assert summary['complete'] and not list(root.rglob('*.partial'))
    assert not (root/'failure.json').exists()
    parent_audit = read(experiment.AUDIT)
    parent = next(a for a in parent_audit['artifacts'] if a['host_n'] == host_n)
    source = read(root/'source_manifest.json')
    assert source['run'] == experiment.PARENT_RUN
    assert source['commit'] == experiment.PARENT_COMMIT
    assert source['parent_audit_sha256'] == experiment.sha(experiment.AUDIT)
    assert source['artifact_id'] == parent['artifact_id']
    assert source['zip_sha256'] == parent['zip_sha256']
    assert source['verified_parent_files'] == len(parent['file_sha256'])
    for rel, value in source['selected_file_sha256'].items():
        assert value == parent['file_sha256'][rel]
        assert experiment.sha(root/'parent'/rel) == value, rel
    with np.load(root/'psfs.npz', allow_pickle=False) as psfs:
        for module in ('A','B'):
            raw = fits.getdata(root/f'parent/parent/source/CEERS_PSF/Pointings12_F444W_Module_{module}.fits')
            np.testing.assert_array_equal(psfs[module], experiment.normalize_psf(raw)[0])

    manifest = read(root/'image_manifest.json')
    files = [p for p in root.rglob('*.npz') if p.relative_to(root).parts[0] != 'parent']
    assert set(manifest) == {str(p.relative_to(root)) for p in files}
    count = 0
    for rel, record in manifest.items():
        assert experiment.sha(root/rel) == record['file_sha256'], rel
        with np.load(root/rel, allow_pickle=False) as f:
            assert set(f.files) == set(record['arrays'])
            for key in f.files:
                array = f[key]
                assert np.isfinite(array).all()
                assert record['arrays'][key] == dict(shape=list(array.shape),
                    dtype=str(array.dtype), sha256=experiment.digest(array))
                count += 1
    assert len(files) == 49 and count == (170 if host_n == 1 else 138)
    workers, renders = summary['workers'], summary['renders']
    rows, starts = summary['results'], summary['starts']
    assert len(workers) == len(summary['refinements']) == 8
    assert len(renders) == 16 and len(rows) == len(starts) == 24
    assert len({r['case'] for r in rows}) == 24
    assert read(root/'worker_progress.json') == workers
    csv_check(root/'metrics.csv', rows)
    csv_check(root/'fit_starts.csv', starts)
    warnings, runtimes = [], []
    for worker in workers:
        directory = root/'renders'/worker['name']
        assert read(directory/'process_result.json') == worker
        assert worker['success'] and worker['returncode'] == 0
        wc = read(directory/'worker_config.json')
        assert wc['case'] == worker['case'] and wc['module'] == worker['module']
        assert wc['accuracy'] == worker['accuracy']
        assert wc['timeout_seconds'] == experiment.TIMEOUT
        assert wc['address_space_bytes'] == experiment.ADDRESS_SPACE_BYTES
        command = read(directory/'command.json')
        assert command[:3] == ['/usr/bin/timeout','--kill-after=5s','120']
        assert Path(command[4]).name == 'run_agn_compact_renderer.py'
        result = read(directory/'result.json')
        assert result == dict(success=True, renders=worker['renders'])
        assert read(directory/'render_progress.json') == worker['renders']
        assert [dict(**r, worker=worker['name']) for r in worker['renders']] == [
            r for r in renders if r['worker'] == worker['name']]
        warnings += [dict(worker=worker['name'], **w) for w in read(directory/'warnings.json')]
        runtime = read(directory/'runtime.json')
        assert runtime['address_space_bytes'] == experiment.ADDRESS_SPACE_BYTES
        assert runtime['wall_seconds'] > 0 and runtime['peak_rss_kib'] > 0
        runtimes.append(dict(worker=worker['name'], **runtime))
    images = {}
    for row in renders:
        directory = root/'renders'/row['worker']
        values = experiment.radius_convention(row['case'], row['convention'])
        assert all(row[k] == v for k,v in values.items())
        with np.load(directory/(row['convention']+'.npz'), allow_pickle=False) as f:
            image = f['sersic'].copy()
            assert image.shape == (201,201) and image.dtype == np.float64
            assert experiment.digest(image) == row['sersic_sha256']
            assert experiment.image_stats(image) == row['sersic_stats']
            images[row['case']['name'], row['module'], row['accuracy'], row['convention']] = image
            if row['case']['n'] == .5:
                assert experiment.digest(f['gaussian']) == row['gaussian_sha256']
                assert experiment.image_stats(f['gaussian']) == row['gaussian_stats']
                assert experiment.comparison(image, f['gaussian']) == row['gaussian_comparison']
                np.testing.assert_array_equal(image-f['gaussian'], f['gaussian_residual'])
    for row in summary['refinements']:
        key = row['case']['name'], row['module']
        coarse = images[*key, 'coarse', row['convention']]
        fine = images[*key, 'fine', row['convention']]
        assert row['coarse_sha256'] == experiment.digest(coarse)
        assert row['fine_sha256'] == experiment.digest(fine)
        assert all(row[k] == v for k,v in experiment.comparison(coarse, fine).items())
        name = f"{key[0]}_{key[1]}_{row['convention']}_refinement.npz"
        with np.load(root/'comparisons'/name, allow_pickle=False) as f:
            np.testing.assert_array_equal(f['coarse'], coarse)
            np.testing.assert_array_equal(f['fine'], fine)
            np.testing.assert_array_equal(f['residual'], coarse-fine)
    errors = dict(prediction=0., cost=0., gradient=0.)
    for row, start in zip(rows, starts):
        assert start == dict(**row, start=0, start_type='one direct NNLS, not nonlinear multistart')
        assert row['solver'] == 'scipy.optimize.nnls' and row['success']
        assert row['amplitude'] >= 0 and row['hit_amplitude_zero'] == (row['amplitude'] == 0)
        with np.load(root/'comparisons'/(row['case']+'.npz'), allow_pickle=False) as f:
            reference, template, prediction = f['reference'], f['template'], f['prediction']
            np.testing.assert_array_equal(reference, images[row['shape'], row['module'], 'fine', row['convention']])
            path = root/f"parent/renders/{row['shape']}_{row['module']}_s{row['imfit_sampling']}/native.npz"
            with np.load(path, allow_pickle=False) as parent_file:
                np.testing.assert_array_equal(template, parent_file['image'])
            assert experiment.digest(reference) == row['reference_sha256']
            assert experiment.digest(template) == row['template_sha256']
            difference = float(np.abs(row['amplitude']*template-prediction).max())
            errors['prediction'] = max(errors['prediction'], difference)
            assert difference <= 1e-12
            residual = prediction-reference
            np.testing.assert_array_equal(f['residual'], residual)
            cost = float(.5*np.sum(residual**2)/np.mean(reference**2))
            gradient = float(np.sum(template*residual))
            errors['cost'] = max(errors['cost'], abs(cost-row['cost']))
            errors['gradient'] = max(errors['gradient'], abs(gradient-row['gradient']))
            assert abs(cost-row['cost']) <= 1e-12*max(1.,cost)
            assert abs(gradient-row['gradient']) <= 1e-12
            assert gradient >= -1e-12 and abs(row['amplitude']*gradient) <= 1e-12
            assert all(row[k] == v for k,v in experiment.comparison(template, reference).items())
            assert row['scaled_l1_over_reference_l1'] == experiment.comparison(prediction, reference)['l1_over_reference_l1']
    convention_changes = []
    for case in experiment.cases(host_n):
        for module in ('A','B'):
            for accuracy in ('coarse','fine'):
                nominal = images[case['name'],module,accuracy,'nominal_hlr']
                equivalent = images[case['name'],module,accuracy,'imfit_bn_equivalent']
                convention_changes.append(dict(case=case,module=module,accuracy=accuracy,
                    **experiment.comparison(equivalent, nominal)))
    return dict(host_n=host_n, artifact_id=ARTIFACTS[host_n], zip_sha256=ZIP_HASHES[host_n],
        config=cfg, counts=dict(workers=8, sersic_images=16, gaussian_images=16 if host_n==1 else 0,
            refinements=8, direct_fits=24, starts=24, new_npz_files=49, new_npz_arrays=count,
            worker_failures=0, zero_amplitudes=sum(r['hit_amplitude_zero'] for r in rows)),
        bookkeeping_errors=errors, warnings=warnings, worker_runtimes=runtimes,
        runtime=read(root/'runtime.json'), renders=renders, refinements=summary['refinements'],
        convention_changes=convention_changes, results=rows, image_manifest=manifest,
        file_sha256={str(p.relative_to(root)):experiment.sha(p) for p in sorted(root.rglob('*')) if p.is_file()})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--n1', type=Path, required=True)
    parser.add_argument('--n4', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = dict(run_id=RUN, commit=COMMIT,
        github_confirmation=dict(observed_date='2026-09-03', status='completed', conclusion='success',
            updated_at='2026-09-03T14:50:10Z',
            jobs=[dict(id=i,status='completed',conclusion='success') for i in (100684749911,100684750112)],
            regression_run=33766246298, regression_conclusion='success',
            source='GitHub connector run/jobs queries; receipt recorded after direct inspection'),
        evidence='Actual downloaded and ZIP-checksummed C5i artifacts; no rendering or optimizer rerun',
        artifacts=[audit(args.n1,1), audit(args.n4,4)],
        limitations='Shared signed effective PSF; renderer sensitivity is not physical recovery or a convergence guarantee')
    experiment.dump(args.output,result)
    for a in result['artifacts']:
        print(json.dumps(dict(host_n=a['host_n'], counts=a['counts'], errors=a['bookkeeping_errors'],
            max_refinement_l1=max(r['l1_over_reference_l1'] for r in a['refinements']),
            max_convention_l1=max(r['l1_over_reference_l1'] for r in a['convention_changes']),
            max_child_rss_kib=max(r['peak_rss_kib'] for r in a['worker_runtimes']),
            warnings=a['warnings'], runtime=a['runtime'])))


if __name__ == '__main__':
    main()
