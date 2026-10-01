"""material -> representation -> numerical features."""
import numpy as np
import pandas as pd

from ml.representation.composition_features import MAX_Z, composition_vector, feature_names


class InvalidMaterialError(ValueError):
    pass


def parse_formula(formula):
    from pymatgen.core import Composition, Element

    try:
        comp = Composition(str(formula).strip())
    except Exception as exc:
        raise InvalidMaterialError(f"cannot parse formula {formula!r}") from exc
    if comp.num_atoms <= 0 or not comp.elements:
        raise InvalidMaterialError(f"empty composition: {formula!r}")
    unsupported = [str(e) for e in comp.elements if not isinstance(e, Element) or e.Z > MAX_Z]
    if unsupported:
        raise InvalidMaterialError(f"unsupported elements {unsupported} in {formula!r} (H..Pu only)")
    return comp


def featurize(formula):
    return composition_vector(parse_formula(formula))


def featurize_many(formulas):
    """DataFrame of features, one row per formula (raises InvalidMaterialError on bad input)."""
    rows = np.vstack([featurize(f) for f in formulas]) if len(formulas) else np.empty((0, len(feature_names())))
    return pd.DataFrame(rows, columns=feature_names())


def chemical_system(formula):
    """Sorted element set, e.g. 'Fe-O'. Used to group data so CV does not leak near-duplicates."""
    return "-".join(sorted(el.symbol for el in parse_formula(formula).elements))
