"""Models for the properties besides band gap: formation energy and bulk modulus.

Same recipe as the band-gap model (composition features, chemical-system grouped split, grouped CV
for model selection, split-conformal intervals), with smaller forests: minimum leaf size 8 and 150
trees, which keeps the bundles at about 180 MB (formation energy) and 70 MB (bulk modulus). The
band-gap bundle is over 1 GB, so discovery loads only the properties the spec asks for. Each property
has its own bundle under ml/models/saved/<property>/.
"""
import json
from datetime import datetime, timezone
from functools import lru_cache

import joblib
import numpy as np
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ml.config import MODELS_SAVED, RANDOM_SEED
from ml.evaluation.metrics import regression_metrics
from ml.preprocessing.jarvis import PROPERTY_FIELDS, build_property_table
from ml.prediction.uncertainty import confidence_label, forest_prediction_std
from ml.representation.composition_features import feature_names
from ml.representation.material_representation import (InvalidMaterialError, chemical_system, featurize,
                                                       featurize_many, parse_formula)
from ml.training.cross_validation import grouped_cv_scores, grouped_train_test_split
from ml.training.train import BUNDLE_NAME, CONFORMAL_LEVEL, METADATA_NAME, conformal_half_width

PROPERTY_RF_PARAMS = {"n_estimators": 150, "min_samples_leaf": 8, "max_features": 0.5}


def property_models():
    return {
        "mean_baseline": DummyRegressor(strategy="mean"),
        "ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "random_forest": RandomForestRegressor(random_state=RANDOM_SEED, n_jobs=-1, **PROPERTY_RF_PARAMS),
    }


def property_dir(prop):
    return MODELS_SAVED / prop


def train_property(prop, out_dir=None):
    unit = PROPERTY_FIELDS[prop]["unit"]
    table = build_property_table(prop)
    formulas = table["formula"].tolist()
    y = table["value"].to_numpy(float)
    X = featurize_many(formulas).to_numpy()
    groups = np.array([chemical_system(f) for f in formulas])

    train_idx, test_idx = grouped_train_test_split(len(table), groups)
    X_tr, y_tr, g_tr = X[train_idx], y[train_idx], groups[train_idx]
    X_te, y_te = X[test_idx], y[test_idx]

    results, oof = {}, {}
    for name, model in property_models().items():
        cv_metrics, oof[name] = grouped_cv_scores(model, X_tr, y_tr, g_tr)
        model.fit(X_tr, y_tr)
        results[name] = {"cv": cv_metrics, "test": regression_metrics(y_te, model.predict(X_te))}

    candidates = {k: v for k, v in results.items() if k != "mean_baseline"}
    best_name = min(candidates, key=lambda k: candidates[k]["cv"]["mae"])
    best_model = property_models()[best_name].fit(X_tr, y_tr)
    forest_tr = property_models()["random_forest"].fit(X_tr, y_tr)

    best_test_pred = best_model.predict(X_te)
    half_width = conformal_half_width(y_tr, oof[best_name], CONFORMAL_LEVEL)
    test_std = forest_prediction_std(forest_tr, X_te)
    thresholds = [float(np.quantile(test_std, 0.33)), float(np.quantile(test_std, 0.8))]

    # Deployed models are refit on every formula; the metrics above come from the training split only.
    final_best = property_models()[best_name].fit(X, y)
    final_forest = property_models()["random_forest"].fit(X, y)

    metadata = {
        "property": prop,
        "unit": unit,
        "version": datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
        "best_model": best_name,
        "rf_params": PROPERTY_RF_PARAMS,
        "n_samples": int(len(table)),
        "n_train": int(len(train_idx)),
        "n_test": int(len(test_idx)),
        "data_source": "JARVIS dft_3d (most stable entry per formula)",
        "split": "GroupShuffleSplit by chemical system",
        "results": results,
        "uncertainty": {"std_thresholds": thresholds},
        "conformal": {
            "level": CONFORMAL_LEVEL,
            "half_width": round(half_width, 4),
            "unit": unit,
            "calibration": "out-of-fold residuals of the selected model on the training split",
            "test_coverage": round(float(np.mean(np.abs(y_te - best_test_pred) <= half_width)), 4),
        },
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    bundle = {
        "model": final_best,
        "forest": final_forest,
        "feature_names": feature_names(),
        "metadata": metadata,
    }
    out = out_dir or property_dir(prop)
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, out / BUNDLE_NAME)
    (out / METADATA_NAME).write_text(json.dumps(metadata, indent=2))
    return metadata


@lru_cache(maxsize=4)
def load_property_bundle(prop):
    path = property_dir(prop) / BUNDLE_NAME
    if not path.exists():
        raise FileNotFoundError(f"no {prop} model at {path}; run `python ml/main.py train-property --property {prop}`")
    return joblib.load(path)


def predict_property_many(prop, formulas):
    """One dict per input formula, in the same shape as the band-gap predictions."""
    bundle = load_property_bundle(prop)
    meta = bundle["metadata"]
    results = [None] * len(formulas)
    rows, index = [], []
    for i, formula in enumerate(formulas):
        try:
            reduced = parse_formula(formula).reduced_formula
            rows.append(featurize(formula))
            index.append((i, reduced))
        except InvalidMaterialError as exc:
            results[i] = {"input": formula, "error": str(exc)}
    if rows:
        X = np.vstack(rows)
        values = bundle["model"].predict(X)
        stds = forest_prediction_std(bundle["forest"], X)
        half = meta["conformal"]["half_width"]
        for (i, reduced), value, std in zip(index, values, stds):
            results[i] = {
                "input": formulas[i],
                "formula": reduced,
                "property": prop,
                "unit": meta["unit"],
                "prediction": round(float(value), 4),
                "uncertainty": round(float(std), 4),
                "confidence": confidence_label(std, meta["uncertainty"]["std_thresholds"]),
                "interval_low": round(float(value) - half, 4),
                "interval_high": round(float(value) + half, 4),
                "interval_level": meta["conformal"]["level"],
                "model": meta["best_model"],
                "model_version": meta["version"],
            }
    return results


PROPERTY_NAMES = tuple(PROPERTY_FIELDS)
