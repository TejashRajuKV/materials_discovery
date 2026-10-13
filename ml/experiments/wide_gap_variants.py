"""Compare fixes for wide-gap shrinkage on the development sets (JARVIS test, held-out MP systems).

V0  random forest (current)                        baseline
V1  V0 + monotone calibration fitted on grouped out-of-fold predictions
V2  random forest with wide-gap rows up-weighted
V3  gradient boosting
V4  V3 + monotone calibration
OQMD is not touched here.
"""
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

from ml.config import DATA_PROCESSED, EXPERIMENTS_DIR, RANDOM_SEED, TRAINING_FILE
from ml.experiments.wide_gap import nonmetal, prepare, report
from ml.preprocessing.mp_augment import load_mp_gaps, mp_only_rows
from ml.representation.material_representation import chemical_system
from ml.training.cross_validation import grouped_train_test_split

OUT = EXPERIMENTS_DIR / "generalization" / "wide_gap_variants.json"


def train_groups():
    """Chemical systems for the nonmetal training rows, in the same order as `prepare()` produced them."""
    jarvis = pd.read_csv(DATA_PROCESSED / TRAINING_FILE, keep_default_na=False)
    mp_only, _ = mp_only_rows(jarvis, load_mp_gaps())
    j_tr, _ = grouped_train_test_split(len(jarvis), jarvis["formula"].map(chemical_system).to_numpy())
    m_tr, _ = next(GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=RANDOM_SEED)
                   .split(mp_only, groups=mp_only["system"]))
    return jarvis.iloc[j_tr]["formula"].map(chemical_system).to_numpy(), mp_only.iloc[m_tr]["system"].to_numpy()


def rf(**kw):
    return RandomForestRegressor(n_estimators=300, min_samples_leaf=5, max_features=0.5,
                                 random_state=RANDOM_SEED, n_jobs=-1, **kw)


def gb():
    return GradientBoostingRegressor(n_estimators=400, max_depth=5, learning_rate=0.05, subsample=0.8,
                                     random_state=RANDOM_SEED)


def oof_calibrator(make, X, y, groups):
    """Isotonic map from out-of-fold predictions to labels, fitted on training data only."""
    oof = np.zeros(len(y))
    for tr, va in GroupKFold(n_splits=5).split(X, y, groups):
        oof[va] = make().fit(X[tr], y[tr]).predict(X[va])
    return IsotonicRegression(out_of_bounds="clip").fit(oof, y)


def run(out_path=OUT):
    d = prepare()
    g_j, g_m = train_groups()
    keep_j, keep_m = d["y_jt"] > 0, d["y_mt"] > 0
    X = np.vstack([d["X_jt"][keep_j], d["X_mt"][keep_m]])
    y = np.concatenate([d["y_jt"][keep_j], d["y_mt"][keep_m]])
    groups = np.concatenate([g_j[keep_j], g_m[keep_m]])
    tests = {"jarvis_test": nonmetal(d["X_jv"], d["y_jv"]), "mp_heldout": nonmetal(d["X_mv"], d["y_mv"])}

    variants = {}
    base = rf().fit(X, y)
    variants["V0 rf"] = base.predict
    cal = oof_calibrator(rf, X, y, groups)
    variants["V1 rf+calibration"] = lambda Z: cal.predict(base.predict(Z))
    weighted = rf().fit(X, y, sample_weight=1.0 + 3.0 * (y > 3.0))
    variants["V2 rf weighted"] = weighted.predict
    boost = gb().fit(X, y)
    variants["V3 gb"] = boost.predict
    cal_gb = oof_calibrator(gb, X, y, groups)
    variants["V4 gb+calibration"] = lambda Z: cal_gb.predict(boost.predict(Z))

    rows = []
    for name, predict in variants.items():
        for tname, (Xt, yt) in tests.items():
            rows.append({"variant": name, **report(tname, yt, predict(Xt))})
            print(rows[-1], flush=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rows, indent=2))
    return rows


