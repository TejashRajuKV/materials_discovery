"""External validation: the band-gap model against Materials Project PBE gaps (mp_3d.json).

Two different questions, reported separately:

1. Method agreement. For formulas in both JARVIS and Materials Project, how far do the OptB88vdW gaps
   (JARVIS) and the PBE gaps (Materials Project) differ? This is a property of the DFT methods, not of
   the model, and bounds what any model trained on JARVIS can achieve on PBE labels.
2. Generalisation. For formulas JARVIS never contained, how well does the model predict the PBE gap?
   Formulas in the training set are excluded, since the model has seen their JARVIS labels.

Materials Project entries sharing a formula are summarised by their median PBE gap, the same way
JARVIS entries are in the training table. The test file is streamed, so the 1.9 GB JSON never has to
fit in memory.
"""
import json
from statistics import median

import numpy as np

from ml.config import DATA_PROCESSED, DATA_RAW, EXPERIMENTS_DIR, TRAINING_FILE
from ml.evaluation.metrics import regression_metrics
from ml.preprocessing.cleaning import canonical_formula
from ml.validation.external import iter_json_array

MP_FILE = DATA_RAW / "mp_3d.json"
OUT_FILE = EXPERIMENTS_DIR / "external" / "mp_pbe_validation.json"
RANGES = [(0.0, 0.0, "metal(0)"), (0.0, 1.0, "0-1"), (1.0, 2.0, "1-2"), (2.0, 4.0, "2-4"), (4.0, np.inf, ">4")]


def mp_pbe_gaps(path=MP_FILE):
    """formula -> median PBE gap over its Materials Project entries (canonical formulas, finite gaps only)."""
    gaps = {}
    for record in iter_json_array(path):
        gap = record.get("gap pbe")
        formula = record.get("formula")
        if formula is None or gap is None or not np.isfinite(gap) or gap < 0:
            continue
        try:
            key = canonical_formula(formula)
        except Exception:
            key = None
        if key:
            gaps.setdefault(key, []).append(float(gap))
    return {formula: median(values) for formula, values in gaps.items()}


def _by_range(y, p):
    out = {}
    for low, high, name in RANGES:
        if name == "metal(0)":
            mask = y == 0
        else:
            mask = (y > low) & (y <= high)
        if mask.sum():
            out[name] = {"n": int(mask.sum()), "mae": round(float(np.mean(np.abs(y[mask] - p[mask]))), 4)}
    return out


def run_benchmark(mp_path=MP_FILE, out_path=OUT_FILE):
    import pandas as pd

    from ml.prediction.predict import load_bundle, predict_many

    mp = mp_pbe_gaps(mp_path)
    train = pd.read_csv(DATA_PROCESSED / TRAINING_FILE)
    jarvis = dict(zip(train["formula"], train["band_gap"].astype(float)))

    shared = sorted(set(mp) & set(jarvis))
    method = {"formulas": len(shared)}
    if shared:
        jv = np.array([jarvis[f] for f in shared])
        pb = np.array([mp[f] for f in shared])
        method.update({
            "mae_jarvis_vs_pbe": round(float(np.mean(np.abs(jv - pb))), 4),
            "mean_difference_jarvis_minus_pbe": round(float(np.mean(jv - pb)), 4),
            "pearson_r": round(float(np.corrcoef(jv, pb)[0, 1]), 4),
        })

    novel = sorted(set(mp) - set(jarvis))
    bundle = load_bundle()
    preds = predict_many(novel, bundle)
    rows = [(mp[p["formula"]], p) for p in preds if "error" not in p]
    y = np.array([r[0] for r in rows])
    p_val = np.array([r[1]["prediction"] for r in rows])
    lo = np.array([r[1]["interval_low"] for r in rows])
    hi = np.array([r[1]["interval_high"] for r in rows])
    generalisation = {
        "formulas": len(rows),
        "metrics": {k: round(float(v), 4) for k, v in regression_metrics(y, p_val).items() if k != "n"},
        "interval_coverage_90": round(float(np.mean((y >= lo) & (y <= hi))), 4),
        "by_gap_range": _by_range(y, p_val),
    }

    result = {
        "model_version": bundle["metadata"]["version"],
        "materials_project_formulas_with_gap": len(mp),
        "method_agreement_on_shared_formulas": method,
        "generalisation_to_novel_formulas": generalisation,
        "note": "PBE (Materials Project) labels, not OptB88vdW. Novel formulas are those absent from the JARVIS training set.",
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    return result
