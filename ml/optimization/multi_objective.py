"""Rank candidates by Pareto front, then by a normalised weighted sum within a front.

There is no single "best" material: rank-0 candidates are the trade-off frontier
between hitting the target and model certainty. The weighted score only orders ties.
"""
import numpy as np

from ml.optimization.objectives import OBJECTIVE_NAMES, compute_objectives
from ml.optimization.pareto import non_dominated_ranks


def rank_candidates(candidates, spec, weights=None):
    if not candidates:
        return []
    weights = weights or {"gap_distance": 0.7, "uncertainty": 0.3}
    for c in candidates:
        c["objectives"] = compute_objectives(c, spec)
    F = np.array([[c["objectives"][k] for k in OBJECTIVE_NAMES] for c in candidates])
    ranks = non_dominated_ranks(F)
    span = np.where(F.max(axis=0) - F.min(axis=0) > 0, F.max(axis=0) - F.min(axis=0), 1.0)
    norm = (F - F.min(axis=0)) / span
    for c, r, row in zip(candidates, ranks, norm):
        c["pareto_rank"] = int(r)
        c["score"] = round(float(1 - sum(weights[k] * v for k, v in zip(OBJECTIVE_NAMES, row))), 4)
    candidates.sort(key=lambda c: (c["pareto_rank"], -c["score"]))
    for i, c in enumerate(candidates, start=1):
        c["rank"] = i
    return candidates
