"""Apply requirements + layered validation to predicted candidates."""
from ml.optimization.constraints import evaluate_constraints
from ml.validation.candidate_validation import validate_candidate


def filter_candidates(predictions, spec, keep_warnings=True):
    """Return (kept, stats). A candidate is kept iff every property constraint holds and
    validation has no failing layer (warnings optional)."""
    kept, stats = [], {"evaluated": len(predictions), "failed_constraints": 0, "failed_validation": 0}
    for p in predictions:
        if "error" in p:
            continue
        constraint_result = evaluate_constraints(p, spec)
        if not constraint_result["satisfied"]:
            stats["failed_constraints"] += 1
            continue
        validation = validate_candidate(p, constraint_result)
        if validation["overall"] == "fail" or (validation["overall"] == "warn" and not keep_warnings):
            stats["failed_validation"] += 1
            continue
        p["validation"] = validation
        kept.append(p)
    stats["kept"] = len(kept)
    return kept, stats
