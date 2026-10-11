"""Audit the physical and model-discrepancy support of scalar spectral transfer."""
from pathlib import Path
import json,itertools
import numpy as np,pandas as pd
from gold91_recovery_audit import atomic_json,sha
from verification.nircam_throughput_sensitivity import load_mean_throughput,fnu_response_moments,mapped_target_moments

def audit(bundle,out):
    bundle=Path(bundle);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    root=Path('/home/bahareh/nircam_throughputs_Jan2025_v7/nircam_throughputs/mean_throughputs')
    bands=('F115W','F150W','F277W','F444W');curves={b:load_mean_throughput(b,root) for b in bands}
    moments={b:fnu_response_moments(c.wavelength_um,c.throughput,2) for b,c in curves.items()};rows=[]
    target=curves['F444W'];significant=target.throughput>target.throughput.max()*.001
    for r in json.loads((bundle/'models.json').read_text()):
        if r['status']!='OK':continue
        source=r['spectral']['source_bands'];fluxes=r['source_fluxes_jy']
        coeff=np.linalg.solve(np.vstack([moments[b] for b in source]),[fluxes[b] for b in source])
        lam=target.wavelength_um[significant]*(1+r['z_source'])/4
        spectrum=sum(c*lam**i for i,c in enumerate(coeff))
        minspec=float(spectrum.min())
        omitted=[b for b in fluxes if b not in source]
        holdout=[float(np.dot(moments[b],coeff)/fluxes[b]-1) for b in omitted]
        alternate=[]
        target_m=mapped_target_moments(moments['F444W'],r['z_source'],3.)
        for trio in itertools.combinations(list(fluxes),3):
            # Diagnostic counterfactuals can include unsupported extrapolation;
            # do not promote these into alternative production fluxes.
            c=np.linalg.solve(np.vstack([moments[b] for b in trio]),[fluxes[b] for b in trio])
            alternate.append(float(target_m@c))
        rows.append(dict(source_id=r['source_id'],z_source=r['z_source'],logM=r['logM'],
            min_target_fnu_jy=minspec,positive_on_significant_target_passband=minspec>0,
            holdout_max_abs_relative_error=max(map(abs,holdout),default=np.nan),
            alternate_triplet_flux_range_relative=(max(alternate)-min(alternate))/r['spectral']['source_equivalent_target_fnu_jy'],
            negative_weight_l1=r['spectral']['negative_weight_l1'],flux_mode=r.get('source_flux_mode')))
    d=pd.DataFrame(rows);d.to_csv(out/'spectral_model_audit.csv',index=False)
    receipt=dict(N=len(d),nonphysical_target_spectrum_ids=d.loc[~d.positive_on_significant_target_passband,'source_id'].tolist(),
        models_sha256=sha(bundle/'models.json'),code_sha256=sha(Path(__file__)),
        holdout_relative_error_quantiles=d.holdout_max_abs_relative_error.quantile([.16,.5,.84]).to_dict(),
        limitations='Three broadband values determine the quadratic exactly; fourth-band discrepancies and extrapolative counterfactuals are model-discrepancy diagnostics, not statistical flux uncertainty. No clipping of negative spectral flux.')
    atomic_json(out/'spectral_audit_receipt.json',receipt);print(json.dumps(receipt,indent=2));return d
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();audit(a.bundle,a.output)
