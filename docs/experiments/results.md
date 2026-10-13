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

Band-gap intervals are 90% conformal intervals calibrated on **unseen chemistry**: OQMD formulas absent from
JARVIS and Materials Project, with implausible labels removed (see the OQMD section). They are binned by the
predicted gap (exactly 0, then 0–1, 1–2, 2–4, above 4 eV), and predicted metals are further split by the
classifier's probability of being a non-metal. Each bin has its own half-width, so the interval is narrow for a
confident metal and wide for a large predicted gap. See "Interval recalibration" below for why.

Formation-energy and bulk-modulus intervals are still constant-width conformal intervals calibrated on JARVIS
out-of-fold residuals (coverage 0.91 and 0.90 on the JARVIS test split). They have not been checked on unseen
chemistry, and the band-gap results suggest they are optimistic there.

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

`ml/validation/oqmd_benchmark.py`, `ml/experiments/oqmd_comparison.py`, `ml/validation/label_quality.py`.
OQMD (`all_oqmd.json`, from figshare via jarvis-tools, 817,642 records) is a third source. Only formulas absent
from both JARVIS and Materials Project are scored, so the model has seen neither the formula nor its label:
344,373 formulas, of which 94.6% are metals (zero gap). Metals are easy, so non-metals (18,759) are scored
separately.

**OQMD contains artefact labels, and they dominate the wide-gap error.** OQMD reports gaps of 9–12 eV for
intermetallics: combinations of pure metals such as `AcLaNd`, `AcNdTh` or `AcGdRe`, which are metals with zero
gap. 435 of OQMD's 394,969 formulas are all-metal compounds with a gap above 2 eV (JARVIS has 1, Materials
Project 4). Among the unseen non-metals, 381 (2%) are such entries, including 299 of the 2,138 above 4 eV. Scoring
without them changes the result a great deal, so every comparison below is given both ways.

**Method agreement** (41,989 formulas shared with JARVIS): OQMD and JARVIS gaps differ by 0.17 eV MAE
(correlation 0.91); JARVIS is on average 0.08 eV lower.

**Three models on the same unseen non-metals**, MAE in eV (R² in brackets):

| | JARVIS-only | Previous (JARVIS + MP labels) | Current (+ wide-gap blend, 71 features) |
| --- | --- | --- | --- |
| Without artefact labels (18,378) | 0.820 (0.439) | 0.792 (0.483) | **0.780 (0.496)** |
| 0–1 eV | 0.592 | **0.581** | 0.584 |
| 1–2 eV | 0.785 | **0.701** | 0.713 |
| 2–4 eV | 0.947 | **0.892** | 0.899 |
| Above 4 eV | 1.505 | 1.609 | **1.438** |
| As given, with artefacts (18,759) | 0.929 (0.220) | 0.901 (0.256) | 0.890 (0.266) |
| Above 4 eV, as given | 2.28 | 2.37 | 2.22 |

**What this means.**
- The current model is 4.8% better than JARVIS-only on unseen chemistry (0.820 to 0.780 eV, R² 0.44 to 0.50).
- The Materials Project labels help the 1–4 eV ranges (about 6–11%) but hurt above 4 eV (1.51 to 1.61). The
  wide-gap blend recovers that and then some: 1.61 to 1.44.
- The earlier figure of about 2.3 eV error above 4 eV on unseen chemistry was inflated by the artefact labels.
  Without them it is about 1.4 eV, against 0.93 eV on the JARVIS test split. Wide-gap compounds are still the
  weakest range, but the gap between benchmark and held-out test is much smaller than it first appeared.
- The deployed model's 90% intervals contain 81% of the cleaned OQMD gaps (79% as given), below the 90%
  target, so they are still optimistic on new chemistry.

**Reproduce.** Download `all_oqmd.json.zip` (63 MB, figshare file 26790182) into `ml/data/raw/oqmd/` and unzip
it there, then run `run_benchmark()` and `ml.experiments.oqmd_comparison.run()`. Results go to `experiments/`
(git-ignored). OQMD element symbols carry a trailing space; the reader strips it and fails loudly if too many
records cannot be read. Cached tables are read with `keep_default_na=False`, since the formula `NaN` (sodium
nitride) would otherwise be read as a missing value.

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

