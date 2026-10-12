# Passive disks: joint observed mass–redshift demographics



## Sample and scope
The frozen native sample contains 36,905 eligible galaxies, 25,642 with paired-band measurable morphology, and403 passive disks. All36 published marginal rows reconcile exactly. These are observed conditional fractions, not intrinsic population estimates. Quiescent non-disks are galaxies failing the conjunction of the fixed disk cuts; they are not necessarily pure bulges.

## A. Redshift at fixed mass

For the common mass10–11 range, the fixed-reference passive-disk fraction changes from 2.55% (95% [1.59%, 3.60%]) at0<z<0.5 to 1.33% ([0.55%, 2.28%]) at2.5<z<3. The difference is -1.22 percentage points (95% -2.54, 0.12). This controls coarse mass mix only within the stated support.

The original all-mass marginal endpoints are 4.04% and 0.45%; direct attenuation comparisons also change mass coverage, so they are not a pure adjustment effect.

The redshift-slope sensitivity within exactly10–11 gives odds ratio 0.725 per unit z (tile-cluster95% 0.568–0.924, nominal p=0.009464). It favors a negative average slope, but the six-bin trend is non-monotonic and the endpoint-difference interval includes zero. Thus the data support a weaker conditional average decline, not a demonstrated decline in every mass/redshift interval. This secondary model is not independently multiplicity-adjusted.

## B. Mass at fixed redshift
Across supported passive cells, the disk odds ratio per dex mass is 0.112 (tile-cluster95% 0.081–0.154, Holm p=7.46e-40). Lower-mass passive galaxies are more likely to satisfy the fixed disk rule within the observed measurable sample.
The supported-cell logistic results below summarize the continuous mass slope with redshift-bin intercepts. Odds ratios are per dex mass or per unit redshift. Tile-cluster uncertainties address within-tile dependence approximately (20tiles), not full cosmic variance. Models assume one common linear log-odds slope; cell figures and coarse-bin sensitivities must be read alongside them.

```
variant                test   covariance     N  N_events  N_tiles      beta  odds_ratio  ci95_low  ci95_high        pvalue  converged                                    model  primary_Holm_p
primary       A_PD_redshift     binomial 25574       402       20 -1.045941    0.351361  0.293770   0.420243  2.313473e-30       True audit_passive_disk ~ z + categorical(mb)             NaN
primary       A_PD_redshift tile_cluster 25574       402       20 -1.045941    0.351361  0.287501   0.429405  1.612613e-24       True audit_passive_disk ~ z + categorical(mb)    3.225226e-24
primary B_disk_passive_mass     binomial  4001       400       20 -2.192552    0.111631  0.084830   0.146901  3.227464e-55       True      audit_disk ~ logM + categorical(zb)             NaN
primary B_disk_passive_mass tile_cluster  4001       400       20 -2.192552    0.111631  0.080799   0.154229  2.485474e-40       True      audit_disk ~ logM + categorical(zb)    7.456421e-40
primary  C_passive_redshift     binomial 25574      4022       20 -0.936861    0.391856  0.367974   0.417288 1.899288e-187       True      audit_passive ~ z + categorical(mb)             NaN
primary  C_passive_redshift tile_cluster 25574      4022       20 -0.936861    0.391856  0.352186   0.435994  2.496608e-66       True      audit_passive ~ z + categorical(mb)    9.986431e-66
```

## C. Decomposition

The standardized passive fraction decreases from 38.48% to 14.37%, while effective disk/passive changes from 6.62% to 9.24%. The point decomposition attributes the decline to the passive fraction, partly offset by a rising disk/passive factor. The latter contribution is uncertain and consistent with either sign; the net endpoint decline is also uncertain. Contribution shares can exceed100% when factors oppose and become unstable if the total change approaches zero.

Within the standardized reference, PD/all = P/all × effective D/P holds exactly. Effective D/P is the ratio of standardized PD/all to standardized P/all; it is not an independently mass-weighted passive disk fraction. Symmetric additive endpoint contributions (fractions, not percentage points) are:

