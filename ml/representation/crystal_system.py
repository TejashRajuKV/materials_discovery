"""Space-group number (1-230) -> crystal system, using the standard International Tables ranges."""

CRYSTAL_SYSTEMS = ("triclinic", "monoclinic", "orthorhombic", "tetragonal", "trigonal", "hexagonal", "cubic")

_RANGES = (
    (1, 2, "triclinic"),
    (3, 15, "monoclinic"),
    (16, 74, "orthorhombic"),
    (75, 142, "tetragonal"),
    (143, 167, "trigonal"),
    (168, 194, "hexagonal"),
    (195, 230, "cubic"),
)


def crystal_system(spg_number):
    """Return the crystal system for a space-group number, or None when it is not a valid number."""
    try:
        n = int(float(spg_number))
    except (TypeError, ValueError):
        return None
    for low, high, name in _RANGES:
        if low <= n <= high:
            return name
    return None
