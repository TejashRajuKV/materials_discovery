"""End-to-end discovery: known materials + generated candidates -> predict -> filter -> rank."""
import pandas as pd

from ml.config import DATA_PROCESSED, PROCESSED_FILE, TARGET, TARGET_UNIT
from ml.discovery.candidate_filter import filter_by_constraints, validate_ranked
from ml.discovery.candidate_generation import generate_by_substitution
from ml.explainability.prediction_explanation import explain
from ml.optimization.constraints import normalize_spec
from ml.optimization.multi_objective import rank_candidates
from ml.prediction.predict import load_bundle, predict_many


def _known_as_predictions(df):
    """Known materials carry a recorded value (uncertainty 0), not a model prediction."""
    return [
        {"input": r.formula, "formula": r.formula, "property": TARGET, "unit": TARGET_UNIT,
         "prediction": float(getattr(r, TARGET)), "uncertainty": 0.0, "confidence": "recorded",
         "origin": "known"}
        for r in df.itertuples()
    ]


def run_discovery(spec, generate=True, include_known=True, max_generated=1500, top_k=25, explain_top=5):
    spec = normalize_spec(spec)
    bundle = load_bundle()
    known_df = pd.read_csv(DATA_PROCESSED / PROCESSED_FILE)

    pool = []
    if include_known:
        pool += _known_as_predictions(known_df)
    n_generated = 0
    if generate:
        novel = generate_by_substitution(known_df["formula"].tolist(), limit=max_generated)
        preds = predict_many(novel, bundle)
        for p in preds:
            p["origin"] = "generated"
        pool += preds
        n_generated = len(novel)

    kept, failed_constraints = filter_by_constraints(pool, spec)
    stats = {"evaluated": len(pool), "failed_constraints": failed_constraints, "satisfied_requirements": len(kept),
             "failed_validation": 0}

    # Known entries have a recorded value (uncertainty 0); ranking them against model
    # predictions would be unfair, so each origin is ranked on its own. Ranking is cheap; the
    # chemistry validation is not, so it only runs down the ranking until top_k candidates pass.
    result = {}
    for origin, key in (("known", "known_matches"), ("generated", "novel_candidates")):
        ranked = rank_candidates([c for c in kept if c["origin"] == origin], spec)
        top, failed = validate_ranked(ranked, spec, top_k)
        for c in top[:explain_top]:
            c["explanation"] = explain(c["formula"], bundle)
        result[key] = top
        stats["failed_validation"] += failed
        stats[f"{origin}_kept"] = len(ranked)
        stats[f"{origin}_pareto_front_size"] = sum(1 for c in ranked if c["pareto_rank"] == 0)

    stats.update({"known_considered": int(len(known_df)) if include_known else 0, "generated_considered": n_generated})
    return {"spec": spec, "stats": stats, "model_version": bundle["metadata"]["version"], **result}
