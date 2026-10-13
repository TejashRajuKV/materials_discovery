import numpy as np
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from ml.models.gated import WideGapGatedRegressor
from ml.models.hurdle import HurdleRegressor
from ml.representation.material_representation import all_feature_names, featurize, featurize_many


def _rf(n=40):
    return RandomForestRegressor(n_estimators=n, min_samples_leaf=3, random_state=0)


def _gated(n=40):
    return WideGapGatedRegressor(
        base=_rf(n), specialist=_rf(n),
        gate=RandomForestClassifier(n_estimators=n, min_samples_leaf=3, random_state=0),
    )


def _data(n=600, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.uniform(0, 1, size=(n, 3))
    y = 0.5 + 8.0 * X[:, 0] ** 3 + 0.05 * rng.standard_normal(n)  # a few large values, many small
    return X, y


def test_prediction_is_the_blend_of_base_and_specialist():
    X, y = _data()
    model = _gated().fit(X, y)
    p = model.predict_wide_gap_probability(X[:50])
    expected = model.base_.predict(X[:50]) + p * (model.specialist_.predict(X[:50]) - model.base_.predict(X[:50]))
    assert np.allclose(model.predict(X[:50]), expected)
    assert np.all((p >= 0) & (p <= 1))


def test_specialist_lifts_wide_gap_predictions_and_low_gap_stay_close():
    X, y = _data()
    train, test = slice(0, 450), slice(450, 600)
    model = _gated().fit(X[train], y[train])
    wide = y[test] > 4
    assert wide.any()
    base_err = np.mean(y[test][wide] - model.base_.predict(X[test])[wide])        # shrinkage: positive
    gated_err = np.mean(y[test][wide] - model.predict(X[test])[wide])
    assert gated_err < base_err                                                    # less underprediction
    low = y[test] < 1.5
    assert np.mean(np.abs(model.predict(X[test])[low] - model.base_.predict(X[test])[low])) < 0.3


def test_clones_and_works_as_the_hurdle_regressor_stage():
    X, y = _data()
    y = np.where(X[:, 1] < 0.3, 0.0, y)  # some exact zeros, for the metal stage
    assert clone(_gated()).threshold == 3.5
    hurdle = HurdleRegressor(
        classifier=RandomForestClassifier(n_estimators=30, random_state=0), regressor=_gated(30)
    ).fit(X, y)
    pred = hurdle.predict(X)
    assert pred.shape == y.shape and np.all(pred >= 0)


def test_extended_features_are_opt_in_and_base_layout_is_unchanged():
    base = featurize("NaCl")
    extended = featurize("NaCl", extended=True)
    assert base.shape == (63,) and extended.shape == (71,)
    assert np.allclose(extended[:63], base)  # the base columns keep their positions
    assert len(all_feature_names()) == 63 and len(all_feature_names(True)) == 71
    assert featurize_many(["NaCl", "MgO"], extended=True).shape == (2, 71)
    assert featurize_many(["NaCl"]).shape == (1, 63)
