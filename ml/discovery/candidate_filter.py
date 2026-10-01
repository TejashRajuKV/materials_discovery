"""Requirement filtering (cheap, applied to everything) and layered validation (expensive,
applied lazily to ranked candidates only)."""
from ml.optimization.constraints import evaluate_constraints
from ml.validation.candidate_validation import validate_candidate


def filter_by_constraints(predictions, spec):
    """Keep predictions that satisfy every requirement. Returns (kept, failed_count)."""
    kept, failed = [], 0
    for p in predictions:
        if "error" in p:
            continue
        result = evaluate_constraints(p, spec)
        if result["satisfied"]:
            p["_constraint_result"] = result
            kept.append(p)
        else:
            failed += 1
    return kept, failed


def validate_ranked(ranked, spec, limit, keep_warnings=True):
    """Walk candidates in rank order, validating each, until `limit` survive.

    Returns (survivors, n_failed_validation_checked). Re-numbers `rank` over survivors so ranks
    stay contiguous."""
    survivors, failed = [], 0
    for c in ranked:
        validation = validate_candidate(c, c.pop("_constraint_result"))
        if validation["overall"] == "fail" or (validation["overall"] == "warn" and not keep_warnings):
            failed += 1
            continue
        c["validation"] = validation
        survivors.append(c)
        if len(survivors) >= limit:
            break
    for i, c in enumerate(survivors, start=1):
        c["rank"] = i
    return survivors, failed
