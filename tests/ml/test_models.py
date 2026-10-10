import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from ml.models.hurdle import HurdleRegressor
from ml.training.train import conformal_half_width


def _zero_inflated(n=400, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.uniform(-1, 1, size=(n, 3))
    metal = X[:, 0] < 0  # the first feature decides metal vs non-metal
    gap = np.where(metal, 0.0, 2.0 + X[:, 1] + 0.1 * rng.standard_normal(n))
    return X, gap


def _hurdle():
    return HurdleRegressor(
        classifier=RandomForestClassifier(n_estimators=50, random_state=0),
        regressor=RandomForestRegressor(n_estimators=50, random_state=0),
    )


def test_hurdle_predicts_exact_zero_for_metals_and_gap_for_nonmetals():
    X, y = _zero_inflated()
    model = _hurdle().fit(X[:300], y[:300])
    pred = model.predict(X[300:])
    truth = y[300:]
    assert np.all(pred[truth == 0] == 0.0)  # metals get exactly zero
    nonmetal = truth > 0
    assert np.mean(np.abs(pred[nonmetal] - truth[nonmetal])) < 0.5


def test_hurdle_clones_and_works_inside_cross_validation():
    from sklearn.base import clone
    from ml.training.cross_validation import grouped_cv_scores

    X, y = _zero_inflated()
    groups = np.arange(len(y)) % 20
    metrics, oof = grouped_cv_scores(_hurdle(), X, y, groups, folds=4)
    assert oof.shape == y.shape and metrics["mae"] < 0.8
    assert clone(_hurdle()).threshold == 0.5


def test_conformal_half_width_covers_the_requested_fraction():
    rng = np.random.default_rng(1)
    y_true = rng.normal(size=2000)
    y_pred = np.zeros(2000)
    half = conformal_half_width(y_true, y_pred, level=0.9)
    assert np.mean(np.abs(y_true) <= half) == pytest.approx(0.9, abs=0.02)


def test_conformal_half_width_handles_tiny_samples():
    assert conformal_half_width([1.0, 2.0], [0.0, 0.0], level=0.9) == pytest.approx(2.0)
