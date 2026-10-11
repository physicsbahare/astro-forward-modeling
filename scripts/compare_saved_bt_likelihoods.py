"""Evaluate saved competing structures on ONE identical real-image likelihood.

Only native conditional linear fluxes are refit. No new structural optimizer,
no added noise, no raw-data writes. Delta chi2 is a diagnostic of point solutions,
not a calibrated confidence interval or posterior class probability.
"""
from pathlib import Path
import copy,json,pickle
import numpy as np,pandas as pd
from lenstronomy.Util import class_creator
from galight.tools.measure_tools import model_flux_cal
from optimizer_quality import restore_saved_prior
from gold91_recovery_audit import atomic_json,sha

def compare(reference,candidates,out):
    reference=Path(reference);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    base=restore_saved_prior(pickle.loads(reference.read_bytes()),'bd');spec=base.fitting_specify_class
    imaging=class_creator.create_im_sim(spec.kwargs_data_joint['multi_band_list'],'multi-linear',spec.kwargs_model,
        bands_compute=[True],linear_solver=True,image_likelihood_mask_list=spec.kwargs_likelihood['image_likelihood_mask_list'])
    rows=[]
    for label,path in candidates.items():
        path=Path(path);fit=pickle.loads(path.read_bytes())
        assert fit.fitting_specify_class.light_model_list==spec.light_model_list,'Different model families'
        assert fit.fitting_specify_class.kwargs_data_joint['multi_band_list'][0][0]['image_data'].shape==spec.kwargs_data_joint['multi_band_list'][0][0]['image_data'].shape,'Different crop'
        components=copy.deepcopy(fit.source_result)
        prior=spec.kwargs_likelihood['custom_logL_addition'](None,None,components,None,None,None)
        likelihood,linear=imaging.likelihood_data_given_model(kwargs_lens_light=components,check_positive_flux=False)
        # lenstronomy1.12 MultiLinear.update_linear_kwargs has an index/object
        # issue; use the native one-band model's public updater directly.
        _,_,components,_=imaging._imageModel_list[0].update_linear_kwargs(linear[0],None,None,components,None)
        flux=np.asarray(model_flux_cal(components,sersic_major_axis=True,model_list=spec.light_model_list),float)
        bt=float(flux[1]/flux[:2].sum()) if np.all(flux[:2]>0) else None
        rows.append(dict(label=label,source_fit=str(path),source_sha256=sha(path),log_likelihood=float(likelihood),
            prior_valid=prior==0.,positive_target_flux=bool(np.all(flux[:2]>0)),bt_after_same_data_linear_solve=bt,
            component_radii=[float(k['R_sersic']) for k in components[:2]]))
    best=max(r['log_likelihood'] for r in rows if r['prior_valid'] and r['positive_target_flux'])
    for r in rows:r['delta_chi2_to_best_saved_structure']=-2*(r['log_likelihood']-best)
    pd.DataFrame(rows).to_csv(out/'same_data_structure_comparison.csv',index=False)
    atomic_json(out/'same_data_likelihood_receipt.json',dict(reference_fit=str(reference),reference_sha256=sha(reference),code_sha256=sha(Path(__file__)),rows=rows,
        scope='Same current analytic-total scene, diagonal ERR, mask and PSF for all structures; only linear amplitudes reoptimized. Point-solution diagnostic; no posterior or Wilks confidence claim.'))
    print(pd.DataFrame(rows)[['label','bt_after_same_data_linear_solve','delta_chi2_to_best_saved_structure','prior_valid']].to_string(index=False));return rows
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--reference',type=Path,required=True);p.add_argument('--candidates-json',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();compare(a.reference,json.loads(a.candidates_json.read_text()),a.output)
