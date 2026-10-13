"""Extra composition features aimed at wide-gap (ionic, anion-rich) compounds.

The 63 Magpie-style statistics describe element properties averaged over a formula, but not how much of it
is anion: wide-gap compounds are mostly oxides, fluorides, and chlorides. These add anion fractions by
family, ionic character from the electronegativity spread, and the d- and f-block share (partly filled d and
f shells keep gaps small).
"""
import math

import numpy as np
from pymatgen.core import Composition, Element

HALOGENS = {"F", "Cl", "Br", "I"}
CHALCOGENS = {"S", "Se", "Te"}
PNICTOGENS = {"N", "P", "As"}
EXTRA_NAMES = ["frac_oxygen", "frac_halogen", "frac_chalcogen", "frac_pnictogen", "frac_anion",
               "ionic_character", "frac_d_block", "frac_f_block"]


def _block_flags(symbol):
    z = Element(symbol).Z
    d_block = 21 <= z <= 30 or 39 <= z <= 48 or 72 <= z <= 80
    f_block = 57 <= z <= 71 or 89 <= z <= 103
    return d_block, f_block


def extra_vector(formula):
    comp = Composition(formula).fractional_composition
    frac = {e.symbol: comp.get_atomic_fraction(e) for e in comp.elements}
    oxygen = frac.get("O", 0.0)
    halogen = sum(v for k, v in frac.items() if k in HALOGENS)
    chalcogen = sum(v for k, v in frac.items() if k in CHALCOGENS)
    pnictogen = sum(v for k, v in frac.items() if k in PNICTOGENS)
    x = [Element(k).X for k in frac if not math.isnan(Element(k).X)]
    spread = (max(x) - min(x)) if x else 0.0
    d_share = sum(v for k, v in frac.items() if _block_flags(k)[0])
    f_share = sum(v for k, v in frac.items() if _block_flags(k)[1])
    return np.array([oxygen, halogen, chalcogen, pnictogen, oxygen + halogen + chalcogen + pnictogen,
                     1.0 - math.exp(-0.25 * spread ** 2), d_share, f_share])


def extra_matrix(formulas):
    return np.vstack([extra_vector(f) for f in formulas]) if len(formulas) else np.empty((0, len(EXTRA_NAMES)))
