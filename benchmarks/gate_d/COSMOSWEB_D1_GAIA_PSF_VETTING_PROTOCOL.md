# Gate D1n-d — Gaia-vetted compact-source PSF support diagnostic

## Purpose

D1n-b found 14 compact, isolated, high-S/N detections in the frozen 512x512 COSMOS-Web F444W cutout, but their median stack is substantially broader and less circular than the declared single-position STPSF. Because those detections were not independently identified as stars, the stack cannot be interpreted as an empirical/effective PSF. D1n-c independently showed that background/residual structure is not a sufficient general explanation for the two remaining catastrophic AB=26 D1m interior solutions.

D1n-d asks one narrower question: **which, if any, of the already-frozen D1n-b compact candidates have independent Gaia DR3 stellar astrometric counterparts, and what do those Gaia-vetted image stamps look like relative to the declared STPSF?**

This is a catalog-vetting/support diagnostic only. It does not build or adopt a survey PSF and does not rerun morphology recovery.

## Literature/software check before implementation

- Photutils ePSF guidance recommends bright, isolated stars and warns that robust ePSF construction normally requires a large, clean, visually vetted stellar sample; a small set can produce noisy or incomplete ePSFs.
- Gaia DR3 provides an independent astrometric stellar catalog. `astroquery.gaia` provides maintained TAP/TAP+ cone-search access.
- COSMOS proper-motion work has explicitly propagated Gaia positions when tying deep HST/Subaru astrometry to Gaia, motivating proper-motion propagation rather than a static 2016-position match.

## Frozen design

1. Reuse the exact successful D1n-b artifact from run `33994133478` and its exact 512x512 real COSMOS-Web F444W cutout.
2. Do not rerun or retune DAOStarFinder. The candidate set is exactly the 14 rows already marked `support_selected=true` by D1n-b.
3. Query Gaia DR3 (`gaiadr3.gaia_source`) over the cutout footprint using `astroquery.gaia`.
4. Project the D1n-b candidate pixel coordinates to ICRS using the SCI mosaic WCS.
5. Propagate Gaia positions from their catalog `ref_epoch` to the frozen representative epoch J2023.5 when finite proper motions are available. J2023.5 is a support-match epoch inside the COSMOS-Web observing interval, not a claim that the mosaic has one literal exposure epoch.
6. Use one predeclared positional association radius: 0.15 arcsec. Record nearest separations for every D1n-b candidate whether matched or not. Do not enlarge the radius after inspection.
7. Record Gaia provenance fields needed to interpret each match: source_id, propagated coordinates, original coordinates, ref_epoch, pmra, pmdec, parallax, G magnitude and RUWE when available.
8. If at least three D1n-b candidates are Gaia-matched, form a positive-flux-normalized median stack from their **already archived D1n-b centered stamps** and compare it with the exact archived declared-STPSF stamp using the same D1n-b EE/moment/L1/correlation functions. Do not re-center or re-select stamps.
9. If fewer than three Gaia matches exist, do not construct a stack. That is a valid support limitation and is not repaired by weakening the match radius or adding morphology-based stellar labels.
10. Do not run `EPSFBuilder`, construct a PSF-matching kernel, sharpen any image, inject a source, refit a target, modify SCI/ERR/WHT, add noise, apply Tolman dimming, change segmentation, or change any D1m target/nuisance bound or convergence requirement.

## Interpretation

A coherent Gaia-vetted subset would strengthen evidence that the real mosaic effective PSF differs from the declared ideal STPSF and could justify a later, larger-field stellar ePSF experiment. A tiny or absent Gaia-vetted subset would demonstrate that this 512x512 cutout cannot independently calibrate the effective PSF; it would not justify treating the broader unvetted D1n-b stack as the PSF.

No numerical morphology-recovery acceptance band is introduced.
