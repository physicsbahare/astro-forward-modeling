# B9b result receipt — PyAutoGalaxy/PyAutoArray morphology recovery

**Workflow run:** `33915231971`  
**Conclusion:** `completed / success`  
**Artifact:** `pyautogalaxy-morphology-recovery-b9b` (`9953002625`)

This closes the pinned PyAutoGalaxy/PyAutoArray morphology extension as a verification reference, not as ground truth or a production dependency.

Across the two noiseless common scenes (`n=1` and `n=4`) and three deterministic starts per renderer, all 12 fits were finite and no selected winner hit a bound. The same `scipy.optimize.least_squares` objective and bounds were used for the independent renderer and PyAutoGalaxy renderer. The objective excluded the known four-pixel PSF-edge region while full-frame residuals were retained.

For `n=1`, the PyAutoGalaxy-minus-independent winner differences were: `Δcx=-5.55e-17`, `Δcy=+5.55e-17`, `Δn=0`, `Δq=0`, `ΔRe=1.985997e-4` pixel, and `ΔIe=-1.249921e-6`. For `n=4`: `Δcx=-3.33e-16`, `Δcy=-2.22e-16`, `Δn=0`, `Δq=0`, `ΔRe=2.262203e-6` pixel, and `ΔIe=-1.626506e-8`.

The interior objectives reached numerical-zero residuals for both implementations. The larger full-frame discrepancy for the PyAutoGalaxy `n=4` rendering (`SSE≈1.012e-5`) is confined to the already identified convolution-edge convention and is not evidence of morphology disagreement in the fitted region.

## Scientific decision

The maintained PyAutoGalaxy/PyAutoArray implementation agrees with the independent Sérsic morphology geometry and recovery at the controlled anchors. Gate B therefore has no remaining morphology-extension blocker. No universal morphology tolerance is inferred from this synthetic control.

The next non-redundant required check is the explicit source-SED / chromatic-PSF mismatch stress test: quantify the failure of a single source-independent broadband PSF for a spatial color-gradient source before moving to real-survey injection.
