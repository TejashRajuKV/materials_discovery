"""Non-dominated sorting for minimisation objectives."""
from bisect import bisect_left

import numpy as np


def _ranks_2d(pts):
    """Exact O(n log n) fronts for two objectives (sorted sweep + binary search over fronts).

    Points are processed in lexicographic order; each front keeps its most recently added point,
    whose second objective is the smallest in that front. The smallest rank whose last point does
    not dominate p is p's rank. Identical vectors never dominate each other.
    """
    n = len(pts)
    order = np.lexsort((pts[:, 1], pts[:, 0]))
    ranks = np.empty(n, dtype=int)
    last = []  # last[r] = (f1, f2) of the most recent point in front r

    def dominated(r, p):
        q = last[r]
        return q[1] <= p[1] and not (q[0] == p[0] and q[1] == p[1])

    for i in order:
        p = (pts[i, 0], pts[i, 1])
        lo, hi = 0, len(last)
        while lo < hi:  # first front that does not dominate p (predicate is monotone in r)
            mid = (lo + hi) // 2
            if dominated(mid, p):
                lo = mid + 1
            else:
                hi = mid
        if lo == len(last):
            last.append(p)
        else:
            last[lo] = p
        ranks[i] = lo
    return ranks


def _ranks_general(pts):
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
    return ranks


def non_dominated_ranks(points):
    """Rank 0 = Pareto front, 1 = front after removing rank 0, etc. points: (n, m), minimise all."""
    pts = np.asarray(points, float)
    if len(pts) == 0:
        return []
    ranks = _ranks_2d(pts) if pts.shape[1] == 2 else _ranks_general(pts)
    return ranks.tolist()
