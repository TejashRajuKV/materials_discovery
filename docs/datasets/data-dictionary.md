# Data dictionary

## Training table: `ml/data/processed/band_gap_training.csv`

| Column | Type | Meaning |
| --- | --- | --- |
| `formula` | str | Reduced chemical formula (pymatgen canonical form). Unique after cleaning. |
| `band_gap` | float, eV | Target: median OptB88vdW gap over the entries with this formula. ≥ 0; 0 means metallic. |
| `source` | str | Provenance (`JARVIS dft_3d`, or `synthetic_demo` for the opt-in placeholder). |
| `jid` | str | JARVIS identifier of the first entry kept for this formula. |

## Stability table: `ml/data/processed/stability.csv`

| Column | Type | Meaning |
| --- | --- | --- |
| `formula` | str | Reduced formula, as above. |
| `ehull` | float, eV/atom | Lowest energy above the convex hull across this formula's entries (0 = on the hull). |
| `n_entries` | int | Number of JARVIS entries with this formula that have an `ehull` value. |

## Source table: `ml/data/processed/materials.csv` (from `scripts/data/to_csv.py`)

One row per JARVIS entry: `jid`, `formula`, `nat`, `dimensionality`, `spg_number`, `spg_symbol`,
`density`, `formation_energy_peratom`, `ehull`, `magmom_*`, `func`, `icsd`. Missing values are empty cells
(the source encodes them as the string `na`).

## Derived features (63)

For each of 12 elemental properties (Z, Pauling electronegativity, atomic mass, atomic radius, row,
group, Mendeleev number, melting point, electron affinity, ionization energy, molar volume, average
ionic radius) the fraction-weighted **mean, mean absolute deviation, min, max, range**, plus
`n_elements`, `max_fraction`, `fraction_l2`. Missing elemental values are imputed with the column mean
over elements.

## Property table: `ml/data/processed/properties/<property>.csv`

| Column | Type | Meaning |
| --- | --- | --- |
| `formula` | str | Reduced formula, as above. |
| `value` | float | Formation energy (eV/atom) or bulk modulus (GPa) of the most stable entry that has a value. Bulk moduli ≤ 0 are excluded. |
| `ehull` | float, eV/atom | `ehull` of that entry, used to choose it. |
| `n_entries` | int | Number of JARVIS entries with this formula that have a value. |

## Database: `material_properties`

One row per (formula, property): `recorded` is the JARVIS value (NULL if none), and `predicted`, `uncertainty`,
`interval_low`, `interval_high` come from the property's model. `candidates.properties` stores the same
kind of values per discovery candidate, as JSON.
