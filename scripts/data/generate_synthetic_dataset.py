"""Generate a SYNTHETIC demo dataset (formula, band_gap).

!! These are NOT measured or DFT values. !!
Band gaps come from a crude electronegativity/ionicity heuristic plus noise, so the
pipeline, API and UI can run end to end without network access to a real database.
Any scientific claim requires replacing this with real data (see docs/datasets/).
"""
import itertools
import random
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from pymatgen.core import Composition, Element

from ml.config import DATA_RAW, RANDOM_SEED

CATIONS = ["Li", "Na", "K", "Rb", "Mg", "Ca", "Sr", "Ba", "Al", "Ga", "In", "Sc", "Y", "La",
           "Ti", "Zr", "Hf", "V", "Nb", "Ta", "Cr", "Mo", "W", "Mn", "Fe", "Co", "Ni", "Cu",
           "Zn", "Cd", "Ag", "Sn", "Pb", "Sb", "Bi", "Ge", "Si"]
ANIONS = ["O", "S", "Se", "Te", "F", "Cl", "Br", "I", "N", "P", "As"]
TARGET_ROWS = 2500


def synthetic_band_gap(comp, rng):
    anions = [e for e in comp.elements if e.symbol in ANIONS]
    cations = [e for e in comp.elements if e.symbol not in ANIONS]
    if not anions or not cations:
        return 0.0
    f = comp.fractional_composition
    x_an = sum(e.X * f.get_atomic_fraction(e) for e in anions) / sum(f.get_atomic_fraction(e) for e in anions)
    x_ca = sum(e.X * f.get_atomic_fraction(e) for e in cations) / sum(f.get_atomic_fraction(e) for e in cations)
    ionicity = max(x_an - x_ca, 0.0)
    gap = 1.9 * ionicity ** 1.25 - 0.35 * (anions[0].row - 2)
    tm_fraction = sum(f.get_atomic_fraction(e) for e in cations if e.is_transition_metal)
    gap -= 1.6 * tm_fraction
    gap += rng.normal(0, 0.2)
    return float(max(gap, 0.0))


def main(out_path=None, rows=TARGET_ROWS):
    rng = np.random.default_rng(RANDOM_SEED)
    pyrng = random.Random(RANDOM_SEED)
    seen, rows, n_rows = set(), [], rows
    attempts = 0
    while len(rows) < n_rows and attempts < 400000:
        attempts += 1
        n_cat = pyrng.choice([1, 1, 2])
        cats = pyrng.sample(CATIONS, n_cat)
        an = pyrng.choice(ANIONS)
        counts = {c: pyrng.randint(1, 3) for c in cats}
        counts[an] = pyrng.randint(1, 4)
        comp = Composition(counts)
        formula = comp.reduced_formula
        if formula in seen:
            continue
        try:
            if not comp.oxi_state_guesses():
                continue  # keep only charge-balanceable compositions
        except Exception:
            continue
        seen.add(formula)
        rows.append({"formula": formula, "band_gap": round(synthetic_band_gap(comp, rng), 3),
                     "source": "synthetic_demo"})

    df = pd.DataFrame(rows)
    out = Path(out_path) if out_path else DATA_RAW / "synthetic_demo.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"wrote {len(df)} synthetic rows to {out}", file=sys.stderr)
    return out


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None, int(sys.argv[2]) if len(sys.argv) > 2 else TARGET_ROWS)
