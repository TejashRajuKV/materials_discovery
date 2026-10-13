import numpy as np
import pytest
from pymatgen.core import Lattice, Structure

from ml.representation.structure_features import STRUCTURE_NAMES, build_structure, structure_matrix, structure_vector


def _named(structure):
    return dict(zip(STRUCTURE_NAMES, structure_vector(structure)))


def test_rock_salt_has_six_heteropolar_bonds_at_half_the_cell_edge():
    nacl = Structure.from_spacegroup("Fm-3m", Lattice.cubic(5.64), ["Na", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]])
    f = _named(nacl)
    assert f["n_sites"] == 8
    assert f["volume_per_atom"] == pytest.approx(5.64 ** 3 / 8)
    assert f["nn_distance_mean"] == pytest.approx(2.82, abs=0.01) and f["nn_distance_std"] < 1e-6
    assert f["coordination_mean"] == 6 and f["coordination_max"] == 6
    assert f["bond_hetero_fraction"] == 1.0
    assert f["bond_dX_mean"] == pytest.approx(3.16 - 0.93, abs=0.01)  # Pauling Cl minus Na
    assert f["lattice_ratio_b_a"] == pytest.approx(1.0) and f["angle_deviation"] == pytest.approx(0.0)


def test_fcc_metal_has_twelve_identical_bonds_and_no_ionicity():
    cu = Structure.from_spacegroup("Fm-3m", Lattice.cubic(3.61), ["Cu"], [[0, 0, 0]])
    f = _named(cu)
    assert f["coordination_mean"] == 12
    assert f["bond_hetero_fraction"] == 0.0 and f["bond_dX_mean"] == 0.0 and f["bond_dX_max"] == 0.0
    assert f["packing_fraction"] > 0.5


def test_build_structure_handles_oqmd_trailing_spaces_and_fractional_or_cartesian_coordinates():
    lattice = [[5.64, 0, 0], [0, 5.64, 0], [0, 0, 5.64]]
    frac = build_structure(lattice, [[0, 0, 0], [0.5, 0.5, 0.5]], ["Na ", "Cl "], cartesian=False)
    cart = build_structure(lattice, [[0, 0, 0], [2.82, 2.82, 2.82]], ["Na", "Cl"], cartesian=True)
    assert np.allclose(structure_vector(frac), structure_vector(cart))


def test_matrix_shape_is_finite_and_empty_input_is_handled():
    nacl = Structure.from_spacegroup("Fm-3m", Lattice.cubic(5.64), ["Na", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]])
    sparse = Structure(Lattice.cubic(30.0), ["He"], [[0, 0, 0]])  # nothing within the cutoff
    m = structure_matrix([nacl, sparse])
    assert m.shape == (2, len(STRUCTURE_NAMES)) and np.isfinite(m).all()
    assert structure_matrix([]).shape == (0, len(STRUCTURE_NAMES))
