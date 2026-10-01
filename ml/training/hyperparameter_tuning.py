"""Small grouped-CV grid search for the random forest (opt-in via `train --tune`)."""
import itertools

import numpy as np
from sklearn.ensemble import RandomForestRegressor

from ml.config import RANDOM_SEED
from ml.training.cross_validation import grouped_cv_scores

GRID = {"n_estimators": [200, 400], "max_features": [0.3, 0.6, 1.0], "min_samples_leaf": [1, 2]}


def tune_random_forest(X, y, groups):
    best = (np.inf, None)
    for values in itertools.product(*GRID.values()):
        params = dict(zip(GRID, values))
        model = RandomForestRegressor(random_state=RANDOM_SEED, n_jobs=-1, **params)
        metrics, _ = grouped_cv_scores(model, X, y, groups, folds=3)
        if metrics["mae"] < best[0]:
            best = (metrics["mae"], params)
    return best[1], best[0]
