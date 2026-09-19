# C5r: wrong-PSF free-shape Imfit diagnostic

Frozen 2026-09-04 UTC after auditing C5q run `33830661656`. Both seeded
DE-LHS searches for each matched module reached the unchanged 180-second cap
without complete products. Together with C5o and C5p, this establishes that
the matched-PSF high-contrast problem is strongly start-, solver- and
module-dependent; it does not establish global convergence. That limitation
is carried forward rather than hidden or repaired by a larger resource cap.

## Question and frozen matrix

At the nominal anchor, how does exchanging the two empirical module PSFs alter
the minimum finite host structure and flux recovered across the already
declared deterministic starts?

- truth host `n=1` and `n=4`, `Re=16`, `q=0.6`, `PA=45 deg`;
- noiseless AGN/host=10 only, because this is the declared high-contrast
  prerequisite and avoids mixing target noise or a lower-contrast question;
- module-A data fitted with the module-B PSF and module-B data fitted with the
  module-A PSF; matched controls remain the preserved C5o artifacts;
- the exact C5o truth, compact and extended starts, fixed coincident centers,
  full 201-square crop, constant unit noise map, shape/amplitude bounds,
  one-thread execution and 180-second per-start process cap;
- Imfit 1.9.0 default bounded Levenberg--Marquardt path, recording every
  timeout, finite solution, objective, boundary hit, model and residual;
- signed native empirical PSFs are passed with `--no-normalize`. They remain
  verification templates and are not photon-ready PSFs.

C5r succeeds as an execution when all six attempts per host index and their
logs are recorded and every available finite product passes the read-only
algebra audit. A timeout or boundary solution is a scientific observable, not
a workflow failure. The winner for each direction is the lowest recomputed
finite pixel SSE; there is no recovery or acceptance band.

## Software-first decision

Reuse the checksum-pinned Imfit fitter and C5o adapter. No new optimizer,
renderer or PSF manipulation is introduced. The official Imfit configuration,
PSF-convolution and PointSource conventions checked for C5o still apply.
Zhuang & Shen (2024) specifically predict that mismatched PSFs can bias host
flux and concentration, with the sign depending on whether the adopted PSF is
broader or narrower; C5r measures that response for these archived templates.

Sources checked before freezing:

- Zhuang & Shen 2024, ApJ 962, 139: https://arxiv.org/abs/2304.13776
- Imfit configuration bounds: https://imfit.readthedocs.io/en/latest/config_file_format.html
- Imfit PSF/PointSource conventions: https://imfit.readthedocs.io/en/latest/frequently_asked_questions.html

This synthetic-equivalent diagnostic does not validate the signed PSFs,
prove identifiability, reproduce a survey, or authorize production use.
