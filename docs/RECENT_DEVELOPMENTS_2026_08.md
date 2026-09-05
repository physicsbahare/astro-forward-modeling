# Verification-relevant developments — August/September 2026

This note records developments that materially affect the verification roadmap. It is not a production dependency list and not a paper-reproduction checklist. New external packages or methods enter only when they provide a distinct independently reviewable operator, failure mode, cross-code reference, or survey-reality test.

## PyAutoGalaxy / PyAutoArray

PyAutoGalaxy v2026.8.29.1 introduced relevant maintained PSF-convolution/MGE and upstream numerical changes. The verification action remains a pinned morphology cross-code benchmark before Gate F: identical analytic scenes, exact versions, and comparisons of flux, centroid, second moments, profile shape, and recovered structural parameters. It is an independent reference, not ground truth and not automatically a production dependency.

## AGN-host PSF mismatch and decomposition

The Zhuang & Shen line is now closed as a controlled synthetic-equivalent scope. The final wrong-PSF free-shape diagnostic, C5r (`33842347328`), completed as a workflow but failed scientifically as a morphology-recovery condition: every selected wrong-PSF solution hit a bound and half of the starts timed out. Noise is therefore not layered onto that already-failed noiseless condition.

Dewsnap, Barmby & Gallagher motivate the current independent-fitter branch: acceptable residuals/fit quality need not imply unique or trustworthy host morphology. C6a has now completed successfully (`33849387267`) as an AstroPhot 0.18.0 signed-PSF installation/convention preflight. It verified signed samples, normalization, public orientation, and the package's internal transpose/convolution convention, but it did not fit a Sérsic host and therefore is not a morphology-validation pass.

The immediate next experiment is C6b: a matched-PSF, noiseless, common-scene AstroPhot-versus-Imfit comparison using the already-clean C5o `n=1` control as the common input/reference. Only after that baseline is understood should independent PSF constructions be compared.

Kawase, Shibuya & Matsuda (2026) remain scientifically interesting because the smooth-host + sparse-point-source decomposition and point-source-balance constraint are methodologically distinct. The roadmap no longer assumes that the paper must be reproduced in detail. A minimal controlled test should first determine whether that idea adds a useful recovery capability or diagnostic beyond the existing Sérsic+PSF suite; only then should it influence production design.

## Chromatic / SED-dependent PSFs

SED-dependent broadband PSFs remain a required operator-level capability. The existing chromatic non-commutativity tests are not sufficient on their own because production must also demonstrate the consequence of using the wrong source SED/one generic broadband PSF for a color-gradient source. This stress test remains mandatory before Gate F.

## ScopeSim

ScopeSim remains a design/cross-validation reference for Gate F's source -> optical train -> detector abstraction. Architectural similarity alone is not a reason to add it as a production dependency.

## Current priority

1. Complete Dewsnap C6b common-scene cross-fitter baseline, then C6c PSF-construction comparison if the baseline is interpretable.
2. Run the minimal PyAutoGalaxy/PyAutoArray morphology cross-code extension before architecture freeze.
3. Perform the source-SED/chromatic-PSF mismatch test.
4. Evaluate the distinct Kawase point-source-balance method only to the depth needed to decide whether it adds unique production value.
5. Move to Gate D real-survey injection as soon as the remaining non-redundant synthetic checks are closed. Gate D is the decisive bridge from controlled verification to actual COSMOS-Web/survey recovery behavior.

The earlier statement that Yu et al. (2023) was the immediate Gate-C target is obsolete; Yu has been reviewed as **PASS WITH EXPLAINED DIFFERENCE** and is no longer active work.
