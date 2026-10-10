"""End-to-end discovery: known materials + generated candidates -> predict -> filter -> rank."""
import pandas as pd

from ml.config import DATA_PROCESSED, TARGET, TARGET_UNIT, TRAINING_FILE
from ml.discovery.candidate_filter import filter_candidates
from ml.discovery.candidate_generation import generate_by_substitution
from ml.discovery.charge_balance import save_cache
from ml.discovery.known_lookup import load_known_lookup, load_property_records
from ml.explainability.prediction_explanation import explain
from ml.optimization.constraints import RANGE_PROPERTIES, normalize_spec
from ml.optimization.multi_objective import rank_candidates
from ml.prediction.predict import load_bundle, predict_many
from ml.training.property_models import predict_property_many


def _requested_properties(spec):
    return [p for p in RANGE_PROPERTIES if spec.get(p)]


def _known_as_predictions(df, known, records):
    """Known materials carry a recorded value (uncertainty 0), not a model prediction."""
    out = []
    for r in df.itertuples():
        attrs = known.get(r.formula, {})
        candidate = {
            "input": r.formula, "formula": r.formula, "property": TARGET, "unit": TARGET_UNIT,
            "prediction": float(getattr(r, TARGET)), "uncertainty": 0.0, "confidence": "recorded",
            "origin": "known", "ehull": attrs.get("ehull"),
            "dimensionality": attrs.get("dimensionality"), "crystal_system": attrs.get("crystal_system"),
        }
        properties = {}
        for prop, table in records.items():
            if r.formula in table:
                properties[prop] = {"value": table[r.formula], "uncertainty": 0.0, "source": "recorded"}
        if properties:
            candidate["properties"] = properties
        out.append(candidate)
    return out


def run_discovery(spec, generate=True, include_known=True, max_generated=1500, top_k=25, explain_top=5):
    spec = normalize_spec(spec)
    props = _requested_properties(spec)
    bundle = load_bundle()
    known_df = pd.read_csv(DATA_PROCESSED / TRAINING_FILE)
    records = {p: load_property_records(p) for p in props}

    pool = []
    if include_known:
        pool += _known_as_predictions(known_df, load_known_lookup(), records)
    n_generated = 0
    if generate:
        novel = generate_by_substitution(known_df["formula"].tolist(), limit=max_generated)
        preds = predict_many(novel, bundle)
        for p in preds:
            p["origin"] = "generated"
        for prop in props:
            # Same order as `novel`, so position i of each result belongs to preds[i].
            for p, q in zip(preds, predict_property_many(prop, novel)):
                if "error" in p or "error" in q:
                    continue
                p.setdefault("properties", {})[prop] = {
                    "value": q["prediction"], "uncertainty": q["uncertainty"], "source": "predicted",
                    "interval_low": q["interval_low"], "interval_high": q["interval_high"],
                }
        pool += preds
        n_generated = len(novel)

    kept, stats = filter_candidates(pool, spec)

    # Known entries have a recorded value (uncertainty 0); ranking them against model
    # predictions would be unfair, so each origin is ranked on its own.
    result = {}
    for origin, key in (("known", "known_matches"), ("generated", "novel_candidates")):
        ranked = rank_candidates([c for c in kept if c["origin"] == origin], spec, weights=spec.get("weights"))
        top = ranked[:top_k]
        for c in top[:explain_top]:
            c["explanation"] = explain(c["formula"], bundle)
        result[key] = top
        stats[f"{origin}_kept"] = len(ranked)
        stats[f"{origin}_pareto_front_size"] = sum(1 for c in ranked if c["pareto_rank"] == 0)

    stats.update({"known_considered": int(len(known_df)) if include_known else 0, "generated_considered": n_generated})
    save_cache()
    return {"spec": spec, "stats": stats, "model_version": bundle["metadata"]["version"], **result}
