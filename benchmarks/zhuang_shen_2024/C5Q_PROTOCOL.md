# C5q: seeded Imfit global-search diagnostic

Frozen 2026-09-04 UTC after the complete C5p artifacts from run
`33823405733` were audited. C5p showed that the high-contrast compact start is
solver- and module-dependent: Nelder--Mead stopped in an inferior compact-host
basin for both modules, module-A Levenberg--Marquardt timed out on that path,
and module-B LM reached the lower-cost extended-host solution. C5o remains a
failed preflight and C5p remains a successful diagnostic execution only.

## Question and frozen matrix

Can Imfit's existing bounded population search find a lower objective from the
same difficult configuration without changing any physical or numerical fit
definition?

- reuse the exact C5p data, signed matched PSF, unit noise map and compact
  initial configuration for modules A and B;
- host truth `n=4`, `Re=16`, `q=0.6`, `PA=45 deg`, AGN/host=10;
- fixed coincident centers and the unchanged C5o shape/amplitude bounds;
- Imfit 1.9.0 `--de-lhs` Differential Evolution with Latin-hypercube initial
  population;
- two predeclared positive RNG seeds: `20260904` and `20260905`;
- one thread and the unchanged 180-second process limit for every seed;
- exact process logs, exit status and any complete model/residual products are
  retained. Timeout is an observable, not a reason to expand the cap.

C5q's execution succeeds when both seeded attempts per module are recorded and
the artifact audit reconstructs every available objective. It does not require
the global solver to finish and introduces no recovery band. If finite seeds
agree on a lower objective, that supports a search-basin diagnosis only; it
does not make either renderer truth or establish identifiability.

## Software-first and reproducibility decision

Use the authors' checksum-pinned Imfit implementation rather than write a new
global optimizer. The pinned executable advertises `--de-lhs` and `--seed`;
its bundled 1.9.0 changelog states that `--de-lhs` initializes trial vectors
with Latin-hypercube sampling. Configuration bounds are mandatory for Imfit's
DE solver and are already present. The alternative PyImfit wrapper uses the
same engine and would not add independence here. SciPy Differential Evolution
was already exercised in C5c for the earlier fixed-shape question; substituting
it now would confound engine and free-shape objective differences.

Sources checked before implementation:

- Imfit solver architecture: https://imfit.readthedocs.io/en/latest/api_ref/design-and-architecture.html
- bounded configuration requirements: https://imfit.readthedocs.io/en/latest/config_file_format.html
- Imfit command overview: https://imfit.readthedocs.io/

Imfit remains a verification-only GPL-3.0-or-later runtime dependency. Review
the actual seeded artifacts before deciding whether matched-PSF behavior is
sufficiently characterized to freeze the separate wrong-PSF free-shape arm.
