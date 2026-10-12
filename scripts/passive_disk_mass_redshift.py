"""Observed, conditional mass–redshift demographics; master-notebook entry helper.

No artificial redshifting, fitting, new selection or inverse completeness weights.
The joint multinomial bootstrap preserves nested passive/disk denominators.
"""
from pathlib import Path
import hashlib,json,subprocess,sys,platform,importlib.metadata
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from scipy.stats import norm
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from astropy.stats import binom_conf_interval

def wilson(k,n):
    if not n: return np.nan,np.nan
    low,high=binom_conf_interval(k,n,confidence_level=.95,interval="wilson")
    # Enforce exact analytic endpoints: package rounding can yield +7e-18 at k=0.
    return (0. if k==0 else low),(1. if k==n else high)

SEED=20261012
B=4000

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''): h.update(block)
    return h.hexdigest()

def joint_rates(counts):
    c=np.asarray(counts,float);n=c.sum(axis=-1);p=c[...,0]+c[...,1];d=c[...,0]+c[...,2]
    def div(a,b):return np.divide(a,b,out=np.full(np.broadcast_shapes(a.shape,b.shape),np.nan),where=b>0)
    return dict(pd_all=div(c[...,0],n),passive_all=div(p,n),disk_passive=div(c[...,0],p),passive_disk=div(c[...,0],d))

def shapley_change(p0,d0,p1,d1):
    return (p1-p0)*(d0+d1)/2,(d1-d0)*(p0+p1)/2

def common_support(n,p,min_all=50,min_passive=20):
    return np.all((np.asarray(n)>=min_all)&(np.asarray(p)>=min_passive),axis=-1)

def cell_table(p,ze,me):
    rows=[]
    for j,(ml,mh) in enumerate(zip(me[:-1],me[1:])):
        for i,(zl,zh) in enumerate(zip(ze[:-1],ze[1:])):
            e=p.loc[p.audit_eligible&p.z.between(zl,zh,inclusive='left')&p.logM.between(ml,mh,inclusive='left')]
            q=e[e.native_pair_measurable];pa=q.audit_passive;di=q.audit_disk
            counts=[int((pa&di).sum()),int((pa&~di).sum()),int((~pa&di).sum()),int((~pa&~di).sum())]
            nr=len(e);nm=len(q);npas=int(pa.sum());nd=int(di.sum());k=counts[0]
            r=dict(z_index=i,mass_index=j,z_low=zl,z_high=zh,mass_low=ml,mass_high=mh,
              N_eligible=nr,N_measurable=nm,N_passive=npas,N_passive_eligible=int(e.audit_passive.sum()),
              N_disk=nd,N_passive_disk=k,N_unknown=nr-nm,N_unknown_passive=int((e.audit_passive&~e.native_pair_measurable).sum()),
              N_passive_nondisk=counts[1],N_starforming_disk=counts[2],N_starforming_nondisk=counts[3],completeness_corrected=False)
            for key,kk,nn in [('pd_all',k,nm),('disk_passive',k,npas),('passive_disk',k,nd),('passive_all',npas,nm),('unknown',nr-nm,nr)]:
                low,high=wilson(kk,nn)
                r.update({key:kk/nn if nn else np.nan,key+'_ci95_low':low,key+'_ci95_high':high,key+'_sparse':nn<20,key+'_low_events':min(kk,nn-kk)<5})
            # Fixed measured classifications, unknown disk labels allowed to vary.
            r['pd_all_missing_bound_low']=k/nr if nr else np.nan
            r['pd_all_missing_bound_high']=(k+r['N_unknown_passive'])/nr if nr else np.nan
            r['disk_passive_missing_bound_low']=k/r['N_passive_eligible'] if r['N_passive_eligible'] else np.nan
            r['disk_passive_missing_bound_high']=(k+r['N_unknown_passive'])/r['N_passive_eligible'] if r['N_passive_eligible'] else np.nan
            rows.append(r)
    return pd.DataFrame(rows)

def standardize(t,rng,min_passive=20,draws=B):
    nz=t.z_index.max()+1;nm=t.mass_index.max()+1
    n=t.pivot(index='mass_index',columns='z_index',values='N_measurable').to_numpy()
    p=t.pivot(index='mass_index',columns='z_index',values='N_passive').to_numpy()
    keep=common_support(n,p,50,min_passive)
    if not keep.any():return pd.DataFrame(),None,[]
    mids=np.flatnonzero(keep);sub=t[t.mass_index.isin(mids)].sort_values(['mass_index','z_index'])
    c=sub[['N_passive_disk','N_passive_nondisk','N_starforming_disk','N_starforming_nondisk']].to_numpy().reshape(len(mids),nz,4)
    w=n[keep].sum(axis=1);w=w/w.sum()
    raw=joint_rates(c);point_pd=np.sum(w[:,None]*raw['pd_all'],axis=0);point_p=np.sum(w[:,None]*raw['passive_all'],axis=0)
    boot=np.empty((draws,len(mids),nz,4),int)
    for j in range(len(mids)):
        for i in range(nz):
            nn=int(c[j,i].sum());boot[:,j,i]=rng.multinomial(nn,c[j,i]/nn,size=draws)
    rates=joint_rates(boot);bp=np.sum(w[None,:,None]*rates['passive_all'],axis=1);bpd=np.sum(w[None,:,None]*rates['pd_all'],axis=1)
    bd=bpd/bp
    rows=[]
    for i in range(nz):
        a=sub[sub.z_index==i];r=dict(z_low=a.z_low.iloc[0],z_high=a.z_high.iloc[0],N_measurable=int(a.N_measurable.sum()),N_passive=int(a.N_passive.sum()),N_passive_disk=int(a.N_passive_disk.sum()),min_passive=min_passive,mass_support=','.join(map(str,mids)))
        for key,value,samples in [('pd_all',point_pd[i],bpd[:,i]),('passive_all',point_p[i],bp[:,i]),('disk_passive',point_pd[i]/point_p[i],bd[:,i])]:
            lo,hi=np.quantile(samples,[.025,.975]);r.update({key:value,key+'_ci95_low':lo,key+'_ci95_high':hi})
        rows.append(r)
    refs=[dict(mass_low=me.mass_low.iloc[0],mass_high=me.mass_high.iloc[0],weight=float(w[j]),N_pooled=int(n[mids[j]].sum()),min_passive=min_passive) for j,mid in enumerate(mids) for me in [t[t.mass_index==mid]]]
    return pd.DataFrame(rows),dict(pd=bpd,p=bp,d=bd),refs

