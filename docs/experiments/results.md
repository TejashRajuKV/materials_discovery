# Results: experiment 001 (baseline), JARVIS dft_3d

Current run `20261010-095533`: trained on JARVIS plus 25,287 Materials Project formulas JARVIS lacks (harmonised PBE labels, see the generalisation section). The JARVIS test split is unchanged. Earlier runs: `20261010-033538` (JARVIS only, minimum leaf 5) and `20261009-165022` (minimum leaf 1), trained on 65,319 formulas (52,077 train / 13,242 test). Split: grouped
by chemical system, so no element set appears in both train and test. Gaps in eV, OptB88vdW.

Run `20261009-092936` (plain regressors only) is kept in `experiments/001_baseline/` for comparison.

## Held-out test set

| Model | MAE | RMSE | R² | CV MAE (train) |
| --- | --- | --- | --- | --- |
| mean predictor | 0.797 | 1.210 | −0.000 | 0.813 |
| ridge | 0.624 | 0.949 | 0.384 | 0.630 |
| random forest (previous selection) | 0.284 | 0.602 | 0.752 | 0.300 |
| gradient boosting | 0.413 | 0.751 | 0.614 | 0.415 |
| **hurdle (metal classifier + non-metal forest)** (selected) | **0.268** | 0.659 | 0.703 | 0.385 |

Selection uses grouped 5-fold CV MAE on the training split; the test split does not influence it.

## What the hurdle model changes

The target is 74% zeros, so a single regressor averages between the zero spike and the non-zero gaps.
The hurdle model classifies metal vs non-metal first, then regresses the gap for non-metals only.

| Band-gap range (eV) | n | Random forest MAE | Hurdle MAE |
| --- | --- | --- | --- |
| 0 (metals) | 9,800 | 0.154 | **0.128** |
| 0–1 | 1,292 | 0.419 | 0.627 |
| 1–2 | 754 | 0.500 | 0.492 |
| 2–4 | 913 | 0.781 | **0.610** |
| > 4 | 483 | 1.286 | **1.156** |

The trade-off is real: metals and gaps above 2 eV improve, but small-gap semiconductors (0–2 eV) get
worse. A classifier that calls a small-gap semiconductor "metal" returns exactly 0 eV. GaAs is an
example: the model says metal with probability 0.82. The overall R² falls slightly for the same reason.

## Calibrated intervals

Split-conformal intervals at 90% level. The half-width (1.28 eV) comes from the out-of-fold residuals
of the selected model on the training split. Held-out coverage on the JARVIS test split is 0.932, against a target of 0.90.
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

## External validation: Materials Project PBE gaps (model `20261010-033538`, before augmentation)

> The numbers below describe the JARVIS-only model. The current model is trained on the Materials Project
> formulas this benchmark used as "novel", so the benchmark no longer measures generalisation for it. The
> held-out experiment in the next section is the evidence for the current model; re-measuring needs a source
> the model has not seen, such as OQMD.

`ml/validation/external_benchmark.py` checks the band-gap model against the Materials Project gaps in
`mp_3d.json` (PBE, a different DFT method from JARVIS's OptB88vdW). Run it with
`python -c "from ml.validation.external_benchmark import run_benchmark; run_benchmark()"`. The result JSON
goes to `experiments/external/` (git-ignored).

**Method agreement** (31,140 formulas present in both sources): JARVIS and PBE gaps differ by 0.22 eV MAE
(correlation 0.93), and JARVIS is on average 0.13 eV lower. This is the floor for any model trained on
JARVIS labels, whatever its architecture.

**Generalisation to novel formulas** (25,287 formulas absent from the JARVIS training set):

| Metric | Value |
| --- | --- |
| MAE | 0.80 eV (JARVIS test set: 0.25 eV) |
| RMSE | 1.24 eV |
| R² | 0.41 (JARVIS test set: 0.71) |
| 90% interval coverage | 0.68 (target 0.90) |

By gap range (MAE, eV): metals 0.51, 0–1 eV 0.86, 1–2 eV 0.81, 2–4 eV 1.07, above 4 eV 0.93.

**What this means.** The model's JARVIS test score overstates how well it predicts new compositions or
PBE labels. Part of the gap is the method difference, which accounts for about 0.2 eV. The rest comes from
composition extrapolation. The intervals were calibrated on JARVIS, so they are too narrow for these
labels. Anything that uses the model on new chemistry should treat its intervals as optimistic.

## Generalisation experiment: adding Materials Project labels

`ml/experiments/generalization.py`. The 25,287 Materials Project formulas absent from JARVIS get their PBE
gap mapped onto the JARVIS OptB88vdW scale (linear fit on the 31,140 shared formulas: slope 0.92,
intercept −0.06). Their chemical systems are split 75/25, so the test systems are unseen. Two hurdle models
with the production settings are compared on the same data, scored against the raw PBE gaps:

| | MP test MAE (eV) | MP test R² | JARVIS test MAE (eV) | JARVIS test R² |
| --- | --- | --- | --- | --- |
| JARVIS only | 0.814 | 0.380 | 0.248 | 0.705 |
| JARVIS + MP labels | **0.656** | **0.607** | 0.266 | 0.704 |

On unseen Materials Project chemistry the error falls by 19% and R² rises from 0.38 to 0.61. On JARVIS the
MAE rises by 7% (0.018 eV) with R² unchanged. The deployed model uses all 25,287 formulas, with the
JARVIS test split held out as before: its JARVIS MAE is 0.268 eV.

**Costs.** The 90% interval is wider (half-width 1.28 eV, was 0.92 eV) because its calibration includes the
noisier mixed-source rows. Metals are slightly worse (0.128 vs 0.114 eV), and so is the above-4 eV range
(1.16 vs 0.93 eV). The mapped labels carry the PBE-to-OptB88vdW noise (about 0.2 eV MAE on shared formulas).
