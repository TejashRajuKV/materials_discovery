"""Independent external validation: the band-gap model against OQMD band gaps.

The deployed model trains on JARVIS plus the Materials Project formulas JARVIS lacks, so neither source can
test it. OQMD is a third source. Only OQMD formulas absent from both training sources are scored, so the
model has seen neither the formula nor its label.

OQMD records carry no formula field, so each is derived from the structure's elements. Entries sharing a
formula (polymorphs) are summarised by their median gap, as in the other tables. OQMD gaps come from its own
DFT calculations (PBE-based), so method differences from JARVIS's OptB88vdW still apply; the shared-formula
comparison reports how large they are.

The 450 MB JSON is streamed, so it never has to fit in memory.
"""
import json
from collections import Counter
from statistics import median

import numpy as np
import pandas as pd
from pymatgen.core import Composition

from ml.config import DATA_PROCESSED, DATA_RAW, EXPERIMENTS_DIR, TRAINING_FILE
from ml.evaluation.metrics import regression_metrics
from ml.preprocessing.mp_augment import load_mp_gaps
from ml.validation.external import iter_json_array
from ml.validation.external_benchmark import RANGES, _by_range

OQMD_FILE = DATA_RAW / "oqmd" / "all_oqmd.json"
OUT_FILE = EXPERIMENTS_DIR / "external" / "oqmd_validation.json"
MAX_SKIPPED_FRACTION = 0.2


def oqmd_gaps(path=OQMD_FILE):
    """formula -> median OQMD band gap, plus how many records were read and skipped."""
    gaps, read, skipped = {}, 0, 0
    for record in iter_json_array(path):
        read += 1
        gap = record.get("_oqmd_band_gap")
        elements = (record.get("atoms") or {}).get("elements")
        if gap is None or elements is None or not np.isfinite(gap) or gap < 0:
            skipped += 1
            continue
        try:
            # OQMD symbols carry a trailing space ("Mn "), which pymatgen rejects.
            formula = Composition(dict(Counter(e.strip() for e in elements))).reduced_formula
        except Exception:
            skipped += 1
            continue
        gaps.setdefault(formula, []).append(float(gap))
    if read and skipped / read > MAX_SKIPPED_FRACTION:
        # A parsing problem would otherwise look like an empty or tiny result.
        raise ValueError(f"{skipped} of {read} OQMD records could not be read; check the file format")
    return {f: median(v) for f, v in gaps.items()}, read, skipped


OQMD_CACHE = DATA_PROCESSED / "oqmd_gaps.csv"


def load_oqmd_gaps():
    """formula -> median OQMD gap, cached as CSV after the first (slow) read of the 450 MB file."""
    if not OQMD_CACHE.exists():
        gaps, _, _ = oqmd_gaps()
        OQMD_CACHE.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"formula": list(gaps), "oqmd_gap": list(gaps.values())}).to_csv(OQMD_CACHE, index=False)
    table = pd.read_csv(OQMD_CACHE, keep_default_na=False)
    return dict(zip(table["formula"], table["oqmd_gap"].astype(float)))


def unseen_formulas(oqmd):
    """OQMD formulas absent from both training sources (JARVIS and Materials Project), sorted."""
    jarvis = set(pd.read_csv(DATA_PROCESSED / TRAINING_FILE, keep_default_na=False)["formula"])
    return sorted(set(oqmd) - jarvis - set(load_mp_gaps()["formula"]))


def run_benchmark(oqmd_path=OQMD_FILE, out_path=OUT_FILE):
    from ml.prediction.predict import load_bundle, predict_many

    oqmd, read, skipped = oqmd_gaps(oqmd_path)
    jarvis = pd.read_csv(DATA_PROCESSED / TRAINING_FILE, keep_default_na=False)
    jarvis_gap = dict(zip(jarvis["formula"], jarvis["band_gap"].astype(float)))
    seen = set(jarvis_gap) | set(load_mp_gaps()["formula"])

    shared = sorted(set(oqmd) & set(jarvis_gap))
    method = {"formulas": len(shared)}
    if shared:
        jv = np.array([jarvis_gap[f] for f in shared])
        oq = np.array([oqmd[f] for f in shared])
        method.update({
            "mae_jarvis_vs_oqmd": round(float(np.mean(np.abs(jv - oq))), 4),
            "mean_difference_jarvis_minus_oqmd": round(float(np.mean(jv - oq)), 4),
            "pearson_r": round(float(np.corrcoef(jv, oq)[0, 1]), 4),
        })

    novel = sorted(set(oqmd) - seen)
    bundle = load_bundle()
    preds = predict_many(novel, bundle)
    rows = [(oqmd[p["formula"]], p) for p in preds if "error" not in p]
    y = np.array([r[0] for r in rows])
    pred = np.array([r[1]["prediction"] for r in rows])
    lo = np.array([r[1]["interval_low"] for r in rows])
    hi = np.array([r[1]["interval_high"] for r in rows])
    metrics = {k: round(float(v), 4) for k, v in regression_metrics(y, pred).items() if k != "n"}
    # Most unseen OQMD formulas are metals, which are easy (zero gap), so also report non-metals alone.
    nm = y > 0
    nonmetal = {
        "formulas": int(nm.sum()),
        "metrics": {k: round(float(v), 4) for k, v in regression_metrics(y[nm], pred[nm]).items() if k != "n"},
        "interval_coverage_90": round(float(np.mean((y[nm] >= lo[nm]) & (y[nm] <= hi[nm]))), 4),
    }
    result = {
        "model_version": bundle["metadata"]["version"],
        "oqmd_records_read": read,
        "oqmd_records_skipped": skipped,
        "oqmd_formulas_with_gap": len(oqmd),
        "method_agreement_on_formulas_shared_with_jarvis": method,
        "unseen_formulas": {
            "formulas": len(rows),
            "metrics": metrics,
            "interval_coverage_90": round(float(np.mean((y >= lo) & (y <= hi))), 4),
            "by_gap_range": _by_range(y, pred),
            "fraction_zero_gap": round(float(np.mean(y == 0)), 4),
            "nonmetals_only": nonmetal,
        },
        "note": "Formulas absent from JARVIS and Materials Project, both of which the model trains on.",
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    return result
