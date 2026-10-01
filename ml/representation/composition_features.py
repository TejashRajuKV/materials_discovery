"""Composition-based features: Magpie-style statistics over elemental properties."""
import math
import warnings
from functools import lru_cache

import numpy as np

warnings.filterwarnings("ignore", message="No Pauling electronegativity")
warnings.filterwarnings("ignore", message="No data available")

MAX_Z = 94  # H..Pu
ELEMENT_PROPERTIES = [
    "Z",
    "X",  # Pauling electronegativity
    "atomic_mass",
    "atomic_radius",
    "row",
    "group",
    "mendeleev_no",
    "melting_point",
    "electron_affinity",
    "ionization_energy",
    "molar_volume",
    "average_ionic_radius",
]
STATS = ("mean", "dev", "min", "max", "range")


@lru_cache(maxsize=1)
def _property_table():
    """(MAX_Z+1, n_props) array indexed by atomic number; NaNs imputed with the column mean."""
    from pymatgen.core import Element

    table = np.full((MAX_Z + 1, len(ELEMENT_PROPERTIES)), np.nan)
    for z in range(1, MAX_Z + 1):
        el = Element.from_Z(z)
        for j, prop in enumerate(ELEMENT_PROPERTIES):
            try:
                value = getattr(el, prop)
                value = float(value) if value is not None else math.nan
            except Exception:
                value = math.nan
            table[z, j] = value
    col_means = np.nanmean(table[1:], axis=0)
    for j in range(table.shape[1]):
        nan_rows = np.isnan(table[:, j])
        nan_rows[0] = False
        table[nan_rows, j] = col_means[j]
    table[0] = col_means
    return table


def feature_names():
    names = [f"{stat}_{prop}" for prop in ELEMENT_PROPERTIES for stat in STATS]
    return names + ["n_elements", "max_fraction", "fraction_l2"]


def composition_vector(composition):
    """Feature vector for a pymatgen Composition (fraction-weighted statistics)."""
    table = _property_table()
    comp = composition.fractional_composition
    zs = np.array([el.Z for el in comp.elements])
    fracs = np.array([comp.get_atomic_fraction(el) for el in comp.elements])
    props = table[zs]  # (n_el, n_props)

    mean = fracs @ props
    dev = fracs @ np.abs(props - mean)
    lo, hi = props.min(axis=0), props.max(axis=0)
    stats = np.stack([mean, dev, lo, hi, hi - lo], axis=1)  # (n_props, 5)

    extra = [len(zs), fracs.max(), float(np.linalg.norm(fracs))]
    return np.concatenate([stats.ravel(), extra])
