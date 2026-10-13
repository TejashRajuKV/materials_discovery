import numpy as np
import pytest

from ml.prediction.intervals import (bin_index, fit_binned, fit_constant, fit_scaled, half_widths, interval,
                                     weighted_quantile)


def test_weighted_quantile_matches_the_unweighted_case_and_respects_weights():
    values = np.arange(1.0, 101.0)
    assert weighted_quantile(values, 0.9) == pytest.approx(91.0, abs=1.0)
    # one value standing for 99 rows: the quantile moves to it
    assert weighted_quantile([1.0, 10.0], 0.9, [1.0, 99.0]) == 10.0
    assert weighted_quantile([1.0, 10.0], 0.9, [99.0, 1.0]) == 1.0
    with pytest.raises(ValueError):
        weighted_quantile([], 0.9)


def test_bins_separate_predicted_metals_from_each_gap_range():
    assert list(bin_index([0.0, 0.5, 1.0, 1.5, 3.9, 4.0, 7.0])) == [0, 1, 1, 2, 3, 3, 4]


def _heteroscedastic(n=20000, seed=0):
    rng = np.random.default_rng(seed)
    pred = rng.choice([0.0, 0.5, 1.5, 3.0, 6.0], size=n)
    noise_scale = np.where(pred == 0, 0.02, 0.2 + 0.25 * pred)  # wide-gap predictions are noisier
    y = np.clip(pred + noise_scale * rng.standard_normal(n), 0, None)
    sigma = noise_scale  # a spread estimate that tracks the noise
    return pred, sigma, y


def _coverage(spec, pred, sigma, y):
    low, high = interval(spec, pred, sigma)
    return (y >= low) & (y <= high)


@pytest.mark.parametrize("fit", [fit_constant, fit_binned, fit_scaled])
def test_each_method_reaches_the_target_coverage_on_fresh_data(fit):
    pred, sigma, y = _heteroscedastic(seed=0)
    spec = fit(pred, sigma, y, level=0.9)
    pred2, sigma2, y2 = _heteroscedastic(seed=1)
    assert _coverage(spec, pred2, sigma2, y2).mean() == pytest.approx(0.9, abs=0.02)


def test_binned_and_scaled_intervals_are_adaptive_where_constant_is_not():
    pred, sigma, y = _heteroscedastic()
    constant, binned, scaled = fit_constant(pred, sigma, y), fit_binned(pred, sigma, y), fit_scaled(pred, sigma, y)
    hardest = pred == 6.0
    # Binned calibration guarantees the target within each bin; scaled only overall, so it comes close but
    # need not reach it in one bin. Both do far better than a single width, which under-covers the noisy bin.
    assert _coverage(binned, pred, sigma, y)[hardest].mean() == pytest.approx(0.9, abs=0.03)
    constant_hard = _coverage(constant, pred, sigma, y)[hardest].mean()
    assert constant_hard < 0.8
    assert _coverage(scaled, pred, sigma, y)[hardest].mean() > constant_hard + 0.03
    assert half_widths(binned, np.array([0.0]), None)[0] < half_widths(binned, np.array([6.0]), None)[0]


def test_interval_is_clipped_at_zero_and_unknown_method_is_rejected():
    low, high = interval({"method": "constant", "level": 0.9, "half_width": 1.0}, np.array([0.3]), None)
    assert low[0] == 0.0 and high[0] == pytest.approx(1.3)
    with pytest.raises(ValueError):
        half_widths({"method": "magic"}, np.array([1.0]), None)


def test_binned_scaled_covers_within_each_bin_and_is_narrower_for_confident_predictions():
    from ml.prediction.intervals import fit_binned_scaled
    rng = np.random.default_rng(3)
    n = 30000
    pred = rng.choice([0.5, 3.0], size=n)
    sigma = rng.choice([0.1, 1.0], size=n)                       # a spread estimate that tracks the noise
    y = np.clip(pred + sigma * rng.standard_normal(n), 0, None)
    spec = fit_binned_scaled(pred, sigma, y, level=0.9)
    covered = _coverage(spec, pred, sigma, y)
    for p in (0.5, 3.0):
        assert covered[pred == p].mean() == pytest.approx(0.9, abs=0.03)
    h = half_widths(spec, np.array([3.0, 3.0]), np.array([0.1, 1.0]))
    assert h[0] < h[1]                                           # confident prediction, narrower interval


class _StubModel:
    def predict(self, X):
        return np.array([0.0, 1.5, 6.0])[: len(X)]


def _bundle(extra_metadata):
    metadata = {"uncertainty": {"std_thresholds": [0.1, 0.5]}, "best_model": "stub", "version": "test",
                "conformal": {"half_width_eV": 0.7, "level": 0.9}, **extra_metadata}
    return {"model": _StubModel(), "forest": object(), "metadata": metadata}


