"""Recalibrate the prediction intervals on data the deployed model never trained on.

The deployed intervals come from out-of-fold residuals on the JARVIS/Materials Project training data: constant
width, 90% target, 0.93 coverage on the JARVIS test split but only 0.81 on unseen OQMD chemistry. OQMD is the
one source the model has not seen, so its residuals are honest, and they include the variation between DFT
codes that JARVIS-only calibration misses.

Protocol: unseen OQMD formulas (absent from JARVIS and Materials Project), implausible labels removed, are split
by chemical system into a calibration half and a test half. Methods are fitted on the calibration half only and
scored on the test half. Metals are 94% of the unseen formulas, so a random sample of them is used and weighted
back to their true share.

  constant   one half-width for everything
  binned     a half-width per predicted-gap bin (Mondrian conformal)
  scaled     half-width proportional to the forest's per-material spread (normalised conformal)
"""
import json

import numpy as np
from sklearn.model_selection import GroupShuffleSplit

from ml.config import DATA_PROCESSED, EXPERIMENTS_DIR, MODELS_SAVED, RANDOM_SEED, TARGET
from ml.prediction.uncertainty import forest_prediction_std
from ml.representation.material_representation import chemical_system, featurize_many
from ml.training.train import BUNDLE_NAME
from ml.validation.label_quality import implausible_label
from ml.validation.oqmd_benchmark import load_oqmd_gaps, unseen_formulas

CACHE = DATA_PROCESSED / "features" / "interval_calibration.npz"
OUT = EXPERIMENTS_DIR / "generalization" / "interval_calibration.json"
METAL_SAMPLE = 40_000
BIN_EDGES = [0.0, 1.0, 2.0, 4.0]  # predicted gap; predictions of exactly 0 form their own bin
SIGMA_FLOOR = 0.05


def prepare():
    """Predictions of the deployed model on cleaned unseen OQMD formulas, cached on disk."""
    version = json.loads((MODELS_SAVED / TARGET / "metadata.json").read_text())["version"]
    if CACHE.exists():
        z = np.load(CACHE, allow_pickle=True)
        # A cache with no recorded version, or another model's, would mis-calibrate this model: rebuild it.
        if "model_version" in z.files and "p_nonmetal" in z.files and str(z["model_version"]) == version:
            return {k: z[k] for k in z.files}
    import joblib

    oqmd = load_oqmd_gaps()
    unseen = unseen_formulas(oqmd)
    nonmetals = [f for f in unseen if oqmd[f] > 0 and not implausible_label(f, oqmd[f])]
    metals = [f for f in unseen if oqmd[f] == 0]
    rng = np.random.default_rng(RANDOM_SEED)
    sampled = list(rng.choice(metals, size=min(METAL_SAMPLE, len(metals)), replace=False))
    formulas = nonmetals + sampled
    weight = np.array([1.0] * len(nonmetals) + [len(metals) / len(sampled)] * len(sampled))

    bundle = joblib.load(MODELS_SAVED / TARGET / BUNDLE_NAME)
    X = featurize_many(formulas, extended=bundle["metadata"].get("extended_features", False)).to_numpy()
    pred = np.clip(bundle["model"].predict(X), 0, None)
    out = {
        "formulas": np.array(formulas), "y": np.array([oqmd[f] for f in formulas]), "pred": pred,
        "sigma": forest_prediction_std(bundle["forest"], X), "weight": weight,
        "system": np.array([chemical_system(f) for f in formulas]),
        "model_version": np.array(version),
        # P(non-metal) from the hurdle's classifier; a prediction of 0 is only as safe as this is small.
        "p_nonmetal": bundle["model"].predict_nonmetal_probability(X),
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, **out)
    return out


BIN_LABELS = ["predicted 0", "(0,1]", "(1,2]", "(2,4]", ">4"]
RANGES = [("metals (true gap 0)", lambda y: y == 0), ("0-1", lambda y: (y > 0) & (y <= 1)),
          ("1-2", lambda y: (y > 1) & (y <= 2)), ("2-4", lambda y: (y > 2) & (y <= 4)), (">4", lambda y: y > 4)]


def _wmean(values, weights):
    return float(np.sum(values * weights) / np.sum(weights))


