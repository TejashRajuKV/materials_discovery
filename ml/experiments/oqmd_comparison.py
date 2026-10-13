"""Compare band-gap models on OQMD formulas none of them has seen, with artefact labels removed.

Scored on the unseen OQMD non-metals (formulas absent from JARVIS and Materials Project, median OQMD gap > 0),
both as given and with the implausible labels (all-metal compounds reported with gaps above 2 eV) removed.

  jarvis_only   hurdle model trained on every JARVIS formula, nothing else (63 features)
  previous      the saved model from before the wide-gap work: JARVIS + Materials Project labels (63 features),
                loaded from ml/models/backup/20261010-095533/
  current       the deployed model: the same data, a wide-gap blend, and 71 features
"""
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from ml.config import DATA_PROCESSED, EXPERIMENTS_DIR, MODELS_SAVED, RANDOM_SEED, ROOT, TARGET, TRAINING_FILE
from ml.evaluation.metrics import regression_metrics
from ml.models.hurdle import HurdleRegressor
from ml.representation.material_representation import featurize_many
from ml.validation.external_benchmark import _by_range
from ml.validation.label_quality import implausible_label
from ml.validation.oqmd_benchmark import load_oqmd_gaps, unseen_formulas
from ml.training.train import BUNDLE_NAME

OUT = EXPERIMENTS_DIR / "generalization" / "oqmd_comparison.json"
PREVIOUS = ROOT / "ml" / "models" / "backup" / "20261010-095533" / BUNDLE_NAME
RF = {"n_estimators": 300, "min_samples_leaf": 5, "max_features": 0.5}
BASE_FEATURES = 63


def _score(y, pred):
    return {
        "metrics": {k: round(float(v), 4) for k, v in regression_metrics(y, pred).items() if k != "n"},
        "by_gap_range": _by_range(y, pred),
    }


def run(out_path=OUT):
    oqmd = load_oqmd_gaps()
    formulas = [f for f in unseen_formulas(oqmd) if oqmd[f] > 0]
    y = np.array([oqmd[f] for f in formulas])
    X71 = featurize_many(formulas, extended=True).to_numpy()
    X63 = X71[:, :BASE_FEATURES]  # the extended features append to the base ones
    artefact = np.array([implausible_label(f, g) for f, g in zip(formulas, y)])
    clean = ~artefact

    jarvis = pd.read_csv(DATA_PROCESSED / TRAINING_FILE, keep_default_na=False)
    jarvis_only = HurdleRegressor(
        classifier=RandomForestClassifier(random_state=RANDOM_SEED, n_jobs=-1, **RF),
        regressor=RandomForestRegressor(random_state=RANDOM_SEED, n_jobs=-1, **RF),
    ).fit(featurize_many(jarvis["formula"].tolist()).to_numpy(), jarvis[TARGET].to_numpy(float))
    previous = joblib.load(PREVIOUS)["model"]
    current = joblib.load(MODELS_SAVED / TARGET / BUNDLE_NAME)["model"]

    predictions = {"jarvis_only": jarvis_only.predict(X63), "previous": previous.predict(X63),
                   "current": current.predict(X71)}
    result = {"unseen_nonmetal_formulas": int(len(y)), "artefact_labels_removed": int(artefact.sum())}
    for name, pred in predictions.items():
        result[name] = {"as_given": _score(y, pred), "without_artefacts": _score(y[clean], pred[clean])}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    return result
