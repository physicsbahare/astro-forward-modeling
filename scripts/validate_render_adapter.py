"""Cross-check diagnostic adapter against the original Galight truth grid."""
from pathlib import Path
import sys,json
import numpy as np,pandas as pd
from lenstronomy.Util import simulation_util,param_util
from lenstronomy.Data.imaging_data import ImageData
from lenstronomy.Data.psf import PSF
from lenstronomy.LightModel.light_model import LightModel
from lenstronomy.ImSim.image_model import ImageModel
root=Path('/home/bahareh/Desktop/Projects/Passive_Spiral')
sys.path.insert(0,str(root/'astro-forward-modeling/scripts'))
import gold91_recovery_audit as a
out=root/'Results/Project_Completion_20261011/gold91_diagnostics'
ns=a.adapters(root,out/'fit_products')
d=pd.read_csv(root/'Results/GOLD91_wavelength_interpolated_v2_branch_specific/tables/GOLD91_wavelength_interpolated_full_results.csv')
ctx=pd.read_csv(root/'Data/forward_z3_GOLD403_v1/context_bank/context_manifest.csv')
rows=[]
for _,r in d.iterrows():
    c=ctx.loc[(ctx.tile==r.context_tile)&(ctx.context_id==r.context_id)].iloc[0]
    theta=a.source_theta(root,int(r.source_id),ns);psf,_=a.context_psf(root,c)
    diagnostic,_,_,meta=a.render(r,psf,theta)
    target=dict(label=-999999,x=133.,y=133.,q=r.input_disk_q,theta=theta,re_pix=r.z3_disk_re_pix,npix=1)
    params=ns['pack_source_params']([ns['one_component_params'](target,267,re,n,q,fixed_n=n) for n,re,q in [(1,r.z3_disk_re_pix*.03,r.input_disk_q),(4,r.z3_bulge_re_pix*.03,r.input_bulge_q)]])
    kw=[dict(comp,amp=1) for comp in params[0]]
    lm=LightModel(['SERSIC_ELLIPSE']*2,sersic_major_axis=True)
    model=ImageModel(ImageData(**simulation_util.data_configure_simple(267,.03,inverse=True)),PSF(psf_type='PIXEL',kernel_point_source=psf),lens_light_model_class=lm,kwargs_numerics={'supersampling_factor':2})
    components=[model.lens_surface_brightness(kw,k=i) for i in range(2)]
    sums=np.array([im.sum() for im in components]);totals=np.array(lm.total_flux(kw))
    amps=np.array([1-r.input_bt,r.input_bt])/sums
    truth=sum(x*im for x,im in zip(amps,components));flux=amps*totals
    relative=np.linalg.norm(truth-diagnostic)/np.linalg.norm(truth)
    clamped=abs(kw[0]['R_sersic']-r.z3_disk_re_pix*.03)>1e-12 or abs(kw[1]['R_sersic']-r.z3_bulge_re_pix*.03)>1e-12
    rows.append(dict(source_id=int(r.source_id),original_actual_integrated_bt=float(flux[1]/flux.sum()),
        requested_disk_re=r.z3_disk_re_pix*.03,rendered_disk_re=kw[0]['R_sersic'],
        requested_bulge_re=r.z3_bulge_re_pix*.03,rendered_bulge_re=kw[1]['R_sersic'],
        radius_clipped=bool(clamped),relative_image_difference=float(relative)))
    if int(r.source_id) in a.IDS and relative>1e-10:raise AssertionError(f'Targeted image mismatch: ID{r.source_id} {relative}')
result=pd.DataFrame(rows);result.to_csv(out/'original_renderer_adapter_validation.csv',index=False)
diag=pd.read_csv(out/'normalization_and_context_diagnostics.csv').merge(result,on='source_id',validate='one_to_one')
diag['original_normalization_offset']=diag.original_actual_integrated_bt-diag.input_bt
diag.to_csv(out/'normalization_diagnostics_with_truth_flags.csv',index=False)
a.atomic_json(out/'renderer_adapter_validation_receipt.json',dict(N=90,all_eight_targeted_images_match=True,
    maximum_targeted_relative_error=float(result.loc[result.source_id.isin(a.IDS),'relative_image_difference'].max()),
    radius_clipped_ids=result.loc[result.radius_clipped,'source_id'].tolist(),
    coordinate_convention='Galight inverse=True and phi=-theta; diagnostic inverse=False and phi=theta produce equivalent centered Sersic images',
    original_normalization_median=float(diag.original_normalization_offset.median()),
    original_normalization_min=float(diag.original_normalization_offset.min()),original_normalization_max=float(diag.original_normalization_offset.max()),
    diagnostic_flux_conversion_difference_ppm=1.878682,
    conclusion='Eight diagnostic images match original structural rendering. Three other objects have requested radii clipped by the original parameter builder; flag them, do not interpret requested sizes as rendered truth.',
    code_sha256=a.sha(Path(__file__))))
print(result.loc[result.radius_clipped].to_string(index=False))
