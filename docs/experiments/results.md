# Results — experiment 001 (baseline)

> **Dataset: synthetic demo.** The labels are a heuristic function of electronegativity, which is also
> a feature. These numbers show the pipeline works; they are **not** evidence about real materials.

Held-out test set (471 compounds, grouped by chemical system), band gap in eV:

| Model | MAE | RMSE | R² |
| --- | --- | --- | --- |
| mean predictor | 1.270 | 1.582 | −0.009 |
| ridge | 0.337 | 0.418 | 0.930 |
| random forest | 0.202 | 0.293 | 0.965 |
| histogram gradient boosting | 0.187 | 0.267 | 0.971 |

Selected: histogram gradient boosting (lowest grouped-CV MAE, 0.193 vs 0.205 for the random forest). Uncertainty still comes from the random forest's tree spread, so the reported ± is the forest's, not the selected model's.

- Error is lowest for zero-gap compounds (MAE 0.07) and highest for gaps of 2 eV and above (MAE ≈ 0.30).
- 90% prediction intervals (binned cross-conformal): **91.9 %** empirical coverage on the held-out test set.
- RF tree-spread vs. |error| correlation on held-out data: 0.59 — informative but uncalibrated.
- Top features: `range_X`, `dev_X`, `range_ionization_energy` (expected given how labels were made).

Re-generate with `npm run ml:bootstrap`; rerun and rewrite this file for any real dataset.