def fit_trends(p,ze,me,label):
    t=cell_table(p,ze,me);q=p[p.audit_eligible&p.native_pair_measurable].copy()
    q['zb']=pd.cut(q.z,ze,labels=False,right=False);q['mb']=pd.cut(q.logM,me,labels=False,right=False)
    q=q.merge(t[['z_index','mass_index','N_measurable','N_passive']],left_on=['zb','mb'],right_on=['z_index','mass_index'],validate='many_to_one')
    records=[]
    for name,target,predictor,stratum,selection in [('A_PD_redshift','audit_passive_disk','z','mb',q.N_measurable>=50),('B_disk_passive_mass','audit_disk','logM','zb',(q.N_passive>=20)&q.audit_passive),('C_passive_redshift','audit_passive','z','mb',q.N_measurable>=50)]:
        a=q.loc[selection].copy();x=pd.concat([pd.Series(1.,index=a.index,name='const'),a[[predictor]],pd.get_dummies(a[stratum].astype(int),prefix='stratum',drop_first=True,dtype=float)],axis=1).astype(float)
        model=sm.GLM(a[target].astype(int),x,family=sm.families.Binomial())
        ordinary=model.fit();cluster=model.fit(cov_type='cluster',cov_kwds={'groups':a.tile})
        for cov,fit in [('binomial',ordinary),('tile_cluster',cluster)]:
            beta=fit.params[predictor];ci=fit.conf_int().loc[predictor]
            records.append(dict(variant=label,test=name,covariance=cov,N=len(a),N_events=int(a[target].sum()),N_tiles=a.tile.nunique(),beta=beta,odds_ratio=np.exp(beta),ci95_low=np.exp(ci.iloc[0]),ci95_high=np.exp(ci.iloc[1]),pvalue=fit.pvalues[predictor],converged=fit.converged,model=f'{target} ~ {predictor} + categorical({stratum})'))
    return records

def sfr_match(p,rng):
    q=p[p.audit_eligible&p.native_pair_measurable&p.audit_passive].sort_values('id');d=q[q.audit_disk].copy();c=q[~q.audit_disk].copy()
    dz=d.z.to_numpy()[:,None]-c.z.to_numpy()[None,:];dm=d.logM.to_numpy()[:,None]-c.logM.to_numpy()[None,:]
    allowed=(np.abs(dm)<=.1)&(np.abs(dz)<=.1)
    cost=(dm/.1)**2+(dz/.1)**2
    cost[~allowed]=1e8
    ri,ci=linear_sum_assignment(cost);valid=allowed[ri,ci];ri=ri[valid];ci=ci[valid]
    a=d.iloc[ri].reset_index(drop=True);b=c.iloc[ci].reset_index(drop=True)
    matched=pd.DataFrame(dict(disk_id=a.id,nondisk_id=b.id,disk_z=a.z,nondisk_z=b.z,disk_mass=a.logM,nondisk_mass=b.logM,disk_delta=a.delta_MS,nondisk_delta=b.delta_MS,disk_sfr=a.logSFR,nondisk_sfr=b.logSFR,
       disk_speagle=a.delta_MS_speagle,nondisk_speagle=b.delta_MS_speagle,floor_pair=(a.sfr_l68< -9.9)|(b.sfr_l68< -9.9)))
    summary=[]
    for variant,use in [('all_pairs',np.ones(len(matched),bool)),('exclude_model_floor_pairs',~matched.floor_pair.to_numpy())]:
        m=matched.loc[use];aa=m.disk_delta.to_numpy();bb=m.nondisk_delta.to_numpy();diff=aa-bb;n=len(m)
        boot=rng.integers(0,n,size=(B,n));bc=np.mean(diff[boot],axis=1);bm=np.median(aa[boot],axis=1)-np.median(bb[boot],axis=1)
        null=np.mean(rng.choice([-1,1],size=(20000,n))*diff,axis=1)
        summary.append(dict(variant=variant,N_pairs=n,N_unmatched_disk=len(d)-n,mean_delta_difference=diff.mean(),mean_ci95_low=np.quantile(bc,.025),mean_ci95_high=np.quantile(bc,.975),median_disk=np.median(aa),median_nondisk=np.median(bb),median_difference=np.median(aa)-np.median(bb),median_ci95_low=np.quantile(bm,.025),median_ci95_high=np.quantile(bm,.975),permutation_p=(1+np.sum(np.abs(null)>=abs(diff.mean())))/(len(null)+1),median_logSFR_difference=np.median(m.disk_sfr)-np.median(m.nondisk_sfr),speagle_mean_difference=np.mean(m.disk_speagle-m.nondisk_speagle),mean_mass_imbalance=np.mean(m.disk_mass-m.nondisk_mass),mean_z_imbalance=np.mean(m.disk_z-m.nondisk_z),mass_SMD=np.mean(m.disk_mass-m.nondisk_mass)/np.sqrt((np.var(m.disk_mass)+np.var(m.nondisk_mass))/2),z_SMD=np.mean(m.disk_z-m.nondisk_z)/np.sqrt((np.var(m.disk_z)+np.var(m.nondisk_z))/2),max_abs_mass_difference=np.max(abs(m.disk_mass-m.nondisk_mass)),max_abs_z_difference=np.max(abs(m.disk_z-m.nondisk_z))))
    return matched,pd.DataFrame(summary)