**Independent check (OQMD).** See the OQMD section above. The blend lowers the OQMD error above 4 eV from
1.61 to 1.44 eV on cleaned labels (as given, with artefacts: 2.37 to 2.22 eV). Overall non-metal error improves
by about 1.5%. The development-set gain (20%) is larger than the independent one (11% above 4 eV on cleaned
labels), as expected when variants are selected on the development sets.

## Structure-aware features

`ml/representation/structure_features.py` (17 descriptors: packing and density, lattice shape, nearest-
neighbour distances, coordination, and bond ionicity from the electronegativity difference across bonds) and
`ml/experiments/structure_ablation.py`. Entry-level ablation: each formula's most stable JARVIS entry, with
that entry's own gap, non-metals only, random forests with identical settings. Scored on the JARVIS grouped
test split (3,466) and on unseen OQMD non-metals (18,759, most stable OQMD entry of each, artefact labels not
removed here). MAE in eV:

| | Composition (71 features) | + structure (88 features) |
| --- | --- | --- |
| JARVIS test | 0.605 | **0.572** (−5%) |
| JARVIS test, above 4 eV | 0.993 | 0.950 |
| OQMD unseen | 0.909 | **0.883** (−3%) |
| OQMD unseen, above 4 eV (with artefacts) | 2.776 | 2.725 |

Structure helps a little, 3–5% overall, and does not change the wide-gap picture: the bias above 4 eV is still
large with or without it, and on OQMD it is dominated by the artefact labels. The structure descriptors are not
used in the deployed model, because candidates produced by element substitution have no structure to compute
them from. They would apply to known materials, OQMD entries, or a future structure-generation step.

## Interval recalibration

`ml/prediction/intervals.py`, `ml/experiments/interval_calibration.py`. The first intervals came from
out-of-fold residuals on JARVIS and Materials Project training data: one constant half-width (1.22 eV), 0.93
coverage on the JARVIS test split. On unseen chemistry they were badly miscalibrated.

**The measurement problem.** 94.6% of unseen OQMD formulas are metals with zero gap. Overall coverage is
therefore meaningless: a constant interval 0.03 eV wide reached 0.90 overall by being exactly right on metals,
while covering 2% of non-metals. Coverage is reported conditional on the predicted-gap bin, which is what a
user sees, with metals weighted back to their true share.

**Protocol.** The model never trained on these formulas, so its residuals on them are honest. They are split by
chemical system into a calibration half and a test half; methods are fitted on one half and scored on the other,
averaged over five random splits. Coverage by predicted-gap bin on the held-out half (target 0.90):

| Predicted gap | Previous (constant 1.22 eV) | Recalibrated | Recalibrated half-width (eV) |
| --- | --- | --- | --- |
| 0 (predicted metal) | 0.996 | 0.984 | 0 to 0.62, by classifier probability |
| 0–1 eV | 0.988 | 0.899 | 0.95 |
| 1–2 eV | **0.570** | 0.899 | 1.73 |
| 2–4 eV | **0.431** | 0.888 | 3.11 |
| Above 4 eV | **0.448** | 0.887 | 5.12 |

Predicted metals whose classifier probability of being a non-metal was above 0.35 were covered 0.82 by a
single metal width and 0.89 once split by that probability.

**What this means.** The previous intervals covered fewer than half of the compounds predicted at 2 eV or above
on unseen chemistry. The honest 90% intervals there are wide: ±3.1 eV at 2–4 eV and ±5.1 eV above 4 eV (the lower end is clipped at 0). That
reflects heavy-tailed errors on new chemistry, not a calibration flaw. Scaling each interval by the forest's
per-material spread, with or without the bins, barely narrows them (interval width 5.47 against 5.73 eV in the
2–4 eV bin at equal coverage), so that spread does not identify which predictions will be wrong.

**Limits.**
- OQMD labels come from a different DFT code than JARVIS, so the intervals also absorb about 0.2 eV of
  method difference. They describe the gap as another code would compute it for unseen chemistry.
- The calibration set cannot also test the final model: the deployed intervals are fitted on all of it. The
  held-out figures above come from the split protocol.
- A prediction of exactly zero can still be wrong: GaAs is predicted as a metal with a 0.32 probability of being
  a non-metal, and gets a minimal interval. Roughly 9% of predicted metals at that probability are not metals;
  the displayed probability and the "low" confidence label are the signal.
- A display floor of 0.05 eV stops a predicted metal showing a zero-width interval.
- Retraining invalidates the calibration: `interval_calibration.prepare()` rebuilds its cached predictions when
  the model version changes, and `apply()` must be rerun.
