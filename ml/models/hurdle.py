"""Two-stage (hurdle) regressor for a zero-inflated target such as band gap.

About three quarters of JARVIS band gaps are exactly zero (metals). A single regressor has to
average between that spike at zero and the non-zero gaps, so it is pulled away from both. The
hurdle model splits the problem:

  1. a classifier estimates P(non-metal) for each composition;
  2. a regressor, trained only on non-metals, predicts the gap.

predict() returns the regressor's value where the classifier says non-metal (probability at or
above `threshold`), and exactly 0 otherwise. Thresholding, rather than averaging, keeps the output
on one of the two modes, which suits an absolute-error metric.
"""
import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin, clone

METAL_TOLERANCE = 1e-9  # gaps at or below this are treated as zero


class HurdleRegressor(BaseEstimator, RegressorMixin):
    def __init__(self, classifier=None, regressor=None, threshold=0.5):
        self.classifier = classifier
        self.regressor = regressor
        self.threshold = threshold

    def fit(self, X, y):
        X, y = np.asarray(X), np.asarray(y, dtype=float)
        nonmetal = y > METAL_TOLERANCE
        self.classifier_ = clone(self.classifier).fit(X, nonmetal.astype(int))
        self.regressor_ = clone(self.regressor).fit(X[nonmetal], y[nonmetal])
        return self

    def predict(self, X):
        X = np.asarray(X)
        p_nonmetal = self.classifier_.predict_proba(X)[:, 1]
        gap = np.clip(self.regressor_.predict(X), 0.0, None)
        return np.where(p_nonmetal >= self.threshold, gap, 0.0)

    def predict_nonmetal_probability(self, X):
        return self.classifier_.predict_proba(np.asarray(X))[:, 1]