def savefig(fig,out,name):
    fig.tight_layout()
    for ext in ['pdf','png']:fig.savefig(out/f'{name}.{ext}',dpi=240,bbox_inches='tight')
    plt.close(fig)

def figures(t,std,marginal,matched,out,ze,me):
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    for index,key,den,title in [(1,'pd_all','N_measurable','Passive disks / all measurable galaxies'),(2,'disk_passive','N_passive','Disks / measurable passive galaxies')]:
        fig,ax=plt.subplots(figsize=(10,6.8));v=t.pivot(index='mass_index',columns='z_index',values=key).to_numpy()
        image=ax.imshow(np.ma.masked_invalid(v),origin='lower',aspect='auto',cmap='viridis',vmin=0,vmax=np.nanmax(v[t.pivot(index='mass_index',columns='z_index',values=den).to_numpy()>=20]))
        for _,r in t.iterrows():
            i=int(r.z_index);j=int(r.mass_index);value=r[key];n=int(r[den]);k=int(r.N_passive_disk)
            text=f'{100*value:.1f}%\n{k}/{n}\n[{100*r[key+"_ci95_low"]:.1f},{100*r[key+"_ci95_high"]:.1f}]' if n else 'No data\n0/0'
            sparse=r[key+'_sparse'] or r[key+'_low_events']
            if sparse:ax.add_patch(Rectangle((i-.5,j-.5),1,1,facecolor='white',alpha=.65,hatch='//',edgecolor='gray',linewidth=.3))
            ax.text(i,j,text,ha='center',va='center',fontsize=8,color='black' if sparse or not np.isfinite(value) or value<np.nanmax(v)*.55 else 'white')
        ax.set_xticks(range(len(ze)-1),[f'{a:g}–{b:g}' for a,b in zip(ze[:-1],ze[1:])]);ax.set_yticks(range(len(me)-1),[f'{a:g}–{b:g}' for a,b in zip(me[:-1],me[1:])]);ax.set_xlabel('Source redshift interval');ax.set_ylabel(r'$\log_{10}(M_\star/M_\odot)$ interval');ax.set_title(title+'\nObserved conditional; counts k/n; Wilson 95% intervals (%)',fontsize=11)
        fig.colorbar(image,ax=ax,label='Observed fraction');fig.text(.5,.01,'Hatching: denominator <20 or fewer than5 events/non-events. Empty cells are not zero.',ha='center',fontsize=9)
        savefig(fig,out,f'figure{index}_'+('passive_disk_mass_redshift' if index==1 else 'disk_among_passive_mass_redshift'))
    fig,axes=plt.subplots(2,2,figsize=(11,8),sharex=True,sharey=True)
    for j,ax in enumerate(axes.ravel()):
        a=t[t.mass_index==j];good=~a.pd_all_sparse;g=a[good];x=(g.z_low+g.z_high)/2;y=g.pd_all
        ax.errorbar(x,100*y,yerr=100*np.vstack([y-g.pd_all_ci95_low,g.pd_all_ci95_high-y]),fmt='o-',capsize=3,color='#176e85')
        for _,r in g.iterrows():ax.annotate(f'{int(r.N_passive_disk)}/{int(r.N_measurable)}'+('*' if r.pd_all_low_events else ''),((r.z_low+r.z_high)/2,100*r.pd_all),xytext=(0,8),textcoords='offset points',ha='center',fontsize=8)
        ax.set_title(f'{me[j]:g} ≤ log M < {me[j+1]:g}');ax.set_ylim(bottom=0);ax.set_xlim(0,3)
    for ax in axes[-1]:ax.set_xlabel('Source redshift')
    for ax in axes[:,0]:ax.set_ylabel('Passive disks / all (%)')
    fig.suptitle('Fixed mass intervals: observed conditional fractions\nWilson95%; * fewer than5 events/non-events; denominator<20 omitted',fontsize=11)
    savefig(fig,out,'figure3_redshift_at_fixed_mass')
    fig,axes=plt.subplots(2,3,figsize=(13,8),sharex=True,sharey=True)
    for i,ax in enumerate(axes.ravel()):
        a=t[t.z_index==i];g=a[~a.disk_passive_sparse];x=(g.mass_low+g.mass_high)/2;y=g.disk_passive
        ax.errorbar(x,100*y,yerr=100*np.vstack([y-g.disk_passive_ci95_low,g.disk_passive_ci95_high-y]),fmt='o-',capsize=3,color='#7b4c89')
        for _,r in g.iterrows():ax.annotate(f'{int(r.N_passive_disk)}/{int(r.N_passive)}'+('*' if r.disk_passive_low_events else ''),((r.mass_low+r.mass_high)/2,100*r.disk_passive),xytext=(0,8),textcoords='offset points',ha='center',fontsize=8)
        ax.set_title(f'{ze[i]:g} ≤ z < {ze[i+1]:g}');ax.set_ylim(bottom=0);ax.set_xlim(9.4,11.7)
    for ax in axes[-1]:ax.set_xlabel(r'$\log_{10}(M_\star/M_\odot)$')
    for ax in axes[:,0]:ax.set_ylabel('Disks / passive (%)')
    fig.suptitle('Fixed redshift intervals: Wilson95%; denominator<20 omitted; * low-event cell',fontsize=11)
    savefig(fig,out,'figure4_mass_at_fixed_redshift')
    fig,axes=plt.subplots(1,3,figsize=(13,4.8));x=(std.z_low+std.z_high)/2
    for ax,key,title in zip(axes,['pd_all','passive_all','disk_passive'],['Passive disks / all','Passive / all','Disks / passive (effective)']):
        y=std[key];ax.errorbar(x,100*y,yerr=100*np.vstack([y-std[key+'_ci95_low'],std[key+'_ci95_high']-y]),fmt='o-',capsize=3,label='Fixed mass mix10–11',color='#176e85')
        a=marginal;my=a[key];ax.errorbar((a.z_low+a.z_high)/2,100*my,yerr=100*np.vstack([my-a[key+'_ci95_low'],a[key+'_ci95_high']-my]),fmt='s--',capsize=3,label='Original marginal9.5–13',color='#ac6a2b')
        ax.set_title(title);ax.set_xlabel('Source redshift');ax.set_ylim(bottom=0)
    axes[0].set_ylabel('Observed conditional fraction (%)');axes[0].legend(fontsize=8)
    fig.suptitle('Mass standardization: fixed pooled measurable mass weights; multinomial95% intervals\nEffective D/P = standardized PD/all ÷ standardized P/all; no completeness correction',fontsize=10)
    savefig(fig,out,'figure5_mass_standardized_redshift')
    fig,axes=plt.subplots(1,3,figsize=(14,4.8))
    axes[0].scatter(matched.nondisk_mass,matched.nondisk_sfr,s=10,alpha=.35,color='#8b648e',label='Matched passive non-disk');axes[0].scatter(matched.disk_mass,matched.disk_sfr,s=12,alpha=.5,color='#176e85',label='Passive disk');axes[0].set_xlabel(r'$\log_{10}(M_\star/M_\odot)$');axes[0].set_ylabel(r'$\log_{10}({\rm SFR}/M_\odot\,{\rm yr}^{-1})$');axes[0].legend(fontsize=8);axes[0].set_title(f'{len(matched)} one-to-one matched pairs')
    for name,color in [('disk_delta','#176e85'),('nondisk_delta','#8b648e')]:
        a=np.sort(matched[name]);axes[1].step(a,np.arange(1,len(a)+1)/len(a),where='post',color=color,label=name.split('_')[0])
    axes[1].set_xlabel(r'$\Delta_{\rm MS}$ (dex)');axes[1].set_ylabel('Cumulative matched fraction');axes[1].set_title('Matched ΔMS distributions');axes[1].legend(fontsize=8)
    diff=matched.disk_delta-matched.nondisk_delta;axes[2].hist(diff,bins=np.arange(-10,10.5,.5),color='#176e85',alpha=.7);axes[2].axvline(0,color='black',ls=':');axes[2].set_xlabel(r'Paired $\Delta_{\rm MS,disk}-\Delta_{\rm MS,non-disk}$');axes[2].set_ylabel('Pairs');axes[2].set_title('Paired SED-model offset contrasts')
    fig.suptitle('Matched within0.1dex mass and0.1redshift; without replacement\nModel-floor values retained and flagged; these are not direct SFR limits or quenching timescales',fontsize=10)
    savefig(fig,out,'figure6_matched_SFR_mass_offsets')

