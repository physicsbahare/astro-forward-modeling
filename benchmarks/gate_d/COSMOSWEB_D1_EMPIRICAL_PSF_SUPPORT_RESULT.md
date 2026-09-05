# COSMOS-Web Gate D1n-b — empirical point-source / effective-PSF support result

## Immutable execution receipt

Workflow: `gate-d-cosmosweb-empirical-psf-support`

Confirmed GitHub Actions run: `33994133478`

- status: `completed`
- conclusion: `success`
- head SHA: `8b389e76c440d940a5045ec74fac36ed6d9b022c`
- artifact: `gate-d-cosmosweb-empirical-psf-support`
- artifact id: `9977535930`
- artifact SHA256: `8ce56143f3dceef0bf77b286ed12a3b7a2d38ea0018a5eddee4e302943746e69`

The successful machine-readable `summary.json` was inspected directly from the artifact. Workflow success is execution success only; it is not evidence that the median compact-source stack is the COSMOS-Web effective PSF.

## Machine-readable result

The frozen 512x512 real COSMOS-Web F444W cutout produced 15 DAOStarFinder detections, of which 14 satisfied the predeclared edge, isolation, and central-ERR S/N support cuts. These detections were intentionally not asserted to be stars and were not visually or catalog-vetted.

On the common 31x31 support, the single declared D1d-D1m STPSF has:

- EE50 = 0.08633 arcsec;
- EE80 = 0.18004 arcsec on the truncated 31x31 comparison stamp;
- moment axis ratio = 0.9748.

The positive-flux normalized median stack of all 14 selected compact candidates has:

- EE50 = 0.13532 arcsec;
- EE80 = 0.23415 arcsec;
- moment axis ratio = 0.8173;
- normalized L1 to the declared STPSF = 0.66296;
- normalized cross-correlation to the declared STPSF = 0.86773.

Individual selected objects span a wide morphology range, including strongly elongated/broad cases and substantial negative background-subtracted residual fractions. Therefore the observed stack difference cannot be attributed uniquely to the effective PSF: contamination by compact galaxies, imperfect local-background subtraction, source SED differences, drizzle/exposure-mixture effects, and true PSF mismatch remain confounded.

Photutils `EPSFBuilder` was deliberately not run. The current support set is small and not independently stellar-vetted; forcing an ePSF would overstate the evidence.

## Scientific interpretation

D1n-b establishes two facts simultaneously. First, the literal real mosaic contains a compact-source population whose aggregate shape is materially broader and less circular than the single ideal STPSF used for the injection/recovery path. Second, this 512x512 cutout does not provide a scientifically defensible empirical PSF because the compact objects are not independently identified as stars and the sample is far below the large, clean stellar samples recommended for robust ePSF construction.

The discrepancy therefore motivates an independent stellar-identification step before any matched/mismatched-PSF morphology rerun. It does not justify substituting the 14-object stack for STPSF, deriving a sharpening kernel, changing target bounds, or loosening recovery criteria.

No injection, target refit, noise addition, Tolman factor, PSF sharpening, ERR/WHT modification, or acceptance-threshold change was performed.
