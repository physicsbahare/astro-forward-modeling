# COSMOS-Web Gate D1n-g — multistart identifiability result

## Immutable execution receipt

Workflow: `gate-d-cosmosweb-multistart-identifiability`

Confirmed GitHub Actions run: `34007478747`

- status: `completed`
- conclusion: `success`
- head SHA: `85b034a8426a2c40df96ee44cd752c1b9b2598e9`
- artifact: `gate-d-cosmosweb-multistart-identifiability`
- artifact id: `9981423685`
- artifact SHA256: `0a651f4c2ca39e59d118d01fcc0a2af3322c914fba919953d11660697ea332d5`

The dedicated tests, exact pinned STPSF-data download, frozen D1d artifact download, multistart audit and artifact upload all completed successfully. This receipt records execution provenance and the machine-readable scientific result; workflow success is not morphology success.

## Machine-readable scientific result

All 20 fits (four frozen AB=26 locations x five frozen deterministic starts) returned finite optimizer-successful solutions. No target bound hit occurred.

For the two catastrophic D1m locations, all five starts — including the exact injection-truth oracle — converge to the same catastrophic family:

- near-source index 0 `(168,66)`: best chi-square `4708.254559`; across starts delta-mag is approximately `-1.1116 .. -1.1119`, recovered Re is `0.5095 .. 0.5098 arcsec`, n is `2.3138 .. 2.3151`, and centroid excursion is about `0.4845 pix`. The truth-oracle start gives delta-mag `-1.11187` and Re `0.50978 arcsec`.
- relatively-isolated index 1 `(69,195)`: best chi-square `2879.022608`; across starts delta-mag is approximately `-1.0102 .. -1.0113`, recovered Re is `0.5996 .. 0.6000 arcsec`, n is `3.1050 .. 3.1077`, and centroid excursion is about `1.173 pix`. The truth-oracle start also returns the same failure family.

Raw objective differences between starts are tiny compared with the total chi-square: the near-source case spans only about `1.6e-5` in chi-square and the isolated case about `2.2e-3`. Thus the catastrophic morphology is not rescued by a truth-like initialization.

The two controls are likewise stable across starts and remain near their original D1m solutions. This argues against a general multistart instability.

## Scientific interpretation

D1n-g rejects the simple local-basin explanation for the two catastrophic AB=26 D1m rows. The unchanged real-scene D1m objective itself drives even the injection-truth start toward the same wrong morphology. Therefore adding random restarts, widening target bounds, increasing the iteration budget, or promoting the injection-truth start to a measurement rule is not scientifically justified.

Together with earlier diagnostics:

- D1n-c found no single audited background/residual summary statistic that explains both failures;
- D1n-f showed that the measured published-vs-STPSF mismatch alone produces only small paired-difference biases;
- D1n-g now shows that initialization is not the primary failure.

The next smallest causal diagnostic is to scale only the already-present pre-injection scene-model residual while leaving the injected source, frozen neighbour model, ERR weighting, STPSF, target objective, bounds and optimizer unchanged. This can test whether the real-scene residual itself continuously drives the catastrophic solution.

No production framework implementation is authorized by this result.
