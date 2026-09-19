# COSMOS-Web Gate D1n-i — residual / target-tangent result

## Immutable execution receipt

- workflow run: `34012104662`
- conclusion: `success`
- artifact id: `9982788083`
- artifact digest: `sha256:e808789e3ce05797a47cb0dd936168cba80a7aad8eb955dbec34d9cc92de9059`

This receipt is rendered directly from the immutable machine-readable `summary.json` produced by the successful D1n-i workflow. It records a diagnostic result, not a production acceptance criterion.

## Frozen semantics

- `acceptance_threshold_defined`: `False`
- `bounds_changed`: `False`
- `err_or_wht_modified`: `False`
- `new_noise_added`: `False`
- `optimizer_tolerance_changed`: `False`
- `planar_background_projected_out`: `True`
- `psf_sharpening_performed`: `False`
- `rank_deficiency_retained`: `True`
- `regularization_applied`: `False`
- `same_d1m_err_weighting`: `True`
- `same_d1m_exact_child_mask`: `True`
- `same_d1m_scene_decomposition`: `True`
- `same_d1m_stpsf`: `True`
- `source_shot_noise_added`: `False`
- `target_recovery_refit_performed`: `False`
- `tolman_factor_applied`: `False`

## Machine-readable scientific metrics

### catastrophic — near_source_2_5 index 0 at (168,66)

- valid fraction: `1`
- neighbour models: `1`
- weighted residual L2 before background removal: `69.5113271754`
- background-residualized residual L2: `69.5113271754`
- target-tangent projection L2: `9.69795430591`
- target-tangent power fraction: `0.019464762361`
- tangent rank: `7`
- tangent condition number: `296.262306819`
- singular values: `46.3226086698, 16.264632876, 11.6952948645, 5.8644736785, 4.4450168942, 4.1449065346, 0.156356740644`
- predicted first-order shift per alpha:
  - `dx`: `-0.0850579740756`
  - `dy`: `-0.345014157943`
  - `log_amp_ratio`: `0.594262342069`
  - `log_re`: `0.479857275437`
  - `n`: `0.722088357037`
  - `pa`: `-5.68137462271`
  - `q`: `-0.0554886220479`
- parameter cosine alignment:
  - `dx`: `-0.00381570291194`
  - `dy`: `-0.0238452289039`
  - `log_amp_ratio`: `0.107981354193`
  - `log_re`: `-0.0488778373756`
  - `n`: `-0.0444097897556`
  - `pa`: `-0.0109984368834`
  - `q`: `-0.0513340534026`
- D1n-h alpha=0→0.25 derivative cross-check:
  - `dx`: predicted `-0.0850579740756`, observed `-0.192265618767`, same_sign `True`, observed_minus_predicted `-0.107207644692`
  - `dy`: predicted `-0.345014157943`, observed `-0.315389401511`, same_sign `True`, observed_minus_predicted `0.0296247564318`
  - `log_amp_ratio`: predicted `0.594262342069`, observed `0.736899442935`, same_sign `True`, observed_minus_predicted `0.142637100866`
  - `log_re`: predicted `0.479857275437`, observed `0.63089380572`, same_sign `True`, observed_minus_predicted `0.151036530283`
  - `n`: predicted `0.722088357037`, observed `1.11759886184`, same_sign `True`, observed_minus_predicted `0.395510504802`
  - `pa`: predicted `-5.68137462271`, observed `1.67902860883`, same_sign `False`, observed_minus_predicted `7.36040323155`
  - `q`: predicted `-0.0554886220479`, observed `-0.0336677618912`, same_sign `True`, observed_minus_predicted `0.0218208601566`

### catastrophic — relatively_isolated_ge30 index 1 at (69,195)

- valid fraction: `1`
- neighbour models: `0`
- weighted residual L2 before background removal: `54.3066428828`
- background-residualized residual L2: `54.3066428828`
- target-tangent projection L2: `7.21768651054`
- target-tangent power fraction: `0.0176640431688`
- tangent rank: `7`
- tangent condition number: `291.614175943`
- singular values: `48.0740683637, 17.4348837641, 12.226357101, 6.18651462506, 4.60953159181, 4.35927727253, 0.164855045912`
- predicted first-order shift per alpha:
  - `dx`: `1.03122831804`
  - `dy`: `-0.0623607589418`
  - `log_amp_ratio`: `0.292333777319`
  - `log_re`: `0.321858271685`
  - `n`: `0.667948608745`
  - `pa`: `-11.8341081778`
  - `q`: `0.00820922158139`
- parameter cosine alignment:
  - `dx`: `0.097597831342`
  - `dy`: `-0.0306718363167`
  - `log_amp_ratio`: `0.00874590938233`
  - `log_re`: `0.0273407352414`
  - `n`: `0.00324114922289`
  - `pa`: `-0.0344198954304`
  - `q`: `0.0236560261446`
- D1n-h alpha=0→0.25 derivative cross-check:
  - `dx`: predicted `1.03122831804`, observed `1.06439429915`, same_sign `True`, observed_minus_predicted `0.0331659811034`
  - `dy`: predicted `-0.0623607589418`, observed `-0.0294779572652`, same_sign `True`, observed_minus_predicted `0.0328828016765`
  - `log_amp_ratio`: predicted `0.292333777319`, observed `0.371841201513`, same_sign `True`, observed_minus_predicted `0.0795074241946`
  - `log_re`: predicted `0.321858271685`, observed `0.381344557854`, same_sign `True`, observed_minus_predicted `0.059486286169`
  - `n`: predicted `0.667948608745`, observed `0.888767493432`, same_sign `True`, observed_minus_predicted `0.220818884687`
  - `pa`: predicted `-11.8341081778`, observed `-9.25547992622`, same_sign `True`, observed_minus_predicted `2.57862825161`
  - `q`: predicted `0.00820922158139`, observed `0.0357495541943`, same_sign `True`, observed_minus_predicted `0.0275403326129`

