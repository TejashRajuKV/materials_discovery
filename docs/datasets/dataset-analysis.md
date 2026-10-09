# Dataset analysis: JARVIS dft_3d

Numbers below come from `ml/data/processed/preprocessing_report.json` and the trained model's
`metadata.json` (current version `20261009-165022`).

## Cleaning

| Step | Count |
| --- | --- |
| Raw entries (dft_3d) | 93,902 |
| Dropped: formula cannot be parsed or has elements beyond Pu | 18 |
| Dropped: missing or negative OptB88vdW gap | 0 |
| Merged: duplicate formulas (polymorphs), median gap kept | 28,565 |
| **Training rows** | **65,319** |

Stability uses the same formulas: every one has an `ehull` (the lowest across its entries). About 10%
(6,464 formulas) are within 0.025 eV/atom of the hull.

## Band-gap target (after cleaning)

- mean 0.52 eV, std 1.24 eV, max 17.97 eV
- **73.5% exactly zero** (metals under OptB88vdW). This dominates the error and the metrics.
- Largest values are solid He and Ne (wide-gap insulators in DFT). The plausibility bound was raised
  from 15 to 25 eV for this reason; see `ml/preprocessing/validation.py`.

## Model error on the held-out set (hurdle model, 13,242 compounds)

| Gap range (eV) | n | MAE (eV) |
| --- | --- | --- |
| 0 (metals) | 9,800 | 0.11 |
| 0–1 | 1,292 | 0.55 |
| 1–2 | 754 | 0.55 |
| 2–4 | 913 | 0.57 |
| > 4 | 483 | 0.92 |

Error is largest for the small-gap semiconductors that the metal classifier sometimes misses, and for
wide-gap insulators, which are rare in the training data. The previous plain random forest had lower
error in the 0–2 eV range (0.42–0.50 eV); see `docs/experiments/results.md`.

## Limitations

1. **DFT labels, not experiment.** OptB88vdW systematically underestimates gaps relative to
   experiment, and TBmBJ is closer. Predictions are for DFT gaps.
2. **Zero-inflated target.** The model is strongest on metals and weakest on wide-gap insulators.
3. **Stability is for known entries only.** Generated candidates have no `ehull`.
4. **Composition-only features.** Structure descriptors are not implemented yet.
