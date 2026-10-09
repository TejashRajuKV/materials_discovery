# Results: experiment 001 (baseline), JARVIS dft_3d

Run `20261009-092936`, trained on 65,319 formulas (52,077 train / 13,242 test). Split: grouped by
chemical system, so no element set appears in both train and test. Gaps in eV, OptB88vdW.

## Held-out test set

| Model | MAE | RMSE | R² |
| --- | --- | --- | --- |
| mean predictor | 0.797 | 1.210 | −0.000 |
| ridge | 0.624 | 0.949 | 0.384 |
| **random forest** (selected) | **0.284** | **0.602** | **0.752** |
| gradient boosting | 0.413 | 0.751 | 0.614 |

Selection uses grouped 5-fold CV MAE on the training split. The random forest had the lowest CV MAE
(0.300 eV), ahead of gradient boosting (0.415 eV) and ridge (0.630 eV).

## Findings

- Error grows with the gap: 0.15 eV on metals, 1.29 eV above 4 eV. See `dataset-analysis.md`.
- Forest tree-spread predicts absolute error well on held-out data (correlation 0.80). The thresholds
  it produces give the high/medium/low confidence labels used in the UI. These are relative signals,
  not calibrated intervals.
- Most important features: mean ionization energy, minimum molar volume, maximum Mendeleev number,
  mean melting point, deviation of group number.

## Caveats

- Metrics are against DFT labels. They say nothing yet about experimentally measured gaps.
- The random forest bundle is 1.14 GB (300 full-depth trees). This is the main runtime cost.

## Reproduce

```bash
npm run ml:bootstrap   # preprocess -> train -> export (about 40 min on a laptop CPU)
```

Each run writes `experiments/001_baseline/run_<version>.json` and `ml/models/saved/band_gap/metadata.json`.
