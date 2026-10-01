"""Non-dominated sorting for minimisation objectives."""
import numpy as np


def non_dominated_ranks(points):
    """Rank 0 = Pareto front, 1 = front after removing rank 0, etc. points: (n, m), minimise all."""
    pts = np.asarray(points, float)
    n = len(pts)
    ranks = np.full(n, -1)
    remaining = set(range(n))
    rank = 0
    while remaining:
        idx = sorted(remaining)
        front = [
            i for i in idx
            if not any(np.all(pts[j] <= pts[i]) and np.any(pts[j] < pts[i]) for j in idx if j != i)
        ]
        for i in front:
            ranks[i] = rank
            remaining.discard(i)
        rank += 1
    return ranks.tolist()
