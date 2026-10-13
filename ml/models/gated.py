"""Wide-gap specialist blended into a base regressor, for the non-metal stage of the hurdle model.

A random forest averages over the leaves it lands in, which shrinks large gaps toward the mean: for
compounds above 4 eV the mean error is almost entirely a negative bias. Up-weighting wide-gap rows fixes
that, but also damages the 0-2 eV range, which matters for many applications. So the two are blended:

    prediction = base + p * (specialist - base)

base is trained normally, the specialist with wide-gap rows up-weighted, and p = P(gap > threshold) comes
from a classifier. Compounds that look low-gap (p near 0) keep the base prediction.
"""
import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin, clone


class WideGapGatedRegressor(BaseEstimator, RegressorMixin):
    def __init__(self, base=None, specialist=None, gate=None, threshold=3.5, weight_above=3.0,
                 weight_from=3.0):
        self.base = base
        self.specialist = specialist
        self.gate = gate
        self.threshold = threshold
        self.weight_above = weight_above  # extra weight for rows above `weight_from`
        self.weight_from = weight_from

    def fit(self, X, y):
        X, y = np.asarray(X), np.asarray(y, dtype=float)
        self.base_ = clone(self.base).fit(X, y)
        weights = 1.0 + self.weight_above * (y > self.weight_from)
        self.specialist_ = clone(self.specialist).fit(X, y, sample_weight=weights)
        self.gate_ = clone(self.gate).fit(X, (y > self.threshold).astype(int))
        return self

    def predict(self, X):
        X = np.asarray(X)
        base = self.base_.predict(X)
        return base + self.predict_wide_gap_probability(X) * (self.specialist_.predict(X) - base)

    def predict_wide_gap_probability(self, X):
        proba = self.gate_.predict_proba(np.asarray(X))
        return proba[:, 1] if proba.shape[1] > 1 else np.zeros(len(proba))
