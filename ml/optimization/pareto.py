"""Non-dominated sorting for minimisation objectives.

Vectorised with numpy: domination counts are computed in row chunks, then fronts are peeled off one
at a time. The pure-Python pairwise version took about 10 minutes for a few thousand candidates;
this runs in seconds, with the same ranks.
"""
import numpy as np

CHUNK = 1024  # rows compared at once; bounds the temporary (chunk, n, m) boolean arrays


def _dominates(a, b):
    """(k, n) boolean: row i of `a` dominates row j of `b` (<= in all objectives, < in at least one)."""
    le = (a[:, None, :] <= b[None, :, :]).all(axis=2)
    lt = (a[:, None, :] < b[None, :, :]).any(axis=2)
    return le & lt


def non_dominated_ranks(points):
    """Rank 0 = Pareto front, 1 = front after removing rank 0, etc. points: (n, m), minimise all."""
    pts = np.asarray(points, float)
    n = len(pts)
    if n == 0:
        return []
    # counts[j] = number of points that dominate j
    counts = np.zeros(n, dtype=np.int64)
    for start in range(0, n, CHUNK):
        counts += _dominates(pts[start:start + CHUNK], pts).sum(axis=0)

    ranks = np.full(n, -1)
    front = np.flatnonzero(counts == 0)
    rank = 0
    while front.size:
        ranks[front] = rank
        # Removing this front lowers the domination count of everything it dominates.
        for start in range(0, front.size, CHUNK):
            block = front[start:start + CHUNK]
            counts -= _dominates(pts[block], pts).sum(axis=0)
        front = np.flatnonzero((counts == 0) & (ranks == -1))
        rank += 1
    return ranks.tolist()
