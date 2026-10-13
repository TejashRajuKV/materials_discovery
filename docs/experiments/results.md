# Results: experiment 001 (baseline), JARVIS dft_3d

Current run `20261013-141838`: wide-gap blend and 8 chemistry features (next-but-one section), trained on JARVIS plus 25,287 Materials Project formulas JARVIS lacks (harmonised PBE labels, see the generalisation section). The JARVIS test split is unchanged. Earlier runs: `20261010-033538` (JARVIS only, minimum leaf 5) and `20261009-165022` (minimum leaf 1), trained on 65,319 formulas (52,077 train / 13,242 test). Split: grouped
by chemical system, so no element set appears in both train and test. Gaps in eV, OptB88vdW.

Run `20261009-092936` (plain regressors only) is kept in `experiments/001_baseline/` for comparison.

## Held-out test set

| Model | MAE | RMSE | R² | CV MAE (train) |
| --- | --- | --- | --- | --- |
| mean predictor | 0.797 | 1.210 | −0.000 | 0.813 |
| ridge | 0.624 | 0.949 | 0.384 | 0.630 |
| random forest (previous selection) | 0.284 | 0.602 | 0.752 | 0.300 |
| gradient boosting | 0.413 | 0.751 | 0.614 | 0.415 |
| **hurdle with wide-gap blend** (selected) | **0.259** | 0.651 | 0.71 | 0.374 |

Selection uses grouped 5-fold CV MAE on the training split; the test split does not influence it.

## What the hurdle model changes

The target is 74% zeros, so a single regressor averages between the zero spike and the non-zero gaps.
The hurdle model classifies metal vs non-metal first, then regresses the gap for non-metals only.

| Band-gap range (eV) | n | Random forest MAE | Hurdle MAE |
| --- | --- | --- | --- |
| 0 (metals) | 9,800 | 0.154 | **0.129** |
| 0–1 | 1,292 | 0.419 | 0.635 |
| 1–2 | 754 | 0.500 | 0.489 |
| 2–4 | 913 | 0.781 | **0.589** |
| > 4 | 483 | 1.286 | **0.929** |

The trade-off is real: metals and gaps above 2 eV improve, but small-gap semiconductors (0–2 eV) get
worse. A classifier that calls a small-gap semiconductor "metal" returns exactly 0 eV. GaAs is an
example: the model says metal with probability 0.82. The overall R² falls slightly for the same reason.

## Calibrated intervals

Split-conformal intervals at 90% level. The half-width (1.22 eV) comes from the out-of-fold residuals
of the selected model on the training split. Held-out coverage on the JARVIS test split is 0.933, against a target of 0.90.
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
> held-out experiment in the next section is one piece of evidence, and the OQMD section after it is the
> independent check.

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

## Independent validation: OQMD

`ml/validation/oqmd_benchmark.py` and `ml/experiments/oqmd_comparison.py`. OQMD (`all_oqmd.json`, from
figshare via jarvis-tools, 817,642 records) is a third source. Only formulas absent from both JARVIS and
Materials Project are scored, so the deployed model has seen neither the formula nor its label: 344,373
formulas, of which 94.6% are metals (zero gap). Metals are easy, so the table scores non-metals (18,759
formulas) separately; the all-formula numbers are dominated by them.

**Method agreement** (41,989 formulas shared with JARVIS): OQMD and JARVIS gaps differ by 0.17 eV MAE
(correlation 0.91); JARVIS is on average 0.08 eV lower.

**JARVIS-only vs deployed model**, on the same unseen OQMD formulas:

| | JARVIS-only | Deployed (with MP labels) |
| --- | --- | --- |
| Non-metal MAE (eV) | 0.929 | **0.901** |
| Non-metal R² | 0.220 | **0.256** |
| All-formula MAE (eV) | 0.1185 | 0.118 |
| 0–1 eV, MAE | 0.592 | 0.581 |
| 1–2 eV, MAE | 0.785 | **0.701** |
| 2–4 eV, MAE | 0.982 | **0.928** |
| > 4 eV, MAE | 2.28 | 2.37 |

