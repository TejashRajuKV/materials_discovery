"""Objective functions (all minimised) computed per candidate.

gap_distance : how far the predicted property is from the requested target
               (target if given, else the middle of [min, max], else 0).
uncertainty  : model uncertainty — prefer candidates we are surer about.
"""
from ml.config import TARGET


def gap_reference(spec):
    band = spec[TARGET]
    if "target" in band:
        return band["target"]
    if "min" in band and "max" in band:
        return (band["min"] + band["max"]) / 2
    return None


def compute_objectives(candidate, spec):
    ref = gap_reference(spec)
    distance = abs(candidate["prediction"] - ref) if ref is not None else 0.0
    return {"gap_distance": round(distance, 4), "uncertainty": candidate["uncertainty"]}


OBJECTIVE_NAMES = ("gap_distance", "uncertainty")
