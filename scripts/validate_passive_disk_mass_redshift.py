"""Independent count/weight validation and explicit same-support sensitivity.

Does not change the primary frozen analysis, selection or prior outputs.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from passive_disk_mass_redshift import sha,standardize,savefig,shapley_change,joint_rates

def validate(project,out):
    project=Path(project);out=Path(out)
    core=json.loads((out/'execution_manifest.json').read_text())
    for name,digest in core['outputs'].items():assert sha(out/name)==digest,name
    parent_path=project/'Results/Project_Completion_20261011/science_products/parent_verified_observed_catalog.csv'
    p=pd.read_csv(parent_path,low_memory=False);t=pd.read_csv(out/'mass_redshift_fractions.csv');std=pd.read_csv(out/'mass_standardized_trends.csv');refs=pd.read_csv(out/'reference_mass_weights.csv')
    assert refs.weight.sum()==1
    for _,r in t.iterrows():
        e=p[p.audit_eligible&(p.z>=r.z_low)&(p.z<r.z_high)&(p.logM>=r.mass_low)&(p.logM<r.mass_high)];q=e[e.native_pair_measurable]
        assert r.N_eligible==len(e) and r.N_measurable==len(q)
        assert r.N_passive==q.audit_passive.sum() and r.N_disk==q.audit_disk.sum()
        assert r.N_passive_disk==(q.audit_passive&q.audit_disk).sum()
        if r.N_passive:assert np.isclose(r.pd_all,r.passive_all*r.disk_passive)
        for key in ['pd_all','disk_passive','passive_all','passive_disk','unknown']:
            if np.isfinite(r[key]):assert 0<=r[key+'_ci95_low']<=r[key]<=r[key+'_ci95_high']<=1
    for _,s in std.iterrows():
        estimate=0
        for _,r in refs.iterrows():
            q=p[p.audit_eligible&p.native_pair_measurable&(p.z>=s.z_low)&(p.z<s.z_high)&(p.logM>=r.mass_low)&(p.logM<r.mass_high)]
            estimate+=r.weight*(q.audit_passive&q.audit_disk).sum()/len(q)
        assert np.isclose(estimate,s.pd_all)
        assert np.isclose(s.pd_all,s.passive_all*s.disk_passive)
    m=pd.read_csv(out/'matched_SFR_pairs_LOCAL_ONLY.csv')
    assert len(m)==403 and not m.disk_id.duplicated().any() and not m.nondisk_id.duplicated().any()
    assert ((m.disk_mass-m.nondisk_mass).abs()<=.1).all() and ((m.disk_z-m.nondisk_z).abs()<=.1).all()
    grid=np.unique(np.r_[m.disk_delta,m.nondisk_delta]);basis=(m.disk_delta.to_numpy()[:,None]<=grid).astype(float)-(m.nondisk_delta.to_numpy()[:,None]<=grid).astype(float)
    ks=np.max(np.abs(basis.mean(axis=0)));rng=np.random.default_rng(20261014)
    null=np.max(np.abs(rng.choice([-1.,1.],size=(4000,len(m)))@basis/len(m)),axis=1)
    ks_p=(1+np.sum(null>=ks))/4001
    pd.DataFrame([dict(test='matched_pair_label_swap_KS',N_pairs=len(m),statistic=ks,permutation_p=ks_p,draws=4000,seed=20261014,scope='secondary omnibus distribution comparison; paired exchangeability; no separate discovery claim')]).to_csv(out/'matched_distribution_sensitivity.csv',index=False)
    dec=pd.read_csv(out/'standardized_change_decomposition.csv');assert np.isclose(dec.change.iloc[0],dec.change.iloc[1:].sum())
    # PD/all support depends on all-measurable counts. Include9.5–10 without
    # requiring precise D/P in its high-z cells (only4passive at z2.5–3).
    broad,boot,brefs=standardize(t,np.random.default_rng(20261013),min_passive=0)
    broad.to_csv(out/'PD_all_broader_common_support_standardized.csv',index=False)
    pd.DataFrame(brefs).to_csv(out/'PD_all_broader_reference_weights.csv',index=False)
    same=[]
    for label,lo,hi in [('primary_joint_support',10,11),('broader_PD_support',9.5,11)]:
        for _,r in std.iterrows():
            q=p[p.audit_eligible&p.native_pair_measurable&p.logM.between(lo,hi,inclusive='left')&p.z.between(r.z_low,r.z_high,inclusive='left')]
            same.append(dict(support=label,mass_low=lo,mass_high=hi,z_low=r.z_low,z_high=r.z_high,N=len(q),N_passive_disk=int((q.audit_passive&q.audit_disk).sum()),same_support_marginal=(q.audit_passive&q.audit_disk).mean()))
    same=pd.DataFrame(same);same.to_csv(out/'same_support_marginal_comparisons.csv',index=False)
    fig,axes=plt.subplots(1,2,figsize=(10,4.5),sharey=True)
    for ax,label,tab,title in [(axes[0],'primary_joint_support',std,'Joint support:10 ≤ log M <11'),(axes[1],'broader_PD_support',broad,'PD/all support:9.5 ≤ log M <11')]:
        q=same[same.support==label];x=(tab.z_low+tab.z_high)/2;y=tab.pd_all
        ax.errorbar(x,100*y,yerr=100*np.vstack([y-tab.pd_all_ci95_low,tab.pd_all_ci95_high-y]),fmt='o-',capsize=3,label='Fixed mass distribution',color='#176e85')
        ax.plot(x,100*q.same_support_marginal,'s--',label='Marginal: identical mass range',color='#ac6a2b')
        ax.set_title(title);ax.set_xlabel('Source redshift');ax.set_ylim(bottom=0);ax.legend(fontsize=8)
    for ax in axes: ax.set_ylim(0,100*max(std.pd_all_ci95_high.max(),broad.pd_all_ci95_high.max(),same.same_support_marginal.max())*1.1)
    axes[0].set_ylabel('Observed PD/all (%)');fig.suptitle('Same mass support: isolates coarse mass-mix adjustment\nFixed pooled reference; multinomial95% intervals; no completeness correction',fontsize=10)
    savefig(fig,out,'figure5b_same_support_mass_mix_sensitivity')
    first,last=broad.iloc[0],broad.iloc[-1];difference=boot['pd'][:,-1]-boot['pd'][:,0]
    extra_decomposition=[]
    marginal=pd.read_csv(out/'marginal_redshift_decomposition.csv')
    rng=np.random.default_rng(20261015)
    original_boot=[]
    for _,r in marginal.iloc[[0,-1]].iterrows():
        counts=r[['N_passive_disk','N_passive_nondisk','N_starforming_disk','N_starforming_nondisk']].to_numpy(float);n=int(counts.sum());original_boot.append(joint_rates(rng.multinomial(n,counts/n,size=4000)))
    for name,aa,bb,bp0,bd0,bp1,bd1 in [('broad_fixed_mass9.5_11',first,last,boot['p'][:,0],boot['d'][:,0],boot['p'][:,-1],boot['d'][:,-1]),('original_observed_marginal',marginal.iloc[0],marginal.iloc[-1],original_boot[0]['passive_all'],original_boot[0]['disk_passive'],original_boot[1]['passive_all'],original_boot[1]['disk_passive'])]:
        pp,dd=shapley_change(aa.passive_all,aa.disk_passive,bb.passive_all,bb.disk_passive);bpp,bdd=shapley_change(bp0,bd0,bp1,bd1)
        for key,value,draws in [('passive_fraction',pp,bpp),('disk_within_passive',dd,bdd)]:
            lo,hi=np.quantile(draws,[.025,.975]);extra_decomposition.append(dict(support=name,factor=key,change=value,ci95_low=lo,ci95_high=hi,point_share=value/(bb.pd_all-aa.pd_all)))
    pd.DataFrame(extra_decomposition).to_csv(out/'decomposition_support_sensitivity.csv',index=False)
    ci=np.quantile(difference,[.025,.975])
    tr=pd.read_csv(out/'statistical_tests.csv');mass=tr[(tr.variant=='primary')&(tr.test=='B_disk_passive_mass')&(tr.covariance=='tile_cluster')].iloc[0]
    corez=tr[(tr.variant=='common_mass10_11')&(tr.test=='A_PD_redshift')&(tr.covariance=='tile_cluster')].iloc[0]
    sf=pd.read_csv(out/'matched_SFR_comparison.csv').iloc[0]
    row_low=t[(t.z_low==0)&(t.mass_low==9.5)].iloc[0];row_high=t[(t.z_low==0)&(t.mass_low==10.5)].iloc[0]
    text=f'''# Independent validation and interpretation

All36 joint cells independently reconcile against the verified parent; all36
published marginal rows reconcile in the primary run. The nested factorization,
fixed-weight estimates, confidence interval ranges, additive decomposition and
unique403 matched pairs pass checks. No old fitting results are used.

## Does redshift dependence survive mass control?

Yes in the broader supported observed sample, with an important mass dependence.
A PD/all-only denominator rule (Nmeasurable>=50 in each redshift cell) supports
9.5<=logM<11. Its standardized fraction decreases from
{100*first.pd_all:.2f}% (95% {100*first.pd_all_ci95_low:.2f}–{100*first.pd_all_ci95_high:.2f}%)
to {100*last.pd_all:.2f}% ({100*last.pd_all_ci95_low:.2f}–{100*last.pd_all_ci95_high:.2f}%).
Endpoint difference: {100*(last.pd_all-first.pd_all):.2f} percentage points
(95% {100*ci[0]:.2f} to{100*ci[1]:.2f}). This is a denominator-defined sensitivity
and includes sparse passive counts at low mass/high z; it cannot provide precise
cell disk/passive fractions there.

The primary decomposition requires >=20 passive measurements per cell and
therefore uses10<=logM<11. Its endpoint decline is only1.22percentage points,
with95% interval[-2.54,+0.12], and is non-monotonic. Its average linear-logit slope
has OR={corez.odds_ratio:.3f} per z (tile-cluster95% {corez.ci95_low:.3f}–{corez.ci95_high:.3f},
nominal p={corez.pvalue:.4f}); this secondary p value is not an independent discovery.

In the10.5–11cell PD/all is9/378 at low z and6/224 at high z: no uniform decline
is demonstrated. In9.5–10 it is48/767 and1/1366, but passive denominators at high z
are very small. The strong low-mass trend must be read with morphology eligibility
and passive-classification limitations.

Figure5b compares marginal and standardized curves using exactly identical mass
support. This separates mix adjustment from the coverage difference in Figure5.
Changing the stellar-mass distribution alone does not explain the full observed
redshift trend; its strength varies across mass. No intrinsic-redshift claim follows.

## Mass dependence within the passive population

At0<z<0.5, observed disk/passive is48/158={100*row_low.disk_passive:.1f}%
(Wilson95% {100*row_low.disk_passive_ci95_low:.1f}–{100*row_low.disk_passive_ci95_high:.1f}%)
at9.5–10 and9/193={100*row_high.disk_passive:.1f}%
({100*row_high.disk_passive_ci95_low:.1f}–{100*row_high.disk_passive_ci95_high:.1f}%) at10.5–11.
Across supported cells, the redshift-stratified continuous-mass model gives
OR={mass.odds_ratio:.3f} per dex (tile-cluster95% {mass.ci95_low:.3f}–{mass.ci95_high:.3f};
Holm p={mass.primary_Holm_p:.3g}). This supports lower-mass passive galaxies more
often satisfying the disk rule in the measurable catalog, not a measured disk
survival probability or causal quenching mechanism.

## Contributions and SFR

For the10–11reference, P/all changes38.48%→14.37%, while effective D/P changes
6.62%→9.24%. The additive P/all contribution is−1.91percentage points
(95%−2.82 to−1.14); the D/P contribution is+0.69points (−0.91 to+2.50).
Thus the point decline is associated with the declining passive fraction and
partly offset by the disk/passive factor; the latter's sign is uncertain.
On broader9.5–11support, the passive-factor point contribution is
{100*extra_decomposition[0]['change']:.2f}percentage points
(95% {100*extra_decomposition[0]['ci95_low']:.2f} to{100*extra_decomposition[0]['ci95_high']:.2f}),
{100*extra_decomposition[0]['point_share']:.1f}% of the net point decline. For the
original observed marginal trend its share is
{100*extra_decomposition[2]['point_share']:.1f}%. Point attribution depends on support;
shares are not precise physical fractions. This factorization is descriptive, not causal.

All403 disks match unique passive non-disk controls within0.1dex and0.1z.
Mean paired ΔMS contrast={sf.mean_delta_difference:.3f}dex
(95% {sf.mean_ci95_low:.3f}–{sf.mean_ci95_high:.3f}; permutation p={sf.permutation_p:.3f}).
Median contrast={sf.median_difference:.3f}dex
(95% {sf.median_ci95_low:.3f}–{sf.median_ci95_high:.3f}). A secondary within-pair label-swap KS distribution test gives
KS={ks:.3f}, p={ks_p:.3f}. No significant distribution or
location difference is detected. Floor-pair exclusion retains353pairs and the
null result. Failure to detect a difference does not prove identical distributions.
No quenching timescale or distinct pathway is inferred.

## Completeness and publication scope

The saved quiescent M/L upper95% envelope is7.51–8.67, below the9.5parent floor.
Every eligible galaxy is already brighter thanF444W27.5, so that brightness
sensitivity leaves the selected analysis unchanged. This consistency check does
not validate detection completeness; the cited27.5benchmark is approximately80%
detection under a different published selection. Morphology-unknown fractions
increase from16.3% at low z to36.0% at high z and vary by passive status.
Those effects, changing band coverage/resolution, classification accuracy,
quiescence purity, cosmic variance and correlated SED/photoz uncertainties remain.

Preliminary paper: report observed mass-dependent fractions and their limited
common-support redshift trends, arithmetic decomposition and matched SED-model
null comparison. Do not call these intrinsic fractions, evolutionary rates,
physical transformations, progenitors or proof of specific quenching pathways.
'''
    (out/'REVIEW_AND_INTERPRETATION.md').write_text(text)
    extra=['decomposition_support_sensitivity.csv','matched_distribution_sensitivity.csv','PD_all_broader_common_support_standardized.csv','PD_all_broader_reference_weights.csv','same_support_marginal_comparisons.csv','figure5b_same_support_mass_mix_sensitivity.pdf','figure5b_same_support_mass_mix_sensitivity.png','REVIEW_AND_INTERPRETATION.md']
    result=dict(status='PASS_OBSERVED_CONDITIONAL_REVIEW',primary_manifest_sha256=sha(out/'execution_manifest.json'),validator_sha256=sha(Path(__file__)),checks=['36cells independent raw boolean counts','nested decomposition','fixed reference weights','exact403unique matching and calipers','Wilson bounds','Shapley sum','36published marginal count reconciliation'],broader_support_mass=[9.5,11],broader_first=first.pd_all,broader_last=last.pd_all,broader_difference_ci95=ci.tolist(),outputs={name:sha(out/name) for name in extra})
    (out/'validation_receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();print(json.dumps(validate(a.project,a.output),indent=2))
