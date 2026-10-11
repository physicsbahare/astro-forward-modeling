"""Observe the native optimizer without changing its objective or algorithm.

Single-thread fitting only: temporarily intercept Lenstronomy's imported SciPy
minimize and restore it even after errors. Success is numerical termination,
never scientific identifiability. Enforce the physical ellipticity unit disk.
"""
from contextlib import contextmanager
import numpy as np
from lenstronomy.Sampling import sampler

@contextmanager
def capture_minimize():
    records=[];original=sampler.minimize
    def observed(*args,**kwargs):
        result=original(*args,**kwargs)
        records.append(dict(success=bool(result.success),status=int(result.status),message=str(result.message),
            nit=int(result.nit),nfev=int(result.nfev),objective=float(result.fun),method=kwargs.get('method')))
        return result
    sampler.minimize=observed
    try:yield records
    finally:sampler.minimize=original

def physical_ellipticity(components):
    return all(np.isfinite(k.get('e1',0)) and np.isfinite(k.get('e2',0)) and
               np.hypot(k.get('e1',0),k.get('e2',0))<1 for k in components)

def single_physical_condition(kwargs_lens,kwargs_source,kwargs_lens_light,kwargs_ps,kwargs_special,kwargs_extinction,*args,**kwargs):
    return 0. if physical_ellipticity(kwargs_lens_light) else -1e15

def bd_physical_condition(kwargs_lens,kwargs_source,kwargs_lens_light,kwargs_ps,kwargs_special,kwargs_extinction,*args,**kwargs):
    if not physical_ellipticity(kwargs_lens_light):return -1e15
    if len(kwargs_lens_light)>=2:
        a,b=kwargs_lens_light[:2]
        if np.hypot(a['center_x']-b['center_x'],a['center_y']-b['center_y'])>.03:return -1e15
    return 0.

def physical_condition(base=None):
    # Existing consolidated bd_condition is exactly the 0.03 arcsec center
    # condition, verified from recovered definitions. Top-level functions keep
    # the full prior picklable and identical after saved-fit reload.
    return single_physical_condition if base is None else bd_physical_condition

def restore_saved_prior(fit,branch):
    """Restore the exact known prior removed by Galight.dump_result.

    Unknown historic priors are rejected; the diagnostic MCMC's separately
    declared prior amendment remains explicit in its own workflow.
    """
    if branch not in {'single','bd'}:raise ValueError('Unknown branch')
    fn=single_physical_condition if branch=='single' else bd_physical_condition
    declared=getattr(fit,'declared_prior',None)
    if declared is not None:
        expected=dict(name=fn.__name__,version=1,ellipticity_modulus_max_exclusive=1.,bd_center_separation_max_arcsec=.03 if branch=='bd' else None)
        if declared!=expected:raise ValueError('Saved prior schema mismatch')
    elif fn.__name__ not in getattr(fit,'prior',''):
        raise ValueError('Exact saved prior cannot be established')
    fit.fitting_specify_class.kwargs_likelihood['custom_logL_addition']=fn
    fit.fitting_seq._updateManager.kwargs_likelihood['custom_logL_addition']=fn
    return fit
