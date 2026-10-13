"""Structure-based descriptors from a crystal structure: packing, lattice shape, and bonding.

These need an atomic structure, so they apply to materials that have one (known JARVIS/OQMD entries, or a
structure supplied or generated later). Compositions alone, such as the substitution candidates, have none.

Bonds are nearest-neighbour contacts: for each site, the neighbours within 1.25 times its nearest-neighbour
distance. Bond ionicity (the electronegativity difference across bonds) is the descriptor most directly tied
to the size of a band gap.
"""
import math

import numpy as np
from pymatgen.core import Element, Lattice, Structure

BOND_TOLERANCE = 1.25   # a contact counts as a bond if within this factor of the site's shortest contact
NEIGHBOUR_CUTOFF = 6.0  # angstrom; far enough to find a nearest neighbour in sparse cells
STRUCTURE_NAMES = [
    "n_sites", "volume_per_atom", "density", "packing_fraction",
    "lattice_ratio_b_a", "lattice_ratio_c_a", "angle_deviation",
    "nn_distance_mean", "nn_distance_min", "nn_distance_std", "nn_to_radii_ratio",
    "coordination_mean", "coordination_std", "coordination_max",
    "bond_dX_mean", "bond_dX_max", "bond_hetero_fraction",
]

_FALLBACK_RADIUS = 1.5
_radius_cache, _x_cache = {}, {}


def _radius(symbol):
    if symbol not in _radius_cache:
        r = Element(symbol).atomic_radius
        _radius_cache[symbol] = float(r) if r is not None and not math.isnan(float(r)) else _FALLBACK_RADIUS
    return _radius_cache[symbol]


def _electronegativity(symbol):
    if symbol not in _x_cache:
        x = Element(symbol).X
        _x_cache[symbol] = 0.0 if x is None or math.isnan(float(x)) else float(x)
    return _x_cache[symbol]


def build_structure(lattice_mat, coords, elements, cartesian=False):
    """pymatgen Structure from the lists stored in the processed JSON files. Symbols are stripped, since
    OQMD writes them with a trailing space."""
    return Structure(Lattice(lattice_mat), [e.strip() for e in elements], coords, coords_are_cartesian=bool(cartesian))


def structure_vector(structure):
    """The STRUCTURE_NAMES descriptors for one structure."""
    n = len(structure)
    volume = structure.volume
    symbols = [site.specie.symbol for site in structure]
    atomic_volume = sum(4.0 / 3.0 * math.pi * _radius(s) ** 3 for s in symbols)
    a, b, c = sorted(structure.lattice.abc)
    angles = structure.lattice.angles

    nn_distances, ratios, coordination, dx, hetero = [], [], [], [], 0
    bonds = 0
    for i, neighbours in enumerate(structure.get_all_neighbors(NEIGHBOUR_CUTOFF)):
        if not neighbours:
            continue
        nearest = min(nb.nn_distance for nb in neighbours)
        nn_distances.append(nearest)
        bonded = [nb for nb in neighbours if nb.nn_distance <= BOND_TOLERANCE * nearest]
        coordination.append(len(bonded))
        closest = min(bonded, key=lambda nb: nb.nn_distance)
        ratios.append(nearest / (_radius(symbols[i]) + _radius(closest.specie.symbol)))
        for nb in bonded:
            j = nb.specie.symbol
            dx.append(abs(_electronegativity(symbols[i]) - _electronegativity(j)))
            hetero += j != symbols[i]
            bonds += 1
    if not nn_distances:  # no contact within the cutoff: an isolated atom or a very sparse cell
        nn_distances, ratios, coordination, dx = [NEIGHBOUR_CUTOFF], [1.0], [0], [0.0]
    return np.array([
        n, volume / n, structure.density, atomic_volume / volume,
        b / a, c / a, float(np.mean(np.abs(np.array(angles) - 90.0))),
        np.mean(nn_distances), np.min(nn_distances), np.std(nn_distances), np.mean(ratios),
        np.mean(coordination), np.std(coordination), np.max(coordination),
        np.mean(dx), np.max(dx), (hetero / bonds) if bonds else 0.0,
    ], dtype=float)


def structure_matrix(structures):
    return np.vstack([structure_vector(s) for s in structures]) if len(structures) else np.empty((0, len(STRUCTURE_NAMES)))
