"""Predeclared targeted free-parameter clean gate for integrated B/T repair."""
from pathlib import Path
import sys, json
import numpy as np, pandas as pd
project=Path('/home/bahareh/Desktop/Projects/Passive_Spiral')
sys.path.insert(0,str(project/'astro-forward-modeling/scripts'))
import gold91_recovery_audit as a
from integrated_bt_normalization import integrated_component_amplitudes
output=project/'Results/Project_Completion_20261011/corrected_clean_gate'
output.mkdir(exist_ok=True)
ns=a.adapters(project,output)
a.load_functions(Path('/home/bahareh/Downloads/GOLD91_FINAL_v3_exclude_487778_clean_real_E0.ipynb'),[4],ns,{'fit_clean_bd'})
d=pd.read_csv(project/'Results/GOLD91_wavelength_interpolated_v2_branch_specific/tables/GOLD91_wavelength_interpolated_full_results.csv')
ctx=pd.read_csv(project/'Data/forward_z3_GOLD403_v1/context_bank/context_manifest.csv')
fingerprint=a.sha(Path(__file__))
for oid in [10109,215914,629834]:
    path=output/f'ID{oid}.json'
    if path.exists():
        assert json.loads(path.read_text())['fingerprint']==fingerprint
        continue
    r=d.loc[d.source_id==oid].iloc[0];c=ctx.loc[(ctx.tile==r.context_tile)&(ctx.context_id==r.context_id)].iloc[0]
    theta=a.source_theta(project,oid,ns);psf,_=a.context_psf(project,c)
    _,images,totals,_=a.render(r,psf,theta)
    amplitudes=integrated_component_amplitudes(totals,r.input_bt)
    truth=sum(v*im for v,im in zip(amplitudes,images));truth*=1e4/truth.sum()
    meta=dict(label=-999999,x=133.,y=133.,q=float(r.input_disk_q),theta=theta,re_pix=float(r.z3_disk_re_pix),npix=1)
    params=ns['pack_source_params']([ns['one_component_params'](meta,267,float(re),float(n),float(q),fixed_n=n) for n,re,q in [(1,r.z3_disk_re_pix*.03,r.input_disk_q),(4,r.z3_bulge_re_pix*.03,r.input_bulge_q)]])
    result=ns['fit_clean_bd'](truth,psf,meta,params,savename=output/f'ID{oid}_corrected_clean',seed=2026101150+oid)
    result.update(source_id=oid,input_bt=float(r.input_bt),absolute_error=abs(result['bt']-float(r.input_bt)),fingerprint=fingerprint,criterion='inherited pilot abs(delta B/T)<=0.10',pass_gate=abs(result['bt']-float(r.input_bt))<=.1)
    a.atomic_json(path,result)
    print('CHECKPOINT',oid,result['bt'],result['absolute_error'],flush=True)
