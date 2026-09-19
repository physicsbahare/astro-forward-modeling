#!/usr/bin/env python3
"""Audit information content of the noisy CALIFA-like full-chain morphology cases.

The noisy recovery workflow formally converged for all 60 images but frequently
landed on Re/n/centroid/q bounds.  This diagnostic does not refit or alter any
bound.  Instead it asks whether the apparent contradiction with the quoted
point-source S/N is explained by the galaxies being extended: the survey depth
is a matched-filter *point-source* depth, whereas morphology information is
spread over many pixels.

For each noiseless transferred galaxy we report:
  * point-source-equivalent S/N from the quoted ACS depth;
  * exact known-template matched-filter S/N, sqrt(sum(model**2))/sigma;
  * peak-pixel S/N;
  * whole-stamp flux/sqrt(Npix)/sigma (diagnostic only);
  * Re/PSF FWHM.

No acceptance cut is introduced.  These are observability diagnostics only.
"""
from __future__ import annotations
import csv, json, sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from scripts.run_paulino_afonso_full_chain_califa import CASES,TARGET_Z,transfer_to_target
from verification.paulino_afonso_sersic_floor import (
    PIXEL_SCALE_ARCSEC, PSF_FWHM_ARCSEC, POINT_DEPTH_AB_5SIGMA,
    _kpc_per_arcsec, adaptive_stamp_size, flux_in_depth_units,
    mag_from_depth_units, pixel_noise_from_point_depth,
)

def crop(image,size):
    size=min(size,image.shape[0],image.shape[1]); size-=int(size%2==0)
    y0=(image.shape[0]-size)//2; x0=(image.shape[1]-size)//2
    return np.asarray(image[y0:y0+size,x0:x0+size],float)

def main():
    out=Path('benchmark_output/paulino_afonso_2017/full_chain_information_audit'); out.mkdir(parents=True,exist_ok=True)
    sigma=pixel_noise_from_point_depth(); rows=[]
    for z0 in TARGET_Z:
        z=float(z0); kpa=_kpc_per_arcsec(z)
        for case in CASES:
            sf=flux_in_depth_units(float(case['source_mag_ab']))
            transferred,*_,flux_ratio=transfer_to_target(case,z,sf)
            re_pix=float(case['re_kpc'])/kpa/PIXEL_SCALE_ARCSEC
            image=crop(transferred,adaptive_stamp_size(re_pix))
            target_flux=sf*flux_ratio; target_mag=mag_from_depth_units(target_flux)
            ps_snr=float(5*10**(-0.4*(target_mag-POINT_DEPTH_AB_5SIGMA)))
            template_snr=float(np.sqrt(np.sum(image**2))/sigma)
            peak_snr=float(np.max(image)/sigma)
            stamp_sum_snr=float(np.sum(image)/(sigma*np.sqrt(image.size)))
            rows.append({'case':case['case'],'z_target':z,'input_n':float(case['n']),'input_re_kpc':float(case['re_kpc']),'target_mag_ab':target_mag,'point_source_equivalent_snr':ps_snr,'known_template_matched_snr':template_snr,'peak_pixel_snr':peak_snr,'whole_stamp_sum_snr':stamp_sum_snr,'re_over_psf_fwhm':float(re_pix/(PSF_FWHM_ARCSEC/PIXEL_SCALE_ARCSEC)),'stamp_size':int(image.shape[0])})
    with (out/'rows.csv').open('w',newline='') as h:
        w=csv.DictWriter(h,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    by=[]
    for z0 in TARGET_Z:
        s=[r for r in rows if r['z_target']==float(z0)]
        by.append({'z_target':float(z0),'median_point_source_equivalent_snr':float(np.median([r['point_source_equivalent_snr'] for r in s])),'median_known_template_matched_snr':float(np.median([r['known_template_matched_snr'] for r in s])),'median_peak_pixel_snr':float(np.median([r['peak_pixel_snr'] for r in s])),'median_whole_stamp_sum_snr':float(np.median([r['whole_stamp_sum_snr'] for r in s])),'median_re_over_psf_fwhm':float(np.median([r['re_over_psf_fwhm'] for r in s]))})
    payload={'experiment':'full-chain extended-source information audit','scientific_status':'diagnostic only; no morphology acceptance cut and no bound changes','n_cases':len(rows),'noise_sigma_depth_units':sigma,'by_redshift':by,'rows':rows,'interpretation_rule':'If point-source-equivalent S/N substantially exceeds known-template/peak morphology information while noisy fits hit multiple parameter or centroid bounds, interpret the pathology as extended-source identifiability loss rather than as a reason to widen bounds. If known-template S/N is high yet fits remain pathological, investigate fitter/model mismatch next.'}
    (out/'summary.json').write_text(json.dumps(payload,indent=2)+'\n'); print(json.dumps(payload,indent=2))
if __name__=='__main__': main()