def dev_formulas():
    """Formulas for each development set, aligned with the arrays from `prepare()`."""
    jarvis = pd.read_csv(DATA_PROCESSED / TRAINING_FILE, keep_default_na=False)
    mp_only, _ = mp_only_rows(jarvis, load_mp_gaps())
    j_tr, j_te = grouped_train_test_split(len(jarvis), jarvis["formula"].map(chemical_system).to_numpy())
    m_tr, m_te = next(GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=RANDOM_SEED)
                      .split(mp_only, groups=mp_only["system"]))
    return {"jt": jarvis.iloc[j_tr]["formula"].to_numpy(), "jv": jarvis.iloc[j_te]["formula"].to_numpy(),
            "mt": mp_only.iloc[m_tr]["formula"].to_numpy(), "mv": mp_only.iloc[m_te]["formula"].to_numpy()}


def run_features(out_path=EXPERIMENTS_DIR / "generalization" / "wide_gap_features.json"):
    """V6: random forest with the extra chemistry features. V5: the same, with wide-gap rows up-weighted."""
    from ml.representation.chemistry_features import extra_matrix

    d, names = prepare(), dev_formulas()
    sets = {}
    for key in ("jt", "jv", "mt", "mv"):
        keep = d[f"y_{key}"] > 0
        extra = extra_matrix(list(names[key][keep]))
        sets[key] = (np.hstack([d[f"X_{key}"][keep], extra]), d[f"y_{key}"][keep])
    X = np.vstack([sets["jt"][0], sets["mt"][0]])
    y = np.concatenate([sets["jt"][1], sets["mt"][1]])

    models = {"V6 rf+features": rf().fit(X, y),
              "V5 rf weighted+features": rf().fit(X, y, sample_weight=1.0 + 3.0 * (y > 3.0))}
    rows = []
    for name, model in models.items():
        for tname, key in (("jarvis_test", "jv"), ("mp_heldout", "mv")):
            Xt, yt = sets[key]
            rows.append({"variant": name, **report(tname, yt, model.predict(Xt))})
            print(rows[-1], flush=True)
    out_path.write_text(json.dumps(rows, indent=2))
    return rows


def run_gated(threshold=3.5, out_path=EXPERIMENTS_DIR / "generalization" / "wide_gap_gated.json"):
    """V7: blend a wide-gap specialist into the base model in proportion to P(gap > threshold).

    prediction = base + p * (specialist - base), where base is the unweighted forest with the extra
    chemistry features, specialist is the same forest with wide-gap rows up-weighted, and p comes from a
    classifier. Low-gap compounds (p near 0) keep the base prediction.
    """
    from sklearn.ensemble import RandomForestClassifier

    from ml.representation.chemistry_features import extra_matrix

    d, names = prepare(), dev_formulas()
    sets = {}
    for key in ("jt", "jv", "mt", "mv"):
        keep = d[f"y_{key}"] > 0
        sets[key] = (np.hstack([d[f"X_{key}"][keep], extra_matrix(list(names[key][keep]))]), d[f"y_{key}"][keep])
    X = np.vstack([sets["jt"][0], sets["mt"][0]])
    y = np.concatenate([sets["jt"][1], sets["mt"][1]])

    base = rf().fit(X, y)
    specialist = rf().fit(X, y, sample_weight=1.0 + 3.0 * (y > 3.0))
    gate = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, max_features=0.5,
                                  random_state=RANDOM_SEED, n_jobs=-1).fit(X, (y > threshold).astype(int))

    def predict(Z):
        p = gate.predict_proba(Z)[:, 1]
        b = base.predict(Z)
        return b + p * (specialist.predict(Z) - b)

    rows = []
    for tname, key in (("jarvis_test", "jv"), ("mp_heldout", "mv")):
        Xt, yt = sets[key]
        rows.append({"variant": f"V7 gated (>{threshold})", **report(tname, yt, predict(Xt))})
        print(rows[-1], flush=True)
    out_path.write_text(json.dumps(rows, indent=2))
    return rows
