# C5p: bounded Imfit optimizer-path diagnostic

Frozen 2026-09-04 UTC after C5o run `33819349854` completed with a split
result: the `n=1` shard passed its strict audit, while the `n=4` shard failed
because the compact start for module A at AGN/host=10 reached the frozen
180-second process limit. The failed C5o artifact and its acceptance rule are
preserved; C5p is a separate diagnostic, not a replacement success.

## Question and frozen scope

The C5o truth and extended starts for the same module-A scene completed in
3--4 seconds and reached the same finite solution. Is the compact-start
failure a slow path of Imfit's default Levenberg--Marquardt solver, or does a
second maintained solver expose a distinct local basin under the same image,
model, objective and bounds?

- host truth: `n=4`, `Re=16`, `q=0.6`, `PA=45 deg`;
- empirical matched-PSF modules A and B, tested in separate CI jobs;
- AGN/host=10 only;
- the unchanged C5o compact start: `n=2`, `Re=8`, `q=0.8`, `PA=0`, host
  flux=0.5 and point flux=8;
- fixed coincident centers, zero noise/background, constant unit noise map,
  full 201-square objective and the archived signed native PSF;
- unchanged shape and amplitude bounds and unchanged 180-second per-process
  limit;
- Imfit 1.9.0 default Levenberg--Marquardt and its documented `--nm`
  Nelder--Mead solver. Both use one thread and the identical starting file.

Every attempted process, including timeout or missing product, is a result.
C5p succeeds as an execution/audit record when both solver attempts and their
logs are complete; it does not require either solver to converge and has no
recovery tolerance. A finite Nelder--Mead result is compared by recomputed
pixel SSE, not by exit label. Agreement or a lower objective would diagnose
search behavior, not physical truth.

## Software-first decision

Reuse the already checksum-pinned author Imfit binary rather than add a custom
optimizer. Official Imfit 1.9 documentation states that Levenberg--Marquardt
is the default solver and `--nm` selects Nelder--Mead; Differential Evolution
also exists but is not included in this first bounded replay because its
population cost is materially larger for a 40,401-pixel, six-free-parameter
fit. It remains a later option only if the two bounded paths do not answer the
question.

Sources checked before implementation:

- design/solver dispatch: https://imfit.readthedocs.io/en/latest/api_ref/design-and-architecture.html
- configuration limits: https://imfit.readthedocs.io/en/latest/config_file_format.html
- command examples and solver selection: https://imfit.readthedocs.io/

Imfit is GPL-3.0-or-later, downloaded at runtime, and is not adopted as a
production dependency. C5p does not authorize the wrong-PSF free-shape arm;
its actual artifacts must be reviewed first.
