# C5n: separately frozen resource-bounded Imfit8/10 diagnostic

Frozen 2026-09-03 UTC before any sampling10 images. C5m is an incomplete
LOCAL diagnostic, not a passed or dispatched CI run. Its initial PSF-key
adapter failures and corrected rerun are preserved in c5m_local_20260903.json.
Corrected C5m: all eight sampling8 replays succeeded, but all eight sampling16
calls failed at Imfit Convolver::DoFullSetup memory allocation. No sampling16
science image exists; no CI rerun of this deterministic failure is launched.
The six-GiB cap, timeout and historical C5m protocol remain unchanged.

## Source/software-first resource assessment

Checked the author's exact v1.9 source:
- https://github.com/perwin/imfit/blob/v1.9/core/model_object.cpp
- https://github.com/perwin/imfit/blob/v1.9/core/convolver.cpp

ModelObject expands a square data image D to D+2K, where K is PSF side.
Convolver then uses P=D+3K-1. It allocates three P*P doubles and three
P*(floor(P/2)+1) complex doubles. Here D=200*s+1, K=208*s+1,
P=824*s+3. Those six FFT arrays alone need about 7.77 GiB at s=16,
already exceeding the existing cap, before the model, PSF, plans or process.
At s=10 they need about 3.04 GiB, leaving substantially more headroom.
This is allocation accounting from source, NOT a guaranteed runtime budget.

Select **8 and 10** for a NEW diagnostic to obtain a finer numerical point
with headroom. This is not a substituted success for C5m16, not a change to
physical bounds, and not sufficient by itself to prove convergence. Do not
choose a sampling factor based on favorable flux errors. C5m16 remains a
failed resource observation; no retry, memory-cap increase or cropped PSF.

Alternative: changing convolution implementation (SciPy/GalSim or an
oversampled-subregion Imfit mode) also changes algorithm or support handling,
so is deferred rather than silently substituted. Keep the existing pinned
Imfit 1.9.0 binary, C5h thin adapter and full signed kernel. No new package
or handwritten convolution/integrator. C5M_PROTOCOL.md records all units,
licenses, runtime pins, conventions and prior paper/software search.

## Exact inheritance and completeness

Everything in C5m is inherited except the separately labelled stage and
external numerical sampling 16 -> 10: same eight compact scenes, signed A/B
PSFs, native stamp, full support, flux and radius conventions, 120s worker,
6GiB address-space cap, one thread, five-second kill grace and 35-minute job.
Replays8 compare with archived Imfit8 at inherited absolute 1e-12. Both
samplings compare to Imfit8 and C5l no_cell, retaining all 32 fits, eight
within-Imfit comparisons, 16 fine FITS and 168 new NPZ arrays. Physical
PSFs and all structural bounds are unchanged. All warnings/failures remain.

Implementation is a scoped adapter over C5m code; its sampling scope and
protocol are restored after execution. C5m source and C5n adapter hashes are
recorded separately. No selective winner, new acceptance band or claim that
Imfit/GalSim is ground truth. Review actual CI artifacts before any next
sampling, cross-code or host-shape decision.
