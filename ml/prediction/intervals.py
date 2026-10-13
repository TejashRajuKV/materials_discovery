"""Conformal prediction intervals: constant, binned by predicted gap, or scaled by per-material spread.

Each method turns calibration residuals |y - prediction| into half-widths so that, on new data like the
calibration set, the interval prediction +/- half-width contains the true value with probability about `level`.
Calibration rows can carry weights (a sampled group standing for several real rows). A calibration spec is a
plain dict, stored with the model, and `half_widths(spec, prediction, sigma)` turns it into widths.

  constant   one half-width for everything
  binned     a half-width per predicted-gap bin: exactly 0 (a predicted metal), then (0,1], (1,2], (2,4], > 4 eV
  scaled     half-width = q * (sigma + floor), with sigma the forest's per-material spread
  binned_scaled  both: a scale factor q per predicted-gap bin, applied to (sigma + floor)
  binned_p   binned, and the predicted-metal bin is split by the classifier's P(non-metal): a prediction of 0 is
             only as safe as that probability is small
"""
import numpy as np

BIN_EDGES = [0.0, 1.0, 2.0, 4.0]
SIGMA_FLOOR = 0.05
MIN_BIN_WEIGHT = 50.0  # a bin with less calibration weight than this falls back to the constant half-width


def weighted_quantile(values, level, weights=None):
    """Finite-sample conformal quantile: the smallest value whose weighted share of the sample reaches
    level * (total weight + 1) / total weight, capped at the maximum."""
    values = np.asarray(values, float)
    w = np.ones(len(values)) if weights is None else np.asarray(weights, float)
    if len(values) == 0:
        raise ValueError("no calibration residuals")
    order = np.argsort(values)
    values, w = values[order], w[order]
    cumulative = np.cumsum(w)
    target = level * (cumulative[-1] + 1.0)
    index = np.searchsorted(cumulative, target, side="left")
    return float(values[min(index, len(values) - 1)])


def bin_index(prediction, edges=BIN_EDGES):
    """0 for a prediction of exactly 0, then 1 for (0,1], 2 for (1,2], 3 for (2,4], 4 above."""
    return np.searchsorted(np.asarray(edges, float), np.asarray(prediction, float), side="left")


def fit_constant(prediction, sigma, y, level=0.9, weights=None):
    return {"method": "constant", "level": level,
            "half_width": round(weighted_quantile(np.abs(y - prediction), level, weights), 4)}


def fit_binned(prediction, sigma, y, level=0.9, weights=None, edges=BIN_EDGES):
    residual = np.abs(y - prediction)
    w = np.ones(len(y)) if weights is None else np.asarray(weights, float)
    fallback = weighted_quantile(residual, level, w)
    idx = bin_index(prediction, edges)
    halves = []
    for b in range(len(edges) + 1):
        m = idx == b
        halves.append(round(weighted_quantile(residual[m], level, w[m]) if w[m].sum() >= MIN_BIN_WEIGHT else fallback, 4))
    return {"method": "binned", "level": level, "edges": list(edges), "half_widths": halves}


def fit_scaled(prediction, sigma, y, level=0.9, weights=None, floor=SIGMA_FLOOR):
    scores = np.abs(y - prediction) / (np.asarray(sigma, float) + floor)
    return {"method": "scaled", "level": level, "floor": floor, "q": round(weighted_quantile(scores, level, weights), 4)}


def fit_binned_scaled(prediction, sigma, y, level=0.9, weights=None, edges=BIN_EDGES, floor=SIGMA_FLOOR):
    scores = np.abs(y - prediction) / (np.asarray(sigma, float) + floor)
    w = np.ones(len(y)) if weights is None else np.asarray(weights, float)
    fallback = weighted_quantile(scores, level, w)
    idx = bin_index(prediction, edges)
    qs = []
    for b in range(len(edges) + 1):
        m = idx == b
        qs.append(round(weighted_quantile(scores[m], level, w[m]) if w[m].sum() >= MIN_BIN_WEIGHT else fallback, 4))
    return {"method": "binned_scaled", "level": level, "edges": list(edges), "floor": floor, "qs": qs}


P_EDGES = [0.05, 0.2, 0.35]  # P(non-metal) cut points that split the predicted-metal bin into four


def metal_sub_bin(p_nonmetal, p_edges=P_EDGES):
    """0 for the safest predicted metals (small P(non-metal)) up to len(p_edges) for the riskiest."""
    return np.searchsorted(np.asarray(p_edges, float), np.asarray(p_nonmetal, float), side="right")


def fit_binned_p(prediction, sigma, y, level=0.9, weights=None, edges=BIN_EDGES, p_nonmetal=None, p_edges=P_EDGES):
    """Binned calibration, with the predicted-metal bin split by P(non-metal). `p_nonmetal` is required."""
    if p_nonmetal is None:
        raise ValueError("binned_p calibration needs p_nonmetal")
    spec = fit_binned(prediction, sigma, y, level, weights, edges)
    residual = np.abs(y - prediction)
    w = np.ones(len(y)) if weights is None else np.asarray(weights, float)
    zero = bin_index(prediction, edges) == 0
    sub = metal_sub_bin(p_nonmetal, p_edges)
    constant_zero = spec["half_widths"][0]
    metal_halves = []
    for b in range(len(p_edges) + 1):
        m = zero & (sub == b)
        metal_halves.append(round(weighted_quantile(residual[m], level, w[m]) if w[m].sum() >= MIN_BIN_WEIGHT
                                  else constant_zero, 4))
    return {"method": "binned_p", "level": level, "edges": list(edges), "p_edges": list(p_edges),
            "half_widths": spec["half_widths"], "metal_half_widths": metal_halves}


METHODS = {"constant": fit_constant, "binned": fit_binned, "scaled": fit_scaled, "binned_scaled": fit_binned_scaled,
           "binned_p": fit_binned_p}


def half_widths(spec, prediction, sigma, p_nonmetal=None):
    """Per-prediction half-widths for a calibration spec. `p_nonmetal` is used by binned_p only; without it
    (a model that has no classifier) predicted metals fall back to the widest of the metal sub-bins."""
    prediction = np.asarray(prediction, float)
    if spec["method"] == "constant":
        return np.full(len(prediction), spec["half_width"])
    if spec["method"] == "binned":
        return np.asarray(spec["half_widths"])[bin_index(prediction, spec["edges"])]
    if spec["method"] == "scaled":
        return spec["q"] * (np.asarray(sigma, float) + spec["floor"])
    if spec["method"] == "binned_p":
        h = np.asarray(spec["half_widths"])[bin_index(prediction, spec["edges"])].astype(float)
        zero = bin_index(prediction, spec["edges"]) == 0
        metal = np.asarray(spec["metal_half_widths"])
        h[zero] = metal[metal_sub_bin(p_nonmetal, spec["p_edges"])][zero] if p_nonmetal is not None else metal.max()
        return h
    if spec["method"] == "binned_scaled":
        q = np.asarray(spec["qs"])[bin_index(prediction, spec["edges"])]
        return q * (np.asarray(sigma, float) + spec["floor"])
    raise ValueError(f"unknown interval method {spec['method']!r}")


def interval(spec, prediction, sigma, p_nonmetal=None):
    """(low, high), with the lower end clipped at 0 since a band gap cannot be negative."""
    prediction = np.asarray(prediction, float)
    h = half_widths(spec, prediction, sigma, p_nonmetal)
    return np.clip(prediction - h, 0.0, None), prediction + h
