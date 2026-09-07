#!/usr/bin/env python3
"""Audit the immutable C5g CI products, without rerunning the optimizer.

Supply the two downloaded, unzipped artifacts; stdout is a reproducible JSON
review. GitHub execution status is a separate, explicitly queried observation.
Checks here are inventory/provenance/algebra, never empirical recovery cuts.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from run_agn_empirical_agn_centroid import configuration, PARENT_AUDIT, CENTROID_AUDIT
from run_agn_empirical_psf_phase import models, digest

RUN = 33740141863
COMMIT = 'de3ed949d3497263c458a897f703d5a5e9a6f295'
ARTIFACTS = {1:9887407188, 4:9887408196}
ZIP_HASHES = {1:'89d9065b0302a1f7833dd9ce7b65817b41a7a992a0e3562d6e8c340be2c6e1d1',
              4:'eaeb3531bc055c896fd1578f99f07894edfff506ef927492b23701a68744dbd9'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_identity(path, rows):
    with path.open() as handle:
        saved = list(csv.DictReader(handle))
    assert len(saved) == len(rows)
    for left, right in zip(saved, rows):
        assert left == {k:'' if v is None else str(v) for k,v in right.items()}


def audit(root, host_n):
    config = json.loads((root/'config.json').read_text())
    expected = configuration(host_n)
    expected.update(github_run_id=str(RUN), github_sha=COMMIT)
    assert config == json.loads(json.dumps(expected))
    assert config['pins'] == config['runtime_versions']
    assert (root/'commit.txt').read_text().strip() == COMMIT
    assert config['parent_audit_sha256'] == sha(PARENT_AUDIT)
    assert config['prerequisite_audit_sha256'] == sha(CENTROID_AUDIT)
    manifest = json.loads((root/'source_manifest.json').read_text())
    parent_record = next(a for a in json.loads(PARENT_AUDIT.read_text())['artifacts']
                         if a['artifact_id'] == config['parent_artifact_id'])
    assert manifest['file_sha256'] == parent_record['file_sha256']
    for rel, value in manifest['file_sha256'].items():
        assert sha(root/'parent'/rel) == value, rel
    summary = json.loads((root/'summary.json').read_text())
    assert summary['config'] == config
    rows, fixed, starts = summary['results'], summary['fixed_results'], summary['starts']
    assert (len(rows), len(fixed), len(starts)) == (12,12,36)
    for name, records in [('metrics',rows),('fixed_metrics',fixed),('fit_starts',starts)]:
        csv_identity(root/(name+'.csv'), records)
    assert {r['case'] for r in rows} == {
        f'n{host_n}_truth{t}_fit{f}_ratio{ratio:g}'
        for t in ('A','B') for f in ('A','B') for ratio in (.1,1.,10.)}
    parent_rows = json.loads((root/'parent/summary.json').read_text())['results']
    arrays_seen = 0
    maxima = dict(prediction=0., residual=0., point=0., cost_relative=0., kkt=0., singular=0.)
    with np.load(root/'parent/templates.npz') as p:
        points = {m:models(p[m+'_normalized_input'])['photutils_cubic'] for m in ('A','B')}
        hosts = {m:p[m+'_fine_quintic_host'].copy() for m in ('A','B')}
    yy,xx = np.indices((201,201),dtype=float)
    for r,b in zip(rows,fixed):
        case = r['case']
        assert b['case'] == case
        ss = [s for s in starts if s['case'] == case]
        assert [s['start'] for s in ss] == [0,1,2]
        winner = min(ss,key=lambda s:s['cost'])
        assert all(r[k] == v for k,v in winner.items())
        progress = json.loads((root/(case+'_starts.json')).read_text())
        for saved,s in zip(progress['starts'],ss):
            assert all(s[k] == v for k,v in saved.items())
        assert all(b[k] == v for k,v in progress['fixed'].items())
        parent = next(p for p in parent_rows if p['truth_module']==r['truth_module'] and
            p['fit_module']==r['fit_module'] and p['agn_to_host']==r['agn_to_host'] and
            p['fit_variant']=='fine_quintic')
        for field in ('cost','host_flux','nuclear_flux'):
            assert b['parent_'+field] == parent[field]
            assert b[field+'_change_from_parent'] == b[field]-parent[field]
            assert r['fixed_'+field] == b[field]
            assert r[field+'_change'] == r[field]-b[field]
        assert r['host_flux_bias'] == r['host_flux']-1.
        assert r['nuclear_flux_fractional_bias'] == r['nuclear_flux']/r['agn_to_host']-1.
        assert r['x_start_range'] == float(np.ptp([s['x'] for s in ss]))
        assert r['y_start_range'] == float(np.ptp([s['y'] for s in ss]))
        assert r['cost_start_range'] == float(np.ptp([s['cost'] for s in ss]))
        with np.load(root/(case+'.npz')) as images:
            assert len(images.files) == 16
            arrays_seen += len(images.files)
            assert all(np.isfinite(images[k]).all() for k in images.files)
            data, host = images['data'],images['host_template']
            assert digest(data) == r['data_sha256'] == parent['data_sha256']
            assert np.array_equal(host,hosts[r['fit_module']])
            with np.load(root/f"parent/truth{r['truth_module']}_ratio{r['agn_to_host']:g}.npz") as p:
                for k in ('data','host_truth','nuclear_truth'):
                    assert np.array_equal(images[k],p[k])
            np.testing.assert_allclose(data,images['host_truth']+images['nuclear_truth'],rtol=0,atol=1e-12)
            for prefix,s in [('fixed',b)]+[(f"start{s['start']}",s) for s in ss]:
                point = images[prefix+'_point_template']
                prediction = s['host_flux']*host + s['nuclear_flux']*point
                residual = prediction-data
                expected_point = points[r['fit_module']].evaluate(xx,yy,1.,100+s.get('x',0),100+s.get('y',0))
                for key,a,z in [('prediction',prediction,images[prefix+'_prediction']),
                                ('residual',residual,images[prefix+'_residual']),('point',point,expected_point)]:
                    maxima[key] = max(maxima[key],float(np.max(np.abs(a-z))))
                    np.testing.assert_allclose(a,z,rtol=0,atol=1e-12)
                cost = float(.5*np.sum(residual**2)/np.mean(data**2))
                maxima['cost_relative'] = max(maxima['cost_relative'],abs(cost-s['cost'])/max(1.,cost))
                assert abs(cost-s['cost']) <= 1e-12*max(1.,cost)
                singular = np.linalg.svd(np.column_stack((host.ravel(),point.ravel())),compute_uv=False)
                for field,val in [('template_singular_max',singular[0]),('template_singular_min',singular[-1])]:
                    maxima['singular'] = max(maxima['singular'],abs(float(val)-s[field]))
                    assert abs(float(val)-s[field]) <= 1e-12
                for name,template in [('host',host),('nuclear',point)]:
                    gradient = float(np.sum(template*residual))
                    maxima['kkt'] = max(maxima['kkt'],abs(gradient-s['kkt_'+name+'_gradient']))
                    assert abs(gradient-s['kkt_'+name+'_gradient']) <= 1e-12
                    assert s['hit_'+name+'_flux_zero'] == (s[name+'_flux']==0)
                    assert s[name+'_flux'] >= 0
                if prefix != 'fixed':
                    assert -1 <= s['x'] <= 1 and -1 <= s['y'] <= 1
                    assert s['hit_centroid_bound'] == bool(s['active_x'] or s['active_y'])
                    assert s['radial_offset_pix'] == float(np.hypot(s['x'],s['y']))
    groups=[]
    for truth in ('A','B'):
        for adopted in ('A','B'):
            group=[r for r in rows if r['truth_module']==truth and r['fit_module']==adopted]
            groups.append(dict(truth_module=truth,fit_module=adopted,
                max_radial_offset_pix=max(r['radial_offset_pix'] for r in group),
                host_flux_range=[min(r['host_flux'] for r in group),max(r['host_flux'] for r in group)],
                max_abs_host_flux_change=max(abs(r['host_flux_change']) for r in group),
                max_xy_start_range=max(max(r['x_start_range'],r['y_start_range']) for r in group),
                max_cost_start_range=max(r['cost_start_range'] for r in group)))
    return dict(host_n=host_n,artifact_id=ARTIFACTS[host_n],zip_sha256=ZIP_HASHES[host_n],
        config=config,counts=dict(winners=len(rows),fixed_fits=len(fixed),starts=len(starts),arrays=arrays_seen,
            unsuccessful_starts=sum(not s['success'] for s in starts),
            start_exceptions=sum(bool(s['exception_type']) for s in starts),
            centroid_bound_winners=sum(r['hit_centroid_bound'] for r in rows),
            host_zero_winners=sum(r['hit_host_flux_zero'] for r in rows),
            nuclear_zero_winners=sum(r['hit_nuclear_flux_zero'] for r in rows)),
        bookkeeping_max_abs_errors=maxima,groups=groups,results=rows,
        fixed_parent_max_abs_host_flux_difference=max(abs(r['host_flux_change_from_parent']) for r in fixed),
        runtime=json.loads((root/'runtime.json').read_text()),
        warnings=json.loads((root/'warnings.json').read_text()),
        point_controls=json.loads((root/'point_controls.json').read_text()),
        file_sha256={str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file()})


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--n1',type=Path,required=True)
    parser.add_argument('--n4',type=Path,required=True)
    args=parser.parse_args()
    result=dict(run_id=RUN,commit=COMMIT,
        artifact_evidence='Actual downloaded C5g CI artifacts; optimizer not rerun',
        artifacts=[audit(args.n1,1),audit(args.n4,4)],
        limitations='Signed-model, fixed-host-shape conditional fits; not physical astrometry, morphology recovery, or global optimality')
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__=='__main__':
    main()
