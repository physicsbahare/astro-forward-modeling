# C5o: matched-PSF free-shape Imfit preflight

Frozen 2026-09-03 UTC before any C5o fit. The repaired regression run
`33810187827` and same-setting C5n run `33810187864` must both be explicit
GitHub successes before dispatch.

## Question and separation of effects

C5d--C5g showed large conditional host-flux errors, apparent nuclear offsets
and one zero-host solution when the empirical PSF was mismatched, but held the
host shape fixed. C5h--C5n then tested renderer conventions and resources. The
extreme compact corners remain numerically unconverged; at the actual C5 anchor
(`Re=16` native pixels, `q=0.6`, `n=1` or `4`) the C5h Imfit8/GalSim image L1
difference was only 0.002--0.028 percent. C5o therefore tests the fitting
pipeline only at those declared anchors. It does not validate the extreme
corners.

Before applying a wrong PSF, fit matched-PSF noiseless GalSim data with the
independent Imfit 1.9.0 Sersic implementation and optimizer. This separates
cross-fitter/rendering behavior from physical PSF mismatch. A successful
process exit or agreement among starts is not by itself physical recovery.

## Frozen matrix

- host truth: `n=1` and `n=4`, `Re=16`, `q=0.6`, `PA=45 deg`;
- empirical PSF/data module: A fitted with A, and B fitted with B only;
- AGN/host: 1 and 10; the 0.1 case is deferred because the high-contrast
  identifiability question is the immediate prerequisite for mismatch;
- zero noise and zero background; fixed host and nucleus center at the exact
  detector center;
- free host `PA`, `q` (through `ell=1-q`), `n`, `Re`, and amplitude; free point
  amplitude;
- unchanged physical shape bounds: `0.5 <= n <= 6`, `0.5 <= Re <= 60`,
  `0.15 <= q <= 1`; PA uses the equivalent Imfit interval `[-180,180]`;
- three deterministic starts, fixed before results, including the truth shape
  and two deliberately displaced shapes;
- full 201-square crop and constant unit noise map, so Imfit minimizes the same
  unweighted pixel-space sum of squares used by the earlier controlled fits;
- supplied native effective PSF is the archived signed point template. It is
  passed with `--no-normalize`; negative wings are retained and these scenes
  are not photon-ready.

Imfit requires finite parameter limits. The two nonnegative amplitudes use the
predeclared numerical ceiling `1e6`, many orders above the unit-host and
10-unit nucleus truth. Any ceiling hit is a reported observable and invalidates
the preflight; it is not an astrophysical acceptance bound. No shape bound or
fit tolerance is loosened.

## Software-first decision and conventions

Reuse the authors' checksum-pinned Imfit 1.9.0 Linux binary, not a bespoke
renderer or optimizer. Archive SHA256 is
`9eb10a62baab87de98744c247f7a10ea02b05d32996760b7cef100f5f02a7089`;
the `imfit` executable SHA256 is
`57cc48293aeb25e92ed82f600d2c7e15022c81fd0172970648a9ac7a241f7103`.
Imfit is GPL-3.0-or-later and is downloaded at runtime, not vendored or made a
production dependency.

Official documentation checked before implementation:

- Erwin 2015 / Imfit home and license: https://www.mpe.mpg.de/~erwin/code/imfit/
- configuration limits and `fixed` syntax:
  https://imfit.readthedocs.io/en/latest/config_file_format.html
- PSF convolution, constant external noise maps and saved model/residual:
  https://www.mpe.mpg.de/~erwin/code/imfit/markdown/index.html
- `PointSource` uses the supplied PSF and its amplitude is total flux:
  https://imfit.readthedocs.io/en/latest/frequently_asked_questions.html

The executable's own pinned `--list-parameters` reports Sersic parameters
`PA, ell, n, I_e, r_e` and PointSource parameter `I_tot`. Imfit uses 1-based
centers and PA counter-clockwise from +y, so the archived center is `(101,101)`
and the existing +45-degree GalSim orientation maps to Imfit `PA=-45 deg`.
The PSF already includes detector response; no second pixel convolution or
deconvolution is introduced.

## Outputs and decision rule

Save config, exact inputs, binary identity, every start configuration/stdout/
stderr/best-fit file, model and residual FITS, parsed parameters, metrics CSV,
all image arrays, warnings and resource receipts. The read-only audit must
reconstruct data-model residuals, objective values, truth hashes, start/winner
selection, bounds and completeness. Winner is the minimum finite pixel SSE;
optimizer `success`, failures, negative values and every bound hit remain.

There is no post-hoc recovery band. If the matched-PSF pipeline is complete,
finite and does not collapse to an amplitude/shape boundary, its actual biases
and start dependence may justify a separately frozen wrong-PSF free-shape
experiment. Otherwise diagnose this preflight first. C5o is synthetic-
equivalent and does not close Zhuang & Shen, Dewsnap, chromatic PSF, real-
survey injection or production gates.
