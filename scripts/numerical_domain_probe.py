"""Exploratory fit-domain control using native Galight optimizers.

The old consolidated bounds implied q~>=0.1. A circular q bound retains every
supported truth orientation. A minor-size floor excludes proven quadrature
aliases; it is a numerical admissibility sensitivity, not a calibrated physical
prior or a changed disk threshold. Higher-grid fitted-model checks remain required.
"""
from dataclasses import dataclass,asdict
from pathlib import Path
import copy,json,pickle,hashlib,time
import numpy as np
from lenstronomy.Util import param_util
from lenstronomy.Data.imaging_data import ImageData
from galight.fitting_process import FittingProcess
from optimizer_quality import bd_physical_condition,restore_saved_prior,capture_minimize
from corrected_four_stage import adaptive_numerics
from gold91_recovery_audit import atomic_json,sha

@dataclass(frozen=True)
class NumericalDomain:
    q_min:float=.1
    minimum_minor_radius_arcsec:float=.0015
    def __call__(self,kwargs_lens,kwargs_source,kwargs_lens_light,kwargs_ps,kwargs_special,kwargs_extinction,*args,**kwargs):
        if bd_physical_condition(kwargs_lens,kwargs_source,kwargs_lens_light,kwargs_ps,kwargs_special,kwargs_extinction)!=0.:return -1e15
        for k in kwargs_lens_light:
            e=np.hypot(k['e1'],k['e2']);q=(1-e)/(1+e)
            if q<self.q_min or q*k['R_sersic']<self.minimum_minor_radius_arcsec:return -1e15
        return 0.

def probe(reference,record,out,*,q_min=.1,minimum_minor=.0015,starts=2):
    reference=Path(reference);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    domain=NumericalDomain(q_min,minimum_minor);base=restore_saved_prior(pickle.loads(reference.read_bytes()),'bd')
    # Validate the source truth before any initializer is changed.
    from astropy.cosmology import Planck18
    scale=float(Planck18.angular_diameter_distance(record['z_source']).value/Planck18.angular_diameter_distance(3).value)
    truth=[]
    for component in ['disk','bulge']:
        q=record['model'][component+'_q'];a,b=param_util.phi_q2_ellipticity(-record['theta'],q)
        truth.append(dict(R_sersic=record['model'][component+'_re_arcsec']*scale,e1=a,e2=b,center_x=0.,center_y=0.))
    if domain(None,None,truth,None,None,None)!=0.:raise RuntimeError('Truth outside exploratory numerical domain; never clip it')
    fp=hashlib.sha256(json.dumps(dict(reference_sha=sha(reference),source_model=record,domain=asdict(domain),code=sha(Path(__file__)),kernel=sha(Path(__file__).with_name('corrected_four_stage.py'))),sort_keys=True).encode()).hexdigest()
    for start in range(starts):
        dest=out/f'start{start}.json'
        if dest.exists():
            if json.loads(dest.read_text())['fingerprint']!=fp:raise RuntimeError('Stale diagnostic checkpoint')
            continue
        spec=copy.deepcopy(base.fitting_specify_class);params=copy.deepcopy(spec.kwargs_params['lens_light_model'])
        for i,k in enumerate(truth):
            params[0][i].update(k);params[0][i]['R_sersic']*=([1.3,.7] if start==0 else [.7,1.3])[i]
            params[0][i]['center_x']=.015;params[0][i]['center_y']=-.015
        # Changing guesses is explicit and never changes the truth or dataset.
        for k in params[0]:
            e=np.hypot(k['e1'],k['e2']);maximum=(1-q_min)/(1+q_min)
            if e>=maximum:
                k['e1']*=.95*maximum/e;k['e2']*=.95*maximum/e
            _,q=param_util.ellipticity2phi_q(k['e1'],k['e2'])
            k['R_sersic']=max(k['R_sersic'],1.2*minimum_minor/q)
        spec.kwargs_params['lens_light_model']=params;spec.kwargs_likelihood['custom_logL_addition']=domain
        npix=spec.kwargs_data['image_data'].shape[0];data=ImageData(**spec.kwargs_data)
        centers=[(npix//2,npix//2)]+[data.map_coord2pix(k['center_x'],k['center_y']) for k in base.source_result[2:]]
        spec.kwargs_numerics.update(adaptive_numerics(npix,factor=64,radius=24,centers=centers));spec.build_fitting_seq()
        fit=FittingProcess(spec,savename=str(out/f'start{start}'));np.random.seed(2026101100+start);began=time.time()
        with capture_minimize() as optimizer:
            fit.run(algorithm_list=['SIMPLEX'],setting_list=[{'n_iterations':2000}],fitting_level='norm',threadCount=1)
        fit.declared_prior=dict(name='NumericalDomain',parameters=asdict(domain));fit.optimizer_receipts=optimizer;fit.dump_result()
        flux=[float(g['flux_sersic_model']) for g in fit.final_result_galaxy[:2]]
        bt=flux[1]/sum(flux) if min(flux)>0 else None
        atomic_json(dest,dict(fingerprint=fp,source_id=record['source_id'],start=start,bt=bt,chisq=float(fit.reduced_Chisq),
            seconds=time.time()-began,optimizer_receipts=optimizer,prior=asdict(domain),
            component_radii=[float(k['R_sersic']) for k in fit.source_result[:2]],component_q=[float(g['q']) for g in fit.final_result_galaxy[:2]],
            saved_fit=str(out/f'start{start}.pkl'),status='EXPLORATORY_DOMAIN_CONTROL',
            scope='Same analytic-total scene, ERR and mask. Higher fitted-grid convergence and prior sensitivity not yet passed; no validated class.'))
        print('DOMAIN_CONTROL',record['source_id'],start,bt,optimizer[-1]['success'],flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--reference',type=Path,required=True);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--id',type=int,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--q-min',type=float,default=.1);p.add_argument('--minimum-minor',type=float,default=.0015)
    a=p.parse_args();record=next(r for r in json.loads((a.bundle/'models.json').read_text()) if r['source_id']==a.id)
    probe(a.reference,record,a.output,q_min=a.q_min,minimum_minor=a.minimum_minor)