def run(project,out):
    project=Path(project);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    sci=project/'Results/Project_Completion_20261011/science_products';comp=project/'Results/Project_Completion_20261011/corrected_GOLD403_reviewed_v1/completeness'
    manifest=json.loads((sci/'analysis_execution_manifest.json').read_text());config=json.loads((sci/'frozen_analysis_config.json').read_text());assert config==manifest['config']
    ze=config['z_bins'];me=config['mass_bins'];parent_path=sci/'parent_verified_observed_catalog.csv'
    creceipt=json.loads((comp/'completeness_assessment_receipt.json').read_text())
    assert sha(parent_path)==creceipt['parent_table_sha256']
    assert sha(project/'astro-forward-modeling/scripts/passive_disk_project_analysis.py')==manifest['code_file_sha256']
    assert sha(project/'astro-forward-modeling/scripts/assess_native_completeness.py')==creceipt['code_sha256']
    gold_path=project/'Data/passive_disk_GOLD403_with_visual_flags.csv';assert sha(gold_path)==manifest['inputs'][str(gold_path)]
    params=dict(seed=SEED,bootstrap=B,bin_edges_z=ze,bin_edges_mass=me,min_standardized_all=50,min_standardized_passive=20,matching_mass_caliper=.1,matching_z_caliper=.1,conditional=True,completeness_corrected=False)
    paths=[parent_path,gold_path,sci/'observed_conditional_fractions.csv',sci/'GOLD403_SFR_offset_summaries.csv',sci/'frozen_analysis_config.json',sci/'analysis_execution_manifest.json',comp/'conditional_mass_to_light_limits.csv',comp/'completeness_assessment_receipt.json',comp/'frozen_completeness_config.json',Path(__file__),project/'astro-forward-modeling/scripts/passive_disk_project_analysis.py',out/'ANALYSIS_PROTOCOL.md']
    identity={str(a):sha(a) for a in paths}
    guard=out/'execution_manifest.json'
    if guard.exists():
        old=json.loads(guard.read_text());assert old['inputs']==identity and old['parameters']==params,'Method/input changed: use a new output version'
        for name,digest in old['outputs'].items():assert sha(out/name)==digest,'Changed checkpoint output: '+name
        return old['summary']
    p=pd.read_csv(parent_path,low_memory=False);gold=pd.read_csv(gold_path,low_memory=False)
    assert not p.id.duplicated().any()
    assert set(p.loc[p.audit_eligible&p.audit_passive_disk,'id'])==set(gold.id) and len(gold)==403
    matchedgold=gold[['id','z','logM','logSFR']].merge(p[['id','z','logM','logSFR']],on='id',validate='one_to_one',suffixes=('_gold','_parent'))
    for col in ['z','logM','logSFR']:assert np.allclose(matchedgold[col+'_gold'],matchedgold[col+'_parent'],rtol=0,atol=1e-10)
    t=cell_table(p,ze,me);t.to_csv(out/'mass_redshift_fractions.csv',index=False)
    q=p[p.audit_eligible&p.native_pair_measurable].copy();q['audit_passive_disk']=q.audit_passive&q.audit_disk
    old=pd.read_csv(sci/'observed_conditional_fractions.csv')
    for _,r in old.iterrows():
        a=t[t.z_low.eq(r.bin_low)] if r.dimension=='redshift' else t[t.mass_low.eq(r.bin_low)]
        numerator=a.N_passive_disk.sum();denominator=a[{'passive_disk_among_all':'N_measurable','disk_among_passive':'N_passive','passive_among_disks':'N_disk'}[r.estimand]].sum()
        assert numerator==r.k and denominator==r.n
    marginal=cell_table(p,ze,[me[0],me[-1]]);marginal.to_csv(out/'marginal_redshift_decomposition.csv',index=False)
    rng=np.random.default_rng(SEED);std,boot,refs=standardize(t,rng);assert len(std)==6
    std.to_csv(out/'mass_standardized_trends.csv',index=False);pd.DataFrame(refs).to_csv(out/'reference_mass_weights.csv',index=False)
    a=std.iloc[0];b=std.iloc[-1];pc,dc=shapley_change(a.passive_all,a.disk_passive,b.passive_all,b.disk_passive)
    bp,bd=shapley_change(boot['p'][:,0],boot['d'][:,0],boot['p'][:,-1],boot['d'][:,-1]);change=boot['pd'][:,-1]-boot['pd'][:,0]
    dec=[]
    for name,value,samples in [('total_pd_change',b.pd_all-a.pd_all,change),('passive_fraction_contribution',pc,bp),('disk_within_passive_contribution',dc,bd)]:
        lo,hi=np.quantile(samples,[.025,.975]);dec.append(dict(component=name,change=value,ci95_low=lo,ci95_high=hi,share_of_total_change=value/(b.pd_all-a.pd_all),comparison='z0–0.5 to2.5–3; fixed mass10–11'))
    pd.DataFrame(dec).to_csv(out/'standardized_change_decomposition.csv',index=False)
    records=fit_trends(p,ze,me,'primary')
    records+=fit_trends(p,[0,1,2,3],[9.5,10.5,11.5,13],'deterministic_coarse_bins')
    restricted=p.copy();restricted['audit_eligible']=restricted.audit_eligible&restricted.logM.between(10,11,inclusive='left')
    records+=fit_trends(restricted,ze,me,'common_mass10_11')
    # Eligibility quality/depth restrictions are sensitivities, never replacement cuts.
    wmedian=p.loc[p.audit_eligible&(p.wht_f444w>0),'wht_f444w'].median()
    variants={'F444W_bright':p.mag_model_f444w<27.5,'photoz_width_below_01':p.photoz_interval_valid&(p.photoz_relative_width<.1),'higher_relative_WHT':p.wht_f444w>=wmedian}
    for name,use in variants.items():
        x=p.copy();x['audit_eligible']=x.audit_eligible&use;records+=fit_trends(x,ze,me,name)
    coarse=cell_table(p,[0,1,2,3],[9.5,10.5,11.5,13]);coarse.to_csv(out/'deterministic_coarse_fractions.csv',index=False)
    sen=[]
    for cut in [10,20,50]:
        s,_,r=standardize(t,rng,min_passive=cut,draws=1000)
        if len(s):s['variant']=f'min_passive_{cut}';sen.append(s)
    for name,use in variants.items():
        x=p.copy();x['audit_eligible']=x.audit_eligible&use;s,_,r=standardize(cell_table(x,ze,me),rng,draws=1000)
        if len(s):s['variant']=name;sen.append(s)
    pd.concat(sen,ignore_index=True).to_csv(out/'standardization_sensitivity.csv',index=False)
    # Bin-migration sensitivity: independent Gaussian approximations, labels frozen.
    migration=[];zsig=(p.zpdf_u68-p.zpdf_l68)/2;msig=(p.mass_u68-p.mass_l68)/2
    valid=p.audit_eligible&p.photoz_interval_valid&p.mass_interval_valid
    for k in range(100):
        x=p.copy();x.loc[valid,'z']=rng.normal(p.loc[valid,'z'],zsig[valid]);x.loc[valid,'logM']=rng.normal(p.loc[valid,'logM'],msig[valid])
        x['audit_eligible']=x.audit_eligible&x.z.between(0,3,inclusive='left')&x.logM.between(9.5,13,inclusive='left')
        for i in range(6):
            a=x.loc[x.audit_eligible&x.native_pair_measurable&x.z.between(ze[i],ze[i+1],inclusive='left')&x.logM.between(10,11,inclusive='left')]
            # Apply original reference mass mix, never refit support per perturbation.
            rr=[]
            for ref in refs:
                c=a[a.logM.between(ref['mass_low'],ref['mass_high'],inclusive='left')];rr.append(ref['weight']*c.audit_passive_disk.mean())
            migration.append(dict(draw=k,z_low=ze[i],pd_all=sum(rr)))
    migration=pd.DataFrame(migration);mig=migration.groupby('z_low').pd_all.agg(median='median',p025=lambda x:x.quantile(.025),p975=lambda x:x.quantile(.975)).reset_index();mig['scope']='independent interval Gaussian bin migration; fixed labels/reference weights; not calibrated posterior';mig.to_csv(out/'mass_photoz_migration_sensitivity.csv',index=False)
    matched,sfr=sfr_match(p,rng);matched.to_csv(out/'matched_SFR_pairs_LOCAL_ONLY.csv',index=False);sfr.to_csv(out/'matched_SFR_comparison.csv',index=False)
    cell_sfr=[]
    for _,r in t.iterrows():
        for name,group in [('passive_disk',q[q.audit_passive&q.audit_disk]),('passive_nondisk',q[q.audit_passive&~q.audit_disk])]:
            c=group[group.z.between(r.z_low,r.z_high,inclusive='left')&group.logM.between(r.mass_low,r.mass_high,inclusive='left')];n=len(c);x=c.delta_MS.to_numpy()
            ci=np.quantile(np.median(rng.choice(x,size=(1000,n)),axis=1),[.025,.975]) if n>=5 else [np.nan,np.nan]
            cell_sfr.append(dict(z_low=r.z_low,z_high=r.z_high,mass_low=r.mass_low,mass_high=r.mass_high,population=name,N=n,median_delta_MS=np.median(x) if n else np.nan,p16=np.quantile(x,.16) if n else np.nan,p84=np.quantile(x,.84) if n else np.nan,median_ci95_low=ci[0],median_ci95_high=ci[1],N_floor=int((c.sfr_l68< -9.9).sum()),N_valid_interval=int(c.sfr_interval_valid.sum()),sparse=n<5))
    pd.DataFrame(cell_sfr).to_csv(out/'SFR_mass_redshift_cell_summaries.csv',index=False)
    test=pd.DataFrame(records)
    # Holm correction for the four primary questions, cluster sensitivity as conservative primary.
    primary=test[(test.variant=='primary')&(test.covariance=='tile_cluster')]
    pp=primary.pvalue.tolist()+[sfr.iloc[0].permutation_p];adjust=multipletests(pp,method='holm')[1]
    test['primary_Holm_p']=np.nan
    test.loc[primary.index,'primary_Holm_p']=adjust[:3]
    test.to_csv(out/'statistical_tests.csv',index=False)
    sfr['primary_Holm_p']=[adjust[3],np.nan];sfr.to_csv(out/'matched_SFR_comparison.csv',index=False)
    limits=pd.read_csv(comp/'conditional_mass_to_light_limits.csv');limits.to_csv(out/'reused_conditional_mass_to_light_limits.csv',index=False)
    assess=[]
    for i in range(6):
        l=limits[(limits.z_low==ze[i])&(limits.population=='NUVrJ_quiescent')];boundary=l.ci95_high.max();e=p[p.audit_eligible&p.z.between(ze[i],ze[i+1],inclusive='left')]
        assess.append(dict(z_low=ze[i],z_high=ze[i+1],max_quiescent_ML_ci95_across_depth=boundary,parent_mass_floor=9.5,parent_floor_above_conditional_boundary=9.5>boundary,N_eligible=len(e),N_fainter_than_benchmark=int((e.mag_model_f444w>=27.5).sum()),N_nonpositive_or_missing_WHT=int((~(e.wht_f444w>0)).sum()),morphology_unknown_fraction=(~e.native_pair_measurable).mean(),passive_morphology_eligibility=e.loc[e.audit_passive,'native_pair_measurable'].mean(),nonpassive_morphology_eligibility=e.loc[~e.audit_passive,'native_pair_measurable'].mean(),validated_mass_completeness=False,correction_applied=False))
    assessment=pd.DataFrame(assess);assessment.to_csv(out/'mass_completeness_assessment.csv',index=False)
    figures(t,std,marginal,matched,out,ze,me)
    a=std.iloc[0];b=std.iloc[-1]
    summary=dict(N_eligible=int(p.audit_eligible.sum()),N_measurable=len(q),N_passive_disk=403,N_matched_pairs=len(matched),standardized_mass_range=[10,11],standardized_first=a.pd_all,standardized_last=b.pd_all,standardized_endpoint_difference=b.pd_all-a.pd_all,endpoint_difference_ci95=np.quantile(change,[.025,.975]).tolist(),passive_contribution_share=pc/(b.pd_all-a.pd_all),sfr_mean_difference=sfr.iloc[0].mean_delta_difference,sfr_mean_ci95=[sfr.iloc[0].mean_ci95_low,sfr.iloc[0].mean_ci95_high],sfr_median_difference=sfr.iloc[0].median_difference,all_marginal_counts_reconciled=True,completeness_corrected=False)
    write_report(out,summary,std,marginal,dec,test,sfr,assessment,mig)
    outputs={a.name:sha(a) for a in sorted(out.iterdir()) if a.is_file() and a.name not in ['execution_manifest.json','ANALYSIS_PROTOCOL.md']}
    result=dict(status='VALIDATED_OBSERVED_CONDITIONAL_ANALYSIS; INTRINSIC_DEMOGRAPHICS_UNCALIBRATED',utc=datetime.now(timezone.utc).isoformat(),inputs=identity,parameters=params,outputs=outputs,summary=summary,git_base=subprocess.check_output(['git','-C',str(project/'astro-forward-modeling'),'rev-parse','HEAD'],text=True).strip(),environment={k:importlib.metadata.version(k) for k in ['numpy','pandas','scipy','astropy','matplotlib','statsmodels']},python=platform.python_version(),parent_provenance=manifest,mass_completeness_receipt=creceipt)
    guard.write_text(json.dumps(result,indent=2)+'\n')
    return summary