### control — near_source_2_5 index 1 at (379,254)

- valid fraction: `1`
- neighbour models: `1`
- weighted residual L2 before background removal: `52.3047823744`
- background-residualized residual L2: `52.3047823744`
- target-tangent projection L2: `4.61993468472`
- target-tangent power fraction: `0.0078016932837`
- tangent rank: `7`
- tangent condition number: `290.281727761`
- singular values: `46.6461898102, 16.9077552825, 12.0332484736, 5.96351243825, 4.48485643337, 4.27677703668, 0.160692821316`
- predicted first-order shift per alpha:
  - `dx`: `-0.0599827371568`
  - `dy`: `0.560806964365`
  - `log_amp_ratio`: `-0.0235351912278`
  - `log_re`: `-0.0070090426258`
  - `n`: `0.374913193809`
  - `pa`: `3.33321818611`
  - `q`: `0.059830462205`
- parameter cosine alignment:
  - `dx`: `-0.0203831101254`
  - `dy`: `0.0625008053999`
  - `log_amp_ratio`: `-0.0469746202041`
  - `log_re`: `0.0281954189801`
  - `n`: `0.0503680900415`
  - `pa`: `0.0105414426289`
  - `q`: `0.0355178977263`
- D1n-h alpha=0→0.25 derivative cross-check:
  - `dx`: predicted `-0.0599827371568`, observed `-0.0642375833782`, same_sign `True`, observed_minus_predicted `-0.00425484622136`
  - `dy`: predicted `0.560806964365`, observed `0.551429129819`, same_sign `True`, observed_minus_predicted `-0.00937783454606`
  - `log_amp_ratio`: predicted `-0.0235351912278`, observed `-0.0164848346593`, same_sign `True`, observed_minus_predicted `0.0070503565685`
  - `log_re`: predicted `-0.0070090426258`, observed `-0.00401284951073`, same_sign `True`, observed_minus_predicted `0.00299619311507`
  - `n`: predicted `0.374913193809`, observed `0.441437135844`, same_sign `True`, observed_minus_predicted `0.0665239420346`
  - `pa`: predicted `3.33321818611`, observed `2.65343672826`, same_sign `True`, observed_minus_predicted `-0.679781457844`
  - `q`: predicted `0.059830462205`, observed `0.0477248904327`, same_sign `True`, observed_minus_predicted `-0.0121055717723`

### control — relatively_isolated_ge30 index 0 at (358,97)

- valid fraction: `1`
- neighbour models: `0`
- weighted residual L2 before background removal: `53.6508853625`
- background-residualized residual L2: `53.6508853625`
- target-tangent projection L2: `3.06423136656`
- target-tangent power fraction: `0.00326204029376`
- tangent rank: `7`
- tangent condition number: `289.691494456`
- singular values: `47.5988929937, 17.2792256644, 12.2092098299, 6.09978559986, 4.59151354356, 4.33084657927, 0.164308907595`
- predicted first-order shift per alpha:
  - `dx`: `0.384779096395`
  - `dy`: `0.218316066467`
  - `log_amp_ratio`: `0.0430991892018`
  - `log_re`: `0.094780231464`
  - `n`: `0.146980096884`
  - `pa`: `-10.353668051`
  - `q`: `-0.0121275076863`
- parameter cosine alignment:
  - `dx`: `0.0301475051684`
  - `dy`: `0.0155030948438`
  - `log_amp_ratio`: `-0.0182747742616`
  - `log_re`: `0.0251705846101`
  - `n`: `0.00451843410131`
  - `pa`: `-0.0318550445183`
  - `q`: `0.0178135109726`
- D1n-h alpha=0→0.25 derivative cross-check:
  - `dx`: predicted `0.384779096395`, observed `0.40351099584`, same_sign `True`, observed_minus_predicted `0.0187318994445`
  - `dy`: predicted `0.218316066467`, observed `0.186126873966`, same_sign `True`, observed_minus_predicted `-0.0321891925014`
  - `log_amp_ratio`: predicted `0.0430991892018`, observed `0.0356962071432`, same_sign `True`, observed_minus_predicted `-0.00740298205854`
  - `log_re`: predicted `0.094780231464`, observed `0.0784067821543`, same_sign `True`, observed_minus_predicted `-0.0163734493097`
  - `n`: predicted `0.146980096884`, observed `0.141342317317`, same_sign `True`, observed_minus_predicted `-0.00563777956661`
  - `pa`: predicted `-10.353668051`, observed `-9.66814632309`, same_sign `True`, observed_minus_predicted `0.685521727887`
  - `q`: predicted `-0.0121275076863`, observed `-0.0175023334394`, same_sign `True`, observed_minus_predicted `-0.00537482575307`

## Interpretation guardrail

Preserve rank/conditioning, projection strength, sign disagreements, nonlinear departures, and control/failure overlap as results. Do not regularize the tangent, drop parameters, widen target bounds, alter ERR weighting, change optimizer requirements, or define a post-hoc morphology acceptance threshold from this diagnostic.
