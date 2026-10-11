"""Corrected parametric four-stage transfer using the existing Galight stack.

Truth parameters are never made by an optimizer initializer. Integrated B/T
is set with Lenstronomy total_flux before one common finite-stamp normalization.
The assigned flux is analytic total luminosity; finite aperture loss is retained
rather than compensated. Cleaned-photometry anchors remain explicitly approximate.
"""
from pathlib import Path
import copy,hashlib,json,random,time,traceback
import numpy as np,pandas as pd
from astropy.cosmology import Planck18
from lenstronomy.Util import param_util,simulation_util
from lenstronomy.Data.imaging_data import ImageData
from lenstronomy.Data.psf import PSF
from lenstronomy.LightModel.light_model import LightModel
from lenstronomy.ImSim.image_model import ImageModel
from galight.fitting_specify import FittingSpecify
from galight.fitting_process import FittingProcess
from integrated_bt_normalization import integrated_component_amplitudes
from gold91_recovery_audit import adapters,atomic_json,context_psf,read_context,sha

from optimizer_quality import capture_minimize,physical_ellipticity,physical_condition

PIX=.03

def adaptive_numerics(npix,*,factor=32,radius=6,centers=None):
    mask=np.zeros((npix,npix),dtype=bool)
    for x,y in (centers or [(npix//2,npix//2)]):
        x=int(round(x));y=int(round(y))
        mask[max(0,y-radius):min(npix,y+radius+1),max(0,x-radius):min(npix,x+radius+1)]=True
    return dict(compute_mode='adaptive',supersampling_factor=int(factor),supersampled_indexes=mask,supersampling_convolution=False)

def component_parameters(radius,n,q,theta,npix,*,fixed_n=None,center=(0.,0.)):
    if not (np.isfinite(radius) and radius>0 and np.isfinite(q) and 0<q<=1):
        raise ValueError('Invalid requested radius/axis ratio; no clipping allowed')
    e1,e2=param_util.phi_q2_ellipticity(-float(theta),float(q))
    init=dict(R_sersic=float(radius),n_sersic=float(n),e1=e1,e2=e2,center_x=float(center[0]),center_y=float(center[1]))
    sigma=dict(R_sersic=max(.001,.3*radius),n_sersic=1.,e1=.1,e2=.1,center_x=PIX,center_y=PIX)
    lower=dict(R_sersic=min(.0001,radius*.1),n_sersic=.3,e1=-.95,e2=-.95,center_x=center[0]-2*PIX,center_y=center[1]-2*PIX)
    upper=dict(R_sersic=max((npix-1)*PIX/2,4*radius),n_sersic=9.,e1=.95,e2=.95,center_x=center[0]+2*PIX,center_y=center[1]+2*PIX)
    return init,sigma,({} if fixed_n is None else {'n_sersic':float(fixed_n)}),lower,upper

def render_truth(model,psf,theta,*,branch,scale=1.,npix=267,total_flux=1e4,supersampling=2,numerics=None):
    if branch=='single':
        components=[(float(model['single_n']),float(model['single_re_arcsec'])*scale,float(model['single_q']))]
    elif branch=='bd':
        components=[(1.,float(model['disk_re_arcsec'])*scale,float(model['disk_q'])),(4.,float(model['bulge_re_arcsec'])*scale,float(model['bulge_q']))]
    else:raise ValueError(branch)
    kwargs=[]
    for n,r,q in components:
        e1,e2=param_util.phi_q2_ellipticity(-theta,q)
        kwargs.append(dict(amp=1.,R_sersic=r,n_sersic=n,e1=e1,e2=e2,center_x=0.,center_y=0.))
    light=LightModel(['SERSIC_ELLIPSE']*len(kwargs),sersic_major_axis=True)
    image_model=ImageModel(ImageData(**simulation_util.data_configure_simple(npix,PIX,inverse=True)),
        PSF(psf_type='PIXEL',kernel_point_source=psf),lens_light_model_class=light,
        kwargs_numerics=numerics or {'supersampling_factor':supersampling})
    unit_total=np.array(light.total_flux(kwargs))
    amplitudes=integrated_component_amplitudes(unit_total,float(model['bt'])) if branch=='bd' else 1/unit_total
    for component,a in zip(kwargs,amplitudes):component['amp']=float(a)
    image=image_model.lens_surface_brightness(kwargs)
    finite=float(image.sum())
    if finite<=0 or not np.all(np.isfinite(image)):raise ValueError('Invalid truth image')
    common=total_flux/float(np.sum(light.total_flux(kwargs)))
    image*=common
    for component in kwargs:component['amp']*=common
    total=np.array(light.total_flux(kwargs))
    meta=dict(integrated_bt=float(total[1]/total.sum()) if branch=='bd' else None,
              assigned_analytic_flux=float(total_flux),rendered_stamp_flux=float(image.sum()),analytic_integrated_flux=float(total.sum()),
              stamp_to_analytic_flux_ratio=float(image.sum()/total.sum()),
              requested_equals_rendered=True,psf_signed_sum=float(np.sum(psf)),
              psf_negative_flux=float(-np.sum(np.asarray(psf)[np.asarray(psf)<0])),supersampling=(numerics or {}).get('supersampling_factor',supersampling),
              compute_mode=(numerics or {}).get('compute_mode','regular'))
    return image,kwargs,meta

def make_params(kwargs,theta,npix,branch,ns,neighbours=()):
    components=[]
    for i,k in enumerate(kwargs):
        _,q=param_util.ellipticity2phi_q(k['e1'],k['e2'])
        components.append(component_parameters(k['R_sersic'],k['n_sersic'],q,theta,npix,
                 fixed_n=k['n_sersic'] if branch=='bd' else None))
    for meta in neighbours:
        cx,cy=ns['center_arcsec'](meta,npix)
        components.append(component_parameters(max(.03,float(meta['re_pix'])*PIX),1.5,float(meta['q']),float(meta['theta']),npix,center=(cx,cy)))
    params=ns['pack_source_params'](components)
    for i,component in enumerate(params[0][:len(kwargs)]):
        component['R_sersic']*=1.3 if i==0 else .7
        component['center_x']+=PIX;component['center_y']-=PIX
        if branch=='single':component['n_sersic']=float(np.clip(component['n_sersic']*1.3,.30001,8.99999))
    return params

def fit_image(image,err,seg,psf,model,truth_kwargs,theta,branch,out,ns,*,real=False,seed=2026101101,algorithm='PSO',supersampling=2,adaptive=False,adaptive_settings=None):
    if real:
        prep=ns['_prepare_real_context'](image,err,seg,psf,
            re_reference_arcsec=max(k['R_sersic'] for k in truth_kwargs),q=float(model['disk_q'] if branch=='bd' else model['single_q']),theta=theta)
        dp=prep['dp'];neighbours=prep['neighbours'];npix=prep['npix'];mask=prep['likelihood_mask']
    else:
        npix=len(image);c=npix//2
        meta=dict(label=-999999,x=float(c),y=float(c),q=float(model['disk_q'] if branch=='bd' else model['single_q']),theta=theta,
                  re_pix=max(k['R_sersic'] for k in truth_kwargs)/PIX,npix=1)
        dp,mask=ns['build_galight_data_process'](image,err,seg,psf,meta,[],[]);neighbours=[]
    params=make_params(truth_kwargs,theta,npix,branch,ns,neighbours)
    spec=FittingSpecify(dp,sersic_major_axis=True)
    spec.prepare_fitting_seq(supersampling_factor=supersampling,psf_data=dp.PSF_list[0],
        extend_source_model=['SERSIC_ELLIPSE']*len(params[0]),point_source_num=0,source_params=params,
        condition=physical_condition(ns['bd_condition'] if branch=='bd' else None),mpi=False)
    random.seed(seed);np.random.seed(seed)
    fit=FittingProcess(spec,savename=str(out))
    start=time.time()
    if algorithm=='PSO':fit.run(algorithm_list=['PSO','PSO','SIMPLEX'],setting_list=[None,None,{'n_iterations':1500}],fitting_level='norm',threadCount=1)
    elif algorithm=='SIMPLEX':fit.run(algorithm_list=['SIMPLEX'],setting_list=[{'n_iterations':3000}],fitting_level='norm',threadCount=1)
    else:raise ValueError(algorithm)
    if adaptive:
        # Coarse fits are search initialization only. All reported parameters,
        # likelihoods and uncertainty material come from the adaptive model.
        refined=copy.deepcopy(params)
        for initial,galaxy in zip(refined[0],fit.source_result):
            initial.update({k:float(galaxy[k]) for k in initial if k in galaxy})
        final_spec=FittingSpecify(dp,sersic_major_axis=True)
        final_spec.prepare_fitting_seq(supersampling_factor=2,psf_data=dp.PSF_list[0],
            extend_source_model=['SERSIC_ELLIPSE']*len(params[0]),point_source_num=0,source_params=refined,
            condition=physical_condition(ns['bd_condition'] if branch=='bd' else None),mpi=False)
        centers=[(npix//2,npix//2)]+[(float(m['x']),float(m['y'])) for m in neighbours]
        final_spec.kwargs_numerics.update(adaptive_numerics(npix,centers=centers,**(adaptive_settings or {})))
        final_spec.build_fitting_seq()
        fit=FittingProcess(final_spec,savename=str(out))
        with capture_minimize() as optimizer_records:
            fit.run(algorithm_list=['SIMPLEX'],setting_list=[{'n_iterations':3000}],fitting_level='norm',threadCount=1)
    if not adaptive:
        optimizer_records=[]  # Coarse-only fits cannot claim verified final termination.
    fit.optimizer_receipts=optimizer_records
    fit.declared_prior=dict(name=physical_condition(ns['bd_condition'] if branch=='bd' else None).__name__,version=1,ellipticity_modulus_max_exclusive=1.,bd_center_separation_max_arcsec=PIX if branch=='bd' else None)
    fit.dump_result()
    galaxies=fit.final_result_galaxy
    fluxes=[float(g['flux_sersic_model']) for g in galaxies[:len(truth_kwargs)]]
    bt=fluxes[1]/sum(fluxes) if branch=='bd' and sum(fluxes)>0 else None
    physical=all(np.isfinite(v) and v>0 for v in fluxes)
    ellipticity_valid=physical_ellipticity(fit.source_result)
    optimizer_converged=bool(optimizer_records and optimizer_records[-1]['success'])
    hits=[ns['_bound_hits'](g,params[3][i],params[4][i]) for i,g in enumerate(galaxies[:len(truth_kwargs)])]
    prior_valid=physical_condition(ns['bd_condition'] if branch=='bd' else None)(None,None,fit.source_result,None,None,None)==0.
    neighbour_valid=all(np.isfinite(g['flux_sersic_model']) and g['flux_sersic_model']>0 for g in galaxies[len(truth_kwargs):])
    likelihood_valid=bool(np.isfinite(fit.reduced_Chisq) and optimizer_records and np.isfinite(optimizer_records[-1]['objective']) and optimizer_records[-1]['objective']<1e14)
    record=dict(status='OK' if physical else 'NONPHYSICAL_COMPONENT_FLUX',seconds=time.time()-start,
        n=float(galaxies[0]['n_sersic']) if branch=='single' else None,bt=bt,
        component_radii=[float(g['R_sersic']) for g in galaxies[:len(truth_kwargs)]],
        component_fluxes=fluxes,component_q=[float(g['q']) for g in galaxies[:len(truth_kwargs)]],
        chisq=float(fit.reduced_Chisq),bound_hits=hits,fit_valid=physical and ellipticity_valid and optimizer_converged and prior_valid and neighbour_valid and likelihood_valid and not any(hits),
        final_prior_valid=prior_valid,neighbour_positive_flux=neighbour_valid,finite_nonpenalty_likelihood=likelihood_valid,
        physical_ellipticity=ellipticity_valid,declared_prior=fit.declared_prior,optimizer_converged=optimizer_converged,optimizer_receipts=optimizer_records,
        n_neighbours=len(neighbours),likelihood_fraction=float(np.mean(mask)),seed=seed,algorithm=algorithm,
        saved_fit=str(out)+'.pkl')
    record['reported_numerics']=f"adaptive{(adaptive_settings or {}).get('factor',32)}_core{(adaptive_settings or {}).get('radius',6)}" if adaptive else f'regular{supersampling}'
    return record,fit
