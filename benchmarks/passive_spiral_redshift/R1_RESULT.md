# Passive-disk R1 — real COSMOS-Web transfer-only pilot result

Status: **ATTACHED-DATA / LOCAL RESULT — NOT GITHUB ACTIONS**

This immutable receipt records the first real-galaxy transfer-only execution of the frozen `R1_PROTOCOL.md` using the checksummed A2 SCI cutouts supplied in the conversation. The calculation was performed after the protocol was frozen at commit `38bdad7b8b19b46bde7695893f3afffcccda2ff6`. It is not a completeness measurement and must not be represented as a CI science run.

## Results

| z | band | lambda_source [um] | t | angular scale | I_nu factor | source-equivalent PSF [arcsec] | added kernel [arcsec] | q proxy | RMS size [arcsec] | concentration | flux-scaling residual |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.0 | F277W | 1.985395 | 0.379918 | 0.700882 | 0.365833 | 0.064481 | 0.065622 | 0.570270 | 0.368501 | 0.645038 | +1.985e-4 |
| 1.5 | F277W | 1.588316 | 0.068483 | 0.663288 | 0.187306 | 0.061022 | 0.068850 | 0.573539 | 0.352669 | 0.654822 | +8.58e-6 |
| 2.0 | F444W | 2.098874 | 0.468920 | 0.670556 | 0.108395 | 0.061691 | 0.131222 | 0.584541 | 0.358600 | 0.650005 | -3.157e-4 |
| 2.5 | F444W | 1.799035 | 0.233753 | 0.695368 | 0.068260 | 0.063974 | 0.130124 | 0.583829 | 0.373341 | 0.634514 | +2.522e-4 |
| 3.0 | F444W | 1.574155 | 0.057377 | 0.728668 | 0.045729 | 0.067037 | 0.128573 | 0.582897 | 0.392354 | 0.617191 | +4.633e-4 |

All five cases remain inside the F150W--F277W source spectral support and all five admit a degradation-only PSF kernel. Centroid offsets relative to the catalog-centered transform origin are about `0.0023--0.0036 arcsec`. The global second-moment shape stays elongated through `z=3` in this noiseless transfer-only test. Absolute signed-flux scaling residuals remain below `5e-4`.

## Scientific interpretation

R1 demonstrates that the verified artificial-redshifting operator can be connected coherently to one literal COSMOS-Web disk-like source across the paper's development redshift range without spectral extrapolation, PSF sharpening, or duplicated cosmological dimming. For this object, the transfer operator alone does not erase the global disk-like elongation by `z=3`.

This does **not** establish a passive-spiral recovery fraction. It isolates transfer from survey context. R2 adds real-scene context, and the later paper-facing step must increase the number of input disks and contexts before any completeness fraction is quoted.
