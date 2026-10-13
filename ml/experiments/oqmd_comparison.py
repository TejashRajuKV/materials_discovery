"""Does the Materials Project augmentation help on a source the model never saw?

Both models are hurdle models with the production settings, scored on the same OQMD formulas, which are
absent from JARVIS and Materials Project:

  jarvis_only  trained on every JARVIS formula, nothing else
  deployed     the saved band-gap model: JARVIS plus the Materials Project formulas JARVIS lacks

Most unseen OQMD formulas are metals (zero gap), which any model finds easy, so non-metals are scored
separately. Point predictions only; intervals are reported by the benchmark in ml/validation.
"""
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from ml.config import DATA_PROCESSED, EXPERIMENTS_DIR, RANDOM_SEED, TRAINING_FILE
from ml.evaluation.metrics import regression_metrics
from ml.models.hurdle import HurdleRegressor
from ml.representation.material_representation import featurize_many
from ml.validation.external_benchmark import _by_range
from ml.validation.oqmd_benchmark import load_oqmd_gaps, unseen_formulas

OUT = EXPERIMENTS_DIR / "generalization" / "oqmd_comparison.json"
RF = {"n_estimators": 300, "min_samples_leaf": 5, "max_features": 0.5}


def _score(y, pred):
    nm = y > 0
    return {
        "all": {k: round(float(v), 4) for k, v in regression_metrics(y, pred).items() if k != "n"},
        "nonmetals": {k: round(float(v), 4) for k, v in regression_metrics(y[nm], pred[nm]).items() if k != "n"},
        "nonmetals_by_gap_range": _by_range(y[nm], pred[nm]),
    }


def run(out_path=OUT):
    from ml.prediction.predict import load_bundle

    oqmd = load_oqmd_gaps()
    formulas = unseen_formulas(oqmd)
    valid, rows = [], []
    for start in range(0, len(formulas), 50_000):  # featurise in chunks, skipping any unparseable formula
        chunk = formulas[start:start + 50_000]
        try:
            rows.append(featurize_many(chunk).to_numpy())
            valid += chunk
        except Exception:
            for f in chunk:
                try:
                    rows.append(featurize_many([f]).to_numpy())
                    valid.append(f)
                except Exception:
                    pass
    X = np.vstack(rows)
    y = np.array([oqmd[f] for f in valid])

    jarvis = pd.read_csv(DATA_PROCESSED / TRAINING_FILE, keep_default_na=False)
    baseline = HurdleRegressor(
        classifier=RandomForestClassifier(random_state=RANDOM_SEED, n_jobs=-1, **RF),
        regressor=RandomForestRegressor(random_state=RANDOM_SEED, n_jobs=-1, **RF),
    ).fit(featurize_many(jarvis["formula"].tolist()).to_numpy(), jarvis["band_gap"].to_numpy(float))

    deployed = load_bundle()["model"]
    result = {
        "unseen_formulas": int(len(y)),
        "nonmetal_formulas": int((y > 0).sum()),
        "jarvis_only": _score(y, baseline.predict(X)),
        "deployed": _score(y, deployed.predict(X)),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    return result