```
                       component    change  ci95_low  ci95_high  share_of_total_change                      comparison
                 total_pd_change -0.012176 -0.025389   0.001172               1.000000 z0–0.5 to2.5–3; fixed mass10–11
   passive_fraction_contribution -0.019117 -0.028224  -0.011434               1.570064 z0–0.5 to2.5–3; fixed mass10–11
disk_within_passive_contribution  0.006941 -0.009103   0.024981              -0.570064 z0–0.5 to2.5–3; fixed mass10–11
```

These contributions describe the observed joint counts. They do not identify quenching mechanisms, transformations of individual galaxies or evolutionary progenitors.

## D. Matched SFR–mass comparison

All403 disks have unique within-caliper controls. The paired mean disk-minus-nondisk ΔMS is 0.242dex (95% -0.072–0.551; permutation p=0.131). The matched median contrast is 0.095dex (95% -0.185–0.433). No statistically distinguishable contrast is established; non-detection does not prove identical populations.

One-to-one optimal matching without replacement uses0.1dex mass and0.1redshift calipers. Positive disk-minus-nondisk contrasts mean less suppressed catalog-model SFR for passive disks. Bootstrap resamples complete pairs; sign-flip p values assume paired exchangeability. Matching does not balance dust, environment, SED priors or residual within-caliper covariates. Conditioning on the same passive threshold truncates both distributions.

```
                  variant  N_pairs  N_unmatched_disk  mean_delta_difference  mean_ci95_low  mean_ci95_high  median_disk  median_nondisk  median_difference  median_ci95_low  median_ci95_high  permutation_p  median_logSFR_difference  speagle_mean_difference  mean_mass_imbalance  mean_z_imbalance  mass_SMD     z_SMD  max_abs_mass_difference  max_abs_z_difference  primary_Holm_p
                all_pairs      403                 0               0.242352      -0.071639        0.551152    -2.649067       -2.744016           0.094948        -0.184538          0.432647       0.130743                   0.02087                 0.240093            -0.001455         -0.000112 -0.003094 -0.000199                  0.07411                0.0787        0.130743
exclude_model_floor_pairs      353                50               0.205652      -0.103756        0.499907    -2.554598       -2.631164           0.076566        -0.199626          0.421560       0.181791                   0.00000                 0.203165            -0.001730         -0.000315 -0.003613 -0.000564                  0.07411                0.0787             NaN
```

The excluded-floor variant is a sensitivity only, not a censored-data estimator. There are no trustworthy observational SFR upper-limit flags in these inputs. Model-floor precision and posterior uncertainty are not calibrated direct-SFR constraints. Neither median differences nor significance measures quenching timescales.

## Mass completeness and eligibility

The previously verified faintest30% /95th-percentile mass-to-light diagnostic uses F444W27.5 and separate NUVrJ populations, with relative WHT quartiles. Its upper confidence envelope remains below9.5. This is consistent with the chosen mass floor under that conditional diagnostic; it cannot prove mass/detection completeness. The magnitude benchmark is approximately80% detection in the published selection, which differs from this inherited sample. No inverse completeness weights are used.

