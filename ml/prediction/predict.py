"""Prediction engine: validate -> featurize -> predict -> uncertainty -> format."""
from functools import lru_cache

import joblib
import numpy as np

from ml.config import MODELS_SAVED, TARGET, TARGET_UNIT
from ml.prediction.uncertainty import confidence_label, forest_prediction_std
from ml.representation.material_representation import InvalidMaterialError, featurize, parse_formula
from ml.training.train import BUNDLE_NAME


class ModelNotTrainedError(RuntimeError):
    pass


@lru_cache(maxsize=2)
def load_bundle(path=None):
    path = path or str(MODELS_SAVED / TARGET / BUNDLE_NAME)
    try:
        return joblib.load(path)
    except FileNotFoundError as exc:
        raise ModelNotTrainedError(f"no trained model at {path}; run `python ml/main.py train`") from exc


def predict_many(formulas, bundle=None):
    """One result dict per input formula; invalid inputs get {"error": ...} instead of raising."""
    bundle = bundle or load_bundle()
    thresholds = bundle["metadata"]["uncertainty"]["std_thresholds"]
    results, rows, index = [None] * len(formulas), [], []
    for i, formula in enumerate(formulas):
        try:
            comp = parse_formula(formula)
            rows.append(featurize(formula))
            index.append((i, comp.reduced_formula))
        except InvalidMaterialError as exc:
            results[i] = {"input": formula, "error": str(exc)}
    if rows:
        X = np.vstack(rows)
        values = np.clip(bundle["model"].predict(X), 0, None)
        stds = forest_prediction_std(bundle["forest"], X)
        conformal = bundle["metadata"].get("conformal")
        # Hurdle models also report P(non-metal). Their zero predictions come from this classifier,
        # which the regressor's tree spread does not describe, so an uncertain classifier lowers confidence.
        model = bundle["model"]
        p_nonmetal = (model.predict_nonmetal_probability(X) if hasattr(model, "predict_nonmetal_probability")
                      else [None] * len(values))
        for (i, reduced), value, std, p in zip(index, values, stds, p_nonmetal):
            confidence = confidence_label(std, thresholds)
            if p is not None and 0.3 < p < 0.7:
                confidence = "low"
            results[i] = {
                "input": formulas[i],
                "formula": reduced,
                "property": TARGET,
                "unit": TARGET_UNIT,
                "prediction": round(float(value), 4),
                "uncertainty": round(float(std), 4),
                "confidence": confidence,
                "model": bundle["metadata"]["best_model"],
                "model_version": bundle["metadata"]["version"],
            }
            if p is not None:
                results[i]["nonmetal_probability"] = round(float(p), 4)
            if conformal:
                half = conformal["half_width_eV"]
                results[i]["interval_low"] = round(max(0.0, float(value) - half), 4)
                results[i]["interval_high"] = round(float(value) + half, 4)
                results[i]["interval_level"] = conformal["level"]
    return results
