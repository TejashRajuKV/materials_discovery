"""Charge-balance checks for compositions, cached on disk.

pymatgen's oxidation-state search is accurate but takes about 30 ms per composition, and discovery
asks about the same known materials and generated formulas on every run. Results are therefore cached
in a JSON file keyed by reduced formula: whether a charge-neutral assignment exists, and one example.

Two uses:
  - generation drops anion-containing candidates that cannot balance (intermetallics are not checked,
    since metallic compounds are not charge-balanced in the ionic sense and the target includes metals);
  - the chemical validation layer reports balance and an example assignment for every candidate.
"""
import json

from pymatgen.core import Composition

from ml.config import DATA_PROCESSED

ANION_ELEMENTS = {"F", "Cl", "Br", "I", "O", "S", "Se", "Te", "N", "P", "As"}
CACHE_FILE = DATA_PROCESSED / "charge_state_cache.json"

_cache = None
_dirty = False


def _load():
    global _cache
    if _cache is None:
        _cache = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
    return _cache


def save_cache():
    """Write the cache if it changed. Called after each generation or validation batch."""
    global _dirty
    if _cache is not None and _dirty:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(_cache))
        _dirty = False


def charge_state(composition):
    """(balanced, example) for a pymatgen Composition. `example` is one charge-neutral assignment
    such as 'Na+1, Cl-1', or '' when none exists."""
    global _dirty
    key = composition.reduced_formula
    cache = _load()
    if key not in cache:
        guesses = composition.oxi_state_guesses()
        example = ", ".join(f"{k}{v:+g}" for k, v in guesses[0].items()) if guesses else ""
        cache[key] = [bool(guesses), example]
        _dirty = True
    balanced, example = cache[key]
    return balanced, example


def is_charge_balanceable(formula):
    """Generation filter: anion-containing compositions must balance; intermetallics always pass."""
    comp = Composition(formula)
    if not {e.symbol for e in comp.elements} & ANION_ELEMENTS:
        return True
    return charge_state(comp)[0]
