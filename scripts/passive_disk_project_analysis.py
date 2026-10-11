"""Source-backed recovery/sample products for the permanent master notebook.

Observed fractions are conditional on the inherited catalog selection and
paired-band morphology eligibility. They are not mass-complete population
estimates. No z=3 recovery is applied as a correction to native demographics.
"""
from pathlib import Path
import json, importlib.metadata, subprocess, math
import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.table import Table
from astropy.cosmology import Planck18
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from gold91_recovery_audit import sha, atomic_json, load_functions, IDS

Z_EDGES=[0,.5,1,1.5,2,2.5,3]
M_EDGES=[9.5,10,10.5,11,11.5,12,13]

def true(series):
    return series.astype(str).str.lower().isin(['true','1'])

def wilson(k,n):
    if not n:return np.nan,np.nan
    z=1.959963984540054;p=k/n;den=1+z*z/n
    c=(p+z*z/(2*n))/den;h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return c-h,c+h

def savefig(fig,out,name):
    fig.tight_layout()
    for ext,dpi in [('pdf',None),('png',240)]:fig.savefig(out/f'{name}.{ext}',dpi=dpi,bbox_inches='tight')
    plt.close(fig)

def parent_audit(project,output):
    path=project/'passive_disk/01_parent_clean/clean_parent_selected_columns.csv'
    p=pd.read_csv(path,low_memory=False)
    if p.id.duplicated().any():raise ValueError('Duplicate parent IDs')
    master=Path('/home/bahareh/Desktop/Projects/Data_General/Cosmos_Web/COSMOSWeb_mastercatalog_v1.1.fits')
    work=project/'Data/passive_spiral_working_catalog.fits'
    with fits.open(master,memmap=True) as f, fits.open(work,memmap=True) as w:
        phot=f[1].data;lep=f['LEPHARE'].data;wt=w[1].data
        all_ids=np.array(phot['id'],dtype=int);working_ids=np.array(wt['id'],dtype=int)
        if len(set(all_ids))!=len(all_ids) or not np.array_equal(all_ids,working_ids):raise ValueError('Working/master ID alignment failed')
        idx=p.row_index.to_numpy(int)
        if not np.array_equal(p.id.to_numpy(int),all_ids[idx]):raise ValueError('Parent row-index ID mismatch')
        z=np.array(lep['zfinal'],float);m=np.array(lep['mass_med'],float);s=np.array(lep['sfr_med'],float);ss=np.array(lep['ssfr_med'],float)
        quality=(lep['type']==0)&(phot['warn_flag']==0)&(phot['flag_star_hsc']==0)&np.isfinite(phot['mag_model_f444w'])&(np.abs(phot['mag_model_f444w'])<30)
        original=quality&np.isfinite(z)&(z>0)&(z<4)&np.isfinite(m)&(m>=9)&(m<13)&np.isfinite(s)&(s>-90)&np.isfinite(ss)&(ss>-90)
        if not np.array_equal(np.sort(all_ids[original]),np.sort(p.id.to_numpy(int))):raise ValueError('Parent selection does not reproduce saved membership')
        for col,a in [('z',z),('logM',m),('logSFR',s),('logsSFR',ss)]:
            if not np.allclose(p[col],a[idx],rtol=0,atol=1e-10,equal_nan=True):raise ValueError('Stale parent '+col)
        for band in ['f115w','f150w','f277w','f444w']:
            for saved,native in [('snr_'+band,'snr_'+band),('BT_'+band,'BT_'+band),('sersic_n_'+band,'sersic_n_'+band)]:
                if not np.allclose(p[saved],wt[native][idx],rtol=0,atol=1e-10,equal_nan=True):raise ValueError('Stale morphology '+saved)
        for field in ['zpdf_l68','zpdf_u68','mass_l68','mass_u68','sfr_l68','sfr_u68','flag_chandra','nbfilt','chi2_best']:
            p[field]=np.array(lep[field][idx],float)
        for field in ['wht_f277w','wht_f444w','flag_star','flag_blend']:p[field]=np.array(phot[field][idx],float)
        colors=np.column_stack([np.array(lep[field][idx],float) for field in ['mabs_nuv','mabs_r','mabs_j']])
        p['rest_color_valid']=np.all(np.isfinite(colors)&(colors>-90),axis=1)
        p['photoz_interval_valid']=(p.zpdf_l68>=0)&(p.zpdf_u68>=p.zpdf_l68)&np.isfinite(p.zpdf_u68)
        p['photoz_relative_width']=(p.zpdf_u68-p.zpdf_l68)/(1+p.z)
        p['sfr_interval_valid']=(p.sfr_l68>-90)&(p.sfr_u68>=p.sfr_l68)&(p.logSFR>=p.sfr_l68)&(p.logSFR<=p.sfr_u68)
        p['mass_interval_valid']=(p.mass_l68>0)&(p.mass_u68>=p.mass_l68)&(p.logM>=p.mass_l68)&(p.logM<=p.mass_u68)
    # Recover the subsequently frozen rest-optical prescription. The earlier
    # parent export's chosen primary/confirmation columns predate GOLD403.
    source=project/'Codes/passive_disk_validation_stage.ipynb'
    notebook=json.loads(source.read_text())
    cells=[i for i,c in enumerate(notebook['cells']) if 'def assign_restopt_bands' in ''.join(c['source'])]
    namespace={'np':np}
    load_functions(source,cells,namespace,{'assign_restopt_bands'})
    primary,confirm=namespace['assign_restopt_bands'](p.z.to_numpy())
    p['original_recipe_primary_band']=p.primary_band
    p['original_recipe_confirm_band']=p.confirm_band
    p['primary_band']=primary;p['confirm_band']=confirm
    p['native_pair_measurable']=False
    for band in ['f115w','f150w','f277w','f444w']:
        # Both branches must have finite, physical values; inherited good_morph
        # also requires SNR>20 and the original n range.
        valid=true(p['good_morph_'+band])&p['BT_'+band].between(0,1)&p['sersic_n_'+band].between(.3,9)&(p['snr_'+band]>20)
        p['audit_good_'+band]=valid
    for i,r in p.iterrows():
        primary=str(r.primary_band).lower();confirm=str(r.confirm_band).lower()
        if 'audit_good_'+primary in p and 'audit_good_'+confirm in p:
            p.loc[i,'native_pair_measurable']=bool(r['audit_good_'+primary] and r['audit_good_'+confirm])
    for role in ['primary','confirm']:
        for target,prefix in [('BT','BT'),('sersic_n','sersic_n'),('snr','snr')]:
            values=np.full(len(p),np.nan)
            for band in ['f115w','f150w','f277w','f444w']:
                use=p[role+'_band'].eq(band);values[use]=p.loc[use,prefix+'_'+band]
            p[role+'_'+target]=values
    p['audit_passive']=true(p.passive_both)
    p['audit_disk']=(p.primary_BT<.5)&(p.confirm_BT<.5)&(p.primary_sersic_n<2.5)&(p.confirm_sersic_n<2.5)&p.native_pair_measurable
    p['audit_eligible']=(p.z>0)&(p.z<3)&p.logM.between(9.5,13,inclusive='left')&(p.flag_chandra==0)&p.rest_color_valid&np.isfinite(p.delta_MS)
    p['audit_passive_disk']=p.audit_passive&p.audit_disk
    gold=pd.read_csv(project/'Data/passive_disk_GOLD403_with_visual_flags.csv',low_memory=False)
    reconstructed=p.loc[p.audit_eligible&p.audit_passive_disk,'id'].to_numpy(int)
    if not np.array_equal(np.sort(reconstructed),np.sort(gold.id.to_numpy(int))):
        raise ValueError('Rest-optical parent criteria do not reproduce GOLD403; denominator gate remains open')
    t=Planck18.age(p.z.to_numpy()).value
    p['speagle_logSFR']=(.84-.026*t)*p.logM-(6.51-.11*t)
    p['delta_MS_speagle']=p.logSFR-p.speagle_logSFR
    p['passive_speagle_and_NUVrJ']=(p.delta_MS_speagle< -1)&true(p.passive_NUVrJ)
    p.to_csv(output/'parent_verified_observed_catalog.csv',index=False)
    audit=dict(N_released=784016,N_original_parent=len(p),ID_alignment='exact all rows',
        parent_membership='exact recomputation',physical_and_morphology_values='exact at 1e-10 tolerance',GOLD403_membership='exact reconstruction from rest-optical paired-band criteria',
        cuts='type=0,warn_flag=0,flag_star_hsc=0,abs(mag_model_f444w)<30,0<z<4,9<=logM<13,finite SFR and sSFR >-90',
        missing_population_inputs=['depth-stratified mass completeness for this selection',
          'native morphology recovery for passive and star-forming parent populations',
          'calibrated redshift/SFR quality and censoring treatment',
          'effective survey area after all masks and depth cuts'],
        sfr_upper_limit_policy='No explicit censoring flag identified; posterior interval endpoints are not treated as observational upper limits',
        fractions='Observed, conditional on native paired-band measurement eligibility; no completeness weighting',
        photoz_valid_interval_N=int(p.photoz_interval_valid.sum()),sfr_valid_interval_N=int(p.sfr_interval_valid.sum()))
    atomic_json(output/'parent_denominator_audit.json',audit)
    return p,master,work

