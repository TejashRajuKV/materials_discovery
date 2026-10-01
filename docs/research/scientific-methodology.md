# Scientific methodology

Pipeline: `raw CSV → clean → featurize → grouped split → baselines → select → uncertainty → discover`.

- **Cleaning**: reduce formulas (pymatgen), drop unparsable/unsupported species (H–Pu only),
  drop missing/negative targets, merge duplicate formulas by median.
- **Splitting**: `GroupShuffleSplit` and `GroupKFold` grouped by chemical system (sorted element
  set) so stoichiometry variants of the same system never straddle train/test (leakage control).
- **Models**: mean predictor (sanity floor), ridge, random forest, histogram gradient boosting. Selection by
  grouped-CV MAE on the training split only; the test split is reported once.
- **Final model** is refit on all data; reported metrics are from the held-out evaluation.
- **Uncertainty**: spread of per-tree predictions of the random forest (relative, uncalibrated).
  Confidence bands are quantiles of that spread on held-out data.
- **Prediction intervals**: 90% intervals from the selected model's out-of-fold residuals (grouped CV), binned by
  predicted value because error depends on the regime (cross-conformal; approximate). Empirical coverage is
  measured on the untouched test split and shown on the Models page.
- **Candidate generation**: same-group element substitution on known formulas, deduplicated
  against the known set.
- **Validation cost control**: requirement filtering and ranking run on the whole pool; the expensive chemistry
  checks run down the ranking only until the top-k survive. Pareto sorting is exact (O(n log n) for 2 objectives).
- **Ranking**: objectives (distance to target, uncertainty) → non-dominated sorting → weighted
  score within a front. Known entries (recorded value) and generated ones (predicted) are ranked
  separately because uncertainty 0 is not comparable.
- **Explanations**: model-level only (feature influence, nearest known materials) — not causal.
