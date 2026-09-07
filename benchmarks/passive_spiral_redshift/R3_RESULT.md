# R3 multi-object curved-throughput real-context pilot result

Status: **LOCAL / ATTACHED-DATA RESULT**. This is not a GitHub Actions science execution and is not yet a final passive-spiral completeness measurement.

## Inputs and frozen boundaries
- User-supplied R3 archive SHA256: `73664dd17981dcdfdd42efc3441c358b95cef5d25e01f16970d1e2d81f5ea46e`.
- Archive contains 36/36 successful 30-mas COSMOS-Web SCI cutouts: 9 selected sources x F115W/F150W/F277W/F444W, all `BUNIT=MJy/sr`.
- Exact source redshifts and inherited visual labels are taken from the existing Step-8 visual-calibration table, not redefined after redshifting.
- ID 470340 is retained in the input manifest but is not run as a secure disk because its frozen visual label is `spheroid`; status `INELIGIBLE_VISUAL_CLASS`. No replacement source was selected after seeing this.
- The remaining 8 sources are eligible (`smooth_disk_S0` or `clear_spiral`).
- Real context remains the previously frozen ID 39749 A2 scene from `A2_sci_pilot2.tar.gz`, SHA256 `1830bf67f88c064565b18f8a450c0276117d1dfdf498c640dcc397c38664d1b1`, with pre-injection placements isolated=(80,80), intermediate=(110,215), near-source=(215,155).
- NIRCam throughput archive SHA256: `1aace14fbcfee640ba286102a97e1acfc80dd14796fa229aa33a479e89caceec`.

## Spectral / transfer method
R3 follows `R3_SED_METHOD_AMENDMENT.md`: PSF-homogenized F115W/F150W/F277W images constrain a quadratic per-pixel `F_nu(lambda)` model, and the mapped target filter is integrated through the full supplied NIRCam throughput. The historical R1 pivot-linear interpolation is not used for these new science renders. Downstream transfer retains one `I_nu` redshift factor, FlatLCDM H0=70/Om0=0.3 angular scaling, 30-mas grid, and degradation-only target PSF matching. No extra sky noise or source-shot realization is added.

The source-moment system condition number is 141.17. Curved-SED weights are preserved even when negative; across supported cells `sum(abs(weights))` ranges 1.005--2.436.

## Execution coverage
- 8 eligible sources x 5 target redshifts = 40 requested source/target cells.
- 39 cells are spectrally supported and rendered.
- ID 449902 at z_target=2.0 is preserved as `SPECTRAL_SUPPORT_FAIL` because the mapped target pivot is 2.9264 micron, above the F277W source pivot support boundary; no extrapolation/fallback was used.
- Each of the 39 supported cells was measured source-only and in the three frozen real-context placements, giving 156 `OK` metric rows plus the two retained input/support failures.

## Main population result
The real-scene effect grows strongly with redshift and crowding, while there is substantial object-to-object diversity.

### Isolated context
Median |delta q| rises from 0.009 at z=1 to 0.055 at z=3. Median recovered/source flux falls from 0.996 at z=1 to 0.863 at z=3; the z=3 range is 0.639--0.968. Median |delta concentration| is 0.002 at z=1 and 0.071 at z=3.

### Intermediate context
Median |delta q| is 0.007 at z=1, 0.072 at z=2, and 0.034 at z=3, with a maximum |delta q| of 0.268. Median flux ratio rises from 1.006 at z=1 to 1.123 at z=3, and median |delta concentration| rises from 0.004 to 0.131.

### Near-source context
Contamination dominates. Median |delta q| rises from 0.094 at z=1 to 0.168 at z=3. Median flux ratio rises from 1.527 to 3.967, with individual z=3 values reaching 7.539. Median |delta concentration| rises from 0.225 to 0.453, and centroid offsets reach 0.605 arcsec.

## Object diversity
The multi-object run shows that a single bright anchor is not representative. In the isolated scene, some sources remain very stable while others show much larger q bias: median |delta q| across redshift is about 0.003 for ID 564924 and 0.006 for ID 449902, but about 0.161 for ID 685484 and 0.178 for ID 316667. The faint ID 756543 also loses more flux in the isolated scene (median flux ratio about 0.810) than the bright anchor ID 57977 (about 0.971). This supports carrying source brightness/size/morphology covariates into the later recovery/completeness surface.

## Interpretation / decision
R3 confirms the paper-facing premise that recovery bias depends jointly on source properties, redshift, and scene context. It also confirms that the final completeness correction cannot be calibrated from ID 57977 alone.

This is still descriptive recovery, not a spiral completeness fraction. The next scientific gate is to freeze the actual passive-spiral morphology/classification decision rule independently of these R3 outcomes, then apply that rule to the redshifted images to compute a recovery/completeness surface versus redshift, S/N/brightness, size/resolvedness and crowding. No new q, concentration, B/T or Sersic-n threshold is introduced here.
