"""Does adding Materials Project PBE labels improve generalisation to unseen chemistry?

Protocol (chemical systems are held out whole, so no element set is seen in both train and test):

  1. Materials Project formulas that JARVIS does not contain ("MP-only") get their PBE gap mapped onto
     the JARVIS OptB88vdW scale by a linear fit on the formulas both sources share.
  2. MP-only chemical systems are split 75/25. The 25% are the test set.
  3. Two hurdle models with the production settings are compared, both scored on the same MP test
     set against the raw PBE labels, and on the JARVIS grouped test split:
       baseline   trained on the JARVIS training split
       augmented  trained on the JARVIS training split plus the MP training split (harmonised labels)

The question is whether the augmented model predicts unseen chemistry better without losing accuracy on
JARVIS. A gain on the MP test set and no loss on JARVIS is the outcome that would justify using the data.
"""
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import GroupShuffleSplit

from ml.config import DATA_PROCESSED, EXPERIMENTS_DIR, RANDOM_SEED, TRAINING_FILE
from ml.evaluation.metrics import regression_metrics
from ml.models.hurdle import HurdleRegressor
from ml.representation.material_representation import chemical_system, featurize_many
from ml.training.cross_validation import grouped_train_test_split
from ml.validation.external_benchmark import mp_pbe_gaps

MP_CACHE = DATA_PROCESSED / "mp_pbe_gaps.csv"
OUT = EXPERIMENTS_DIR / "generalization" / "mp_augmentation.json"
RF = {"n_estimators": 300, "min_samples_leaf": 5, "max_features": 0.5}


def load_mp_gaps():
    if not MP_CACHE.exists():
        gaps = mp_pbe_gaps()
        pd.DataFrame({"formula": list(gaps), "pbe_gap": list(gaps.values())}).to_csv(MP_CACHE, index=False)
    return pd.read_csv(MP_CACHE)


def hurdle():
    return HurdleRegressor(
        classifier=RandomForestClassifier(random_state=RANDOM_SEED, n_jobs=-1, **RF),
        regressor=RandomForestRegressor(random_state=RANDOM_SEED, n_jobs=-1, **RF),
    )


def run(out_path=OUT):
    jarvis = pd.read_csv(DATA_PROCESSED / TRAINING_FILE)
    mp = load_mp_gaps()
    shared = mp.merge(jarvis[["formula", "band_gap"]], on="formula")
    slope, intercept = np.polyfit(shared["pbe_gap"], shared["band_gap"], 1)

    mp_only = mp[~mp["formula"].isin(jarvis["formula"])].reset_index(drop=True)
    mp_only["label"] = np.clip(slope * mp_only["pbe_gap"] + intercept, 0.0, None)
    mp_only["system"] = [chemical_system(f) for f in mp_only["formula"]]
    split = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=RANDOM_SEED)
    mp_tr, mp_te = next(split.split(mp_only, groups=mp_only["system"]))
    mp_train, mp_test = mp_only.iloc[mp_tr], mp_only.iloc[mp_te]

    j_tr, j_te = grouped_train_test_split(len(jarvis), jarvis["formula"].map(chemical_system).to_numpy())
    jt, jv = jarvis.iloc[j_tr], jarvis.iloc[j_te]

    X_jt = featurize_many(jt["formula"].tolist()).to_numpy()
    y_jt = jt["band_gap"].to_numpy(float)
    X_mp = featurize_many(mp_train["formula"].tolist()).to_numpy()
    y_mp = mp_train["label"].to_numpy(float)
    X_jv = featurize_many(jv["formula"].tolist()).to_numpy()
    X_mt = featurize_many(mp_test["formula"].tolist()).to_numpy()

    results = {}
    for name, (X, y) in {"baseline": (X_jt, y_jt),
                         "augmented": (np.vstack([X_jt, X_mp]), np.concatenate([y_jt, y_mp]))}.items():
        model = hurdle().fit(X, y)
        results[name] = {
            "mp_test_vs_pbe": regression_metrics(mp_test["pbe_gap"].to_numpy(float), model.predict(X_mt)),
            "jarvis_test": regression_metrics(jv["band_gap"].to_numpy(float), model.predict(X_jv)),
        }
        print(name, {k: round(v["mae"], 3) for k, v in results[name].items()}, flush=True)

    summary = {
        "harmonisation": {"slope": round(float(slope), 4), "intercept": round(float(intercept), 4),
                          "shared_formulas": int(len(shared))},
        "sizes": {"jarvis_train": int(len(jt)), "jarvis_test": int(len(jv)),
                  "mp_only_train": int(len(mp_train)), "mp_only_test": int(len(mp_test))},
        "results": results,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2))
    return summary
