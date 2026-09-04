# C6b result receipt — matched-PSF AstroPhot/Imfit common scene

**Workflow run:** `33886369577`  
**Conclusion:** `completed / success`  
**Artifact:** `dewsnap-astrophot-common-scene-c6b`, id `9942060811`  
**Scope:** noiseless matched-PSF n=1 common-scene cross-fitter diagnostic only.

All 12 AstroPhot attempts were finite and all four cases produced finite winners with no declared shape or point-flux boundary hits. The independent artifact audit passed. The AstroPhot PA convention that matches the archived C5o images is the 135-degree representation of the same physical axis; the alternative 45-degree rendering had a much larger truth-state SSE.

Winner comparison against the preserved Imfit C5o controls was extremely close. For module A the AstroPhot/Imfit SSE ratio was about `1.00535`; for module B it was `1.00000` and `0.99997`. Across the four winners, the cross-code differences were only about `1.3e-4` in Sersic n, `3.5e-4` in q, `8e-4` native pixel in Re, and at most a few `1e-5` in point-source flux. No morphology recovery band was applied or inferred from these numbers.

This closes the C6b matched-PSF baseline as an execution and numerical cross-code control. It does not prove general identifiability, survey realism, or photon-readiness. Because the clean baseline is interpretable, the next non-redundant test is C6c: exchange the two archived empirical PSF constructions at AGN/host=10 while keeping the common scene, starts, bounds, noise state, and software fixed. This isolates PSF-construction mismatch before any target noise is introduced.
