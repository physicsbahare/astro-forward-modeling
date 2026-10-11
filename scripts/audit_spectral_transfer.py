"""Reproduce saved flux inputs; compare with frozen full-throughput operator.

Integrated SED sensitivity only. This does not replace the spatially resolved
R3 synthesis or silently recalibrate existing fitting checkpoints.
"""
from pathlib import Path
import ast,sys,json
import numpy as np,pandas as pd,h5py
from scipy.ndimage import binary_dilation
from skimage.restoration import denoise_wavelet
project=Path('/home/bahareh/Desktop/Projects/Passive_Spiral')
sys.path.insert(0,str(project/'astro-forward-modeling'))
sys.path.insert(0,str(project/'astro-forward-modeling/scripts'))
sys.path.insert(0,str(project/'Codes'))
from passive_disk_forward_model import central_segment_mask
from gold91_recovery_audit import load_functions,sha,atomic_json
from verification.nircam_throughput_sensitivity import load_mean_throughput,fnu_response_moments,curved_fnu_bandpass_weights
output=project/'Results/Project_Completion_20261011/spectral_audit';output.mkdir(exist_ok=True)
ns=dict(np=np,binary_dilation=binary_dilation,denoise_wavelet=denoise_wavelet,central_segment_mask=central_segment_mask,
        SOURCE_MASK_DILATION_PIX=8,SOURCE_WAVELET_LEVELS=3)
load_functions(project/'Codes/05_GOLD403_z3_MODEL_based_injection_FAST_PILOT.ipynb',[15],ns,{'fit_background_plane','clean_source_band'})
root=Path('/home/bahareh/nircam_throughputs_Jan2025_v7/nircam_throughputs/mean_throughputs')
bands=('F115W','F150W','F277W');curves={b:load_mean_throughput(b,root) for b in [*bands,'F444W']}
means={b:fnu_response_moments(c.wavelength_um,c.throughput,1)[1] for b,c in curves.items()}
d=pd.read_csv(project/'Results/GOLD91_wavelength_interpolated_v2_branch_specific/tables/GOLD91_wavelength_interpolated_full_results.csv')
manifest=pd.read_csv(project/'Data/real_cutouts_GOLD403_for_z3/real_cutout_manifest.csv')
rows=[];sources=set()
for _,r in d.iterrows():
    m=manifest.loc[manifest.id==r.source_id].iloc[0];sources.add(Path(m.output_h5))
    flux={};record=dict(source_id=int(r.source_id),status='OK',saved_source_fnu_jy=float(r.e0_source_fnu_jy))
    try:
        with h5py.File(m.output_h5) as f:
            j=int(m.h5_index);assert int(f['id'][j])==int(r.source_id)
            seg=f['SEGMENTATION'][j]
            for b in bands:
                image,support,_,_=ns['clean_source_band'](f[b]['SCI'][j],f[b]['ERR'][j],seg)
                # Exact frozen notebook conversion; rounded arcseconds/radian
                # differs from the precise value by 1.879 ppm, not SED physics.
                value=float(image[support&np.isfinite(image)].sum()*1e6*(.03/206265.)**2)
                if not np.isfinite(value) or value<=0:raise ValueError(f'NONPOSITIVE_{b}_SCENE_FLUX')
                flux[b]=value;record['source_fnu_jy_'+b]=value
        lo=r.e0_flux_low_band;hi=r.e0_flux_high_band
        if lo not in flux or hi not in flux:raise ValueError('Saved bracket outside frozen three bands')
        scalar=np.exp((1-r.e0_flux_alpha_loglambda)*np.log(flux[lo])+r.e0_flux_alpha_loglambda*np.log(flux[hi]))
        discrepancy=scalar/r.e0_source_fnu_jy-1
        if abs(discrepancy)>1e-7:raise ValueError(f'SAVED_FLUX_REPRODUCTION_MISMATCH_{discrepancy}')
        scale=(1+r.z_source)/4;curve=curves['F444W'];lam=curve.wavelength_um*scale
        weight=curve.throughput/lam
        support_fraction=np.trapezoid(weight*((lam>=means['F115W'])&(lam<=means['F277W'])),lam)/np.trapezoid(weight,lam)
        weights=curved_fnu_bandpass_weights(source_bands=bands,target_band='F444W',z_source=r.z_source,z_target=3,directory=root)
        curved=float(np.dot(weights,[flux[b] for b in bands]))
        record.update(recomputed_scalar_fnu_jy=scalar,scalar_closure_fraction=discrepancy,
              source_anchor_coverage=float(support_fraction),weight_F115W=float(weights[0]),weight_F150W=float(weights[1]),weight_F277W=float(weights[2]),
              full_throughput_curved_fnu_jy=curved,curved_to_saved_scalar_ratio=curved/scalar,
              negative_weight_l1=float(-weights[weights<0].sum()))
        if support_fraction<.99:record.update(status='SPECTRAL_SUPPORT_FAILURE')
        elif curved<=0:record.update(status='NONPOSITIVE_CURVED_FLUX')
    except Exception as e:record.update(status='ERROR',error=str(e))
    rows.append(record)
result=pd.DataFrame(rows);result.to_csv(output/'GOLD91_full_throughput_flux_sensitivity.csv',index=False)
supported=result.loc[result.status=='OK','curved_to_saved_scalar_ratio']
atomic_json(output/'spectral_transfer_receipt.json',dict(N=len(result),status_counts=result.status.value_counts().to_dict(),
    ratio_median=float(supported.median()) if len(supported) else None,
    ratio_p16=float(supported.quantile(.16)) if len(supported) else None,ratio_p84=float(supported.quantile(.84)) if len(supported) else None,
    interpretation='Integrated source-flux sensitivity; both choices share the same validated cosmological factor. Not a corrected pixel-SED morphology run or new luminosity evolution.',
    production_gate='Flux difference and negative spectral coefficients need propagation to measurability before the effective-wavelength GOLD91 runs become a final selection calibration.',
    input_hashes={str(p):sha(p) for p in [*sources,Path(__file__),project/'Codes/05_GOLD403_z3_MODEL_based_injection_FAST_PILOT.ipynb']}))
print(result.status.value_counts().to_dict());print('curved/scalar',supported.describe().to_dict())
