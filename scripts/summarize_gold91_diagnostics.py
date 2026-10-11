"""Summarize completed, checkpointed diagnostic fits without repeating them."""
from pathlib import Path
import json, pickle
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from gold91_recovery_audit import IDS, atomic_json
from passive_disk_project_analysis import savefig

def summarize(output):
    output=Path(output)
    records=[json.loads(p.read_text()) for p in sorted(output.glob('ID*.json'))]
    fits=pd.DataFrame(records)
    expected={(oid,name) for oid in IDS for name in ['same_context_seed1','same_context_seed2','independent_context']}
    observed=set(zip(fits.source_id,fits.experiment))
    if observed!=expected or fits.status.ne('OK').any():raise RuntimeError('24 diagnostic rows not all complete and OK; retain errors and inspect')
    fits.to_csv(output/'all_24_targeted_fit_receipts.csv',index=False)
    diag=pd.read_csv(output/'normalization_diagnostics_with_truth_flags.csv')
    # Three requested radii were clipped by the original parameter builder.
    # Use the independently validated rendered truth for historical-run claims.
    diag['legacy_integrated_bt']=diag.original_actual_integrated_bt
    summaries=[]
    for oid in IDS:
        q=fits.loc[fits.source_id==oid];r=diag.loc[diag.source_id==oid].iloc[0]
        seed=q.loc[q.experiment.str.startswith('same_context')]
        alt=q.loc[q.experiment=='independent_context'].iloc[0]
        values=np.r_[r.real_bt,q.bt.to_numpy()]
        crossed=bool(np.any(values<.5) and np.any(values>=.5))
        summaries.append(dict(source_id=oid,input_bt=r.input_bt,actual_integrated_truth_bt=r.legacy_integrated_bt,
            legacy_clean_bt=r.clean_bt,legacy_real_bt=r.real_bt,new_seed1_bt=float(seed.loc[seed.experiment=='same_context_seed1','bt'].iloc[0]),
            new_seed2_bt=float(seed.loc[seed.experiment=='same_context_seed2','bt'].iloc[0]),
            independent_context_bt=float(alt.bt),seed_range=float(seed.bt.max()-seed.bt.min()),
            same_context_chisq_range=float(seed.chisq.max()-seed.chisq.min()),
            crosses_bt_boundary=crossed,source_only_ap_snr=r.source_only_ap_snr,
            scene_ap_snr=r.original_scene_ap_snr,
            diagnosis='CONTEXT_OR_OPTIMIZER_SENSITIVE_CLASS' if crossed else 'REPEATED_RECOVERY_BIAS; NO_PHYSICAL_TRANSFORMATION_CLAIM',
            final_quality='BT_ROBUSTNESS_UNCALIBRATED'))
    summary=pd.DataFrame(summaries);summary.to_csv(output/'eight_case_resolution_receipt.csv',index=False)
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    ax=axes[0];x=np.arange(len(summary))
    for column,label,marker,color,offset in [('input_bt','Input','o','#333333',-.18),('legacy_real_bt','Saved real','v','#c47729',-.06),('new_seed1_bt','New seed 1','s','#327c9b',.06),('independent_context_bt','Second context','D','#8e6198',.18)]:
        ax.scatter(x+offset,summary[column],label=label,marker=marker,color=color,s=25)
    ax.axhline(.5,color='gray',ls='--');ax.set_xticks(x,summary.source_id,rotation=50,ha='right');ax.set_ylabel('Integrated fitted B/T');ax.set_ylim(0,1);ax.legend(fontsize=7,ncol=2)
    ax.set_title('Eight apparent non-disk → disk changes')
    ax=axes[1];ax.scatter(diag.input_bt,diag.legacy_integrated_bt-diag.input_bt,s=16,c='#327c9b',alpha=.7)
    ax.axhline(0,color='gray',ls='--');ax.set_xlabel('Requested input B/T');ax.set_ylabel('Actual integrated truth B/T − requested B/T');ax.set_title('Finite-stamp normalization mismatch (90)')
    savefig(fig,output,'bt_convention_and_robustness')
    # Compare observed fit/model/residual directly, preserving all signed data.
    for oid in IDS:
        fig,axes=plt.subplots(2,3,figsize=(9,6))
        for row,label in enumerate(['same_context_seed1','independent_context']):
            files=list((output/'fit_products'/f'ID{oid}_{label}').glob('*.pkl'))
            if len(files)!=1:raise ValueError('Missing/ambiguous local fit product')
            fit=pickle.loads(files[0].read_bytes()) # Only this run's own trusted checkpoint.
            data=fit.flux_2d_out['data'];model=fit.flux_2d_out['model'];residual=fit.flux_2d_out['normalized residual']
            mask=fit.fitting_specify_class.kwargs_likelihood['image_likelihood_mask_list'][0]
            lo,hi=np.percentile(data[np.isfinite(data)],[1,99.5])
            for col,(image,title) in enumerate([(data,'SCI + injection'),(model,'Fitted model'),(np.where(mask,residual,np.nan),'(data − model) / ERR')]):
                ax=axes[row,col];ax.imshow(image,origin='lower',cmap='RdBu_r' if col==2 else 'magma',vmin=-4 if col==2 else lo,vmax=4 if col==2 else hi);ax.set_xticks([]);ax.set_yticks([]);ax.set_title(title,fontsize=9)
            receipt=fits.loc[(fits.source_id==oid)&(fits.experiment==label)].iloc[0]
            axes[row,0].set_ylabel(f'{label}\nB/T={receipt.bt:.3f}',fontsize=8)
        fig.suptitle(f'ID {oid}: matched legacy truth; diagonal ERR residual diagnostic')
        savefig(fig,output,f'ID{oid}_real_model_residual')
    offset=diag.legacy_integrated_bt-diag.input_bt
    closed=np.abs(diag.corrected_linear_bt-diag.input_bt)
    receipt=dict(N_targeted=24,N_OK=int(fits.status.eq('OK').sum()),N_class_sensitive=int(summary.crosses_bt_boundary.sum()),
        class_sensitive_ids=summary.loc[summary.crosses_bt_boundary,'source_id'].tolist(),
        normalization_median=float(offset.median()),normalization_min=float(offset.min()),normalization_max=float(offset.max()),
        corrected_fixed_shape_max_error=float(closed.max()),
        conclusion='Finite-stamp/infinite B/T mismatch is real but does not explain the large real-context shifts. Free structural fits introduce context/optimizer sensitivity. These injections measure recovery bias, not intrinsic morphology change.',
        identifiability='Neither no bound hit nor high aperture SNR is a calibrated posterior identifiability test; all eight retain explicit uncertainty.',
        selection_correction='Not estimated: three trials per disputed case cannot calibrate a population recovery matrix.')
    atomic_json(output/'robustness_summary.json',receipt)
    return receipt

if __name__=='__main__':
    import sys
    print(summarize(sys.argv[1]))