def wavelength_audit(project,output):
    gold=pd.read_csv(project/'Data/passive_disk_GOLD403_with_visual_flags.csv',low_memory=False)
    curves={}
    paths=[]
    for band in ['F115W','F150W','F277W','F444W']:
        path=Path('/home/bahareh/nircam_throughputs_Jan2025_v7/nircam_throughputs/mean_throughputs')/f'{band}_May2024_mean_system_throughput.txt'
        a=np.genfromtxt(path,comments='#');curves[band]=(a[:,0],a[:,1]);paths.append(path)
    ns=dict(np=np,CURVES=curves,TARGET_FILTER='F444W',Z_TARGET=3.,AVAILABLE_MORPH_BANDS=('F115W','F150W','F277W','F444W'),
       INTERP_WEIGHT_TOL=1e-6,_SINGLE_MORPH_CACHE={},_BD_MORPH_CACHE={})
    source=Path('/home/bahareh/Downloads/GOLD91_FINAL_v3_exclude_487778_clean_real_E0.ipynb')
    needed={'photon_weighted_mean_lambda_um','mapped_target_effective_lambda_um','_band_effective_lambda_um',
            '_single_branch_valid','_bd_branch_valid','_available_branch_measurements','_closest_valid_bracketing_pair',
            '_log_interp_positive','_linear_interp','wavelength_interpolated_single_morphology','wavelength_interpolated_bd_morphology'}
    load_functions(source,[5],ns,needed)
    morph={}
    with fits.open('/home/bahareh/Desktop/Projects/Data_General/Cosmos_Web/COSMOSWeb_mastercatalog_v1.1.fits',memmap=True) as f:
        idx=gold.row_index.to_numpy(int)
        if not np.array_equal(np.array(f[1].data['id'][idx],int),gold.id):raise ValueError('GOLD403 catalog ID join failed')
        for _,r in gold.iterrows():
            i=int(r.row_index);g=f[7].data[i];bd=f['B+D'].data[i]
            for band in curves:
                b=band.lower();disk=float(g[f'mag_disk_{b}_bd']);bulge=float(g[f'mag_bulge_{b}_bd'])
                bt=1/(1+10**(-.4*(disk-bulge))) if np.isfinite(disk+bulge) and disk>0 and bulge>0 and disk<90 and bulge<90 else np.nan
                def q_component(label):
                    for col in [f'qratio_{label}_{b}_bd',f'q_{label}_{b}_bd',f'qratio_{b}_{label}_bd',f'axisratio_{label}_{b}_bd']:
                        if col in f[7].columns.names and 0<float(g[col])<=1:return float(g[col])
                    return float(np.clip(bd[f'{label}_axratio'],.08,1))
                morph[(int(r.id),band)]=dict(single_n=float(g[f'nsersic_{b}_sersic']),single_re_arcsec=float(g[f'rearc_{b}_sersic']),
                    single_q=float(g[f'qratio_{b}_sersic']),disk_re_arcsec=float(g[f'rearc_disk_{b}_bd']),
                    bulge_re_arcsec=float(g[f'rearc_bulge_{b}_bd']),disk_q=q_component('disk'),bulge_q=q_component('bulge'),bt=bt,morph_filter=band)
    ns['_published_morphology_for_band']=lambda r,b:morph[(int(r['id']),b)]
    rows=[]
    for _,r in gold.iterrows():
        row=dict(source_id=int(r.id),z_source=float(r.z),original_band=r.primary_band,status='OK')
        try:
            single=ns['wavelength_interpolated_single_morphology'](r)
            bd=ns['wavelength_interpolated_bd_morphology'](r)
            row.update(mapped_lambda_um=single['target_lambda_eff_um'],single_low_band=single['low_band'],single_high_band=single['high_band'],
                bd_low_band=bd['low_band'],bd_high_band=bd['high_band'],input_n=single['single_n'],input_bt=bd['bt'],
                input_disk=single['single_n']<2.5 and bd['bt']<.5)
        except Exception as e:row.update(status='UNSUPPORTED_MORPHOLOGY',reason=str(e))
        rows.append(row)
    result=pd.DataFrame(rows);result.to_csv(output/'GOLD403_wavelength_support_audit.csv',index=False)
    previous=pd.read_csv(project/'Results/GOLD91_wavelength_interpolated_v2_branch_specific/tables/GOLD91_wavelength_interpolated_full_results.csv')
    check=result.merge(previous[['source_id','input_single_n','input_bt']],on='source_id',suffixes=('','_saved'),validate='one_to_one')
    if not np.allclose(check.input_n,check.input_single_n,rtol=0,atol=1e-9) or not np.allclose(check.input_bt,check.input_bt_saved,rtol=0,atol=1e-9):raise ValueError('GOLD91 interpolation reproduction mismatch')
    atomic_json(output/'wavelength_audit_receipt.json',dict(N403=len(result),status_counts=result.status.value_counts().to_dict(),
        GOLD91_reproduction='90/90 n and B/T agree to 1e-9',
        flux_method_gate='Saved GOLD91 uses logFnu/loglambda scalar interpolation at an effective wavelength, not the frozen R3 full-throughput curved SED method. Do not promote to final production until validated or explicitly amended.',
        throughput_hashes={str(p):sha(p) for p in paths}))
    return result,paths

