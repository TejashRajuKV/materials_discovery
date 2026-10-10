"""Attributes of known materials, read from the stability table built by `preprocess`.

Each formula maps to its most stable JARVIS polymorph: energy above the hull, dimensionality, and
crystal system. Generated candidates are not in this table, so they have no attributes.
"""
import pandas as pd

from ml.config import DATA_PROCESSED, STABILITY_FILE
from ml.representation.crystal_system import crystal_system


def load_known_lookup(path=DATA_PROCESSED / STABILITY_FILE):
    """formula -> {ehull, dimensionality, crystal_system}. Empty when the table has not been built."""
    if not path.exists():
        return {}
    table = pd.read_csv(path, dtype={"formula": str, "dimensionality": str, "spg_number": str},
                        keep_default_na=False)
    lookup = {}
    for row in table.itertuples(index=False):
        lookup[row.formula] = {
            "ehull": float(row.ehull),
            "dimensionality": row.dimensionality or None,
            "crystal_system": crystal_system(row.spg_number),
        }
    return lookup


def load_property_records(prop, directory=DATA_PROCESSED / "properties"):
    """formula -> recorded value of a non-band-gap property (most stable JARVIS entry). Empty when the
    property table has not been built."""
    path = directory / f"{prop}.csv"
    if not path.exists():
        return {}
    table = pd.read_csv(path, dtype={"formula": str})
    return dict(zip(table["formula"], table["value"].astype(float)))
