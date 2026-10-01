"""Train baseline models, compare them with grouped CV, and save the best bundle."""
import hashlib
import json
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ml.config import (DATA_PROCESSED, MODELS_SAVED, PROCESSED_FILE, RANDOM_SEED, TARGET,
                       TARGET_UNIT)
from ml.evaluation.error_analysis import error_analysis
from ml.evaluation.metrics import regression_metrics
from ml.prediction.uncertainty import forest_prediction_std
from ml.representation.composition_features import feature_names
from ml.representation.material_representation import chemical_system, featurize_many
from ml.training.cross_validation import grouped_cv_scores, grouped_train_test_split
from ml.training.hyperparameter_tuning import tune_random_forest

BUNDLE_NAME = "bundle.joblib"
METADATA_NAME = "metadata.json"


def baseline_models(rf_params=None):
    rf_params = rf_params or {"n_estimators": 300, "min_samples_leaf": 1, "max_features": 0.5}
    return {
        "mean_baseline": DummyRegressor(strategy="mean"),
        "ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "random_forest": RandomForestRegressor(random_state=RANDOM_SEED, n_jobs=-1, **rf_params),
        "gradient_boosting": GradientBoostingRegressor(random_state=RANDOM_SEED),
    }


def _file_sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def train(tune=False, processed_file=PROCESSED_FILE, out_dir=None):
    data_path = DATA_PROCESSED / processed_file
    df = pd.read_csv(data_path)
    formulas = df["formula"].tolist()
    y = df[TARGET].to_numpy(float)
    X = featurize_many(formulas).to_numpy()
    groups = np.array([chemical_system(f) for f in formulas])

    train_idx, test_idx = grouped_train_test_split(len(df), groups)
    X_tr, y_tr, g_tr = X[train_idx], y[train_idx], groups[train_idx]
    X_te, y_te = X[test_idx], y[test_idx]

    rf_params = None
    if tune:
        rf_params, _ = tune_random_forest(X_tr, y_tr, g_tr)

    results = {}
    for name, model in baseline_models(rf_params).items():
        cv_metrics, _ = grouped_cv_scores(model, X_tr, y_tr, g_tr)
        model.fit(X_tr, y_tr)
        results[name] = {
            "cv": cv_metrics,
            "test": regression_metrics(y_te, model.predict(X_te)),
        }

    candidates = {k: v for k, v in results.items() if k != "mean_baseline"}
    best_name = min(candidates, key=lambda k: candidates[k]["cv"]["mae"])
    models = baseline_models(rf_params)
    best_model = models[best_name].fit(X_tr, y_tr)
    rf = models["random_forest"].fit(X_tr, y_tr)  # always kept: uncertainty + importances

    best_test_pred = best_model.predict(X_te)
    analysis = error_analysis([formulas[i] for i in test_idx], y_te, best_test_pred)

    # Uncertainty bands: tree-spread terciles on the held-out set.
    test_std = forest_prediction_std(rf, X_te)
    thresholds = [float(np.quantile(test_std, 0.33)), float(np.quantile(test_std, 0.8))]
    corr = float(np.corrcoef(test_std, np.abs(rf.predict(X_te) - y_te))[0, 1])

    # Final deployed models are refit on ALL data; metrics above stay honest (held-out).
    final_best = baseline_models(rf_params)[best_name].fit(X, y)
    final_rf = baseline_models(rf_params)["random_forest"].fit(X, y)
    scaler = StandardScaler().fit(X)
    neighbors = NearestNeighbors(n_neighbors=5).fit(scaler.transform(X))

    version = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    metadata = {
        "version": version,
        "target": TARGET,
        "unit": TARGET_UNIT,
        "best_model": best_name,
        "rf_params": rf_params,
        "n_samples": int(len(df)),
        "n_train": int(len(train_idx)),
        "n_test": int(len(test_idx)),
        "dataset_file": processed_file,
        "dataset_sha256_16": _file_sha256(data_path),
        "data_source": sorted(df["source"].unique().tolist()) if "source" in df else ["unknown"],
        "split": "GroupShuffleSplit by chemical system",
        "results": results,
        "error_analysis": analysis,
        "uncertainty": {"std_thresholds": thresholds, "std_vs_abs_error_corr": corr},
        "feature_importance": dict(sorted(
            zip(feature_names(), map(float, rf.feature_importances_)), key=lambda kv: -kv[1])[:15]),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "metrics_note": "cv/test metrics come from models fit on the training split only; "
                        "the saved bundle is refit on all data.",
    }

    bundle = {
        "model": final_best,
        "forest": final_rf,
        "scaler": scaler,
        "neighbors": neighbors,
        "train_formulas": formulas,
        "train_targets": y,
        "feature_names": feature_names(),
        "feature_means": X.mean(axis=0),
        "feature_stds": X.std(axis=0) + 1e-9,
        "importances": final_rf.feature_importances_,
        "metadata": metadata,
    }
    out = out_dir or (MODELS_SAVED / TARGET)
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, out / BUNDLE_NAME)
    (out / METADATA_NAME).write_text(json.dumps(metadata, indent=2))
    return metadata
