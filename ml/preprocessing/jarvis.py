"""JARVIS band-gap target loader.

Joins the long-format targets file (one row per jid and DFT method) to the material table so
that each row is (formula, band_gap, source) for a single, named DFT method. Output has the same
columns `ml.preprocessing.cleaning.clean` expects, plus `jid` for traceability.
"""
import pandas as pd

from ml.config import JARVIS_BANDGAP_METHOD, JARVIS_MATERIALS_FILE, JARVIS_TARGETS_FILE, TARGET


def build_stability_table(materials_path=JARVIS_MATERIALS_FILE):
    """One row per formula, describing its most stable polymorph (lowest `ehull`, eV/atom):
    ehull, dimensionality, space group, and how many JARVIS entries share the formula.
    Entries without an `ehull` value are skipped; formulas that cannot be parsed are dropped."""
    from ml.preprocessing.cleaning import canonical_formula

    if not materials_path.exists():
        raise FileNotFoundError(f"{materials_path} not found; see load_jarvis_band_gap for how to create it.")
    m = pd.read_csv(materials_path, usecols=["jid", "formula", "ehull", "dimensionality", "spg_number", "spg_symbol"],
                    dtype={"jid": str, "formula": str, "dimensionality": str, "spg_symbol": str},
                    keep_default_na=False)
    m["ehull"] = pd.to_numeric(m["ehull"], errors="coerce")
    m = m.dropna(subset=["ehull"])
    m["formula"] = m["formula"].map(canonical_formula)
    m = m.dropna(subset=["formula"])
    counts = m.groupby("formula")["jid"].count().rename("n_entries")
    most_stable = m.sort_values(["ehull", "jid"]).drop_duplicates("formula", keep="first").set_index("formula")
    out = most_stable[["ehull", "dimensionality", "spg_number", "spg_symbol"]].join(counts).reset_index()
    return out.sort_values("formula").reset_index(drop=True)


def load_jarvis_band_gap(materials_path=JARVIS_MATERIALS_FILE, targets_path=JARVIS_TARGETS_FILE,
                         method=JARVIS_BANDGAP_METHOD):
    for path in (materials_path, targets_path):
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found. Download JARVIS dft_3d (`python scripts/data/download_jarvis.py dft_3d`) "
                "and convert it (`python scripts/data/to_csv.py dft_3d.json`)."
            )

    # 'formula' is read without NA parsing so no composition string is mistaken for a missing value.
    materials = pd.read_csv(materials_path, usecols=["jid", "formula"], dtype={"jid": str, "formula": str},
                            keep_default_na=False)
    targets = pd.read_csv(targets_path, dtype={"jid": str, "property": str, "method": str, "source": str})

    targets = targets[(targets["property"] == TARGET) & (targets["method"] == method)]
    if targets.empty:
        raise ValueError(f"no '{TARGET}' values for method '{method}' in {targets_path}")

    df = targets.merge(materials, on="jid", how="inner", validate="many_to_one")
    df = df.rename(columns={"value": TARGET})
    df = df[["formula", TARGET, "source", "jid"]].reset_index(drop=True)
    return df
