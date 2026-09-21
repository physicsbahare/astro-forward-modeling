# Portable JWST artificial-redshifting method and limitations

## Method

The notebook uses a native observed source (or a user-supplied parametric
model), obtains a native-clean model through Galight recovery, renders that
structure with Lenstronomy at the target redshift, and recovers both a clean
target model and an injected target-real model. Angular sizes scale with
angular-diameter distance. At matched rest frequency, the Fnu factor is

`((1 + z_target) / (1 + z_source)) * (D_L(source) / D_L(target))^2`.

SED/filter interpolation and luminosity evolution are recorded separately.
The notebook requires bracketing photometry or an SED if source and target
filters do not sample the same rest wavelength.

## Noise

The default real-mosaic experiment is deterministic source addition into an
already observed target SCI image. It retains the existing sky, detector/read,
and drizzle-correlated noise and intentionally does not add another realization
of them. The original target ERR remains the uncertainty map in this default.

An injected source has photon variance in detector counts, but a final drizzled
mosaic plus a scalar exposure/header quantity generally cannot reconstruct its
exact covariance. Therefore source-Poisson mode requires a validated
data-unit-to-count-rate conversion and effective exposure metadata. The
notebook never manufactures Poisson noise from MJy/sr. Its mosaic-level
source-Poisson result must be labeled an approximation unless an exposure-level
forward model is used.

The blank-sky patch diagnostic quantifies empirical RMS / ERR mismatch caused
by correlated noise or map semantics. It warns by default; users may explicitly
request an ERR scaling only after documenting why a scalar adjustment is valid.

For users without a real background, `SYNTHETIC_BACKGROUND` accepts only an
explicit Gaussian model with shape, pixel scale, background mean/RMS, and RNG
seed. It draws that background exactly once before source injection, gives it a
matching ERR map, and labels it uncorrelated synthetic noise. It cannot model
drizzle covariance, detector artifacts, or real crowding without a more
specific user-supplied forward model.

## Structural interpretation

Published/native, native-clean, target-clean, and target-real are distinct
stages. Target-clean is the resolution/redshift baseline. Target-real adds
observational context. Compact B+D components, optimizer alternatives, or
bound hits can make B/T non-identifiable; warning flags are diagnostics, not a
universal threshold. Signed PSF wings are preserved, not clipped.

## Scope boundaries

The notebook does not assume COSMOS-Web PSFEx, a specific JWST release,
F444W, z=3, 0.03 arcsec/pixel, a GOLD403 catalog, or any private path. Its
simple public fit masks segmented neighbours; crowded scenes needing explicit
neighbour models require field-specific validation before physical claims.