Source methods: [COSMOS-Web mass-function analysis](https://arxiv.org/html/2511.05259v1#S2); [COSMOS2025 release](https://cosmos2025.iap.fr/catalog.html).

```
 z_low  z_high  max_quiescent_ML_ci95_across_depth  parent_mass_floor  parent_floor_above_conditional_boundary  N_eligible  N_fainter_than_benchmark  N_nonpositive_or_missing_WHT  morphology_unknown_fraction  passive_morphology_eligibility  nonpassive_morphology_eligibility  validated_mass_completeness  correction_applied
   0.0     0.5                            7.506550                9.5                                     True        2131                         0                             0                     0.163304                        0.809524                           0.850388                        False               False
   0.5     1.0                            7.688974                9.5                                     True        9825                         0                             0                     0.236743                        0.758432                           0.764644                        False               False
   1.0     1.5                            7.917051                9.5                                     True        7958                         0                             1                     0.292913                        0.729688                           0.702755                        False               False
   1.5     2.0                            8.081344                9.5                                     True        7911                         0                             0                     0.397421                        0.675904                           0.593984                        False               False
   2.0     2.5                            8.337100                9.5                                     True        5603                         0                             0                     0.332143                        0.774704                           0.662804                        False               False
   2.5     3.0                            8.665302                9.5                                     True        3477                         0                             0                     0.360368                        0.735484                           0.635160                        False               False
```

Detection completeness, M/L boundaries, morphology eligibility and classification accuracy are separate quantities. Passive and nonpassive eligibility differ substantially. Missing-label bounds in the joint table are conditional on detected eligible sources and correct measured labels, not bounds on the full population.

## Robustness and uncertainties

Primary bin edges are inherited; deterministic coarser bins, support thresholds10/20/50, bright-F444W, relative-depth and narrow-photoz subsets are secondary sensitivity tests. Primary logistic and paired-SFR questions use a Holm family of four. Cell Wilson intervals are pointwise, not simultaneous; many correlated cell comparisons should not be independently claimed as discoveries. Multinomial standardization uncertainty conditions on fixed reference weights and observed labels.

Independent Gaussian perturbations inferred from mass/photoz68% half-widths produce the following standardization migration diagnostic:

```
 z_low   median     p025     p975                                                                                                 scope
   0.0 0.025584 0.022498 0.029159 independent interval Gaussian bin migration; fixed labels/reference weights; not calibrated posterior
   0.5 0.015367 0.014290 0.016701 independent interval Gaussian bin migration; fixed labels/reference weights; not calibrated posterior
   1.0 0.014941 0.013670 0.016021 independent interval Gaussian bin migration; fixed labels/reference weights; not calibrated posterior
   1.5 0.015235 0.013779 0.016589 independent interval Gaussian bin migration; fixed labels/reference weights; not calibrated posterior
   2.0 0.010377 0.008137 0.012410 independent interval Gaussian bin migration; fixed labels/reference weights; not calibrated posterior
   2.5 0.010661 0.007989 0.013818 independent interval Gaussian bin migration; fixed labels/reference weights; not calibrated posterior
```

This freezes passive/morphology labels and band choices, ignores covariance and multimodal posteriors, and retains invalid-interval objects unperturbed. It is not a complete uncertainty propagation. Large redshift uncertainties can migrate sources across empirical-MS and morphology-band boundaries; those label changes remain uncalibrated.

## Figure captions and interpretation

1. `figure1_passive_disk_mass_redshift`: PD/all across original cells. Counts and pointwise Wilson95% intervals show support; hatching marks small denominators/events. Demonstrates conditional distribution, not intrinsic abundance.

2. `figure2_disk_among_passive_mass_redshift`: disk/passive with the same bins. Demonstrates morphology fractions within measured passive galaxies, not calibrated disk survival.

3. `figure3_redshift_at_fixed_mass`: PD/all in fixed coarse mass intervals. Demonstrates whether marginal decline survives stratification; residual selection remains.

4. `figure4_mass_at_fixed_redshift`: disk/passive within each redshift interval. Demonstrates observed mass dependence, not bulge growth histories.

5. `figure5_mass_standardized_redshift`: original marginal and fixed10–11mass reference. Demonstrates distribution adjustment and factorization; comparison also changes support and supplies no intrinsic correction.

6. `figure6_matched_SFR_mass_offsets`: identical matched groups shown in SFR–mass, cumulativeΔMS and paired differences. Demonstrates catalog-model distribution contrast, not quenching timescales.

## Defensible preliminary claims
Reproducible observed joint fractions, coarse-mass-controlled trends and matched SED-model contrasts can enter a preliminary draft with explicit eligibility and uncertainty scope. Intrinsic disk abundance, quenching rates, causal pathways and physical SFR-floor interpretation require independent completeness, class-confusion, SED/censoring and correlated redshift/mass calibrations. Historical403 artificial-redshifting fits are not used here.
