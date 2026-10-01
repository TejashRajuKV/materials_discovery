# Data dictionary

| Column | Type | Meaning |
| --- | --- | --- |
| `formula` | str | Reduced chemical formula (pymatgen canonical form). Unique after cleaning. |
| `band_gap` | float, eV | Target. ≥ 0; 0 means metallic/zero gap. |
| `source` | str | Provenance of the row (`synthetic_demo` for the placeholder set). |

Derived features (63): for each of 12 elemental properties (Z, Pauling electronegativity, atomic mass,
atomic radius, row, group, Mendeleev number, melting point, electron affinity, ionization energy,
molar volume, average ionic radius) the fraction-weighted **mean, mean absolute deviation, min, max,
range**, plus `n_elements`, `max_fraction`, `fraction_l2`. Missing elemental values are imputed with
the column mean over elements.
