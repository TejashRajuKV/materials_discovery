"""Calibrated prediction intervals from out-of-fold residuals (cross-conformal, binned).

Residual size depends strongly on the predicted band gap (metals are easy, wide-gap compounds are
hard), so one global width would over-cover some regimes and under-cover others. We bin by predicted
value and use each bin's finite-sample-corrected (1-alpha) quantile of |OOF residual| as the half-width.

Guarantee is approximate: it assumes new compounds resemble the cross-validation folds (which are
grouped by chemical system). For compositions far from the training chemistry, coverage can be lower.
"""
import numpy as np

DEFAULT_ALPHA = 0.1


def fit_binned_intervals(pred, y, alpha=DEFAULT_ALPHA, n_bins=5, min_bin=30):
    pred, y = np.asarray(pred, float), np.asarray(y, float)
    residual = np.abs(y - pred)

    def halfwidth(r):
        n = len(r)
        level = min(1.0, np.ceil((n + 1) * (1 - alpha)) / n)
        return float(np.quantile(r, level))

    edges = np.unique(np.quantile(pred, np.linspace(0, 1, n_bins + 1)[1:-1])).tolist()
    # Merge bins that are too small to give a stable quantile.
    while edges:
        idx = np.digitize(pred, edges)
        counts = np.bincount(idx, minlength=len(edges) + 1)
        small = int(np.argmin(counts))
        if counts[small] >= min_bin:
            break
        edges.pop(max(small - 1, 0) if small == len(edges) else small)
    idx = np.digitize(pred, edges)
    widths = [halfwidth(residual[idx == b]) for b in range(len(edges) + 1)]
    return {"alpha": alpha, "edges": edges, "halfwidths": widths}


def halfwidths(calibration, pred):
    idx = np.digitize(np.asarray(pred, float), calibration["edges"])
    return np.asarray(calibration["halfwidths"])[idx]


def interval(calibration, pred):
    """(lower, upper) arrays; the band gap cannot be negative so lower is clipped at 0."""
    pred = np.asarray(pred, float)
    hw = halfwidths(calibration, pred)
    return np.clip(pred - hw, 0, None), pred + hw


def empirical_coverage(calibration, pred, y):
    lo, hi = interval(calibration, pred)
    y = np.asarray(y, float)
    return float(np.mean((y >= lo) & (y <= hi)))
