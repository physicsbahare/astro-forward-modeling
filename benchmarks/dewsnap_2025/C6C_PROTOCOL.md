# C6c protocol — crossed empirical-PSF construction under the clean C6b scene

Frozen after C6b workflow `33886369577` completed successfully and its artifact audit showed 12/12 finite AstroPhot attempts, four finite winners, no winner boundary hits, and near-identical matched-PSF minima to the archived Imfit C5o controls.

## Scientific question

When the two already archived empirical PSF constructions are exchanged while the source scene, fitter, starts, bounds, and noise state remain unchanged, does AstroPhot show the same directional morphology/flux failure seen previously with Imfit C5r, or does fitter choice materially change the failure mode?

This is a controlled synthetic-equivalent PSF-construction mismatch diagnostic. It is not a literal reproduction of Dewsnap et al. (2025), Photutils, PSFEx, CEERS, or JWST calibration.

## Frozen matrix

- host truth: n=1, Re=16 native pixels, q=0.6, physical PA=45 deg;
- AGN/host ratio: 10 only;
- noiseless, zero background, fixed coincident host/nucleus center;
- module-A data fitted with module-B PSF and module-B data fitted with module-A PSF;
- exact C5o n=1 input images and signed PSFs from run `33819349854`, artifact `9917787955`;
- exact C5o truth/compact/extended deterministic starts;
- AstroPhot `0.18.0`, CPU torch `2.14.0+cpu`;
- PA mapping fixed from C6b: the archived image axis maps to AstroPhot 135 deg (same Imfit numeric PA modulo 180 after the established convention transform); it is not re-selected from C6c results;
- unchanged bounds: q [0.15,1], n [0.5,6], Re [0.5,60], point flux [0,1e6]; host amplitude remains AstroPhot Ie with no claim of numerical equivalence to the finite Imfit host-amplitude ceiling;
- full 201x201 unit-variance Gaussian least squares;
- signed PSF samples retained; no clipping and no ad-hoc normalization;
- AstroPhot LM max_iter=100 and relative_tolerance=1e-5, unchanged from C6b;
- winner is the minimum finite recomputed pixel SSE in each direction regardless of optimizer status text.

## Outputs and interpretation

Record all six starts, optimizer messages, loss histories, fitted n/Re/q/PA/Ie/point flux, rendered host and point sums, recomputed SSE, residual L1/data L1, boundary hits, exact input hashes, and model/residual/component arrays. Compare each directional winner with the persisted Imfit C5r n=1 winner from run `33842347328`.

There is no recovery acceptance band and no post-hoc tolerance/bound change. Boundary collapse, start dependence, non-convergence, or a qualitatively different flux transfer between AstroPhot and Imfit are scientific observables. C6c does not authorize noise injection, production architecture, or survey-level claims.
