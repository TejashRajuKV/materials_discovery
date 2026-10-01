import numpy as np
import pytest

from ml.representation.composition_features import feature_names
from ml.representation.material_representation import (InvalidMaterialError, chemical_system, featurize,
                                                        featurize_many, parse_formula)


def test_feature_vector_shape_and_finite():
    x = featurize("LiFePO4")
    assert x.shape == (len(feature_names()),)
    assert np.isfinite(x).all()


def test_equivalent_formulas_give_same_features():
    assert np.allclose(featurize("Fe2O3"), featurize("Fe4O6"))


def test_known_physics_signal():
    names = feature_names()
    nacl, gaas = featurize("NaCl"), featurize("GaAs")
    i = names.index("range_X")
    assert nacl[i] > gaas[i]  # ionic compound has the larger electronegativity spread


@pytest.mark.parametrize("bad", ["", "Xx9", "not a formula", "Zz"])
def test_invalid_formulas_rejected(bad):
    with pytest.raises(InvalidMaterialError):
        parse_formula(bad)


def test_chemical_system_is_order_independent():
    assert chemical_system("LiFePO4") == chemical_system("PO4FeLi") == "Fe-Li-O-P"


def test_featurize_many_empty():
    assert featurize_many([]).shape == (0, len(feature_names()))
