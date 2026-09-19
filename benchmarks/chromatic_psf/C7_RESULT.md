# C7 result receipt — source-SED / chromatic-PSF mismatch

**Workflow run:** `33920504456`  
**Conclusion:** `completed / success`  
**Artifact:** `chromatic-source-sed-mismatch-c7` (`9954837896`)

C7 isolates the operator-level error made when a spatial color-gradient source is replaced by a band-integrated intrinsic image convolved with one broadband PSF derived from the global source SED.

## Controls

Both predeclared algebra controls close at numerical precision:

- same-SED control normalized image L1 difference: `1.7705686643311242e-15`; second-moment relative difference: `9.505900778146412e-15`;
- achromatic-PSF control normalized image L1 difference: `2.2426364317139198e-15`; second-moment relative difference: `9.379627120939325e-15`.

Flux conservation is also numerical in all three cases (`~5–6e-16` relative error).

## Color-gradient result

For the frozen blue-extended + red-compact scene with wavelength-dependent PSF:

- blue-component effective PSF sigma: `2.108104648030845` px;
- red-component effective PSF sigma: `2.524521310138081` px;
- global-SED effective PSF sigma: `2.3568035288348685` px;
- normalized image L1 difference between the correct wavelength-resolved operator and the one-global-PSF shortcut: `0.047031413678326354`;
- central enclosed fraction at r=3 px: correct `0.27009325304762966`, shortcut `0.2891410747644992` (an absolute increase of `0.01904782171686954`, about 7.05% relative to the correct central fraction);
- enclosed fraction at r=10 px: correct `0.830934744425562`, shortcut `0.8287144928575497`;
- second-moment size relative difference: `4.0274652144176156e-15`.

The near-zero second-moment difference is not evidence that the shortcut is harmless: the exact global broadband PSF preserves this global second moment for the centered mixture, while the radial light distribution is measurably redistributed. Concentration-like/local morphology diagnostics therefore change even when total flux and this particular global size moment do not.

## Scientific decision

The project-level source-SED/chromatic-PSF mismatch requirement is now demonstrated with two closing controls. A single source-independent broadband PSF is not generally a valid replacement for wavelength-resolved PSF application when morphology and SED vary spatially.

No universal 4.7% image-difference or 7% concentration criterion is inferred from this synthetic scene. These numbers are stress-test outputs, not production acceptance bands.

With the PyAutoGalaxy/PyAutoArray morphology extension and this chromatic operator check complete, the next scientifically non-redundant priority is Gate D real-survey injection/recovery rather than adding redundant literature reproductions. Kawase remains a conditional method evaluation, not a blocker.