def fraction_tables(p,output):
    rows=[]
    for dimension,edges,col in [('redshift',Z_EDGES,'z'),('mass',M_EDGES,'logM')]:
        for lo,hi in zip(edges[:-1],edges[1:]):
            eligible=p.audit_eligible&p[col].between(lo,hi,inclusive='left')
            measured=eligible&p.native_pair_measurable
            for name,den in [('passive_disk_among_all',measured),('disk_among_passive',measured&p.audit_passive),('passive_among_disks',measured&p.audit_disk)]:
                n=int(den.sum());k=int((den&p.audit_passive_disk).sum());low,high=wilson(k,n)
                unknown=eligible&~p.native_pair_measurable
                up=int((unknown&p.audit_passive).sum());un=int((unknown&~p.audit_passive).sum())
                if name=='disk_among_passive':unknown &=p.audit_passive
                nunknown=int(unknown.sum())
                if name=='passive_among_disks':
                    bound_low=k/(n+un) if n+un else np.nan
                    bound_high=(k+up)/(n+up) if n+up else np.nan
                else:
                    bound_low=k/(n+nunknown) if n+nunknown else np.nan
                    bound_high=(k+up)/(n+nunknown) if n+nunknown else np.nan
                rows.append(dict(dimension=dimension,bin_low=lo,bin_high=hi,estimand=name,k=k,n=n,
                    observed_fraction=k/n if n else np.nan,ci95_low=low,ci95_high=high,N_eligible=int(eligible.sum()),
                    N_morphology_unknown=nunknown,N_unknown_passive=up,N_unknown_nonpassive=un,
                    missing_morphology_bound_low=bound_low,missing_morphology_bound_high=bound_high,
                    bound_scope='eligible catalog only; no bound on undetected sources',sparse_denominator=n<20,completeness_corrected=False))
    table=pd.DataFrame(rows);table.to_csv(output/'observed_conditional_fractions.csv',index=False)
    # For passive-among-disks the unknown disk denominator can range 0..Nunknown;
    # these conservative bounds allow any unknown membership/passivity.
    sensitivity=[]
    for label,passive,disk,eligibility in [
        ('inherited_dual',p.audit_passive,p.audit_disk,p.audit_eligible&p.native_pair_measurable),
        ('NUVrJ_only',true(p.passive_NUVrJ),p.audit_disk,p.audit_eligible&p.native_pair_measurable),
        ('Speagle_and_NUVrJ',p.passive_speagle_and_NUVrJ,p.audit_disk,p.audit_eligible&p.native_pair_measurable),
        ('stricter_BT04_n20',p.audit_passive,(p.primary_BT<.4)&(p.confirm_BT<.4)&(p.primary_sersic_n<2)&(p.confirm_sersic_n<2),p.audit_eligible&p.native_pair_measurable),
        ('photoz_width_below_01',p.audit_passive,p.audit_disk,p.audit_eligible&p.native_pair_measurable&p.photoz_interval_valid&(p.photoz_relative_width<.1))]:
        sensitivity.append(dict(variant=label,N_eligible=int(eligibility.sum()),N_passive=int((eligibility&passive).sum()),
            N_disk=int((eligibility&disk).sum()),N_passive_disk=int((eligibility&disk&passive).sum()),purpose='preliminary sensitivity; no threshold tuning'))
    pd.DataFrame(sensitivity).to_csv(output/'observed_definition_sensitivity.csv',index=False)
    for dimension,col in [('redshift','z'),('mass','logM')]:
        fig,axes=plt.subplots(1,3,figsize=(12,3.8))
        for ax,name,title in zip(axes,['passive_disk_among_all','disk_among_passive','passive_among_disks'],['Passive disks / eligible','Disks / passive','Passive / disks']):
            t=table.loc[(table.dimension==dimension)&(table.estimand==name)]
            x=(t.bin_low+t.bin_high)/2;y=t.observed_fraction
            ax.errorbar(x,y,yerr=np.vstack([y-t.ci95_low,t.ci95_high-y]),fmt='o',color='#1c657f',capsize=3)
            upper=t.ci95_high[np.isfinite(t.ci95_high)]
            ax.set_title(title);ax.set_ylim(0,min(1,max(.06,float(upper.max())*1.3 if len(upper) else 1)));ax.set_xlabel('Source redshift' if dimension=='redshift' else r'$\log_{10}(M_\star/M_\odot)$')
            for a,b,n in zip(x,y,t.n):
                if np.isfinite(b):ax.annotate(f'n={n}'+(' (sparse)' if n<20 else ''),(a,b),xytext=(0,9),textcoords='offset points',fontsize=7,ha='center')
        axes[0].set_ylabel('Observed conditional fraction')
        fig.suptitle('Native catalog; paired-band measurable; uncorrected selection',fontsize=11)
        savefig(fig,output,f'observed_conditional_fraction_vs_{dimension}')
    return table

