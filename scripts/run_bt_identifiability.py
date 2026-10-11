"""Checkpointed conditional B/T uncertainty diagnostics from saved Galight fits.

Uses Lenstronomy's emcee sampler and conditional linear-amplitude covariance.
These profile-likelihood chains are conditional on the declared structural
priors and diagonal ERR map, not a calibrated population posterior. Convergence
is assessed explicitly; no unconverged chain promotes a morphology class.
"""
from pathlib import Path
import copy,json,hashlib,pickle,traceback
import numpy as np
import emcee
from lenstronomy.Util import class_creator
from galight.tools.measure_tools import model_flux_cal
from gold91_recovery_audit import adapters,atomic_json,sha

def diagnose(project,fit_path,out,*,seed=20261011,max_steps=6000,burn=300):
    project=Path(project);fit_path=Path(fit_path);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    fingerprint=hashlib.sha256(json.dumps(dict(fit_sha=sha(fit_path),code_sha=sha(Path(__file__)),seed=seed,max_steps=max_steps,burn=burn),sort_keys=True).encode()).hexdigest()
    header=out/'manifest.json'
    if header.exists() and json.loads(header.read_text())['fingerprint']!=fingerprint:raise RuntimeError('Posterior inputs changed')
    atomic_json(header,dict(fingerprint=fingerprint,input_fit=str(fit_path),seed=seed,burn=burn,max_steps=max_steps,
        model='profile likelihood under diagonal ERR; conditional Gaussian linear amplitude covariance included',
        convergence='postburn N>50*tau for every structural parameter and <5% change in tau estimate'))
    final=out/'identifiability.json'
    if final.exists():return json.loads(final.read_text())
    fit=pickle.loads(fit_path.read_bytes()) # Only trusted local fitting products.
    ns=adapters(project,out)
    seq=fit.fitting_seq;spec=fit.fitting_specify_class
    def physical_condition(kwargs_lens,kwargs_source,kwargs_lens_light,kwargs_ps,kwargs_special,kwargs_extinction,*args,**kwargs):
        if any(np.hypot(k.get('e1',0),k.get('e2',0))>=1 for k in kwargs_lens_light):return -1e15
        return ns['bd_condition'](kwargs_lens,kwargs_source,kwargs_lens_light,kwargs_ps,kwargs_special,kwargs_extinction)
    seq._updateManager.kwargs_likelihood['custom_logL_addition']=physical_condition
    backend_path=out/'chain.h5'
    np.random.seed(seed);previous_tau=None;converged=False;tau=None
    nparam=seq.param_class.num_param()[0];walkers=max(4*nparam,32)
    backend=emcee.backends.HDFBackend(str(backend_path),name='lenstronomy_mcmc_emcee')
    current=int(backend.iteration) if backend_path.exists() and backend.initialized else 0
    while current<max_steps+burn:
        chunk=min(1000,max_steps+burn-current)
        seq.mcmc(n_burn=burn,n_run=chunk if current else max(1,chunk-burn),n_walkers=walkers,sigma_scale=.1,
                 threadCount=1,backend_filename=str(backend_path),start_from_backend=current>0,progress=False)
        current=int(backend.iteration)
        chain=backend.get_chain(discard=min(burn,current-1))
        tau=emcee.autocorr.integrated_time(chain,quiet=True,tol=50)
        stable=previous_tau is not None and np.all(np.abs(tau-previous_tau)/tau<.05)
        converged=bool(np.all(len(chain)>50*tau) and stable)
        atomic_json(out/'chain_checkpoint.json',dict(fingerprint=fingerprint,total_steps=current,postburn_steps=len(chain),
                    tau=tau.tolist(),tau_stable=bool(stable),converged=converged))
        print('CHAIN_CHECKPOINT',fit_path.name,current,'converged',converged,'max_tau',float(tau.max()),flush=True)
        if converged:break
        previous_tau=tau
    chain=backend.get_chain(discard=burn);flat=chain.reshape(-1,nparam)
    # Bounded deterministic translation sample. Structural samples retain their
    # chain dependence; these quantiles do not imply independent samples.
    rng=np.random.default_rng(seed+1);indices=np.linspace(0,len(flat)-1,min(3000,len(flat)),dtype=int)
    imaging=class_creator.create_im_sim(spec.kwargs_data_joint['multi_band_list'],'multi-linear',spec.kwargs_model,
              bands_compute=[True],linear_solver=True,image_likelihood_mask_list=spec.kwargs_likelihood['image_likelihood_mask_list'])
    bt_samples=[];bt_profile=[];rejected=0;errors=0
    for index in indices:
        kwargs=seq.param_class.args2kwargs(flat[index]);kwargs.pop('kwargs_tracer_source',None)
        try:
            _,_,covariance,_=imaging.image_linear_solve(inv_bool=True,**kwargs)
            components=kwargs['kwargs_lens_light'];amp=np.array([k['amp'] for k in components],float)
            flux=np.array(model_flux_cal(components,sersic_major_axis=True,model_list=spec.light_model_list),float)
            if np.any(flux[:2]<=0):rejected+=1;continue
            bt_profile.append(float(flux[1]/flux[:2].sum()))
            covariance=np.asarray(covariance[0] if isinstance(covariance,list) else covariance,float)
            sampled_amp=rng.multivariate_normal(amp,covariance,check_valid='ignore')
            sampled_flux=flux*sampled_amp/amp
            if np.any(sampled_flux[:2]<=0):rejected+=1;continue
            bt_samples.append(float(sampled_flux[1]/sampled_flux[:2].sum()))
        except Exception:errors+=1
    samples=np.asarray(bt_samples)
    if not len(samples):raise RuntimeError('No finite positive-amplitude B/T draws')
    np.savez_compressed(out/'bt_draws.npz',bt=samples,profile_bt=np.asarray(bt_profile),translation_indices=indices)
    result=dict(fingerprint=fingerprint,fit=str(fit_path),converged=converged,postburn_steps=len(chain),
        tau_max=float(tau.max()),effective_structural_sample_lower_bound=float(len(chain)*walkers/tau.max()),
        N_bt_draws=len(samples),translation_errors=errors,rejected_nonpositive_draws=rejected,
        bt_quantiles95=np.quantile(samples,[.025,.5,.975]).tolist(),p_bt_below_05=float(np.mean(samples<.5)),
        status='CONDITIONAL_CLASS_AMBIGUOUS' if converged and np.quantile(samples,.025)<.5<np.quantile(samples,.975) else
               'CONDITIONAL_CHAIN_CONVERGED' if converged else 'MCMC_UNCONVERGED',
        limitations='Structural profile-likelihood chain, physical ellipticity domain, conditional amplitude covariance; resampled noise covariance and between-context variation not calibrated. No intrinsic morphology claim.')
    atomic_json(final,result);return result

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--fit',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--seed',type=int,default=20261011);p.add_argument('--max-steps',type=int,default=6000)
    a=p.parse_args()
    try:print(diagnose(a.project,a.fit,a.output,seed=a.seed,max_steps=a.max_steps))
    except Exception as e:
        a.output.mkdir(parents=True,exist_ok=True);atomic_json(a.output/'ERROR.json',dict(status='ERROR',error=f'{type(e).__name__}: {e}',traceback=traceback.format_exc()));raise
