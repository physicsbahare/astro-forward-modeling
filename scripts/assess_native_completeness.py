"""Catalog-aligned completeness requirements, not intrinsic fraction correction.

The mass-to-light diagnostic follows the released COSMOS-Web SMF prescription:
F444W<27.5, faintest 30%, 95th percentile rescaled mass. This is a conditional
M/L boundary and does not change the cited ~80% detection benchmark into 95%
detection completeness. Relative WHT strata are not assigned exposure counts.
"""
from pathlib import Path
import json
import numpy as np,pandas as pd
from astropy.io import fits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from gold91_recovery_audit import atomic_json,sha

Z_BINS=[.2,.5,1.,1.5,2.,2.5,3.]
M_BINS=[9.5,10.,10.5,11.,11.5,12.]

def assess(project,out,*,align_observed=False):
    project=Path(project);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    z_bins=Z_BINS;mass_bins=M_BINS
    if align_observed:
        observed=pd.read_csv(project/'Results/Project_Completion_20261011/science_products/observed_conditional_fractions.csv')
        def bin_edges(dimension):
            rows=observed.loc[observed.dimension==dimension]
            return sorted(set(rows.bin_low.tolist()+rows.bin_high.tolist()))
        z_bins=bin_edges('redshift');mass_bins=bin_edges('mass')
        if not z_bins or not mass_bins:raise RuntimeError('Observed bin definition unavailable')
    master=Path('/home/bahareh/Desktop/Projects/Data_General/Cosmos_Web/COSMOSWeb_mastercatalog_v1.1.fits')
    config=dict(z_bins=z_bins,mass_bins=mass_bins,bin_alignment='observed denominator bins' if align_observed else 'bounded initial diagnostic',magnitude_limit_F444W=27.5,faint_fraction=.30,mass_percentile=.95,
                bootstrap=400,seed=20261011,min_faint_objects=20,depth='quartiles of positive F444W WHT; relative depth only',
                quiescence='NUVrJ only for reference M/L limits; inherited dual-passive labels for morphology eligibility',
                population='quality and valid mass/redshift/colors; no lower mass floor or morphology cut in M/L reference',
                correction_applied=False)
    atomic_json(out/'frozen_completeness_config.json',config)
    with fits.open(master,memmap=True) as f:
        phot=f[1].data;lep=f['LEPHARE'].data
        ids=np.array(phot['id'],int);z=np.array(lep['zfinal'],float);mass=np.array(lep['mass_med'],float);mag=np.array(phot['mag_model_f444w'],float)
        wht=np.array(phot['wht_f444w'],float);star=np.array(lep['chi_star'],float);gal=np.array(lep['chi2_best'],float);agn=np.array(lep['chi2_agn'],float)
        colors=np.column_stack([np.array(lep[k],float) for k in ['mabs_nuv','mabs_r','mabs_j']])
        valid_colors=np.all(np.isfinite(colors)&(colors>-90),axis=1)
        quiescent=(colors[:,0]-colors[:,1]>3*(colors[:,1]-colors[:,2])+1)&(colors[:,0]-colors[:,1]>3.1)&valid_colors
        valid=(lep['type']==0)&(phot['warn_flag']==0)&(phot['flag_star_hsc']==0)&(lep['flag_chandra']==0)&valid_colors
        valid &=np.isfinite(z)&(z>=z_bins[0])&(z<z_bins[-1])&np.isfinite(mass)&(mass>0)&(mass<13)&np.isfinite(mag)&(np.abs(mag)<30)&(mag<27.5)&np.isfinite(wht)&(wht>0)
        ref=pd.DataFrame(dict(id=ids[valid],z=z[valid],logM=mass[valid],mag_f444w=mag[valid],wht=wht[valid],NUVrJ_quiescent=quiescent[valid],
                             stellar_SED_preferred=np.isfinite(star[valid])&(star[valid]>=0)&(star[valid]<gal[valid]),
                             AGN_SED_preferred=np.isfinite(agn[valid])&(agn[valid]>=0)&(agn[valid]<gal[valid])))
    edges=np.quantile(ref.wht,[0,.25,.5,.75,1]);edges[0]=np.nextafter(edges[0],-np.inf);edges[-1]=np.nextafter(edges[-1],np.inf)
    ref['relative_depth_quartile']=np.digitize(ref.wht,edges[1:-1])+1
    ref['logM_at_flux_limit']=ref.logM+.4*(ref.mag_f444w-27.5)
    ref.to_csv(out/'mass_completeness_reference_catalog.csv',index=False)
    rng=np.random.default_rng(20261011);limits=[]
    for depth in [0,1,2,3,4]:
        for group in ['all','NUVrJ_quiescent','NUVrJ_nonquiescent']:
            subset=ref if depth==0 else ref.loc[ref.relative_depth_quartile==depth]
            if group!='all':subset=subset.loc[subset.NUVrJ_quiescent==(group=='NUVrJ_quiescent')]
            for lo,hi in zip(z_bins[:-1],z_bins[1:]):
                a=subset.loc[subset.z.between(lo,hi,inclusive='left')]
                n=len(a);nf=int(np.ceil(.3*n));faint=a.nlargest(nf,'mag_f444w');values=faint.logM_at_flux_limit.to_numpy()
                row=dict(depth_quartile=depth,population=group,z_low=lo,z_high=hi,N_reference=n,N_faint=nf,calibrated_detection_completeness=False)
                if nf<20:row.update(status='INSUFFICIENT_FAINT_REFERENCE',logM_limit95=None,ci95_low=None,ci95_high=None)
                else:
                    samples=rng.choice(values,size=(400,nf),replace=True);boot=np.quantile(samples,.95,axis=1);ci=np.quantile(boot,[.025,.975])
                    row.update(status='CONDITIONAL_ML_DIAGNOSTIC',logM_limit95=float(np.quantile(values,.95)),ci95_low=float(ci[0]),ci95_high=float(ci[1]))
                limits.append(row)
    limits=pd.DataFrame(limits);limits.to_csv(out/'conditional_mass_to_light_limits.csv',index=False)
    parent_path=project/'Results/Project_Completion_20261011/science_products/parent_verified_observed_catalog.csv'
    parent=pd.read_csv(parent_path,low_memory=False);rows=[]
    for population in ['all','dual_passive','not_dual_passive']:
        group=parent.loc[parent.audit_eligible]
        if population!='all':group=group.loc[group.audit_passive==(population=='dual_passive')]
        for zlo,zhi in zip(z_bins[:-1],z_bins[1:]):
            for mlo,mhi in zip(mass_bins[:-1],mass_bins[1:]):
                g=group.loc[group.z.between(zlo,zhi,inclusive='left')&group.logM.between(mlo,mhi,inclusive='left')]
                n=len(g);nm=int(g.native_pair_measurable.sum())
                rows.append(dict(population=population,z_low=zlo,z_high=zhi,mass_low=mlo,mass_high=mhi,N_eligible=n,N_native_pair_eligible=nm,
                    native_pair_eligibility_fraction=nm/n if n else None,N_unknown_morphology=n-nm,
                    metric='observed operational eligibility; not detection or correct-classification probability'))
    eligibility=pd.DataFrame(rows);eligibility.to_csv(out/'native_morphology_eligibility_z_mass.csv',index=False)
    gold=pd.read_csv(project/'Data/passive_disk_GOLD403_with_visual_flags.csv',low_memory=False)
    gold_qc=gold[['id','z','logM']].merge(ref[['id','stellar_SED_preferred','AGN_SED_preferred']],on='id',how='left',validate='one_to_one')
    gold_qc.to_csv(out/'GOLD403_SED_contamination_diagnostic.csv',index=False)
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for group,color,label in [('NUVrJ_quiescent','#8d5da1','NUVrJ quiescent'),('NUVrJ_nonquiescent','#1d758b','NUVrJ non-quiescent')]:
        t=limits.loc[(limits.depth_quartile==0)&(limits.population==group)&(limits.status=='CONDITIONAL_ML_DIAGNOSTIC')]
        x=(t.z_low+t.z_high)/2;y=t.logM_limit95
        axes[0].errorbar(x,y,yerr=np.vstack([y-t.ci95_low,t.ci95_high-y]),fmt='o-',color=color,label=label,capsize=3)
    axes[0].axhline(mass_bins[0],color='gray',ls=':',label='Observed parent lower mass cut');axes[0].set_xlabel('Native redshift');axes[0].set_ylabel('Conditional 95% M/L mass boundary');axes[0].legend(fontsize=8)
    t=eligibility.loc[eligibility.population=='dual_passive'].pivot(index='mass_low',columns='z_low',values='native_pair_eligibility_fraction')
    im=axes[1].imshow(t.to_numpy(),origin='lower',aspect='auto',vmin=0,vmax=1,cmap='viridis');axes[1].set_xticks(range(len(t.columns)),[f'{x:.1f}' for x in t.columns]);axes[1].set_yticks(range(len(t.index)),[f'{x:.1f}' for x in t.index]);axes[1].set_xlabel('Native redshift bin lower edge');axes[1].set_ylabel('Mass bin lower edge');axes[1].set_title('Dual-passive paired-band eligibility');fig.colorbar(im,ax=axes[1],label='Observed eligibility fraction')
    fig.suptitle('Completeness requirements: conditional diagnostics, no intrinsic fraction correction',fontsize=10);fig.tight_layout()
    for ext in ['pdf','png']:fig.savefig(out/f'completeness_requirements.{ext}',dpi=220,bbox_inches='tight')
    plt.close(fig)
    receipt=dict(N_mass_reference=len(ref),positive_WHT_quartile_edges=edges.tolist(),source_master_sha256=sha(master),parent_table_sha256=sha(parent_path),code_sha256=sha(Path(__file__)),config=config,
        source_method='https://arxiv.org/html/2511.05259v1#S2',
        limitations=['M/L percentile is conditional on detected catalog; F444W=27.5 benchmark is ~80% detection, not 95%',
          'GOLD-compatible masks/type cuts are not a full reproduction of the published compact AGN/LRD/star selection',
          'WHT quartiles are relative depth strata; no survey area inferred from object counts',
          'Native morphology accuracy/class confusion and quiescence purity are uncalibrated; no inverse weights or intrinsic fractions calculated'])
    atomic_json(out/'completeness_assessment_receipt.json',receipt)
    print('Mass reference:',len(ref));print(limits.loc[(limits.depth_quartile==0)&(limits.population=='NUVrJ_quiescent')].to_string(index=False))
    return receipt

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--align-observed',action='store_true');a=p.parse_args();assess(a.project,a.output,align_observed=a.align_observed)