def sample_sfr(p,gold,output):
    g=gold[['id']].merge(p,on='id',validate='one_to_one')
    # A flag, not a cut or an observed upper limit. Values approach the
    # catalog log-SFR lower grid edge near -10; precision there is model driven.
    g['sfr_near_model_floor']=g.sfr_l68< -9.9
    g.loc[g.sfr_near_model_floor,['id','z','logM','logSFR','sfr_l68','sfr_u68']].to_csv(output/'GOLD403_SFR_floor_sensitive_rows.csv',index=False)
    g.to_csv(output/'GOLD403_observed_SFR_mass_catalog.csv',index=False)
    Table.from_pandas(g[['id','z','logM','logSFR','sfr_l68','sfr_u68','mass_l68','mass_u68','delta_MS','delta_MS_speagle','sfr_interval_valid']]).write(output/'GOLD403_observed_SFR_mass_catalog.fits',overwrite=True)
    rng=np.random.default_rng(20261011); summaries=[]
    for dim,edges,col in [('redshift',Z_EDGES,'z'),('mass',M_EDGES,'logM')]:
        for lo,hi in zip(edges[:-1],edges[1:]):
            q=g.loc[g[col].between(lo,hi,inclusive='left')];x=q.delta_MS.to_numpy();n=len(x)
            if not n:continue
            ci=np.quantile(np.median(rng.choice(x,size=(2000,n),replace=True),axis=1),[.025,.975]) if n>=5 else [np.nan,np.nan]
            summaries.append(dict(dimension=dim,bin_low=lo,bin_high=hi,n=n,median_delta_MS=float(np.median(x)),
                p16=float(np.quantile(x,.16)),p84=float(np.quantile(x,.84)),median_ci95_low=ci[0],median_ci95_high=ci[1],
                valid_sfr_interval_n=int(q.sfr_interval_valid.sum()),model_floor_sensitive_n=int(q.sfr_near_model_floor.sum()),median_speagle_offset=float(q.delta_MS_speagle.median()),
                interval_estimable=n>=5,
                uncertainty_scope='conditional catalog scatter; no censoring or selection correction'))
    pd.DataFrame(summaries).to_csv(output/'GOLD403_SFR_offset_summaries.csv',index=False)
    fits_ms=pd.read_csv(p.attrs['project']/'passive_disk/02_main_sequence/step2_main_sequence_fits.csv')
    fig,axes=plt.subplots(2,3,figsize=(12,8),sharex=True,sharey=True)
    for ax,lo,hi in zip(axes.ravel(),Z_EDGES[:-1],Z_EDGES[1:]):
        q=p.loc[p.audit_eligible&p.z.between(lo,hi,inclusive='left')]
        sf=q.loc[~true(q.passive_NUVrJ)]
        ax.hexbin(sf.logM,sf.logSFR,gridsize=35,mincnt=1,bins='log',cmap='Greys',extent=(9.5,12.5,-10.5,3),rasterized=True)
        nd=q.loc[q.audit_passive&q.native_pair_measurable&~q.audit_disk]
        ax.scatter(nd.logM,nd.logSFR,s=6,c='#9f869f',alpha=.25,rasterized=True)
        disk=g.loc[g.z.between(lo,hi,inclusive='left')]
        ax.scatter(disk.logM,disk.logSFR,s=12,c='#007c91',alpha=.8,zorder=4)
        interval=disk.loc[disk.sfr_interval_valid&disk.mass_interval_valid]
        ax.errorbar(interval.logM,interval.logSFR,yerr=np.vstack([interval.logSFR-interval.sfr_l68,interval.sfr_u68-interval.logSFR]),fmt='none',ecolor='#007c91',alpha=.15,linewidth=.5)
        ms=fits_ms.loc[(fits_ms.z_low==lo)&(fits_ms.z_high==hi)].iloc[0];xx=np.linspace(9.5,12,70)
        ax.plot(xx,ms.MS_slope*xx+ms.MS_intercept,c='#ce7b24',lw=1.3)
        ax.plot(xx,ms.MS_slope*xx+ms.MS_intercept-1,c='#ce7b24',ls='--',lw=1)
        age=Planck18.age((lo+hi)/2).value
        ax.plot(xx,(.84-.026*age)*xx-(6.51-.11*age),c='#3f3f3f',ls=':',lw=1)
        ax.set_title(f'{lo:.1f} ≤ z < {hi:.1f}; GOLD n={len(disk)}');ax.set_xlim(9.5,12.5);ax.set_ylim(-10.5,3)
    for ax in axes[-1]:ax.set_xlabel(r'$\log_{10}(M_\star/M_\odot)$')
    for ax in axes[:,0]:ax.set_ylabel(r'$\log_{10}({\rm SFR}/M_\odot\,{\rm yr}^{-1})$')
    fig.suptitle('Catalog SED-model SFR: GOLD403 cyan; passive non-disks purple; star-forming density gray\nVery low passive SFR values and intervals depend on the SED model grid',fontsize=10)
    savefig(fig,output,'SFR_mass_redshift_slices')
    return g

