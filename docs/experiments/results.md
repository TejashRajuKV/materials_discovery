# Results: experiment 001 (baseline), JARVIS dft_3d

Current run `20261009-165022`, trained on 65,319 formulas (52,077 train / 13,242 test). Split: grouped
by chemical system, so no element set appears in both train and test. Gaps in eV, OptB88vdW.

Run `20261009-092936` (plain regressors only) is kept in `experiments/001_baseline/` for comparison.

## Held-out test set

| Model | MAE | RMSE | R² | CV MAE (train) |
| --- | --- | --- | --- | --- |
| mean predictor | 0.797 | 1.210 | −0.000 | 0.813 |
| ridge | 0.624 | 0.949 | 0.384 | 0.630 |
| random forest (previous selection) | 0.284 | 0.602 | 0.752 | 0.300 |
| gradient boosting | 0.413 | 0.751 | 0.614 | 0.415 |
| **hurdle (metal classifier + non-metal forest)** (selected) | **0.235** | 0.634 | 0.725 | **0.251** |

Selection uses grouped 5-fold CV MAE on the training split; the test split does not influence it.

## What the hurdle model changes

The target is 74% zeros, so a single regressor averages between the zero spike and the non-zero gaps.
The hurdle model classifies metal vs non-metal first, then regresses the gap for non-metals only.

| Band-gap range (eV) | n | Random forest MAE | Hurdle MAE |
| --- | --- | --- | --- |
| 0 (metals) | 9,800 | 0.154 | **0.106** |
| 0–1 | 1,292 | 0.419 | 0.550 |
| 1–2 | 754 | 0.500 | 0.547 |
| 2–4 | 913 | 0.781 | **0.565** |
| > 4 | 483 | 1.286 | **0.917** |

The trade-off is real: metals and gaps above 2 eV improve, but small-gap semiconductors (0–2 eV) get
worse. A classifier that calls a small-gap semiconductor "metal" returns exactly 0 eV. GaAs is an
example: the model says metal with probability 0.82. The overall R² falls slightly for the same reason.

## Calibrated intervals

Split-conformal intervals at 90% level. The half-width (0.87 eV) comes from the out-of-fold residuals
of the selected model on the training split. Held-out coverage is 0.909, against a target of 0.90.
Intervals are the same width for every material, so they are wide (1.74 eV) and not adaptive; the
forest's tree-spread uncertainty remains the per-material signal.

## Other findings

- Forest tree-spread predicts absolute error well on held-out data (correlation 0.80). The high, medium,
  and low confidence labels use its thresholds, plus the classifier's probability for hurdle models.
- Most important features (regressor forest): mean ionization energy, minimum molar volume, maximum
  Mendeleev number, mean melting point, deviation of group number.

## Caveats

- Metrics are against DFT labels (OptB88vdW). They say nothing yet about experimentally measured gaps.
- The bundle is ~1.2 GB (the regressor and classifier forests, 300 full-depth trees each). This is the
  main runtime cost.

## Reproduce

```bash
python ml/main.py train     # about 50 min on a laptop CPU
python ml/main.py export
npm run db:seed
```

Each run writes `experiments/001_baseline/run_<version>.json` and `ml/models/saved/band_gap/metadata.json`.

## Other properties: formation energy and bulk modulus

Same recipe as the band-gap model (grouped split, grouped CV, conformal intervals), with smaller forests
so the bundles stay small. Each property uses the most stable JARVIS entry per formula. Trained by
`python ml/main.py train-property --property <name>`.

| Property | Formulas (train / test) | Model | Test MAE | Mean-baseline MAE | Test R² | 90% interval coverage |
| --- | --- | --- | --- | --- | --- | --- |
| Formation energy (eV/atom) | 65,319 (52,077 / 13,242) | random forest | 0.156 | 0.774 | 0.93 | 0.909 |
| Bulk modulus (GPa) | 24,372 (19,437 / 4,935) | random forest | 16.5 | 54.5 | 0.84 | 0.903 |

Interval half-widths are 0.37 eV/atom and 38.8 GPa, constant for every material. Bulk moduli below zero
are dropped as unphysical. About 41,000 formulas have no bulk modulus in JARVIS, so that model covers less of the dataset.
