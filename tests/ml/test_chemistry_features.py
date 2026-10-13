import numpy as np
import pytest

from ml.representation.chemistry_features import EXTRA_NAMES, extra_matrix, extra_vector


def test_oxide_fluoride_and_metal_get_sensible_values():
    nacl = dict(zip(EXTRA_NAMES, extra_vector("NaCl")))
    assert nacl["frac_halogen"] == pytest.approx(0.5) and nacl["frac_anion"] == pytest.approx(0.5)
    assert nacl["ionic_character"] > 0.5 and nacl["frac_d_block"] == 0

    mgo = dict(zip(EXTRA_NAMES, extra_vector("MgO")))
    assert mgo["frac_oxygen"] == pytest.approx(0.5)

    fe = dict(zip(EXTRA_NAMES, extra_vector("Fe")))
    assert fe["frac_anion"] == 0 and fe["frac_d_block"] == 1 and fe["ionic_character"] == 0

    ce2o3 = dict(zip(EXTRA_NAMES, extra_vector("Ce2O3")))
    assert ce2o3["frac_f_block"] == pytest.approx(0.4)


def test_matrix_shape_and_empty_input():
    assert extra_matrix(["NaCl", "MgO", "Fe"]).shape == (3, len(EXTRA_NAMES))
    assert extra_matrix([]).shape == (0, len(EXTRA_NAMES))
    assert np.isfinite(extra_matrix(["He", "NaCl"])).all()