def test_predict_many_uses_the_calibration_spec_with_a_display_floor(monkeypatch):
    from ml.prediction import predict as predict_module
    monkeypatch.setattr(predict_module, "forest_prediction_std", lambda forest, X: np.full(len(X), 0.2))
    spec = {"method": "binned", "level": 0.9, "edges": [0.0, 1.0, 2.0, 4.0], "half_widths": [0.0, 1.0, 2.0, 3.0, 5.0]}
    out = predict_module.predict_many(["NaCl", "MgO", "ZnS"], _bundle({"interval_calibration": {"spec": spec}}))
    metal, middle, wide = out
    assert (metal["interval_low"], metal["interval_high"]) == (0.0, 0.05)      # zero width raised to the floor
    assert (middle["interval_low"], middle["interval_high"]) == (0.0, 3.5)     # 1.5 - 2.0 clipped at 0
    assert (wide["interval_low"], wide["interval_high"]) == (1.0, 11.0)
    assert middle["interval_level"] == 0.9


def test_predict_many_falls_back_to_the_constant_interval_for_older_bundles(monkeypatch):
    from ml.prediction import predict as predict_module
    monkeypatch.setattr(predict_module, "forest_prediction_std", lambda forest, X: np.full(len(X), 0.2))
    out = predict_module.predict_many(["NaCl", "MgO", "ZnS"], _bundle({}))
    assert out[2]["interval_low"] == pytest.approx(5.3) and out[2]["interval_high"] == pytest.approx(6.7)


def _metal_data(n=40000, seed=5):
    """Predicted metals whose chance of really being a non-metal grows with the classifier's probability."""
    rng = np.random.default_rng(seed)
    p = rng.uniform(0, 0.5, size=n)
    nonmetal = rng.uniform(size=n) < p * 0.8
    y = np.where(nonmetal, rng.uniform(0.5, 3.0, size=n), 0.0)
    return np.zeros(n), np.full(n, 0.1), y, p


def test_binned_p_widens_only_the_risky_predicted_metals():
    from ml.prediction.intervals import fit_binned_p, metal_sub_bin
    pred, sigma, y, p = _metal_data()
    spec = fit_binned_p(pred, sigma, y, level=0.9, p_nonmetal=p)
    widths = spec["metal_half_widths"]
    assert widths[0] == 0.0 and widths[-1] > 0.5          # the safe sub-bin stays tight, the risky one widens
    low, high = interval(spec, pred, sigma, p)
    covered = (y >= low) & (y <= high)
    sub = metal_sub_bin(p)
    for b in range(len(widths)):
        assert covered[sub == b].mean() >= 0.88            # every sub-bin keeps about the target coverage


def test_binned_p_needs_probabilities_to_fit_and_is_conservative_without_them():
    from ml.prediction.intervals import fit_binned_p
    pred, sigma, y, p = _metal_data(2000)
    with pytest.raises(ValueError, match="p_nonmetal"):
        fit_binned_p(pred, sigma, y)
    spec = fit_binned_p(pred, sigma, y, p_nonmetal=p)
    without = half_widths(spec, np.array([0.0]), None)[0]
    assert without == max(spec["metal_half_widths"])      # a model with no classifier gets the widest metal width


class _ClassifierStub(_StubModel):
    def predict_nonmetal_probability(self, X):
        return np.array([0.01, 0.4, 0.9])[: len(X)]


def test_predict_many_widens_a_predicted_metal_when_the_classifier_is_unsure(monkeypatch):
    from ml.prediction import predict as predict_module
    monkeypatch.setattr(predict_module, "forest_prediction_std", lambda forest, X: np.full(len(X), 0.2))
    spec = {"method": "binned_p", "level": 0.9, "edges": [0.0, 1.0, 2.0, 4.0], "p_edges": [0.05, 0.2, 0.35],
            "half_widths": [0.0, 1.0, 2.0, 3.0, 5.0], "metal_half_widths": [0.0, 0.0, 0.0, 0.6]}
    bundle = _bundle({"interval_calibration": {"spec": spec}})
    bundle["model"] = type("M", (), {"predict": lambda self, X: np.array([0.0, 0.0, 6.0])[: len(X)],
                                     "predict_nonmetal_probability": lambda self, X: np.array([0.01, 0.4, 0.9])[: len(X)]})()
    safe, unsure, wide = predict_module.predict_many(["NaCl", "MgO", "ZnS"], bundle)
    assert safe["interval_high"] == 0.05                      # safe predicted metal: only the display floor
    assert unsure["interval_high"] == pytest.approx(0.6)      # unsure predicted metal: widened
    assert wide["interval_high"] == pytest.approx(11.0)
