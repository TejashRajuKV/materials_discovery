import numpy as np
import pytest

from ml.discovery.charge_balance import ANION_ELEMENTS, is_charge_balanceable
from ml.optimization.constraints import InvalidSpecError, normalize_spec
from ml.optimization.pareto import non_dominated_ranks
from ml.service import dispatch


def _reference_ranks(points):
    pts = np.asarray(points, float)
    n = len(pts)
    ranks = np.full(n, -1)
    remaining = set(range(n))
    rank = 0
    while remaining:
        idx = sorted(remaining)
        front = [i for i in idx
                 if not any(np.all(pts[j] <= pts[i]) and np.any(pts[j] < pts[i]) for j in idx if j != i)]
        for i in front:
            ranks[i] = rank
            remaining.discard(i)
        rank += 1
    return ranks.tolist()


@pytest.mark.parametrize("seed,integers", [(0, False), (1, True), (2, True)])
def test_vectorised_pareto_matches_pairwise_reference(seed, integers):
    rng = np.random.default_rng(seed)
    points = rng.integers(0, 5, size=(200, 2)).astype(float) if integers else rng.random((200, 2))
    assert non_dominated_ranks(points) == _reference_ranks(points)


def test_pareto_handles_empty_input():
    assert non_dominated_ranks(np.empty((0, 2))) == []


def test_charge_balance_applies_to_anion_compounds_only():
    assert is_charge_balanceable("NaCl") is True
    assert is_charge_balanceable("NaCl2") is False          # Na+ cannot balance two Cl- on its own
    assert is_charge_balanceable("GaAs") is True           # As gets a negative state with Ga
    assert is_charge_balanceable("EuInPd2") is True        # intermetallic: not checked
    assert "O" in ANION_ELEMENTS


def test_weights_are_normalised_and_validated():
    spec = normalize_spec({"band_gap": {"min": 1, "max": 2}, "weights": {"gap_distance": 3, "uncertainty": 1}})
    assert spec["weights"] == pytest.approx({"gap_distance": 0.75, "uncertainty": 0.25})
    assert normalize_spec({"band_gap": {"min": 1, "max": 2}})["weights"] is None
    for bad in ({"speed": 1}, {"gap_distance": -1}, {"gap_distance": 0, "uncertainty": 0}):
        with pytest.raises(InvalidSpecError):
            normalize_spec({"band_gap": {"min": 1, "max": 2}, "weights": bad})


def test_service_returns_structured_errors_without_models():
    assert dispatch("/nope", {})["error"] == "NotFound"
    doc = dispatch("/predict", {"formulas": ["NaCl"], "property": "hardness"})
    assert doc["error"] == "FileNotFoundError"
