"""Test fitted components, not just injected truth, for numerical convergence."""
from pathlib import Path
import json,pickle
import numpy as np,pandas as pd
from lenstronomy.Data.imaging_data import ImageData
from lenstronomy.Data.psf import PSF
from lenstronomy.LightModel.light_model import LightModel
from lenstronomy.ImSim.image_model import ImageModel
from corrected_four_stage import adaptive_numerics
from gold91_recovery_audit import atomic_json,sha

def audit(candidates,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);rows=[]
    for label,path in candidates.items():
        path=Path(path);fit=pickle.loads(path.read_bytes());spec=fit.fitting_specify_class
        data,psf,original_numerics=spec.kwargs_data_joint['multi_band_list'][0];image_data=ImageData(**data);npix=data['image_data'].shape[0]
        n_target=1 if path.stem.endswith('_single') else 2
        for index,k in enumerate(fit.source_result):
            light=LightModel(['SERSIC_ELLIPSE'],sersic_major_axis=True);center=image_data.map_coord2pix(k['center_x'],k['center_y'])
            images={}
            for factor,radius in [(32,6),(64,24),(128,24)]:
                model=ImageModel(image_data,PSF(**psf),lens_light_model_class=light,
                    kwargs_numerics=adaptive_numerics(npix,factor=factor,radius=radius,centers=[center]))
                images[factor]=model.lens_surface_brightness([k])
            actual_model=ImageModel(image_data,PSF(**psf),lens_light_model_class=light,kwargs_numerics=original_numerics)
            actual_image=actual_model.lens_surface_brightness([k])
            norm=np.linalg.norm(images[128]);e32=float(np.linalg.norm(images[32]-images[128])/norm);e64=float(np.linalg.norm(images[64]-images[128])/norm)
            analytic=float(light.total_flux([k])[0]);_,q=__import__('lenstronomy.Util.param_util',fromlist=['ellipticity2phi_q']).ellipticity2phi_q(k['e1'],k['e2'])
            actual_error=float(np.linalg.norm(actual_image-images[128])/norm)
            rows.append(dict(label=label,kind='target' if index<n_target else 'neighbor',original_factor=original_numerics.get('supersampling_factor'),actual_grid_relative_l2=actual_error,actual_grid_valid=actual_error<.001,fit=str(path),fit_sha256=sha(path),component=index,n=k['n_sersic'],radius_arcsec=k['R_sersic'],q=float(q),
                minor_radius_arcsec=float(q*k['R_sersic']),relative_l2_32_vs_128=e32,relative_l2_64_vs_128=e64,
                stamp_to_analytic32=float(images[32].sum()/analytic),stamp_to_analytic128=float(images[128].sum()/analytic),
                original_grid_component_valid=e32<.001,finer_grid_component_valid=e64<.001))
            print('FITTED_NUMERICS',label,index,e32,e64,flush=True)
    d=pd.DataFrame(rows);d.to_csv(out/'fitted_component_numerics.csv',index=False)
    atomic_json(out/'fitted_numerical_receipt.json',dict(N_components=len(d),code_sha256=sha(Path(__file__)),tolerance=.001,
        rows=rows,scope='Native convolved component images at identical fixed parameters and amplitudes. No stamp renormalization; no fits or raw-data modifications. Convergence is not identifiability.'))
    return d
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--candidates-json',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();audit(json.loads(a.candidates_json.read_text()),a.output)