**What this means.** The Materials Project labels do help on a source the model never saw, but by about
3% in non-metal MAE, not the 19% seen on held-out Materials Project chemistry. Part of that larger gain came
from the mapped labels matching Materials Project's own PBE settings. Gaps above 4 eV remain the weak spot
(about 2.3 eV error, and slightly worse after augmentation). The deployed model's 90% intervals contain the
OQMD gap for 80% of unseen non-metal formulas, short of the 90% target, so they remain optimistic on new
chemistry.

**Reproduce.** Download `all_oqmd.json.zip` (63 MB, figshare file 26790182) into `ml/data/raw/oqmd/` and
unzip it there, then run `run_benchmark()` and `ml.experiments.oqmd_comparison.run()`. Results go to
`experiments/` (git-ignored). OQMD element symbols carry a trailing space; the reader strips it and fails
loudly if too many records cannot be read.

## Wide-gap predictions (compounds above 4 eV)

**Diagnosis.** For wide-gap non-metals the error is almost entirely bias: the forest averages over its leaves
and shrinks large gaps toward the mean. On the JARVIS test split the mean error above 4 eV was −1.09 eV for
an MAE of 1.11 eV, and the largest prediction was 7.2 eV while labels reach 18 eV.

**Variants** (non-metals only, scored on the JARVIS test split and on held-out Materials Project chemical
systems; OQMD was not used to choose). MAE in eV:

| Variant | JARVIS > 4 | MP > 4 | JARVIS 0–1 | JARVIS 1–2 | JARVIS all | MP all |
| --- | --- | --- | --- | --- | --- | --- |
| Forest (previous) | 1.111 | 0.680 | 0.683 | 0.376 | 0.636 | 0.650 |
| + monotone calibration | 0.996 | 0.652 | 0.641 | 0.405 | 0.615 | 0.656 |
| Wide-gap rows up-weighted | 0.802 | 0.492 | 0.792 | 0.449 | 0.637 | 0.668 |
| Gradient boosting | 1.113 | 0.676 | 0.707 | 0.442 | 0.673 | 0.671 |
| + 8 chemistry features | 1.074 | 0.668 | 0.672 | 0.372 | 0.624 | 0.640 |
| Up-weighted + features | 0.785 | 0.481 | 0.775 | 0.436 | 0.624 | 0.656 |
| **Blend: specialist weighted by P(gap > 3.5)** | **0.887** | **0.556** | 0.689 | 0.381 | **0.603** | **0.638** |

Up-weighting fixes the wide-gap bias but costs the 0–2 eV range about 15%. The blend keeps most of the
gain while the 0–2 eV ranges stay within 2% of the previous model. The extra features (anion fractions,
ionic character, d- and f-block share) give about 2% everywhere. The deployed model is the blend with the
features: JARVIS test MAE 0.259 eV, above 4 eV 0.929 eV (was 1.156).

**Independent check (OQMD, unseen non-metal formulas, 18,759).**

| | Previous model | Blend model |
| --- | --- | --- |
| Non-metal MAE (eV) | 0.901 | **0.890** |
| Non-metal R² | 0.256 | **0.266** |
| Above 4 eV, MAE (eV) | 2.37 | **2.22** |
| 0–1 / 1–2 / 2–4 eV, MAE | 0.581 / 0.701 / 0.928 | 0.584 / 0.713 / 0.935 |
| 90% interval coverage | 0.80 | 0.79 |

The development-set gain does not carry over: above 4 eV the OQMD error falls 6%, not 20%, and overall
non-metal error improves by about 1%. The remaining 2.2 eV is not mainly disagreement between databases:
on formulas present in both, JARVIS and OQMD differ by 0.43 eV MAE where JARVIS is above 4 eV, and
0.68 eV where OQMD is. So it is real model error on unseen wide-gap chemistry. Composition statistics do
not seem to carry enough information there; structural information is the likelier next step.
