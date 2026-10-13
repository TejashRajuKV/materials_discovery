"""Does structure information help predict band gaps, especially wide ones?

Entry-level ablation. For every formula the most stable JARVIS entry is used, with that entry's own
OptB88vdW gap as the label, so composition and structure describe the same crystal. Non-metals only (the
metal/non-metal decision is a separate stage of the deployed model). Two random forests with identical
settings are compared:

  composition   the 71 composition features (63 statistics + 8 chemistry features)
  structure     those plus 17 structure descriptors (ml/representation/structure_features.py)

Scored on the JARVIS grouped test split, and once on OQMD formulas absent from JARVIS and Materials Project
(the most stable OQMD entry of each, with its own structure and gap), which neither model has seen.
"""
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from ml.config import DATA_PROCESSED, EXPERIMENTS_DIR, JARVIS_BANDGAP_METHOD, JARVIS_TARGETS_FILE, RANDOM_SEED
from ml.experiments.wide_gap import report
from ml.representation.material_representation import chemical_system, featurize_many
from ml.representation.structure_features import STRUCTURE_NAMES, build_structure, structure_vector
from ml.training.cross_validation import grouped_train_test_split
from ml.validation.external import iter_json_array
from ml.validation.oqmd_benchmark import OQMD_FILE, load_oqmd_gaps, unseen_formulas

STRUCTURES = DATA_PROCESSED / "structures"
CACHE = DATA_PROCESSED / "features" / "structure_ablation.npz"
OUT = EXPERIMENTS_DIR / "generalization" / "structure_ablation.json"
RF = {"n_estimators": 300, "min_samples_leaf": 5, "max_features": 0.5}


def jarvis_entries():
    """formula, jid, gap of each formula's most stable entry, for non-metals with a structure file."""
    stable = pd.read_csv(DATA_PROCESSED / "stability.csv", keep_default_na=False)[["formula", "jid"]]
    targets = pd.read_csv(JARVIS_TARGETS_FILE, dtype={"jid": str}, keep_default_na=False)
    targets = targets[(targets["property"] == "band_gap") & (targets["method"] == JARVIS_BANDGAP_METHOD)]
    table = stable.merge(targets[["jid", "value"]].rename(columns={"value": "gap"}), on="jid")
    table["gap"] = table["gap"].astype(float)
    table = table[table["gap"] > 0]
    return table[[(STRUCTURES / f"{j}.json").exists() for j in table["jid"]]].reset_index(drop=True)


def jarvis_structure_features(table):
    rows = []
    for jid in table["jid"]:
        rec = json.loads((STRUCTURES / f"{jid}.json").read_text())
        rows.append(structure_vector(build_structure(rec["lattice_mat"], rec["coords"], rec["elements"], rec.get("cartesian"))))
    return np.vstack(rows)


def oqmd_entries():
    """Most stable OQMD entry of each unseen non-metal formula: (formulas, gaps, structure features)."""
    oqmd = load_oqmd_gaps()
    wanted = {f for f in unseen_formulas(oqmd) if oqmd[f] > 0}
    from collections import Counter
    from pymatgen.core import Composition
    best = {}
    for rec in iter_json_array(OQMD_FILE):
        elements = (rec.get("atoms") or {}).get("elements")
        gap = rec.get("_oqmd_band_gap")
        if elements is None or gap is None or gap <= 0:
            continue
        try:
            formula = Composition(dict(Counter(e.strip() for e in elements))).reduced_formula
        except Exception:
            continue
        stability = rec.get("_oqmd_stability")
        if formula in wanted and stability is not None and (formula not in best or stability < best[formula][0]):
            best[formula] = (stability, float(gap), rec["atoms"])
    formulas = sorted(best)
    feats, keep = [], []
    for f in formulas:
        a = best[f][2]
        try:
            feats.append(structure_vector(build_structure(a["lattice_mat"], a["coords"], a["elements"], a.get("cartesian"))))
            keep.append(f)
        except Exception:
            pass
    return keep, np.array([best[f][1] for f in keep]), np.vstack(feats)


def prepare():
    if CACHE.exists():
        z = np.load(CACHE, allow_pickle=True)
        return {k: z[k] for k in z.files}
    table = jarvis_entries()
    data = {"j_formulas": table["formula"].to_numpy(), "j_gap": table["gap"].to_numpy(float),
            "j_struct": jarvis_structure_features(table)}
    print("jarvis structure features", data["j_struct"].shape, flush=True)
    data["j_comp"] = featurize_many(list(data["j_formulas"]), extended=True).to_numpy()
    o_formulas, o_gap, o_struct = oqmd_entries()
    data.update({"o_formulas": np.array(o_formulas), "o_gap": o_gap, "o_struct": o_struct,
                 "o_comp": featurize_many(o_formulas, extended=True).to_numpy()})
    print("oqmd entries", len(o_formulas), flush=True)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, **data)
    return data


def rf():
    return RandomForestRegressor(random_state=RANDOM_SEED, n_jobs=-1, **RF)


def run(out_path=OUT):
    d = prepare()
    groups = np.array([chemical_system(f) for f in d["j_formulas"]])
    train, test = grouped_train_test_split(len(groups), groups)
    sets = {"composition": (d["j_comp"], d["o_comp"]),
            "structure": (np.hstack([d["j_comp"], d["j_struct"]]), np.hstack([d["o_comp"], d["o_struct"]]))}
    rows, importances = [], {}
    for name, (Xj, Xo) in sets.items():
        model = rf().fit(Xj[train], d["j_gap"][train])
        rows.append({"features": name, **report("jarvis_test", d["j_gap"][test], model.predict(Xj[test]))})
        rows.append({"features": name, **report("oqmd_unseen", d["o_gap"], model.predict(Xo))})
        if name == "structure":
            names = list(range(Xj.shape[1]))
            top = np.argsort(-model.feature_importances_)[:8]
            from ml.representation.material_representation import all_feature_names
            labels = all_feature_names(True) + STRUCTURE_NAMES
            importances = {labels[i]: round(float(model.feature_importances_[i]), 4) for i in top}
        print(rows[-2], "\n", rows[-1], flush=True)
    out = {"rows": rows, "top_structure_model_features": importances,
           "sizes": {"jarvis_train": int(len(train)), "jarvis_test": int(len(test)), "oqmd_unseen": int(len(d["o_gap"]))}}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    return out
