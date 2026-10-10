"""Controlled candidate generation by chemically-motivated element substitution.

Each known formula has one element swapped for a same-group element (or one with a
shared common oxidation state). Candidates must still pass validation and prediction;
generation only proposes, it never certifies.
"""
import random
from functools import lru_cache

from pymatgen.core import Composition, Element

from ml.config import RANDOM_SEED
from ml.representation.composition_features import MAX_Z


@lru_cache(maxsize=1)
def _partners():
    elements = [Element.from_Z(z) for z in range(1, MAX_Z + 1)]
    elements = [e for e in elements if not e.is_noble_gas and e.Z <= 83]
    partners = {}
    for e in elements:
        ox = set(e.common_oxidation_states)
        same = [
            o.symbol for o in elements
            if o.symbol != e.symbol and (
                (o.group == e.group and o.row != e.row) or (ox and ox & set(o.common_oxidation_states) and o.group == e.group)
            )
        ]
        partners[e.symbol] = same
    return partners


def generate_by_substitution(known_formulas, limit=2000, seed=RANDOM_SEED, charge_balanced=True):
    """Return novel reduced formulas (not in known_formulas), at most `limit`. With charge_balanced,
    anion-containing compositions that cannot balance their charges are dropped."""
    from ml.discovery.charge_balance import is_charge_balanceable, save_cache
    rng = random.Random(seed)
    known = set(known_formulas)
    partners = _partners()
    out = set()
    pool = list(known_formulas)
    rng.shuffle(pool)
    for formula in pool:
        comp = Composition(formula)
        for el in comp.elements:
            for new in partners.get(el.symbol, []):
                amounts = {(new if e.symbol == el.symbol else e.symbol): comp[e] for e in comp.elements}
                if len(amounts) < len(comp.elements):
                    continue  # substitution collapsed two elements
                candidate = Composition(amounts).reduced_formula
                if candidate in known or candidate in out:
                    continue
                if charge_balanced and not is_charge_balanceable(candidate):
                    continue
                out.add(candidate)
        if len(out) >= limit:
            break
    save_cache()
    result = sorted(out)
    rng.shuffle(result)
    return result[:limit]