def evaluate(spec, d, test, level=0.9):
    """Weighted coverage and width on the test rows: overall, non-metals, and by true gap range."""
    from ml.prediction.intervals import interval

    y, pred, sigma, w = d["y"][test], d["pred"][test], d["sigma"][test], d["weight"][test]
    p = d["p_nonmetal"][test]
    low, high = interval(spec, pred, sigma, p)
    covered = ((y >= low) & (y <= high)).astype(float)
    width = high - low
    nm = y > 0
    out = {"coverage": _wmean(covered, w), "width": _wmean(width, w),
           "nonmetal_coverage": _wmean(covered[nm], w[nm]), "nonmetal_width": _wmean(width[nm], w[nm])}
    for name, mask_fn in RANGES:
        m = mask_fn(y)
        out[f"cov {name}"] = _wmean(covered[m], w[m]) if m.any() else float("nan")
    # What a user sees is the predicted gap, so also report coverage and width within each predicted bin.
    from ml.prediction.intervals import bin_index
    idx = bin_index(pred)
    for b, label in enumerate(BIN_LABELS):
        m = idx == b
        out[f"pred {label} cov"] = _wmean(covered[m], w[m]) if m.any() else float("nan")
        out[f"pred {label} width"] = _wmean(width[m], w[m]) if m.any() else float("nan")
        out[f"pred {label} share"] = float(w[m].sum() / w.sum())
    # Predicted metals, split by the classifier's P(non-metal): the safest to the riskiest.
    from ml.prediction.intervals import P_EDGES, metal_sub_bin
    zero, sub = idx == 0, metal_sub_bin(p)
    for b in range(len(P_EDGES) + 1):
        m = zero & (sub == b)
        out[f"metal sub{b} cov"] = _wmean(covered[m], w[m]) if m.any() else float("nan")
        out[f"metal sub{b} width"] = _wmean(width[m], w[m]) if m.any() else float("nan")
    return out


def fit_method(name, fit, d, rows, level):
    """Fit one method on the given rows, passing the classifier probability to the methods that use it."""
    extra = {"p_nonmetal": d["p_nonmetal"][rows]} if name == "binned_p" else {}
    return fit(d["pred"][rows], d["sigma"][rows], d["y"][rows], level, d["weight"][rows], **extra)


def run(out_path=OUT, seeds=(0, 1, 2, 3, 4), level=0.9):
    from ml.prediction.intervals import METHODS

    d = prepare()
    deployed = json.loads((MODELS_SAVED / TARGET / "metadata.json").read_text())["conformal"]
    rows = {}
    for seed in seeds:
        cal, test = next(GroupShuffleSplit(n_splits=1, test_size=0.5, random_state=seed).split(d["y"], groups=d["system"]))
        specs = {"deployed (JARVIS-calibrated, constant)": {"method": "constant", "level": level,
                                                            "half_width": deployed["half_width_eV"]}}
        for name, fit in METHODS.items():
            specs[name] = fit_method(name, fit, d, cal, level)
        for name, spec in specs.items():
            rows.setdefault(name, []).append(evaluate(spec, d, test, level))
    summary = {name: {k: round(float(np.nanmean([r[k] for r in runs])), 3) for k in runs[0]} for name, runs in rows.items()}
    spread = {name: round(float(np.std([r["coverage"] for r in runs])), 3) for name, runs in rows.items()}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"summary": summary, "coverage_std_over_splits": spread}, indent=2))
    return summary, spread


def apply(method="binned", level=0.9):
    """Fit `method` on all cleaned unseen OQMD rows and store it with the deployed model (metadata.json and the
    bundle), with its provenance and the held-out check. No retraining. Predictions then use these intervals."""
    import joblib
    from datetime import datetime, timezone

    from ml.prediction.intervals import METHODS

    d = prepare()
    spec = fit_method(method, METHODS[method], d, np.arange(len(d["y"])), level)
    summary, _ = run()
    held_out = {k: v for k, v in summary[method].items() if k.startswith("pred ") and k.endswith(" cov")}
    calibration = {
        "spec": spec,
        "source": "OQMD formulas absent from JARVIS and Materials Project, implausible labels removed",
        "calibration_rows": int(len(d["y"])),
        "calibration_weight": round(float(d["weight"].sum())),
        "held_out_coverage_by_predicted_bin": {k[5:-4]: round(v, 3) for k, v in held_out.items()},
        "held_out_note": "mean over 5 chemical-system splits, calibrated on one half and scored on the other",
        "calibrated_at": datetime.now(timezone.utc).isoformat(),
    }
    directory = MODELS_SAVED / TARGET
    meta_path = directory / "metadata.json"
    metadata = json.loads(meta_path.read_text())
    metadata["interval_calibration"] = calibration
    meta_path.write_text(json.dumps(metadata, indent=2))
    bundle = joblib.load(directory / BUNDLE_NAME)
    bundle["metadata"]["interval_calibration"] = calibration
    joblib.dump(bundle, directory / BUNDLE_NAME)
    return calibration
