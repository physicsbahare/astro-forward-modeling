# R2 preliminary real-context stress protocol

Status: **LOCAL/ATTACHED-DATA PROTOCOL FROZEN BEFORE INJECTION; NOT A GITHUB/CI SCIENCE RUN**

Purpose: obtain a small real-survey-context stress result using only the already supplied, checksummed A2 SCI cutouts. This is descriptive and is **not** the final completeness measurement.

Source: COSMOS2025 ID 57977; use frozen R1 renders at z=1,1.5,2,2.5,3 and target pivot bands F277W,F277W,F444W,F444W,F444W.

Real context: literal 39749 A2 SCI cutout in the matching target band. Do not add sky/background noise. No ERR/WHT modification. No source-shot-noise realization.

Placements are fixed from the **pre-injection** 39749 F444W scene on the previously inspected grid: `isolated=(80,80)`, `intermediate=(110,215)`, `near-source=(215,155)` pixels. The same placements are used in F277W and F444W. Here `isolated` explicitly means a deliberately nearly empty real-sky patch; it is the low-crowding control, not a location expected to contain a visible source.

Measurement (descriptive, no acceptance threshold):
- local scalar background = median in 1.2-1.5 arcsec annulus;
- measurement aperture r<=1.0 arcsec;
- q from positive-residual second moments;
- concentration = positive residual flux r<=0.3 arcsec / r<=1.0 arcsec;
- signed aperture-flux recovery ratio;
- centroid offset from known injection center.

No disk/spiral pass-fail threshold is introduced. Crowding failures are retained.
