#!/usr/bin/env python3
"""Standalone deterministic *TOY* two-component identifiability diagnostic.

Not a Lenstronomy/Galight substitute; uses circular pixel-sampled Sersic n=1/4
with Gaussian PSF. Fits ONLY two nonnegative amplitudes at FIXED shape/centroid.
Does not use COSMOS-Web catalog, PSFEx, science thresholds or previous products.
"""
import argparse, csv, hashlib, json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.optimize import nnls
from scipy.special import gammaincinv

CASES = [
    ("well_resolved", 4.0, 1.0),
    ("marginal", 1.4, 0.45),
    ("unresolved", 0.50, 0.15),
]
SEED = 20261023
FWHM = 2.0
N_SIDE = 64
N_TRIALS = 400

def component(n, re, psf_fwhm, side=N_SIDE):
    axis=np.arange(side,dtype=float)-(side-1)/2
    xx,yy=np.meshgrid(axis,axis)
    r=np.hypot(xx,yy)
    bn=gammaincinv(2*n,0.5)
    # Finite central pixel, not integrated over pixel; toy only.
    z=np.exp(-bn*((r/re)**(1./n)-1.))
    z=gaussian_filter(z, psf_fwhm/2.354820045, mode='constant',cval=0.)
    return z/z.sum()

def one_case(rng,label,rd,rb,snr,bt,model_fwhm):
    d=component(1,rd,FWHM).ravel()
    b=component(4,rb,FWHM).ravel()
    design=np.column_stack((component(1,rd,model_fwhm).ravel(),component(4,rb,model_fwhm).ravel()))
    cs= np.dot(d,b)/(np.linalg.norm(d)*np.linalg.norm(b))
    norm_design=design/np.linalg.norm(design,axis=0)
    cond=float(np.linalg.cond(norm_design))
    signal=(1-bt)*d+bt*b
    noise_sigma=np.linalg.norm(signal)/snr
    # Matrix-level noise draw; exact repeated trials with frozen seed.
    observations=signal[:,None]+rng.normal(0,noise_sigma,(len(signal),N_TRIALS))
    # For 2-component linear fixed-shape amplitude fit, precompute normal equations.
    gram_inv=np.linalg.pinv(design.T@design)
    uncon=gram_inv@(design.T@observations)
    raw_negative=np.any(uncon<0,axis=0)
    fitted=[]
    for j in range(N_TRIALS):
        amps=uncon[:,j]
        if np.any(amps<0):
            amps=nnls(design,observations[:,j])[0]
        fitted.append(amps)
    fitted=np.asarray(fitted)
    denomin=fitted.sum(axis=1)
    recovered=np.divide(fitted[:,1],denomin,out=np.full(N_TRIALS,np.nan),where=denomin>0)
    true_is_disk=bt<0.5
    measured_disk=recovered<0.5
    return {
        'label':label,'input_re_disk_px':rd,'input_re_bulge_px':rb,
        'psf_fwhm_px':FWHM,'fit_psf_fwhm_px':model_fwhm,
        'input_bt':bt,'integrated_template_snr':snr,'trials':N_TRIALS,
        'template_cosine':float(cs),'normalized_design_condition':cond,
        'mean_recovered_bt':float(np.mean(recovered)),
        'median_recovered_bt':float(np.median(recovered)),
        'bt_bias_median':float(np.median(recovered)-bt),
        'bt_sigma_robust':float(0.5*(np.percentile(recovered,84)-np.percentile(recovered,16))),
        'bt_p16':float(np.percentile(recovered,16)),
        'bt_p84':float(np.percentile(recovered,84)),
        'wrong_side_of_bt_0p5_fraction':float(np.mean(measured_disk!=true_is_disk)),
        'unconstrained_negative_amplitude_fraction':float(np.mean(raw_negative)),
        'fixed_truth_shape':True,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',default='toy_results')
    args=p.parse_args()
    rng=np.random.default_rng(SEED)
    rows=[]
    for label,rd,rb in CASES:
        for snr in (30.0,100.0):
            for bt in (0.25,0.45,0.55,0.75):
                rows.append(one_case(rng,label,rd,rb,snr,bt,FWHM))
    # Isolate PSF-model mismatch to show systematic B/T effects; same input truth.
    for mismatch in (1.8,2.2):
        rows.append(one_case(rng,'well_resolved_psf_mismatch',4.0,1.0,100.0,0.45,mismatch))
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    fields=list(rows[0]);
    with (out/'toy_results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest={
      'scientific_status':'TOY_ONLY_NOT_COSMOS_WEB',
      'purpose':'Fixed-shape, two-amplitude toy diagnostic; no production calibration',
      'experiment_id':'toy_bt_identifiability_20261023_v1',
      'seed':SEED,'n_trials_per_cell':N_TRIALS,'n_synthetic_cells':len(rows),
      'synthetic_sources':'circular sampled Sersic n=1 disk and n=4 bulge; Gaussian PSF',
      'important_assumptions':['fitted shapes and centers known perfectly',
        'white independent Gaussian pixel noise','fixed total noiseless source flux=1',
        'single-band, no colors, no neighboring sources','per-case SNR is integrated template norm / pixel RMS',
        'psf mismatch results conflate amplitude and fixed wrong PSF shape'],
      'limitations':['not a Galight/Lenstronomy fit','not a real JWST PSFEx',
        'finite-stamp, center-point pixel sampling','linear amplitudes only',
        'not comparable to GOLD91/403 numerical receipts',
        'cannot establish scientific B/T identifiability thresholds, completeness, or class-purity'],
      'code_sha256':sha,
    }
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    # Internal sanity checks; do not calibrate thresholds with toy data.
    for row in rows:
        assert 0<=row['mean_recovered_bt']<=1
        assert 0<=row['wrong_side_of_bt_0p5_fraction']<=1
        assert row['template_cosine']<=1.000000001
    for case in CASES:
        for n,re in [(1,case[1]),(4,case[2])]:
            assert np.isclose(component(n,re,FWHM).sum(),1,atol=1e-12)
    print(json.dumps({'manifest':manifest,'rows':rows},indent=2))

if __name__=='__main__':
    main()
