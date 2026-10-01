"""Uncertainty from the spread of a random forest's individual trees.

This is an ensemble-disagreement heuristic, not a calibrated confidence interval:
it tends to be low for compositions far from the training data. Treat as relative.
"""
import numpy as np


def forest_prediction_std(forest, X):
    per_tree = np.stack([tree.predict(np.asarray(X)) for tree in forest.estimators_])
    return per_tree.std(axis=0)


def confidence_label(std, thresholds):
    """thresholds = (low_max, medium_max) taken from training-time out-of-fold residuals."""
    if std <= thresholds[0]:
        return "high"
    if std <= thresholds[1]:
        return "medium"
    return "low"
