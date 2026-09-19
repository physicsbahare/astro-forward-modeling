# COSMOS-Web Gate D1n-c — background / residual-context audit result

## Immutable execution receipt

Workflow: `gate-d-cosmosweb-background-residual-audit`

Confirmed GitHub Actions run: `33990384369`

- status: `completed`
- conclusion: `success`
- head SHA: `db90b9b2703d2dce20c7cbc17ae11722cce85bf3`
- artifact: `gate-d-cosmosweb-background-residual-audit`
- artifact id: `9976474474`
- artifact SHA256: `2ea071f2debfbc979f44dbe30e3cfdb50fe85310026be3774d3ac6b4011851c0`

The artifact `summary.json` was inspected directly. All nine frozen AB=26 locations are retained; no target was refitted and no post-hoc scientific acceptance cut was introduced.

## Machine-readable result

The two largest absolute D1m magnitude errors remain:

1. near-source index 0 at (168,66): delta-mag = -1.11193, Re ratio = 2.832, centroid excursion = 0.485 pix;
2. relatively-isolated index 1 at (69,195): delta-mag = -1.01134, Re ratio = 3.331, centroid excursion = 1.173 pix.

The first failure does occur in a somewhat more structured patch than the cleanest controls: standardized residual std = 1.069, low-frequency variance fraction = 0.1008, quadratic variance-explained fraction = 0.0246, ERR coefficient of variation = 0.1106.

The second catastrophic failure, however, occurs in an otherwise ordinary residual context: standardized residual std = 0.835, low-frequency variance fraction = 0.0683, quadratic variance-explained fraction = 0.0174, ERR coefficient of variation = 0.0284. Several accurately recovered controls have comparable residual correlation and low-frequency fractions. Conversely, intermediate index 2 has the most conspicuous residual/coverage pathology (standardized std = 1.980, low-frequency fraction = 0.1053, ERR coefficient of variation = 0.273) but its morphology error, while substantial, is not one of the two catastrophic bright/large interior solutions.

## Scientific interpretation

Background/coverage/residual structure can worsen individual locations, but D1n-c does not support it as a sufficient general explanation for the remaining D1m catastrophic interior failures. In particular, the isolated catastrophic solution survives in a patch whose residual statistics are close to normal for this nine-location sample.

This shifts the next diagnostic away from further background-plane or segmentation tuning. The remaining plausible family includes PSF/effective-PSF mismatch, compact unmodelled scene structure, and intrinsic morphology identifiability/path dependence. D1n-b independently shows that the compact-source population in the real mosaic is broader and more heterogeneous than the declared single ideal STPSF, but that population is not yet stellar-vetted.

No low-S/N/bad recovery is discarded; no bound, optimizer setting, segmentation setting, ERR/WHT plane, noise model, Tolman factor, or PSF kernel is changed.
