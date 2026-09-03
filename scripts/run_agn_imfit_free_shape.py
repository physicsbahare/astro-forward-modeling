#!/usr/bin/env python3
"""C5o matched-PSF free-shape Imfit preflight; no PSF mismatch or noise."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import time

import numpy as np
from astropy.io import fits

from run_agn_empirical_psf_transfer import PINS, dump
from run_agn_imfit_renderer import IMFIT_ARCHIVE_SHA, unit_sersic_ie

ROOT=Path(__file__).resolve().parents[1]
PARENT_RUN=33717899427
PARENT_COMMIT='88f3fb646a0b89e6cb9b8b8ee1aacae377edca56'
ARTIFACTS={1:9880481087,4:9880386950}
AUDIT=ROOT/'benchmarks/zhuang_shen_2024/empirical_transfer_33717899427.json'
PROTOCOL=ROOT/'benchmarks/zhuang_shen_2024/C5O_PROTOCOL.md'
IMFIT_SHA='57cc48293aeb25e92ed82f600d2c7e15022c81fd0172970648a9ac7a241f7103'
RATIOS=(1.,10.)
MODULES=('A','B')
SHAPE_BOUNDS=dict(pa=(-180.,180.),ell=(0.,.85),n=(.5,6.),re=(.5,60.))
AMPLITUDE_BOUNDS=(0.,1e6)
STARTS=(
    dict(label='truth',pa=-45.,q=.6,n=None,re=16.,host_flux=1.,point_fraction=1.),
    dict(label='compact',pa=0.,q=.8,n=2.,re=8.,host_flux=.5,point_fraction=.8),
    dict(label='extended',pa=-80.,q=.3,n=5.,re=30.,host_flux=1.5,point_fraction=1.2),
)


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def configuration(host_n):
    if host_n not in ARTIFACTS: raise ValueError('host n must be 1 or 4')
    starts=[]
    for s in STARTS:
        row=dict(s); row['n']=float(host_n) if row['n'] is None else row['n']; starts.append(row)
    return dict(stage='C5o matched-PSF free-shape Imfit preflight',
        github_run_id=os.getenv('GITHUB_RUN_ID'),github_sha=os.getenv('GITHUB_SHA'),
        parent_run=PARENT_RUN,parent_commit=PARENT_COMMIT,parent_artifact_id=ARTIFACTS[host_n],
        parent_audit_sha256=sha(AUDIT),protocol_sha256=sha(PROTOCOL),host_n=host_n,
        modules=list(MODULES),ratios=list(RATIOS),starts=starts,stamp=201,
        truth=dict(re=16.,q=.6,pa_deg=45.,host_flux=1.),
        shape_bounds=SHAPE_BOUNDS,amplitude_bounds=AMPLITUDE_BOUNDS,
        centers='fixed at Imfit 1-based (101,101); host and nucleus coincident',
        objective='constant unit noise map; full-crop unweighted pixel-space chi-square',
        psf='archived native fine-Quintic point template; matched module; signed; --no-normalize',
        imfit_version='1.9.0',imfit_archive_sha256=IMFIT_ARCHIVE_SHA,
        imfit_binary_sha256=IMFIT_SHA,imfit_threads=1,timeout_seconds=180,
        pins=PINS,runtime_versions={k:importlib.metadata.version(k) for k in PINS},
        expected_cases=4,expected_starts=12,
        winner='minimum finite recomputed SSE regardless of optimizer exit label',
        acceptance='complete finite provenance/algebra and no amplitude/shape boundary collapse; no recovery band',
        limitations='matched PSF only; nominal anchors only; signed PSF; no noise, mismatch, survey or production claim')


def verified_parent(source,out,host_n):
    receipt=json.loads(AUDIT.read_text())
    if receipt['run_id']!=PARENT_RUN or receipt['commit']!=PARENT_COMMIT or receipt['github_conclusion']!='success':
        raise RuntimeError('unreviewed C5d parent')
    record=next(x for x in receipt['artifacts'] if x['host_n']==host_n)
    for rel,expected in record['file_sha256'].items():
        if sha(source/rel)!=expected: raise RuntimeError('parent checksum mismatch: '+rel)
    if record['artifact_id']!=ARTIFACTS[host_n]: raise RuntimeError('wrong parent artifact')
    dump(out/'parent_manifest.json',dict(run=PARENT_RUN,commit=PARENT_COMMIT,
        artifact_id=record['artifact_id'],file_sha256=record['file_sha256']))


def model_text(host_n,start,ratio):
    q=float(start['q']); n=float(start['n']); re=float(start['re'])
    ie=unit_sersic_ie(n,re,q,2)*4*float(start['host_flux'])
    point=ratio*float(start['point_fraction'])
    lo,hi=AMPLITUDE_BOUNDS
    return '\n'.join([
        'X0 101 fixed','Y0 101 fixed','FUNCTION Sersic # LABEL host',
        f"PA {start['pa']:.17g} {SHAPE_BOUNDS['pa'][0]:g},{SHAPE_BOUNDS['pa'][1]:g}",
        f"ell {1-q:.17g} {SHAPE_BOUNDS['ell'][0]:g},{SHAPE_BOUNDS['ell'][1]:g}",
        f"n {n:.17g} {SHAPE_BOUNDS['n'][0]:g},{SHAPE_BOUNDS['n'][1]:g}",
        f'I_e {ie:.17g} {lo:g},{hi:g}',
        f"r_e {re:.17g} {SHAPE_BOUNDS['re'][0]:g},{SHAPE_BOUNDS['re'][1]:g}",
        'FUNCTION PointSource # LABEL nucleus',f'I_tot {point:.17g} {lo:g},{hi:g}',''])


def parse_bestfit(path):
    rows=[]; center={}; component=None
    for raw in path.read_text().splitlines():
        line=raw.split('#',1)[0].strip()
        if not line: continue
        fields=line.split()
        if fields[0] in ('X0','Y0') and len(fields)>1: center[fields[0]]=float(fields[1])
        elif fields[0]=='FUNCTION': component=fields[1]
        elif component and fields[0] in ('PA','ell','n','I_e','r_e','I_tot'):
            rows.append((component,fields[0],float(fields[1])))
    values={(c,p):v for c,p,v in rows}
    required=[('Sersic',p) for p in ('PA','ell','n','I_e','r_e')]+[('PointSource','I_tot')]
    if any(k not in values for k in required) or center!={'X0':101.,'Y0':101.}:
        raise RuntimeError('incomplete best-fit parameter file')
    return dict(pa=values['Sersic','PA'],q=1-values['Sersic','ell'],n=values['Sersic','n'],
        ie=values['Sersic','I_e'],re=values['Sersic','r_e'],point_flux=values['PointSource','I_tot'])


def bound_hits(p):
    eps=1e-9
    checks={'pa':SHAPE_BOUNDS['pa'],'q':(.15,1.),'n':SHAPE_BOUNDS['n'],'re':SHAPE_BOUNDS['re'],
            'ie':AMPLITUDE_BOUNDS,'point_flux':AMPLITUDE_BOUNDS}
    return [name for name,(lo,hi) in checks.items() if abs(p[name]-lo)<=eps*max(1,abs(lo)) or abs(p[name]-hi)<=eps*max(1,abs(hi))]


def run_start(binary,data,psf,noise,host_n,ratio,start,directory):
    directory.mkdir(parents=True,exist_ok=False)
    cfg=directory/'initial.dat'; cfg.write_text(model_text(host_n,start,ratio))
    best=directory/'bestfit.dat'; model=directory/'model.fits'; residual=directory/'residual.fits'
    cmd=['/usr/bin/timeout','--kill-after=5s','180',str(binary),str(data),'-c',str(cfg),
         '--noise',str(noise),'--psf',str(psf),'--no-normalize','--max-threads','1',
         '--save-params',str(best),'--save-model',str(model),'--save-residual',str(residual),'--quiet']
    dump(directory/'command.json',cmd); t=time.monotonic()
    with (directory/'stdout.txt').open('w') as stdout,(directory/'stderr.txt').open('w') as stderr:
        result=subprocess.run(cmd,stdout=stdout,stderr=stderr,check=False)
    row=dict(label=start['label'],returncode=result.returncode,wall_seconds=time.monotonic()-t)
    if result.returncode!=0 or not all(p.exists() for p in (best,model,residual)):
        row.update(success=False,error='nonzero exit or missing products'); dump(directory/'result.json',row); return row
    pars=parse_bestfit(best)
    with fits.open(data,memmap=False) as h: observed=np.asarray(h[0].data,dtype=float)
    with fits.open(model,memmap=False) as h: predicted=np.asarray(h[0].data,dtype=float)
    with fits.open(residual,memmap=False) as h: saved_residual=np.asarray(h[0].data,dtype=float)
    calc=observed-predicted
    if not all(np.isfinite(x).all() for x in (observed,predicted,saved_residual)):
        raise RuntimeError('nonfinite fit image')
    row.update(success=True,**pars,bound_hits=bound_hits(pars),sse=float(np.sum(calc**2)),
        residual_l1_over_data_l1=float(np.abs(calc).sum()/np.abs(observed).sum()),
        saved_residual_max_abs_error=float(np.max(np.abs(calc-saved_residual))),
        model_sha256=sha(model),residual_sha256=sha(residual),bestfit_sha256=sha(best))
    np.savez_compressed(directory/'images.npz',data=observed,model=predicted,
                        residual=calc,saved_residual=saved_residual)
    dump(directory/'result.json',row); return row


def write_csv(path,rows):
    keys=[]
    for row in rows:
        for k in row:
            if k not in keys: keys.append(k)
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader()
        for row in rows:w.writerow({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in row.items()})


def run(host_n,source,binary,out):
    out.mkdir(parents=True,exist_ok=False); cfg=configuration(host_n); dump(out/'config.json',cfg)
    if cfg['runtime_versions']!=cfg['pins']: raise RuntimeError('dependency pin mismatch')
    if sha(binary)!=IMFIT_SHA: raise RuntimeError('wrong Imfit executable')
    verified_parent(source,out,host_n)
    version=subprocess.run([str(binary),'--version'],capture_output=True,text=True,check=False)
    dump(out/'binary.json',dict(sha256=sha(binary),stdout=version.stdout,stderr=version.stderr,
        returncode=version.returncode))
    if 'version 1.9.0' not in version.stdout: raise RuntimeError('wrong Imfit version')
    with np.load(source/'templates.npz') as z: templates={k:z[k].copy() for k in z.files}
    input_dir=out/'inputs'; input_dir.mkdir(); fits.writeto(input_dir/'noise.fits',np.ones((201,201)),overwrite=False)
    all_rows=[]; winners=[]
    for module in MODULES:
        psf=input_dir/f'psf_{module}.fits'; fits.writeto(psf,templates[f'{module}_fine_quintic_point'],overwrite=False)
        for ratio in RATIOS:
            bundle=source/f'truth{module}_ratio{ratio:g}.npz'
            with np.load(bundle) as z:data=z['data'].copy()
            data_path=input_dir/f'data_{module}_ratio{ratio:g}.fits'; fits.writeto(data_path,data,overwrite=False)
            case=f'n{host_n}_{module}_ratio{ratio:g}'; rows=[]
            for start in cfg['starts']:
                row=run_start(binary,data_path,psf,input_dir/'noise.fits',host_n,ratio,start,out/'fits'/case/start['label'])
                row.update(case=case,module=module,ratio=ratio,true_n=host_n,true_re=16.,true_q=.6,
                           true_pa_imfit=-45.,true_point_flux=ratio)
                rows.append(row); all_rows.append(row); write_csv(out/'fit_starts.csv',all_rows)
            finite=[r for r in rows if r['success'] and np.isfinite(r['sse'])]
            if len(finite)!=len(STARTS): raise RuntimeError('incomplete fit starts')
            winner=dict(min(finite,key=lambda r:r['sse'])); winner['winner']=True; winners.append(winner)
            write_csv(out/'metrics.csv',winners)
    if len(winners)!=4 or len(all_rows)!=12: raise RuntimeError('incomplete experiment')
    dump(out/'summary.json',dict(config=cfg,results=winners,starts=all_rows,
        interpretation='matched-PSF nominal-anchor cross-fitter preflight; convergence is not physical truth'))


def main():
    p=argparse.ArgumentParser(); p.add_argument('--source',type=Path,required=True)
    p.add_argument('--imfit',type=Path,required=True); p.add_argument('--host-n',type=int,choices=(1,4),required=True)
    p.add_argument('--out',type=Path,required=True); a=p.parse_args(); start=time.monotonic()
    try: run(a.host_n,a.source,a.imfit,a.out)
    except Exception as error:
        a.out.mkdir(parents=True,exist_ok=True); dump(a.out/'failure.json',dict(type=type(error).__name__,message=str(error))); raise
    finally:
        a.out.mkdir(parents=True,exist_ok=True); dump(a.out/'runtime.json',dict(wall_seconds=time.monotonic()-start,
            max_resident_set_kib_linux=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


if __name__=='__main__': main()
