# GOLD403 -> z=3 model-only batch

This branch adds `scripts/run_gold403_z3_model.py` for the current 403-object passive-disk GOLD catalog.

## Scope

- Target redshift: `z=3.0`
- Target band: `F444W`
- Pixel scale: `0.03 arcsec/pix`
- Target PSF FWHM: `0.145 arcsec`
- No COSMOS-Web mosaics, backgrounds, neighbors, or noise yet.
- Uses the measured single-Sersic `Re`, `n`, and `q` in the available morphology band nearest the source wavelength corresponding to target F444W at z=3.
- Uses the verified angular rescaling, I_nu dimming, and Gaussian degradation primitives from `verification.passive_disk_real_pilot`.
- Preserves the full input catalog in the output table so later analyses can use stellar mass, SFR, B/T, visual flags, and transformed structural quantities together.

## Run

```bash
python scripts/run_gold403_z3_model.py \
  --catalog /path/to/passive_disk_GOLD403_with_visual_flags.csv \
  --output /path/to/GOLD403_z3_model_only
```

The unpublished 403-row science catalog is intentionally not committed to this public repository.

## Outputs

- `GOLD403_z3_transform_metrics.csv`: compact transformation metadata.
- `GOLD403_z3_catalog_with_properties.csv`: original science catalog plus the z=3 transformation columns, suitable for mass-z / size-z / B/T / visual-flag analyses.
- `GOLD403_z3_model_images.npz`: all 403 model-only redshifted images in catalog row order.
- `GOLD403_z3_run_summary.json`: counts and run configuration.

These products are pre-mosaic structural forward models. They must not be interpreted as realistic completeness/detectability simulations until the real-image/noise stage is added.
