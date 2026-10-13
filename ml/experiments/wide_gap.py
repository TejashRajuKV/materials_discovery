"""Why are wide-gap (> 4 eV) predictions poor, and what helps?

Development protocol. Variants are compared only on two sets the model does not train on:
  - the JARVIS grouped test split, and
  - Materials Project chemical systems held out whole (labels harmonised to the JARVIS scale).
OQMD is deliberately not used here, so that it remains an independent check of whatever is chosen.

Only the non-metal regressor stage of the hurdle model is varied; metals are handled by the classifier and
are unaffected. So training and scoring use non-metals (label > 0).
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from ml.config import DATA_PROCESSED, RANDOM_SEED, TRAINING_FILE
from ml.preprocessing.mp_augment import load_mp_gaps, mp_only_rows
from ml.representation.material_representation import chemical_system, featurize_many
from ml.training.cross_validation import grouped_train_test_split

CACHE = DATA_PROCESSED / "features" / "wide_gap_dev.npz"
BINS = [(0.0, 1.0, "0-1"), (1.0, 2.0, "1-2"), (2.0, 4.0, "2-4"), (4.0, np.inf, ">4")]


def prepare():
    """Feature arrays for the development split, cached on disk (featurising 90k formulas takes minutes)."""
    if CACHE.exists():
        z = np.load(CACHE, allow_pickle=False)
        return {k: z[k] for k in z.files}
    jarvis = pd.read_csv(DATA_PROCESSED / TRAINING_FILE, keep_default_na=False)
    mp_only, _ = mp_only_rows(jarvis, load_mp_gaps())
    j_tr, j_te = grouped_train_test_split(len(jarvis), jarvis["formula"].map(chemical_system).to_numpy())
    split = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=RANDOM_SEED)
    m_tr, m_te = next(split.split(mp_only, groups=mp_only["system"]))
    parts = {
        "jt": jarvis.iloc[j_tr], "jv": jarvis.iloc[j_te],
        "mt": mp_only.iloc[m_tr], "mv": mp_only.iloc[m_te],
    }
    out = {}
    for name, df in parts.items():
        out[f"X_{name}"] = featurize_many(df["formula"].tolist()).to_numpy()
        out[f"y_{name}"] = df["band_gap" if name in ("jt", "jv") else "label"].to_numpy(float)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, **out)
    return out


def nonmetal(X, y):
    keep = y > 0
    return X[keep], y[keep]


def report(name, y, pred):
    """MAE overall and per range, plus mean signed error (pred - y) for the widest range."""
    row = {"set": name, "n": int(len(y)), "mae": round(float(np.mean(np.abs(y - pred))), 3)}
    for low, high, label in BINS:
        mask = (y > low) & (y <= high)
        if mask.any():
            row[f"mae {label}"] = round(float(np.mean(np.abs(y[mask] - pred[mask]))), 3)
    wide = y > 4
    if wide.any():
        row["bias >4"] = round(float(np.mean(pred[wide] - y[wide])), 3)
        row["max pred"] = round(float(pred.max()), 2)
    return row
