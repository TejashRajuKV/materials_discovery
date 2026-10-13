"""Flag band-gap labels that are physically implausible.

A compound made only of metallic elements is an intermetallic, which is a metal with zero gap. A reported
gap of several eV for one is a calculation artefact, not a property to learn or to score against. OQMD
contains many such entries (for example AcLaNd with a gap above 11 eV), and they dominate its wide-gap error.
"""
import re
from functools import lru_cache

from pymatgen.core import Element

IMPLAUSIBLE_GAP_EV = 2.0  # an all-metal compound with a gap above this is treated as an artefact


@lru_cache(maxsize=None)
def _is_metal(symbol):
    try:
        return bool(Element(symbol).is_metal)
    except Exception:
        return False


def is_all_metal(formula):
    """True when every element in the formula is a metal (pymatgen's classification)."""
    symbols = set(re.findall(r"[A-Z][a-z]?", str(formula)))
    return bool(symbols) and all(_is_metal(s) for s in symbols)


def implausible_label(formula, gap, threshold=IMPLAUSIBLE_GAP_EV):
    """An all-metal compound reported with a gap above `threshold` eV."""
    return gap > threshold and is_all_metal(formula)
