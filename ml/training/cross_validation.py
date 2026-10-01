"""Chemical-system-grouped splitting: all compounds sharing an element set stay together,
so near-duplicates (e.g. polymorphs / stoichiometry variants) cannot leak across folds."""
import numpy as np
from sklearn.base import clone
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

from ml.config import CV_FOLDS, RANDOM_SEED, TEST_SIZE
from ml.evaluation.metrics import regression_metrics


def grouped_train_test_split(n_samples, groups, test_size=TEST_SIZE, seed=RANDOM_SEED):
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_idx, test_idx = next(splitter.split(np.zeros(n_samples), groups=groups))
    return train_idx, test_idx


def grouped_cv_scores(model, X, y, groups, folds=CV_FOLDS):
    """Out-of-fold metrics for `model` using GroupKFold."""
    X, y = np.asarray(X), np.asarray(y)
    oof = np.zeros(len(y))
    for tr, va in GroupKFold(n_splits=folds).split(X, y, groups):
        fitted = clone(model).fit(X[tr], y[tr])
        oof[va] = fitted.predict(X[va])
    return regression_metrics(y, oof), oof
