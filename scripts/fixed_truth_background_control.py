"""Native linear-amplitude control with frozen truth geometry and sky nuisance.

Separates nonlinear structural degeneracy from conditional amplitude/background
bias. The truth is known in the injection experiment; this is not a substitute
for fitting unknown observed galaxies or calibrated covariance/identifiability.
"""
from pathlib import Path
import copy,json,pickle
import numpy as np,pandas as pd
from astropy.cosmology import Planck18
from lenstronomy.Util import class_creator,param_util
from lenstronomy.ImSim import de_lens
from galight.tools.measure_tools import model_flux_cal
from optimizer_quality import restore_saved_prior
from gold91_recovery_audit import atomic_json,sha

def control(bundle,fit_dir,out,ids):
    bundle=Path(bundle);fit_dir=Path(fit_dir);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    models={r['source_id']:r for r in json.loads((bundle/'models.json').read_text())};rows=[]
    for oid in ids:
        path=fit_dir/f'ID{oid}_real_bd.pkl';fit=restore_saved_prior(pickle.loads(path.read_bytes()),'bd');spec=fit.fitting_specify_class
        r=models[oid];scale=float(Planck18.angular_diameter_distance(r['z_source']).value/Planck18.angular_diameter_distance(3).value)
        components=copy.deepcopy(fit.source_result)
        for i,label in enumerate(['disk','bulge']):
            a,b=param_util.phi_q2_ellipticity(-r['theta'],r['model'][label+'_q'])
            components[i].update(R_sersic=r['model'][label+'_re_arcsec']*scale,n_sersic=1. if i==0 else 4.,e1=a,e2=b,center_x=0.,center_y=0.)
        imaging=class_creator.create_im_sim(spec.kwargs_data_joint['multi_band_list'],'multi-linear',spec.kwargs_model,bands_compute=[True],linear_solver=True,image_likelihood_mask_list=spec.kwargs_likelihood['image_likelihood_mask_list'])
        one=imaging._imageModel_list[0]
        # Use the exact native masked response and variance, then augment by an
        # explicitly declared constant sky basis in image-data units.
        A=one._linear_response_matrix(None,None,components,None,None,None)
        variance,_=one._error_response(None,None,kwargs_special=None);data=one.data_response
        for sky in [False,True]:
            design=np.vstack([A,np.ones(A.shape[1])]) if sky else A
            p,cov,pred=de_lens.get_param_WLS(design.T,1/variance,data,inv_bool=True)
            ll=copy.deepcopy(components);one.update_linear_kwargs(p[:len(components)],None,None,ll,None)
            flux=np.asarray(model_flux_cal(ll,sersic_major_axis=True,model_list=spec.light_model_list),float)
            rows.append(dict(source_id=oid,sky_constant=sky,truth_bt=r['model']['bt'],bt_fixed_truth=float(flux[1]/flux[:2].sum()) if np.all(flux[:2]>0) else None,
                sky_offset=float(p[-1]) if sky else 0.,chi2=float(np.sum((data-pred)**2/variance)),positive_target_flux=bool(np.all(flux[:2]>0)),
                weighted_design_condition=float(np.linalg.cond(design.T/np.sqrt(variance)[:,None])),fit_sha256=sha(path)))
    d=pd.DataFrame(rows);d.to_csv(out/'fixed_truth_sky_control.csv',index=False)
    atomic_json(out/'fixed_truth_sky_receipt.json',dict(rows=rows,models_sha256=sha(bundle/'models.json'),code_sha256=sha(Path(__file__)),
        scope='Known injected target geometry fixed; recovered neighbor shapes fixed; native linear amplitudes and optional sky constant only. Diagonal ERR likelihood; not a free morphology recovery or calibrated uncertainty.'))
    print(d[['source_id','sky_constant','truth_bt','bt_fixed_truth','sky_offset','chi2']].to_string(index=False));return d
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--fit-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--ids',default='10109,215914,732291');a=p.parse_args();control(a.bundle,a.fit_dir,a.output,[int(s) for s in a.ids.split(',')])
