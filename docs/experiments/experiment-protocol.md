# Experiment protocol

1. Fix the dataset (file + SHA-256 prefix are recorded) and `RANDOM_SEED` (42).
2. Split with `GroupShuffleSplit` by chemical system (test 20 %); select with 5-fold `GroupKFold` CV
   on the training split; touch the test split once per run.
3. Always include the mean predictor; a model that cannot beat it is not a result.
4. Run `python ml/main.py train [--tune]` — writes `ml/models/saved/band_gap/{bundle.joblib,metadata.json}`
   and `experiments/001_baseline/run_<version>.json`. `experiments/` outputs are git-ignored.
5. Inspect error by band-gap range and material class before trusting an aggregate number.
