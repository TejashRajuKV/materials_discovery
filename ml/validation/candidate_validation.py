"""Layered validation of a candidate: chemical -> stability -> model uncertainty -> property constraints."""
from ml.validation.chemical_validation import validate_composition
from ml.validation.stability_validation import validate_stability


def uncertainty_layer(prediction):
    # Low confidence is a warning, not a failure: it marks a prediction to check, and a spec that needs
    # certainty uses max_uncertainty to exclude it. Failing it hid every candidate under strict specs.
    conf = prediction["confidence"]
    status = {"high": "pass", "recorded": "pass", "medium": "warn", "low": "warn"}[conf]
    return {"layer": "uncertainty", "status": status,
            "checks": [{"name": "model_confidence", "ok": conf != "low", "detail": f"{conf} (std={prediction['uncertainty']})"}]}


def constraints_layer(constraint_result):
    ok = constraint_result["satisfied"]
    return {"layer": "property_constraints", "status": "pass" if ok else "fail", "checks": constraint_result["checks"]}


def validate_candidate(prediction, constraint_result):
    layers = [
        validate_composition(prediction["formula"]),
        validate_stability(prediction),
        uncertainty_layer(prediction),
        constraints_layer(constraint_result),
    ]
    statuses = [layer["status"] for layer in layers]
    overall = "fail" if "fail" in statuses else ("warn" if "warn" in statuses else "pass")
    return {"overall": overall, "layers": layers}