def write_report(out,s,std,marginal,dec,test,sfr,assessment,mig):
    a=std.iloc[0];b=std.iloc[-1]
    fmt=lambda x:f'{100*x:.2f}%'
    primary_mass=test[(test.variant=='primary')&(test.test=='B_disk_passive_mass')&(test.covariance=='tile_cluster')].iloc[0]
    common_z=test[(test.variant=='common_mass10_11')&(test.test=='A_PD_redshift')&(test.covariance=='tile_cluster')].iloc[0]
    lines=['# Passive disks: joint observed mass–redshift demographics','',
    f'## Sample and scope\nThe frozen native sample contains {s["N_eligible"]:,} eligible galaxies, {s["N_measurable"]:,} with paired-band measurable morphology, and403 passive disks. All36 published marginal rows reconcile exactly. These are observed conditional fractions, not intrinsic population estimates. Quiescent non-disks are galaxies failing the conjunction of the fixed disk cuts; they are not necessarily pure bulges.',
    '## A. Redshift at fixed mass',
    f'For the common mass10–11 range, the fixed-reference passive-disk fraction changes from {fmt(a.pd_all)} (95% [{fmt(a.pd_all_ci95_low)}, {fmt(a.pd_all_ci95_high)}]) at0<z<0.5 to {fmt(b.pd_all)} ([{fmt(b.pd_all_ci95_low)}, {fmt(b.pd_all_ci95_high)}]) at2.5<z<3. The difference is {100*s["standardized_endpoint_difference"]:.2f} percentage points (95% {100*s["endpoint_difference_ci95"][0]:.2f}, {100*s["endpoint_difference_ci95"][1]:.2f}). This controls coarse mass mix only within the stated support.',
    f'The original all-mass marginal endpoints are {fmt(marginal.iloc[0].pd_all)} and {fmt(marginal.iloc[-1].pd_all)}; direct attenuation comparisons also change mass coverage, so they are not a pure adjustment effect.',
    f'The redshift-slope sensitivity within exactly10–11 gives odds ratio {common_z.odds_ratio:.3f} per unit z (tile-cluster95% {common_z.ci95_low:.3f}–{common_z.ci95_high:.3f}, nominal p={common_z.pvalue:.4g}). It favors a negative average slope, but the six-bin trend is non-monotonic and the endpoint-difference interval includes zero. Thus the data support a weaker conditional average decline, not a demonstrated decline in every mass/redshift interval. This secondary model is not independently multiplicity-adjusted.',
    f'## B. Mass at fixed redshift\nAcross supported passive cells, the disk odds ratio per dex mass is {primary_mass.odds_ratio:.3f} (tile-cluster95% {primary_mass.ci95_low:.3f}–{primary_mass.ci95_high:.3f}, Holm p={primary_mass.primary_Holm_p:.3g}). Lower-mass passive galaxies are more likely to satisfy the fixed disk rule within the observed measurable sample.\nThe supported-cell logistic results below summarize the continuous mass slope with redshift-bin intercepts. Odds ratios are per dex mass or per unit redshift. Tile-cluster uncertainties address within-tile dependence approximately (20tiles), not full cosmic variance. Models assume one common linear log-odds slope; cell figures and coarse-bin sensitivities must be read alongside them.',
    '```\n'+test[(test.variant=='primary')].to_string(index=False)+'\n```',
    '## C. Decomposition',
    f'The standardized passive fraction decreases from {fmt(a.passive_all)} to {fmt(b.passive_all)}, while effective disk/passive changes from {fmt(a.disk_passive)} to {fmt(b.disk_passive)}. The point decomposition attributes the decline to the passive fraction, partly offset by a rising disk/passive factor. The latter contribution is uncertain and consistent with either sign; the net endpoint decline is also uncertain. Contribution shares can exceed100% when factors oppose and become unstable if the total change approaches zero.',
    'Within the standardized reference, PD/all = P/all × effective D/P holds exactly. Effective D/P is the ratio of standardized PD/all to standardized P/all; it is not an independently mass-weighted passive disk fraction. Symmetric additive endpoint contributions (fractions, not percentage points) are:',
    '```\n'+pd.DataFrame(dec).to_string(index=False)+'\n```',
    'These contributions describe the observed joint counts. They do not identify quenching mechanisms, transformations of individual galaxies or evolutionary progenitors.',
    '## D. Matched SFR–mass comparison',
    f'All403 disks have unique within-caliper controls. The paired mean disk-minus-nondisk ΔMS is {sfr.iloc[0].mean_delta_difference:.3f}dex (95% {sfr.iloc[0].mean_ci95_low:.3f}–{sfr.iloc[0].mean_ci95_high:.3f}; permutation p={sfr.iloc[0].permutation_p:.3f}). The matched median contrast is {sfr.iloc[0].median_difference:.3f}dex (95% {sfr.iloc[0].median_ci95_low:.3f}–{sfr.iloc[0].median_ci95_high:.3f}). No statistically distinguishable contrast is established; non-detection does not prove identical populations.',
    'One-to-one optimal matching without replacement uses0.1dex mass and0.1redshift calipers. Positive disk-minus-nondisk contrasts mean less suppressed catalog-model SFR for passive disks. Bootstrap resamples complete pairs; sign-flip p values assume paired exchangeability. Matching does not balance dust, environment, SED priors or residual within-caliper covariates. Conditioning on the same passive threshold truncates both distributions.',
    '```\n'+sfr.to_string(index=False)+'\n```',
    'The excluded-floor variant is a sensitivity only, not a censored-data estimator. There are no trustworthy observational SFR upper-limit flags in these inputs. Model-floor precision and posterior uncertainty are not calibrated direct-SFR constraints. Neither median differences nor significance measures quenching timescales.',
    '## Mass completeness and eligibility',
    'The previously verified faintest30% /95th-percentile mass-to-light diagnostic uses F444W27.5 and separate NUVrJ populations, with relative WHT quartiles. Its upper confidence envelope remains below9.5. This is consistent with the chosen mass floor under that conditional diagnostic; it cannot prove mass/detection completeness. The magnitude benchmark is approximately80% detection in the published selection, which differs from this inherited sample. No inverse completeness weights are used.',
    'Source methods: [COSMOS-Web mass-function analysis](https://arxiv.org/html/2511.05259v1#S2); [COSMOS2025 release](https://cosmos2025.iap.fr/catalog.html).',
    '```\n'+assessment.to_string(index=False)+'\n```',
    'Detection completeness, M/L boundaries, morphology eligibility and classification accuracy are separate quantities. Passive and nonpassive eligibility differ substantially. Missing-label bounds in the joint table are conditional on detected eligible sources and correct measured labels, not bounds on the full population.',
    '## Robustness and uncertainties',
    'Primary bin edges are inherited; deterministic coarser bins, support thresholds10/20/50, bright-F444W, relative-depth and narrow-photoz subsets are secondary sensitivity tests. Primary logistic and paired-SFR questions use a Holm family of four. Cell Wilson intervals are pointwise, not simultaneous; many correlated cell comparisons should not be independently claimed as discoveries. Multinomial standardization uncertainty conditions on fixed reference weights and observed labels.',
    'Independent Gaussian perturbations inferred from mass/photoz68% half-widths produce the following standardization migration diagnostic:',
    '```\n'+mig.to_string(index=False)+'\n```',
    'This freezes passive/morphology labels and band choices, ignores covariance and multimodal posteriors, and retains invalid-interval objects unperturbed. It is not a complete uncertainty propagation. Large redshift uncertainties can migrate sources across empirical-MS and morphology-band boundaries; those label changes remain uncalibrated.',
    '## Figure captions and interpretation',
    '1. `figure1_passive_disk_mass_redshift`: PD/all across original cells. Counts and pointwise Wilson95% intervals show support; hatching marks small denominators/events. Demonstrates conditional distribution, not intrinsic abundance.',
    '2. `figure2_disk_among_passive_mass_redshift`: disk/passive with the same bins. Demonstrates morphology fractions within measured passive galaxies, not calibrated disk survival.',
    '3. `figure3_redshift_at_fixed_mass`: PD/all in fixed coarse mass intervals. Demonstrates whether marginal decline survives stratification; residual selection remains.',
    '4. `figure4_mass_at_fixed_redshift`: disk/passive within each redshift interval. Demonstrates observed mass dependence, not bulge growth histories.',
    '5. `figure5_mass_standardized_redshift`: original marginal and fixed10–11mass reference. Demonstrates distribution adjustment and factorization; comparison also changes support and supplies no intrinsic correction.',
    '6. `figure6_matched_SFR_mass_offsets`: identical matched groups shown in SFR–mass, cumulativeΔMS and paired differences. Demonstrates catalog-model distribution contrast, not quenching timescales.',
    '## Defensible preliminary claims\nReproducible observed joint fractions, coarse-mass-controlled trends and matched SED-model contrasts can enter a preliminary draft with explicit eligibility and uncertainty scope. Intrinsic disk abundance, quenching rates, causal pathways and physical SFR-floor interpretation require independent completeness, class-confusion, SED/censoring and correlated redshift/mass calibrations. Historical403 artificial-redshifting fits are not used here.']
    (out/'SCIENTIFIC_RESULTS.md').write_text('\n\n'.join(lines)+'\n')

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();print(json.dumps(run(a.project,a.output),indent=2))