def run(project,output):
    project=Path(project);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    config=dict(z_bins=Z_EDGES,mass_bins=M_EDGES,selection='inherited rest-optical GOLD403 selection; no retuning',
        disk='primary AND confirmation n<2.5,B/T<0.5; each band SNR>20 and physical values',
        passive='inherited empirical delta_MS<-1 AND NUVrJ',AGN='exclude flag_chandra=1 from numerator and all denominators',
        passive_denominator_quality='valid finite rest-frame NUV,r,J absolute magnitudes >-90; finite delta_MS',
        estimand='conditional on original clean parent, native paired-band morphology eligibility; not total population',
        completeness='uncorrected',interval='95% Wilson conditional binomial; median CI bootstrap 2000 draws')
    config_path=output/'frozen_analysis_config.json'
    if config_path.exists() and json.loads(config_path.read_text())!=config:raise RuntimeError('Selection changed; use new output directory')
    atomic_json(config_path,config)
    p,master,work=parent_audit(project,output);p.attrs['project']=project
    wave,curves=wavelength_audit(project,output)
    fractions=fraction_tables(p,output)
    gold=pd.read_csv(project/'Data/passive_disk_GOLD403_with_visual_flags.csv',low_memory=False)
    sfr=sample_sfr(p,gold,output)
    final=gold.merge(wave,left_on='id',right_on='source_id',how='left',validate='one_to_one')
    diag=pd.read_csv(project/'Results/Project_Completion_20261011/gold91_diagnostics/normalization_and_context_diagnostics.csv')
    full=pd.read_csv(project/'Results/GOLD91_wavelength_interpolated_v2_branch_specific/tables/GOLD91_wavelength_interpolated_full_results.csv')
    final=final.merge(full[['source_id','clean_single_n','clean_bt','e0_real_single_n','e0_real_bt','e0_real_n_valid','e0_real_bt_valid','e0_real_single_snr','e0_real_bd_snr']],on='source_id',how='left',validate='one_to_one')
    final['corrected_recovery_state']=np.where(final.id.isin(IDS),'DISPUTED_BT_RECOVERY',np.where(final.id.isin(full.source_id),'GOLD91_PROVISIONAL','NOT_RUN_CORRECTED'))
    final.loc[final.status!='OK','corrected_recovery_state']='UNSUPPORTED_MORPHOLOGY'
    truth_flags=pd.read_csv(project/'Results/Project_Completion_20261011/gold91_diagnostics/original_renderer_adapter_validation.csv')
    final=final.merge(truth_flags[['source_id','radius_clipped','rendered_disk_re','rendered_bulge_re','original_actual_integrated_bt']],on='source_id',how='left',validate='one_to_one')
    final.loc[final.radius_clipped.eq(True),'corrected_recovery_state']='REQUESTED_TRUTH_RADIUS_CLIPPED'
    final['publication_final_recovery']=False
    final.to_csv(output/'GOLD403_source_by_source_checkpoint.csv',index=False)
    Table.from_pandas(final[['id','z','logM','status','input_n','input_bt','clean_single_n','clean_bt','e0_real_single_n','e0_real_bt','corrected_recovery_state','publication_final_recovery']]).write(output/'GOLD403_source_by_source_checkpoint.fits',overwrite=True)
    paths=[master,work,project/'Data/passive_disk_GOLD403_with_visual_flags.csv',project/'passive_disk/01_parent_clean/clean_parent_selected_columns.csv',
           project/'passive_disk/02_main_sequence/step2_main_sequence_fits.csv',project/'Codes/passive_disk.ipynb',project/'Codes/passive_disk_validation_stage.ipynb',Path(__file__),*curves]
    identity={str(path):sha(path) for path in paths}
    versions={pkg:importlib.metadata.version(pkg) for pkg in ['numpy','scipy','pandas','astropy','galight','lenstronomy','galsim','nbformat','matplotlib']}
    atomic_json(output/'analysis_execution_manifest.json',dict(inputs=identity,environment=versions,config=config,
        code_base=subprocess.check_output(['git','-C',str(project/'astro-forward-modeling'),'rev-parse','HEAD'],text=True).strip(),
        code_file_sha256=identity[str(Path(__file__))],status='PRELIMINARY_OBSERVED_PRODUCTS_COMPLETE; FINAL_POPULATION_AND_CORRECTED_PRODUCTION_GATES_OPEN'))
    return dict(parent=len(p),GOLD403=len(sfr),wavelength_status=wave.status.value_counts().to_dict(),observed_rows=len(fractions))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--project',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();print(run(a.project,a.output))
